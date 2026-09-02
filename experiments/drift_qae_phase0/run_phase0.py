"""Execute the frozen drift-aware amplitude-estimation Phase-0 screen."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from .drift_models import (
    gate_visibility,
    odd_geometric_depths,
    readout_visibility,
    rescaled_drift_path,
    target_probability,
    total_variation,
)
from .estimators import simulate_amplified_trial, simulate_direct_trial
from .qae_core import (
    fit_power_law,
    known_visibility_fisher,
    per_round_efficient_fisher,
    physical_depth_budget,
    search_visibility_confounding_witness,
    stationary_visibility_fisher,
)


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = Path(__file__).resolve().parent
OUT = ROOT / "results" / "drift_qae_phase0"
PROTOCOL_PATH = EXPERIMENT / "protocol.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def json_safe(value):
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def coherent_offset_audit(depths: np.ndarray) -> dict[str, object]:
    """Exact no-go when the nuisance enters the same generator as theta."""

    theta_first = 0.203
    theta_second = 0.251
    offset_first = 0.029
    offset_second = theta_first + offset_first - theta_second
    first = target_probability(theta_first + offset_first, depths, np.ones(len(depths)))
    second = target_probability(theta_second + offset_second, depths, np.ones(len(depths)))
    return {
        "theta_first": theta_first,
        "theta_second": theta_second,
        "offset_first": offset_first,
        "offset_second": offset_second,
        "theta_separation": abs(theta_second - theta_first),
        "offset_total_variation_first": 0.0,
        "offset_total_variation_second": 0.0,
        "maximum_probability_gap": float(np.max(np.abs(first - second))),
        "exactly_indistinguishable": bool(np.max(np.abs(first - second)) < 1e-14),
        "minimax_absolute_error_lower_bound": 0.5 * abs(theta_second - theta_first),
        "interpretation": "A trusted reference is necessary when calibration drift shares theta's generator.",
    }


def run_confounding_audit(protocol: dict[str, object]) -> list[dict[str, object]]:
    config = protocol["confounding_search"]
    rows: list[dict[str, object]] = []
    for levels in protocol["levels"]:
        depths = odd_geometric_depths(int(levels))
        maximum_depth = int(depths[-1])
        for scale in config["separation_over_inverse_max_depth"]:
            separation = float(scale) / maximum_depth
            witness = search_visibility_confounding_witness(
                separation=separation,
                depths=depths,
                visibility_bounds=tuple(config["visibility_bounds"]),
                theta_bounds=tuple(protocol["theta_bounds"]),
                points=int(config["theta_points"]),
                variation_budget=float(config["variation_budget"]),
            )
            row: dict[str, object] = {
                "levels": int(levels),
                "maximum_depth": maximum_depth,
                "separation_scale": float(scale),
                "theta_separation": separation,
                "variation_budget": float(config["variation_budget"]),
                "witness_found": witness is not None,
            }
            if witness is not None:
                row.update(
                    {
                        "theta_first": witness.theta_first,
                        "theta_second": witness.theta_second,
                        "visibility_first": list(witness.visibility_first),
                        "visibility_second": list(witness.visibility_second),
                        "total_variation_first": witness.total_variation_first,
                        "total_variation_second": witness.total_variation_second,
                        "maximum_probability_gap": witness.maximum_probability_gap,
                    }
                )
            rows.append(row)
    return rows


def model_path(protocol: dict[str, object], model: str, levels: int, phase: float) -> tuple[np.ndarray, np.ndarray]:
    depths = odd_geometric_depths(levels)
    if model == "readout":
        config = protocol["readout_model"]
        nuisance = rescaled_drift_path(
            levels,
            float(config["visibility_center"]),
            float(config["total_variation"]),
            float(config["visibility_bounds"][0]),
            float(config["visibility_bounds"][1]),
            phase,
        )
        visibility = readout_visibility(nuisance, depths)
    elif model == "gate":
        config = protocol["gate_model"]
        nuisance = rescaled_drift_path(
            levels,
            float(config["rate_center"]),
            float(config["total_variation"]),
            float(config["rate_bounds"][0]),
            float(config["rate_bounds"][1]),
            phase,
        )
        visibility = gate_visibility(nuisance, depths)
    else:
        raise ValueError(model)
    return nuisance, np.asarray(visibility, dtype=float)


def fisher_audit(protocol: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    target_shots = int(protocol["target_shots_per_depth"])
    anchor_shots = int(protocol["anchor_shots_per_depth"])
    for model in ("readout", "gate"):
        phases = protocol[f"{model}_model"]["heldout_phases"]
        for theta in protocol["theta_values"]:
            for path_index, phase in enumerate(phases):
                for levels in protocol["levels"]:
                    depths = odd_geometric_depths(int(levels))
                    nuisance, visibility = model_path(protocol, model, int(levels), float(phase))
                    known = known_visibility_fisher(theta, depths, visibility, target_shots)
                    anchored = per_round_efficient_fisher(
                        theta, depths, visibility, target_shots, anchor_shots
                    )
                    unanchored = per_round_efficient_fisher(theta, depths, visibility, target_shots, 0)
                    stationary = stationary_visibility_fisher(
                        theta,
                        depths,
                        float(np.mean(visibility)),
                        target_shots,
                        0,
                    )
                    rows.append(
                        {
                            "model": model,
                            "theta": float(theta),
                            "path_index": path_index,
                            "path_phase": float(phase),
                            "levels": int(levels),
                            "maximum_depth": int(depths[-1]),
                            "target_only_budget": physical_depth_budget(depths, target_shots, 0),
                            "anchored_budget": physical_depth_budget(depths, target_shots, anchor_shots),
                            "nuisance_total_variation": total_variation(nuisance),
                            "minimum_visibility": float(np.min(visibility)),
                            "known_fisher": known,
                            "anchored_efficient_fisher": anchored,
                            "unanchored_efficient_fisher": unanchored,
                            "stationary_unknown_fisher": stationary,
                            "anchor_efficiency_fraction": anchored / known if known > 0 else 0.0,
                            "known_local_error": 1.0 / math.sqrt(known) if known > 0 else float("inf"),
                            "anchored_local_error": 1.0 / math.sqrt(anchored) if anchored > 0 else float("inf"),
                        }
                    )
    return rows


def run_monte_carlo(protocol: dict[str, object]) -> list[dict[str, object]]:
    rng = np.random.default_rng(int(protocol["seed"]))
    target_shots = int(protocol["target_shots_per_depth"])
    anchor_shots = int(protocol["anchor_shots_per_depth"])
    trials = int(protocol["monte_carlo_trials"])
    theta_bounds = tuple(protocol["theta_bounds"])
    rows: list[dict[str, object]] = []
    for model in ("readout", "gate"):
        config = protocol[f"{model}_model"]
        phases = config["heldout_phases"]
        estimators = ("oracle", "anchored", "nominal_unanchored") if model == "readout" else ("oracle", "anchored")
        for theta in protocol["theta_values"]:
            for path_index, phase in enumerate(phases):
                for levels in protocol["levels"]:
                    depths = odd_geometric_depths(int(levels))
                    nuisance, visibility = model_path(protocol, model, int(levels), float(phase))
                    for estimator in estimators:
                        used_anchor_shots = anchor_shots if estimator == "anchored" else 0
                        budget = physical_depth_budget(depths, target_shots, used_anchor_shots)
                        nominal = (
                            float(config["visibility_center"])
                            if model == "readout"
                            else float(np.exp(-float(config["rate_center"])))
                        )
                        visibility_bounds = (
                            tuple(config["visibility_bounds"])
                            if model == "readout"
                            else (1e-6, 1.0 - 1e-9)
                        )
                        for trial in range(trials):
                            outcome = simulate_amplified_trial(
                                rng,
                                float(theta),
                                depths,
                                visibility,
                                target_shots,
                                anchor_shots,
                                visibility_bounds,
                                theta_bounds,
                                estimator,
                                nominal,
                            )
                            rows.append(
                                {
                                    "model": model,
                                    "estimator": estimator,
                                    "theta": float(theta),
                                    "path_index": path_index,
                                    "levels": int(levels),
                                    "maximum_depth": int(depths[-1]),
                                    "physical_depth_budget": budget,
                                    "trial": trial,
                                    **outcome,
                                }
                            )

                    direct_budget = physical_depth_budget(depths, target_shots, anchor_shots)
                    direct_visibility = (
                        float(config["visibility_center"])
                        if model == "readout"
                        else float(np.exp(-float(config["rate_center"])))
                    )
                    for trial in range(trials):
                        outcome = simulate_direct_trial(
                            rng,
                            float(theta),
                            direct_budget,
                            direct_visibility,
                            theta_bounds,
                        )
                        rows.append(
                            {
                                "model": model,
                                "estimator": "direct_k1_oracle_visibility",
                                "theta": float(theta),
                                "path_index": path_index,
                                "levels": int(levels),
                                "maximum_depth": int(depths[-1]),
                                "physical_depth_budget": direct_budget,
                                "trial": trial,
                                **outcome,
                            }
                        )
    return rows


def aggregate_trials(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    groups: dict[tuple[object, ...], list[dict[str, object]]] = defaultdict(list)
    fields = ("model", "estimator", "theta", "path_index", "levels", "maximum_depth", "physical_depth_budget")
    for row in rows:
        groups[tuple(row[field] for field in fields)].append(row)
    aggregates: list[dict[str, object]] = []
    for key, group in groups.items():
        errors = np.asarray([float(row["absolute_error"]) for row in group])
        squared = np.asarray([float(row["squared_error"]) for row in group])
        estimates = np.asarray([float(row["estimate"]) for row in group])
        failures = np.asarray([bool(row["branch_failure"]) for row in group])
        record = dict(zip(fields, key, strict=True))
        record.update(
            {
                "trials": len(group),
                "bias": float(np.mean(estimates) - float(record["theta"])),
                "median_absolute_error": float(np.median(errors)),
                "rmse": float(np.sqrt(np.mean(squared))),
                "q90_absolute_error": float(np.quantile(errors, 0.9)),
                "branch_failure_rate": float(np.mean(failures)),
            }
        )
        aggregates.append(record)

    slope_groups: dict[tuple[object, ...], list[dict[str, object]]] = defaultdict(list)
    for row in aggregates:
        slope_groups[(row["model"], row["estimator"], row["theta"], row["path_index"])].append(row)
    for group in slope_groups.values():
        group.sort(key=lambda row: int(row["levels"]))
        fit = fit_power_law(
            np.asarray([row["physical_depth_budget"] for row in group]),
            np.asarray([row["rmse"] for row in group]),
        )
        for row in group:
            row["tail_rmse_slope"] = fit["slope"]
            row["tail_rmse_slope_r_squared"] = fit["r_squared"]
    return sorted(
        aggregates,
        key=lambda row: (
            str(row["model"]),
            str(row["estimator"]),
            float(row["theta"]),
            int(row["path_index"]),
            int(row["levels"]),
        ),
    )


def analytic_depth_ceiling(protocol: dict[str, object]) -> dict[str, object]:
    gamma = float(protocol["gate_model"]["rate_center"])
    return {
        "fixed_rate": gamma,
        "per_physical_depth_fisher_upper_bound": 2.0 / (math.e * gamma),
        "total_fisher_upper_bound": "I_Q <= 2 Q / (e gamma)",
        "local_rmse_lower_bound": "sqrt(e gamma / (2 Q))",
        "fixed_gamma_scaling_exponent": -0.5,
        "derivation": (
            "I_k <= 4 k^2 exp(-2 gamma k); divide by cost k and maximize "
            "k exp(-2 gamma k) at k=1/(2 gamma)."
        ),
    }


def summarize(
    protocol: dict[str, object],
    coherent: dict[str, object],
    confounding: list[dict[str, object]],
    fisher_rows: list[dict[str, object]],
    aggregate_rows: list[dict[str, object]],
) -> dict[str, object]:
    tolerance = float(protocol["gates"]["probability_identity_tolerance"])
    witnesses = [row for row in confounding if row["witness_found"]]
    exact_witnesses = [
        row for row in witnesses if float(row["maximum_probability_gap"]) <= tolerance
    ]
    readout_fisher = [row for row in fisher_rows if row["model"] == "readout"]
    maximum_unanchored_fraction = max(
        float(row["unanchored_efficient_fisher"]) / float(row["known_fisher"])
        if float(row["known_fisher"]) > 0
        else 0.0
        for row in readout_fisher
    )
    minimum_anchor_fraction = min(float(row["anchor_efficiency_fraction"]) for row in readout_fisher)

    def slopes(model: str, estimator: str) -> list[float]:
        seen: set[tuple[float, int]] = set()
        values: list[float] = []
        for row in aggregate_rows:
            if row["model"] != model or row["estimator"] != estimator:
                continue
            key = (float(row["theta"]), int(row["path_index"]))
            if key not in seen:
                seen.add(key)
                values.append(float(row["tail_rmse_slope"]))
        return values

    def maximum_failure(model: str, estimator: str) -> float:
        selected = [
            float(row["branch_failure_rate"])
            for row in aggregate_rows
            if row["model"] == model and row["estimator"] == estimator
        ]
        return max(selected) if selected else float("nan")

    readout_anchor_slopes = slopes("readout", "anchored")
    readout_direct_slopes = slopes("readout", "direct_k1_oracle_visibility")
    gate_anchor_slopes = slopes("gate", "anchored")
    threshold = float(protocol["gates"]["superclassical_slope_threshold"])
    physical_ceiling = analytic_depth_ceiling(protocol)
    criteria = {
        "coherent_generator_offset_exactly_nonidentifiable": bool(coherent["exactly_indistinguishable"]),
        "unanchored_visibility_exact_confounding_found": bool(exact_witnesses),
        "per_round_unanchored_efficient_information_zero": maximum_unanchored_fraction < 1e-10,
        "matched_anchors_restore_regular_information": minimum_anchor_fraction
        >= float(protocol["gates"]["minimum_anchor_efficiency_fraction"]),
        "fixed_depth_noise_has_sql_information_ceiling": physical_ceiling["fixed_gamma_scaling_exponent"] == -0.5,
        "gate_anchor_empirical_tail_not_superclassical": float(np.median(gate_anchor_slopes)) > threshold,
    }
    broad_killed = all(
        criteria[name]
        for name in (
            "coherent_generator_offset_exactly_nonidentifiable",
            "unanchored_visibility_exact_confounding_found",
            "per_round_unanchored_efficient_information_zero",
            "matched_anchors_restore_regular_information",
            "fixed_depth_noise_has_sql_information_ceiling",
        )
    )
    gate_killed = criteria["fixed_depth_noise_has_sql_information_ceiling"]
    readout_survives_empirically = (
        float(np.median(readout_anchor_slopes)) < threshold
        and maximum_failure("readout", "anchored")
        <= float(protocol["gates"]["maximum_branch_failure_rate"])
    )
    verdict = "KILL_BROAD_DRIFT_ASTAR" if broad_killed else "SURVIVES_PHASE0_ONLY"
    return {
        "schema_version": 1,
        "verdict": verdict,
        "hardware_spending_authorized": False,
        "protocol_sha256": sha256(PROTOCOL_PATH),
        "structural_criteria": criteria,
        "model_verdicts": {
            "gate_accumulating": "KILLED_BY_FIXED_DEPTH_NOISE" if gate_killed else "SURVIVES_PHASE0_ONLY",
            "post_circuit_readout": (
                "EMPIRICAL_SCALING_ONLY_NOT_NEW_BOUNDARY"
                if readout_survives_empirically
                else "KILLED_BY_ESTIMATOR_OR_IDENTIFIABILITY_GATE"
            ),
        },
        "coherent_offset_no_go": coherent,
        "visibility_confounding": {
            "tested_rows": len(confounding),
            "witnesses_found": len(witnesses),
            "exact_witnesses": len(exact_witnesses),
            "largest_exact_separation": max(
                (float(row["theta_separation"]) for row in exact_witnesses), default=0.0
            ),
        },
        "fisher_audit": {
            "maximum_unanchored_information_fraction": maximum_unanchored_fraction,
            "minimum_anchor_efficiency_fraction": minimum_anchor_fraction,
        },
        "empirical_scaling": {
            "readout_anchor_median_tail_rmse_slope": float(np.median(readout_anchor_slopes)),
            "readout_direct_median_tail_rmse_slope": float(np.median(readout_direct_slopes)),
            "gate_anchor_median_tail_rmse_slope": float(np.median(gate_anchor_slopes)),
            "readout_anchor_maximum_branch_failure_rate": maximum_failure("readout", "anchored"),
            "gate_anchor_maximum_branch_failure_rate": maximum_failure("gate", "anchored"),
        },
        "analytic_depth_ceiling": physical_ceiling,
        "interpretation": (
            "The broad drift claim decomposes into an unidentifiable model, a calibrated "
            "post-circuit nuisance model, and a known depth-attenuation SQL regime. No new "
            "drift-specific minimax phase transition survives this frozen screen."
        ),
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"no rows for {path}")
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value) if isinstance(value, (list, dict)) else value for key, value in row.items()})


def write_report(summary: dict[str, object]) -> None:
    scaling = summary["empirical_scaling"]
    confounding = summary["visibility_confounding"]
    fisher = summary["fisher_audit"]
    report = f"""# Drift-aware amplitude estimation Phase-0 final report

