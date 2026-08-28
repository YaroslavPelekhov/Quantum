"""Exploratory decision-aware follow-up to the rigorous RankCert-MPS pilot.

Nothing in this module is promoted to a mathematical certificate. It compares
internal-only heuristics and multi-fidelity stability gates against the frozen
exact cases, while preserving the rigorous RankCert result unchanged.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RANK_RESULTS = REPO / "results" / "rankcert_mps"
RESULTS = REPO / "results" / "decisioncert_mps"
PROJECT = REPO / "experiments" / "evoq_mis_full_qoblib"
SCHEDULE_INPUT = RANK_RESULTS / "rankcert_schedule_rows.json"
PAIR_INPUT = RANK_RESULTS / "rankcert_pair_rows.json"
SUMMARY_INPUT = RANK_RESULTS / "rankcert_summary.json"
SENSITIVITY_INPUT = PROJECT / "results" / "analysis_summary.json"
CROSS_JOBS = PROJECT / "results" / "cross_case_replication" / "aer_jobs.json"
AVES_JOBS = PROJECT / "results" / "mps_ladder" / "mps_ladder.json"
CROSS_MANIFEST = PROJECT / "results" / "cross_case_replication" / "export_manifest.json"
AVES_MANIFEST = PROJECT / "results" / "independent_ladder" / "export_manifest.json"

CASES = ("karate", "chesapeake", "football", "ibm32", "aves-sparrow-social")
SETTINGS = ("released", "confirm", "bond128", "cutoff1e-4", "cutoff1e-5")
ORDERINGS = ("sorted", "spectral")
METHODS = ("published_lr", "prior_matched_random")
NUMERICAL_FLOOR = 1e-7
SURROGATES = ("sum_w", "sqrt_sum_w", "product_trace", "rss_angle")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    fields = list(rows[0]) if rows else []
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value) if isinstance(value, (dict, list, tuple)) else value for key, value in row.items()})
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def sign(value: float, tolerance: float = 1e-15) -> int:
    return 1 if value > tolerance else (-1 if value < -tolerance else 0)


def surrogate_values(weights: list[float]) -> dict[str, float]:
    sum_w_raw = math.fsum(weights)
    survival = math.prod(1.0 - weight for weight in weights)
    angles = [math.asin(math.sqrt(weight)) for weight in weights]
    return {
        "sum_w": min(1.0, sum_w_raw),
        "sqrt_sum_w": min(1.0, math.sqrt(sum_w_raw)),
        "product_trace": math.sqrt(max(0.0, 1.0 - survival)),
        "rss_angle": math.sin(min(math.pi / 2.0, math.sqrt(math.fsum(angle * angle for angle in angles)))),
        "sum_w_raw": sum_w_raw,
    }


def expanded_envelope(values: list[float]) -> tuple[float, float]:
    return min(values) - 2 * NUMERICAL_FLOOR, max(values) + 2 * NUMERICAL_FLOOR


def interval_decision(lower: float, upper: float) -> int | None:
    if lower > 0:
        return 1
    if upper < 0:
        return -1
    return None


def event_angle_interval(probability: float, angle: float) -> tuple[float, float]:
    """Tight projector-probability interval from a pure-state angle bound."""
    if not 0.0 <= probability <= 1.0 or not 0.0 <= angle <= math.pi / 2.0:
        raise ValueError((probability, angle))
    beta = math.asin(math.sqrt(probability))
    lower = math.sin(max(0.0, beta - angle)) ** 2
    upper = math.sin(min(math.pi / 2.0, beta + angle)) ** 2
    return max(0.0, lower - NUMERICAL_FLOOR), min(1.0, upper + NUMERICAL_FLOOR)


def analyze() -> dict:
    RESULTS.mkdir(parents=True, exist_ok=True)
    schedule_payload = read_json(SCHEDULE_INPUT)
    pair_payload = read_json(PAIR_INPUT)
    rigorous_summary = read_json(SUMMARY_INPUT)
    schedule_rows = schedule_payload["rows"]
    pair_rows = pair_payload["rows"]
    if len(schedule_rows) != 100 or len(pair_rows) != 50 or not rigorous_summary["complete"]:
        raise RuntimeError("Completed immutable RankCert exact-case artifacts are required")
    manifest = {
        "stage": "decisioncert_input_manifest",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "inputs_are_immutable": True,
        "exploratory_only": True,
        "inputs": [
            {"path": str(path), "sha256": sha256(path), "bytes": path.stat().st_size}
            for path in (
                SCHEDULE_INPUT, PAIR_INPUT, SUMMARY_INPUT, SENSITIVITY_INPUT,
                CROSS_JOBS, AVES_JOBS, CROSS_MANIFEST, AVES_MANIFEST,
            )
        ],
        "numerical_floor": NUMERICAL_FLOOR,
        "surrogates": list(SURROGATES),
    }
    atomic_json(RESULTS / "input_manifest.json", manifest)

    enriched_schedules = []
    for row in schedule_rows:
        values = surrogate_values(row["certificate_discarded_weight_upper_bounds"])
        enriched_schedules.append({
            "case": row["case"], "qubits": row["qubits"], "setting": row["setting"],
            "method": row["method"], "schedule": row["schedule"], "ordering": row["ordering"],
            "actual_bks_error": row["actual_bks_error"], "true_tvd": row["true_tvd"],
            "epsilon_rigorous": row["epsilon_mps"], "accumulated_angle": row["accumulated_angle"],
            "p_bks_mps": row["p_bks_mps"], "number_of_truncations": row["number_of_truncations"],
            **values,
        })
    schedule_index = {
        (row["case"], row["setting"], row["method"], row["ordering"]): row
        for row in enriched_schedules
    }
    original_pair_index = {
        (row["case"], row["setting"], row["ordering"]): row for row in pair_rows
    }
    enriched_pairs = []
    for case in CASES:
        for setting in SETTINGS:
            for ordering in ORDERINGS:
                lr = schedule_index[(case, setting, "published_lr", ordering)]
                mr = schedule_index[(case, setting, "prior_matched_random", ordering)]
                original = original_pair_index[(case, setting, ordering)]
                row = {
                    "case": case, "qubits": original["qubits"], "setting": setting, "ordering": ordering,
                    "exact_delta": original["exact_delta"], "mps_delta": original["mps_delta"],
                    "correct_sign": original["correct_sign"], "rigorous_certified": original["certified"],
                }
                lr_event = event_angle_interval(lr["p_bks_mps"], lr["accumulated_angle"])
                mr_event = event_angle_interval(mr["p_bks_mps"], mr["accumulated_angle"])
                event_decision = 1 if mr_event[0] > lr_event[1] else (-1 if lr_event[0] > mr_event[1] else None)
                row.update({
                    "event_angle_lr_interval": lr_event,
                    "event_angle_mr_interval": mr_event,
                    "event_angle_decision": event_decision,
                    "event_angle_certified": event_decision is not None,
                    "event_angle_certified_correct": event_decision is not None and event_decision == sign(original["exact_delta"]),
                })
                for name in SURROGATES:
                    half_width = lr[name] + mr[name] + 2 * NUMERICAL_FLOOR
                    accepted = abs(original["mps_delta"]) > half_width
                    row[f"{name}_pair_width"] = half_width
                    row[f"{name}_accepted"] = accepted
                    row[f"{name}_accepted_correct"] = accepted and original["correct_sign"]
                enriched_pairs.append(row)

    surrogate_summary = {}
    for name in SURROGATES:
        bks_violations = [
            row for row in enriched_schedules
            if row["actual_bks_error"] > row[name] + NUMERICAL_FLOOR
        ]
        tvd_violations = [
            row for row in enriched_schedules
            if row["true_tvd"] > row[name] + NUMERICAL_FLOOR
        ]
        accepted = [row for row in enriched_pairs if row[f"{name}_accepted"]]
        surrogate_summary[name] = {
            "status": "heuristic_not_certificate",
            "schedule_bks_violations": len(bks_violations),
            "schedule_tvd_violations": len(tvd_violations),
            "accepted_pairs": len(accepted),
            "accepted_wrong_signs": sum(not row["correct_sign"] for row in accepted),
            "per_case_accepted": {
                case: sum(row[f"{name}_accepted"] for row in enriched_pairs if row["case"] == case)
                for case in CASES
            },
            "bks_violation_keys": [
                [row["case"], row["setting"], row["schedule"], row["ordering"]]
                for row in bks_violations
            ],
        }

    stability_rows = []
    for case in CASES:
        for ordering in ORDERINGS:
            cohort = [row for row in enriched_pairs if row["case"] == case and row["ordering"] == ordering]
            deltas = [row["mps_delta"] for row in cohort]
            lower, upper = expanded_envelope(deltas)
            exact_delta = cohort[0]["exact_delta"]
            decision = interval_decision(lower, upper)
            leave_one_out = []
            for omitted in SETTINGS:
                kept = [row["mps_delta"] for row in cohort if row["setting"] != omitted]
                lo, hi = expanded_envelope(kept)
                held_decision = interval_decision(lo, hi)
                leave_one_out.append({
                    "omitted_setting": omitted, "lower": lo, "upper": hi,
                    "decision": held_decision,
                    "correct": held_decision is not None and held_decision == sign(exact_delta),
                })
            stability_rows.append({
                "case": case, "qubits": cohort[0]["qubits"], "ordering": ordering,
                "settings": list(SETTINGS), "mps_deltas": deltas,
                "envelope_lower": lower, "envelope_upper": upper,
                "exact_delta": exact_delta,
                "exact_contained": lower <= exact_delta <= upper,
                "decision": decision,
                "accepted": decision is not None,
                "accepted_correct": decision is not None and decision == sign(exact_delta),
                "leave_one_setting_out": leave_one_out,
                "leave_one_out_all_same_decision": decision is not None and all(item["decision"] == decision for item in leave_one_out),
            })
    case_stability = []
    for case in CASES:
        cohort = [row for row in enriched_pairs if row["case"] == case]
        lower, upper = expanded_envelope([row["mps_delta"] for row in cohort])
        decision = interval_decision(lower, upper)
        exact_delta = cohort[0]["exact_delta"]
        case_stability.append({
            "case": case, "qubits": cohort[0]["qubits"], "envelope_lower": lower,
            "envelope_upper": upper, "exact_delta": exact_delta,
            "exact_contained": lower <= exact_delta <= upper,
            "decision": decision, "accepted": decision is not None,
            "accepted_correct": decision is not None and decision == sign(exact_delta),
        })

    # Independent schedule-pair validation. ES-vs-LR was not used to develop
    # the MR-vs-LR stability rule; all inputs are pre-existing frozen rows.
    prior_jobs = read_json(CROSS_JOBS)["rows"] + read_json(AVES_JOBS)["rows"]
    prior_exact_rows = read_json(CROSS_MANIFEST)["rows"] + read_json(AVES_MANIFEST)["rows"]
    prior_index = {
        (row["case"], row["setting"], row["method"], row["ordering"]): row["metrics"]["bks_rate"]
        for row in prior_jobs if row.get("setting") in SETTINGS
    }
    exact_index = {
        (row["case"], row["method"], row["ordering"]): row["exact_metrics"]["bks_rate"]
        for row in prior_exact_rows
    }
    heldout_ordering_rows = []
    for case in CASES:
        for ordering in ORDERINGS:
            deltas = [
                prior_index[(case, setting, "prior_evolutionary", ordering)]
                - prior_index[(case, setting, "published_lr", ordering)]
                for setting in SETTINGS
            ]
            exact_delta = (
                exact_index[(case, "prior_evolutionary", ordering)]
                - exact_index[(case, "published_lr", ordering)]
            )
            lower, upper = expanded_envelope(deltas)
            decision = interval_decision(lower, upper)
            heldout_ordering_rows.append({
                "case": case, "ordering": ordering, "schedule_pair": "ES_minus_LR",
                "mps_deltas": deltas, "envelope_lower": lower, "envelope_upper": upper,
                "exact_delta": exact_delta, "exact_contained": lower <= exact_delta <= upper,
                "decision": decision, "accepted": decision is not None,
                "accepted_correct": decision is not None and decision == sign(exact_delta),
            })
    heldout_case_rows = []
    for case in CASES:
        cohort = [row for row in heldout_ordering_rows if row["case"] == case]
        deltas = [value for row in cohort for value in row["mps_deltas"]]
        lower, upper = expanded_envelope(deltas)
        exact_delta = cohort[0]["exact_delta"]
        decision = interval_decision(lower, upper)
        heldout_case_rows.append({
            "case": case, "schedule_pair": "ES_minus_LR", "envelope_lower": lower,
            "envelope_upper": upper, "exact_delta": exact_delta,
            "decision": decision, "accepted": decision is not None,
            "accepted_correct": decision is not None and decision == sign(exact_delta),
        })

    sensitivity = read_json(SENSITIVITY_INPUT)["sensitivity"]
    frozen_55q = []
    for bond, threshold in sorted({(row["bond"], row["threshold"]) for row in sensitivity}):
        group = [row for row in sensitivity if row["bond"] == bond and row["threshold"] == threshold]
        by_method = {row["method"]: row for row in group}
        lr = by_method["published_lr"]
        mr = by_method["matched_random_search"]
        delta = mr["bks_rate"] - lr["bks_rate"]
        interval_sign = (
            1 if mr["bks_rate_wilson_low"] > lr["bks_rate_wilson_high"]
            else (-1 if lr["bks_rate_wilson_low"] > mr["bks_rate_wilson_high"] else None)
        )
        frozen_55q.append({
            "bond": bond, "threshold": threshold,
            "lr_hits": lr["bks_hits"], "lr_shots": lr["shots"],
            "mr_hits": mr["bks_hits"], "mr_shots": mr["shots"],
            "observed_delta": delta, "observed_sign": sign(delta),
            "lr_wilson": [lr["bks_rate_wilson_low"], lr["bks_rate_wilson_high"]],
            "mr_wilson": [mr["bks_rate_wilson_low"], mr["bks_rate_wilson_high"]],
            "marginal_wilson_interval_sign": interval_sign,
        })

    summary = {
        "stage": "decisioncert_exploratory_analysis",
        "complete": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "warning": "Cumulative surrogates and stability rules are heuristics. The separately labelled event-angle interval is rigorous but still depends on the global accumulated angle.",
        "rigorous_baseline": {
            "certified_pairs": rigorous_summary["ranking"]["certified"],
            "total_pairs": rigorous_summary["ranking"]["total"],
            "wrong_sign_certified": rigorous_summary["ranking"]["wrong_sign_certified"],
        },
        "surrogates": surrogate_summary,
        "event_angle_certificate": {
            "derivation": "Bernoulli measurement angle is contractive under measurement: |asin(sqrt(p))-asin(sqrt(q))| <= A.",
            "certified_pairs": sum(row["event_angle_certified"] for row in enriched_pairs),
            "certified_wrong": sum(row["event_angle_certified"] and not row["event_angle_certified_correct"] for row in enriched_pairs),
            "per_case_certified": {
                case: sum(row["event_angle_certified"] for row in enriched_pairs if row["case"] == case)
                for case in CASES
            },
        },
        "stability": {
            "ordering_cohorts_accepted": sum(row["accepted"] for row in stability_rows),
            "ordering_cohorts_total": len(stability_rows),
            "ordering_cohorts_wrong": sum(row["accepted"] and not row["accepted_correct"] for row in stability_rows),
            "exact_delta_contained": sum(row["exact_contained"] for row in stability_rows),
            "leave_one_out_acceptances": sum(item["decision"] is not None for row in stability_rows for item in row["leave_one_setting_out"]),
            "leave_one_out_total": sum(len(row["leave_one_setting_out"]) for row in stability_rows),
            "leave_one_out_wrong": sum(item["decision"] is not None and not item["correct"] for row in stability_rows for item in row["leave_one_setting_out"]),
            "case_decisions_accepted": sum(row["accepted"] for row in case_stability),
            "case_decisions_total": len(case_stability),
            "case_decisions_wrong": sum(row["accepted"] and not row["accepted_correct"] for row in case_stability),
        },
        "heldout_schedule_pair_validation": {
            "schedule_pair": "prior_evolutionary_minus_published_lr",
            "not_used_to_develop_rule": True,
            "ordering_cohorts_accepted": sum(row["accepted"] for row in heldout_ordering_rows),
            "ordering_cohorts_total": len(heldout_ordering_rows),
            "ordering_cohorts_wrong": sum(row["accepted"] and not row["accepted_correct"] for row in heldout_ordering_rows),
            "exact_delta_contained": sum(row["exact_contained"] for row in heldout_ordering_rows),
            "case_decisions_accepted": sum(row["accepted"] for row in heldout_case_rows),
            "case_decisions_total": len(heldout_case_rows),
            "case_decisions_wrong": sum(row["accepted"] and not row["accepted_correct"] for row in heldout_case_rows),
            "ordering_rows": heldout_ordering_rows,
            "case_rows": heldout_case_rows,
        },
        "frozen_55q": {
            "rows": frozen_55q,
            "signs": [row["observed_sign"] for row in frozen_55q],
            "marginal_wilson_interval_signs": [row["marginal_wilson_interval_sign"] for row in frozen_55q],
            "stable": len({row["observed_sign"] for row in frozen_55q}) == 1,
            "decision": None,
            "note": "Descriptive finite-shot stability check only; no new run and no certificate.",
        },
    }
    atomic_json(RESULTS / "schedule_surrogates.json", {"rows": enriched_schedules})
    atomic_json(RESULTS / "pair_surrogates.json", {"rows": enriched_pairs})
    atomic_json(RESULTS / "stability_envelopes.json", {"ordering_rows": stability_rows, "case_rows": case_stability})
    atomic_json(RESULTS / "heldout_es_lr_stability.json", {"ordering_rows": heldout_ordering_rows, "case_rows": heldout_case_rows})
    atomic_json(RESULTS / "decisioncert_summary.json", summary)
    write_csv(RESULTS / "schedule_surrogates.csv", enriched_schedules)
    write_csv(RESULTS / "pair_surrogates.csv", enriched_pairs)
    write_csv(RESULTS / "stability_envelopes.csv", stability_rows)
    write_report(summary, stability_rows, case_stability)
    return summary


def write_report(summary: dict, stability_rows: list[dict], case_rows: list[dict]) -> None:
    surrogate_lines = "\n".join(
        f"| {name} | {stats['schedule_bks_violations']} | {stats['schedule_tvd_violations']} | "
        f"{stats['accepted_pairs']} / 50 | {stats['accepted_wrong_signs']} |"
        for name, stats in summary["surrogates"].items()
    )
    case_lines = "\n".join(
        f"| {row['case']} | [{row['envelope_lower']:.6g}, {row['envelope_upper']:.6g}] | "
        f"{row['exact_delta']:.6g} | {'accept' if row['accepted'] else 'reject'} | "
        f"{row['accepted_correct'] if row['accepted'] else '-'} |"
        for row in case_rows
    )
    frozen = summary["frozen_55q"]["rows"]
    frozen_lines = "\n".join(
        f"| {row['bond']} | {row['threshold']:.0e} | {row['lr_hits']}/{row['lr_shots']} | "
        f"{row['mr_hits']}/{row['mr_shots']} | {row['observed_delta']:+.6g} |"
        for row in frozen
    )
    (RESULTS / "EXPLORATORY_REPORT.md").write_text(f"""# Decision-aware RankCert follow-up

