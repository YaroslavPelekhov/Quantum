"""Run the frozen hardware model-witness Phase-0 falsification screen."""

from __future__ import annotations

import csv
import json
import platform
import random
import subprocess
import sys
from bisect import bisect_left
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.stats import beta

from witness_core import (
    Candidate,
    Witness,
    cyclic_shift_witness,
    enumerate_candidates,
    evaluate_witness,
    exhaustive_witness,
    gst_like_germ_baseline,
    matched_pair_count,
    validate_matching,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "hardware_model_witness_phase0"
LENGTHS = tuple(range(4, 9))
TRAIN_EPSILON = 0.02
TRAIN_DELTA = 0.01
RANDOM_BUDGETS = (16, 64, 256, 1024)
RANDOM_TRIALS = 128
RANDOM_SEED = 20260828
SHOTS = 10_000
FAMILY_ALPHA = 0.05


def candidate_record(candidate: Candidate) -> dict[str, object]:
    return {
        "sequence": list(candidate.sequence),
        "counts": list(candidate.counts),
        "p0": candidate.p0,
        "declared_p0": candidate.declared_p0,
    }


def witness_record(witness: Witness) -> dict[str, object]:
    return {
        "gap": witness.gap,
        "high": candidate_record(witness.high),
        "low": candidate_record(witness.low),
    }


def choose_group(rng: random.Random, groups, cumulative, total_pairs):
    draw = rng.randrange(total_pairs)
    index = bisect_left(cumulative, draw + 1)
    return groups[index]


def random_baseline(groups_map, optimum: float) -> list[dict[str, object]]:
    groups = list(groups_map.values())
    weights = [len(group) * (len(group) - 1) // 2 for group in groups]
    cumulative = np.cumsum(weights).tolist()
    total_pairs = cumulative[-1]
    trial_rows = []
    for trial in range(RANDOM_TRIALS):
        rng = random.Random(RANDOM_SEED + trial)
        running_best = 0.0
        snapshots = {}
        for query in range(1, max(RANDOM_BUDGETS) + 1):
            group = choose_group(rng, groups, cumulative, total_pairs)
            first, second = rng.sample(group, 2)
            running_best = max(running_best, abs(first.p0 - second.p0))
            if query in RANDOM_BUDGETS:
                snapshots[query] = running_best
        for budget in RANDOM_BUDGETS:
            trial_rows.append(
                {
                    "trial": trial,
                    "pair_budget": budget,
                    "best_gap": snapshots[budget],
                    "fraction_of_optimum": snapshots[budget] / optimum if optimum else 1.0,
                }
            )
    return trial_rows


def summarize_random(rows):
    summary = []
    for budget in RANDOM_BUDGETS:
        values = np.array([row["fraction_of_optimum"] for row in rows if row["pair_budget"] == budget])
        summary.append(
            {
                "pair_budget": budget,
                "median_fraction_of_optimum": float(np.median(values)),
                "p90_fraction_of_optimum": float(np.quantile(values, 0.9)),
                "success_rate_at_90_percent": float(np.mean(values >= 0.9)),
            }
        )
    return summary


def clopper_pearson(count: int, shots: int, interval_alpha: float) -> tuple[float, float]:
    lower = 0.0 if count == 0 else float(beta.ppf(interval_alpha / 2.0, count, shots - count + 1))
    upper = 1.0 if count == shots else float(beta.ppf(1.0 - interval_alpha / 2.0, count + 1, shots - count))
    return lower, upper


def shot_test(witness: Witness, hypotheses: int, shots: int) -> dict[str, object]:
    # Two simultaneous intervals per tested pair.
    interval_alpha = FAMILY_ALPHA / (2.0 * hypotheses)
    high_count = round(witness.high.p0 * shots)
    low_count = round(witness.low.p0 * shots)
    high_interval = clopper_pearson(high_count, shots, interval_alpha)
    low_interval = clopper_pearson(low_count, shots, interval_alpha)
    return {
        "shots_per_circuit": shots,
        "family_alpha": FAMILY_ALPHA,
        "hypotheses": hypotheses,
        "interval_alpha": interval_alpha,
        "expected_integer_counts": {"high": high_count, "low": low_count},
        "clopper_pearson": {"high": list(high_interval), "low": list(low_interval)},
        "intervals_separated": high_interval[0] > low_interval[1],
    }


def minimum_shots(witness: Witness, hypotheses: int, limit: int = 10_000_000) -> int | None:
    low = 100
    high = low
    while high <= limit and not shot_test(witness, hypotheses, high)["intervals_separated"]:
        high *= 2
    if high > limit:
        return None
    while low + 1 < high:
        middle = (low + high) // 2
        if shot_test(witness, hypotheses, middle)["intervals_separated"]:
            high = middle
        else:
            low = middle
    return high


def heldout_grid(witness: Witness) -> list[dict[str, object]]:
    rows = []
    for epsilon in (0.005, 0.01, 0.02, 0.04):
        for delta in (0.0, 0.005, 0.01, 0.02):
            if epsilon == TRAIN_EPSILON and delta == TRAIN_DELTA:
                continue
            row = {"epsilon": epsilon, "delta": delta}
            row.update(evaluate_witness(witness, epsilon, delta))
            row["retains_half_training_gap"] = row["absolute_gap"] >= 0.5 * witness.gap
            rows.append(row)
    return rows


def git_value(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    candidates, groups, enumerated = enumerate_candidates(LENGTHS, TRAIN_EPSILON, TRAIN_DELTA)
    optimum = exhaustive_witness(groups)
    pair_count = matched_pair_count(groups)
    matching = validate_matching(optimum)
    cyclic = cyclic_shift_witness(candidates)
    germ = gst_like_germ_baseline(TRAIN_EPSILON, TRAIN_DELTA)
    random_rows = random_baseline(groups, optimum.gap)
    random_summary = summarize_random(random_rows)
    shots = shot_test(optimum, pair_count, SHOTS)
    shots["minimum_expected_shots_for_separation"] = minimum_shots(optimum, pair_count)
    heldout = heldout_grid(optimum)
    heldout_same_order = float(np.mean([row["same_order"] for row in heldout]))
    heldout_half_gap = float(np.mean([row["retains_half_training_gap"] for row in heldout]))

    prior_art_kill = True
    cyclic_fraction = cyclic.gap / optimum.gap if optimum.gap else 1.0
    germ_effect_ratio = germ["max_process_fidelity_residual"] / optimum.gap if optimum.gap else 1.0
    latest_random = next(item for item in random_summary if item["pair_budget"] == 1024)
    criteria = {
        "prior_art_core_capability_exists": prior_art_kill,
        "simple_baseline_at_least_90_percent": max(cyclic_fraction, germ_effect_ratio) >= 0.9,
        "random_majority_at_90_percent_1024": latest_random["success_rate_at_90_percent"] >= 0.5,
        "shot_intervals_overlap_10000": not shots["intervals_separated"],
        "matching_feature_violation": not all(matching.values()),
        "heldout_transfer_failure": heldout_same_order < 0.75 or heldout_half_gap < 0.50,
    }
    killed_by = [name for name, failed in criteria.items() if failed]
    verdict = "KILL_ASTAR_DIRECTION" if killed_by else "SURVIVES_PHASE0_ONLY"

    result = {
        "schema_version": 1,
        "experiment": "hardware_model_witness_phase0",
        "frozen_protocol": "experiments/hardware_model_witness_phase0/PREREGISTRATION.md",
        "parameters": {
            "lengths": list(LENGTHS),
            "epsilon": TRAIN_EPSILON,
            "delta": TRAIN_DELTA,
            "random_budgets": list(RANDOM_BUDGETS),
            "random_trials": RANDOM_TRIALS,
            "random_seed": RANDOM_SEED,
            "shots_per_circuit": SHOTS,
        },
        "search_space": {
            "sequences_enumerated": enumerated,
            "identity_candidates": len(candidates),
            "matched_equivalence_classes": len(groups),
            "matched_pair_hypotheses": pair_count,
        },
        "exhaustive_witness": witness_record(optimum),
        "matching_checks": matching,
        "declared_model_tie_gap": abs(optimum.high.declared_p0 - optimum.low.declared_p0),
        "depolarizing_negative_control_gap": 0.0,
        "cyclic_shift_baseline": {**witness_record(cyclic), "fraction_of_optimum": cyclic_fraction},
        "gst_like_germ_baseline": {**germ, "residual_to_matched_gap_ratio": germ_effect_ratio},
        "random_baseline_summary": random_summary,
        "shot_analysis": shots,
        "heldout_transfer": {
            "draws": heldout,
            "same_order_fraction": heldout_same_order,
            "retains_half_training_gap_fraction": heldout_half_gap,
        },
        "kill_criteria": criteria,
        "killed_by": killed_by,
        "verdict": verdict,
    }

    (OUT / "phase0_results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    with (OUT / "random_baseline_trials.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(random_rows[0]))
        writer.writeheader()
        writer.writerows(random_rows)
    with (OUT / "heldout_transfer.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(heldout[0]))
        writer.writeheader()
        writer.writerows(heldout)

    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "git_head_before_results_commit": git_value("rev-parse", "HEAD"),
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "command": "python experiments/hardware_model_witness_phase0/run_phase0.py",
        "hardware_queries": 0,
        "simulated_shots_executed": 0,
        "note": "Expected counts only; no hardware or sampled-shot data.",
    }
    (OUT / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    report = f"""# Phase-0 final report: matched hardware noise-model witnesses

## Verdict

**{verdict}**.  The direction is killed by: {', '.join(killed_by)}.

This is a simulator-only falsification result.  It does not contain QPU data.

## Exact result

- Enumerated sequences: {enumerated:,}
- Identity candidates: {len(candidates):,}
- Matched equivalence classes: {len(groups):,}
- Matched pair hypotheses: {pair_count:,}
- Exhaustive best `P(0)` gap: {optimum.gap:.12f}
- Declared-model gap for the same pair: {abs(optimum.high.declared_p0 - optimum.low.declared_p0):.3g}
- High sequence: `{' '.join(optimum.high.sequence)}` (`P(0)={optimum.high.p0:.12f}`)
- Low sequence: `{' '.join(optimum.low.sequence)}` (`P(0)={optimum.low.p0:.12f}`)
- All frozen matching checks pass: {all(matching.values())}

## Baselines

- Cyclic-shift gap: {cyclic.gap:.12f} ({cyclic_fraction:.3%} of exhaustive optimum).
- GST-like maximum process-fidelity residual: {germ['max_process_fidelity_residual']:.12f}
  ({germ_effect_ratio:.3f} times the matched-pair gap).
- Random 1024-pair median fraction of optimum:
  {latest_random['median_fraction_of_optimum']:.3%}; success rate at 90%:
  {latest_random['success_rate_at_90_percent']:.3%}.

## Statistical and transfer checks

- Bonferroni-corrected 10,000-shot intervals separated: {shots['intervals_separated']}.
- Minimum expected shots for corrected separation: {shots['minimum_expected_shots_for_separation']}.
- Held-out draws preserving ordering: {heldout_same_order:.3%}.
- Held-out draws retaining at least half the training gap: {heldout_half_gap:.3%}.
- Gate-local depolarizing negative-control gap: 0 by construction and exact channel symmetry.

## Interpretation

The matched constraint can produce a real counterexample to a scalar isolated-gate
model, but the physical capability is not new: GST germs, iterative RB, and
context/model-violation tests already design circuits that amplify precisely
these hidden coherent or contextual errors.  The experiment asks whether the
matching constraint adds a nontrivial search advantage.  The frozen kill gates
above decide that question without relaxing thresholds after seeing results.

Accordingly, no hardware run is authorized from this branch.  The code and
negative result are retained as a reproducible closed-hypothesis record.
"""
    (OUT / "FINAL_REPORT.md").write_text(report, encoding="utf-8")
    print(json.dumps({"verdict": verdict, "killed_by": killed_by, "best_gap": optimum.gap}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