## Verdict

**{summary['verdict']}**.  No QPU run is authorised from this branch.

The proposed broad claim does not survive decomposition into physically
distinct nuisance models.  This is a CPU-only structural and Monte Carlo
falsification; it contains no hardware observations.

## Decisive structural results

1. A coherent calibration offset entering the same generator as the ideal
   amplitude is exactly nonidentifiable.  The frozen pair differs in `theta` by
   {summary['coherent_offset_no_go']['theta_separation']:.6f}, has zero nuisance
   total variation, and has maximum probability gap
   {summary['coherent_offset_no_go']['maximum_probability_gap']:.3g} at every
   tested depth.
2. The bounded-variation visibility search found {confounding['exact_witnesses']}
   exact unanchored witnesses among {confounding['tested_rows']} frozen rows.
   The largest tested exact theta separation was
   {confounding['largest_exact_separation']:.8g}.
3. Treating visibility as a separate nuisance at every round leaves at most
   {fisher['maximum_unanchored_information_fraction']:.3g} of the known-nuisance
   local Fisher information.  Matched anchors restore at least
   {fisher['minimum_anchor_efficiency_fraction']:.3%}; this is ordinary
   calibrated-nuisance information, not evidence for a new drift boundary.
4. For fixed gate-accumulating rate `gamma`,
   `I_Q <= 2 Q / (e gamma)`, hence local RMSE is
   `Omega(sqrt(gamma/Q))`.  Fixed nonzero depth noise therefore permits only
   standard-quantum-limit physical-depth scaling even when the nuisance is
   known.