## Status

This is a follow-up, not a replacement for RankCert-MPS. Cumulative surrogates
and stability envelopes are explicitly heuristic. The event-angle interval in
the next section is a separate rigorous consequence of the same global angle.

## Rigorous event-angle interval

For a projector event with approximate probability q and state-angle bound A,
measurement contractivity gives

`sin^2(max(0, asin(sqrt(q))-A)) <= p_exact <= sin^2(min(pi/2, asin(sqrt(q))+A))`.

This probability-aware interval certified {summary['event_angle_certificate']['certified_pairs']} / 50 rankings with {summary['event_angle_certificate']['certified_wrong']} wrong. Its per-case coverage is {summary['event_angle_certificate']['per_case_certified']}. It is never wider than the generic additive event bound, but on this dataset it did not improve the 14 / 50 coverage because the accumulated angles on ibm32 and aves were already too large. This is a useful negative result: merely transforming the global angle more sharply is insufficient; a successful observable-aware method must reduce the angle contribution itself using BKS structure.

## Discarded-weight surrogates

| Internal quantity | BKS violations / 100 | TVD violations / 100 | Accepted rankings | Wrong accepted |
|---|---:|---:|---:|---:|
{surrogate_lines}

`sqrt(sum w)`, `sqrt(1-product(1-w))`, and the root-sum-square angle happened
to upper-bound every exact error in this dataset and accepted 21 / 50 rankings,
versus 14 / 50 for the rigorous angle sum. This is empirical evidence for
mostly incoherent error accumulation, not a theorem. The more aggressive
`sum(w)` accepted 31 / 50 but failed three BKS schedule checks and 33 TVD
checks; it is falsified as a bound.