## Frozen Monte Carlo screen

- Post-circuit/readout anchored median tail RMSE slope:
  {scaling['readout_anchor_median_tail_rmse_slope']:.4f}
- Strong direct `k=1` comparator median tail RMSE slope:
  {scaling['readout_direct_median_tail_rmse_slope']:.4f}
- Gate-accumulating anchored median tail RMSE slope:
  {scaling['gate_anchor_median_tail_rmse_slope']:.4f}
- Maximum readout anchored branch-failure rate:
  {scaling['readout_anchor_maximum_branch_failure_rate']:.3%}
- Maximum gate anchored branch-failure rate:
  {scaling['gate_anchor_maximum_branch_failure_rate']:.3%}

Positive readout-model scaling, if present, cannot rescue the hardware-facing
claim: depth-independent visibility was assumed, while the separate physical
model has exponential visibility loss and an analytic SQL ceiling.

## Research conclusion

The attractive phrase "QAE under drift" hides three different problems:

- generator-aligned drift requires a trusted reference or is impossible;
- post-circuit visibility drift is removable by matched calibration under the
  common-nuisance assumption;
- depth-accumulating noise destroys asymptotic quadratic scaling before drift
  becomes the novel issue.

Consequently there is no defensible A* contribution in the broad candidate as
registered.  A future branch would need a different computational object or a
restricted, independently validated anchor model with a theorem not reducible
to these three cases.  The current result must not be advertised as a positive
quantum advantage.
"""
    (OUT / "FINAL_REPORT.md").write_text(report, encoding="utf-8")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    maximum_depths = odd_geometric_depths(max(protocol["levels"]))
    coherent = coherent_offset_audit(maximum_depths)
    confounding = run_confounding_audit(protocol)
    fisher_rows = fisher_audit(protocol)
    raw_trials = run_monte_carlo(protocol)
    aggregate_rows = aggregate_trials(raw_trials)
    summary = summarize(protocol, coherent, confounding, fisher_rows, aggregate_rows)

    write_csv(OUT / "confounding_audit.csv", confounding)
    write_csv(OUT / "fisher_audit.csv", fisher_rows)
    write_csv(OUT / "raw_trials.csv", raw_trials)
    write_csv(OUT / "aggregate.csv", aggregate_rows)
    (OUT / "identifiability_audit.json").write_text(
        json.dumps(
            {"coherent_offset": coherent, "visibility_confounding": confounding},
            indent=2,
            default=json_safe,
        ),
        encoding="utf-8",
    )
    (OUT / "phase0_summary.json").write_text(
        json.dumps(summary, indent=2, default=json_safe), encoding="utf-8"
    )
    run_manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "command": "python -m experiments.drift_qae_phase0.run_phase0",
        "protocol_sha256": sha256(PROTOCOL_PATH),
        "monte_carlo_rows": len(raw_trials),
        "hardware_queries": 0,
        "qpu_observations": 0,
    }
    (OUT / "run_manifest.json").write_text(json.dumps(run_manifest, indent=2), encoding="utf-8")
    write_report(summary)
    print(json.dumps(summary, indent=2, default=json_safe))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