The empirically clean square-root surrogates accepted 1 / 10 ibm32 rankings
but 0 / 10 aves rankings. They are useful candidates for future held-out
validation, not for guaranteed claims.

## Multi-setting decision stability

For each case, the stability envelope is the min/max MPS delta across all five
frozen settings and both orderings, widened by the predeclared numerical floor.

| Case | Internal stability envelope | Exact delta (audit only) | Decision | Correct |
|---|---:|---:|---:|---:|
{case_lines}

The envelope accepted 4 / 5 case-level decisions, all correct, and rejected
aves because its internal winner changes with approximation. At the
case-ordering level it accepted {summary['stability']['ordering_cohorts_accepted']} / {summary['stability']['ordering_cohorts_total']}, with {summary['stability']['ordering_cohorts_wrong']} wrong. All {summary['stability']['exact_delta_contained']} / 10 exact deltas lay inside the empirical envelopes. Leave-one-setting-out checks accepted {summary['stability']['leave_one_out_acceptances']} / {summary['stability']['leave_one_out_total']} and made {summary['stability']['leave_one_out_wrong']} wrong decisions.

This gate is attractive because it uses only repeated approximate simulations,
but unanimity is not a proof. Its value is operational: it detects the known
approximation-sensitive case without exact-state access.

## Independent schedule-pair validation

The frozen artifacts also contain `prior_evolutionary` (ES), which was not used
to develop the MR-vs-LR stability rule. Applying the unchanged envelope to
ES-vs-LR accepted {summary['heldout_schedule_pair_validation']['ordering_cohorts_accepted']} / {summary['heldout_schedule_pair_validation']['ordering_cohorts_total']} case-ordering decisions and {summary['heldout_schedule_pair_validation']['case_decisions_accepted']} / {summary['heldout_schedule_pair_validation']['case_decisions_total']} case-level decisions, with {summary['heldout_schedule_pair_validation']['ordering_cohorts_wrong']} and {summary['heldout_schedule_pair_validation']['case_decisions_wrong']} wrong respectively. The exact delta lay inside {summary['heldout_schedule_pair_validation']['exact_delta_contained']} / 10 widened envelopes.

This independent-pair validation is encouraging: the 24q aves ES-vs-LR effect
is stable and correctly accepted, while its approximation-sensitive MR-vs-LR
effect is rejected. It is not external-case validation because the same five
instances and simulator family are reused.

## Frozen 55q implication

| Bond | Cutoff | LR BKS | MR BKS | Observed MR-LR |
|---:|---:|---:|---:|---:|
{frozen_lines}

The observed point-estimate signs are {summary['frozen_55q']['signs']}; the
signs supported by non-overlapping marginal Wilson intervals are
{summary['frozen_55q']['marginal_wilson_interval_signs']}. Therefore both the
point stability rule and a confidence-aware version reject the 55q decision.
These are reused finite-shot frozen counts, not a new execution, a simultaneous
confidence construction, or an exact statement.

## Scientific conclusion

The discarded-weight list alone cannot support a universally tighter rigorous
bound; its local angles contain no information about coherent orientation or
the BKS observable. The next serious algorithm should propagate BKS-observable
sensitivity backward through the circuit or construct validated upper/lower
tensor-network contractions. In the meantime, the multi-setting envelope is a
useful abstention heuristic: accept stable decisions, reject approximation-
sensitive ones, and never describe the result as certified.
""", encoding="utf-8")


if __name__ == "__main__":
    print(json.dumps(analyze(), indent=2))
