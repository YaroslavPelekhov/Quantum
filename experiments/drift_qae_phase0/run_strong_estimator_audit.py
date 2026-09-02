"""Run the preregistered global-likelihood control after the Phase-0 screen."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from .drift_models import odd_geometric_depths
from .estimators import simulate_direct_trial, simulate_global_mle_trial
from .qae_core import physical_depth_budget
from .run_phase0 import (
    OUT,
    PROTOCOL_PATH,
    aggregate_trials,
    model_path,
    sha256,
    write_csv,
)


def run_trials(protocol: dict[str, object]) -> list[dict[str, object]]:
    rng = np.random.default_rng(int(protocol["seed"]))
    target_shots = int(protocol["target_shots_per_depth"])
    anchor_shots = int(protocol["anchor_shots_per_depth"])
    trials = int(protocol["monte_carlo_trials"])
    theta_bounds = tuple(protocol["theta_bounds"])
    rows: list[dict[str, object]] = []
    for model in ("readout", "gate"):
        config = protocol[f"{model}_model"]
        estimators = (
            ("global_mle_oracle", "global_mle_anchored", "global_mle_nominal_unanchored")
            if model == "readout"
            else ("global_mle_oracle", "global_mle_anchored")
        )
        for theta in protocol["theta_values"]:
            for path_index, phase in enumerate(config["heldout_phases"]):
                for levels in protocol["levels"]:
                    depths = odd_geometric_depths(int(levels))
                    _, visibility = model_path(protocol, model, int(levels), float(phase))
                    nominal = (
                        float(config["visibility_center"])
                        if model == "readout"
                        else float(np.exp(-float(config["rate_center"])))
                    )
                    bounds = (
                        tuple(config["visibility_bounds"])
                        if model == "readout"
                        else (1e-6, 1.0 - 1e-9)
                    )
                    for estimator in estimators:
                        charged_anchors = anchor_shots if estimator == "global_mle_anchored" else 0
                        budget = physical_depth_budget(depths, target_shots, charged_anchors)
                        for trial in range(trials):
                            outcome = simulate_global_mle_trial(
                                rng,
                                float(theta),
                                depths,
                                visibility,
                                target_shots,
                                anchor_shots,
                                bounds,
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


def unique_slopes(rows: list[dict[str, object]], model: str, estimator: str) -> list[float]:
    values: dict[tuple[float, int], float] = {}
    for row in rows:
        if row["model"] == model and row["estimator"] == estimator:
            values[(float(row["theta"]), int(row["path_index"]))] = float(row["tail_rmse_slope"])
    return list(values.values())


def maximum_failure(rows: list[dict[str, object]], model: str, estimator: str) -> float:
    values = [
        float(row["branch_failure_rate"])
        for row in rows
        if row["model"] == model and row["estimator"] == estimator
    ]
    return max(values)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    raw = run_trials(protocol)
    aggregate = aggregate_trials(raw)
    threshold = float(protocol["gates"]["superclassical_slope_threshold"])
    readout_anchor_slope = float(
        np.median(unique_slopes(aggregate, "readout", "global_mle_anchored"))
    )
    readout_oracle_slope = float(
        np.median(unique_slopes(aggregate, "readout", "global_mle_oracle"))
    )
    readout_direct_slope = float(
        np.median(unique_slopes(aggregate, "readout", "direct_k1_oracle_visibility"))
    )
    gate_anchor_slope = float(
        np.median(unique_slopes(aggregate, "gate", "global_mle_anchored"))
    )
    gate_oracle_slope = float(
        np.median(unique_slopes(aggregate, "gate", "global_mle_oracle"))
    )
    readout_failure = maximum_failure(aggregate, "readout", "global_mle_anchored")
    gate_failure = maximum_failure(aggregate, "gate", "global_mle_anchored")
    readout_scaling_control_passes = (
        readout_anchor_slope < threshold
        and readout_failure <= float(protocol["gates"]["maximum_branch_failure_rate"])
    )
    summary = {
        "schema_version": 1,
        "purpose": "strong estimator control; does not alter the structural Phase-0 verdict",
        "protocol_sha256": sha256(PROTOCOL_PATH),
        "strong_preregistration": "experiments/drift_qae_phase0/STRONG_ESTIMATOR_PREREGISTRATION.md",
        "rows": len(raw),
        "readout_model": {
            "oracle_median_tail_rmse_slope": readout_oracle_slope,
            "anchored_median_tail_rmse_slope": readout_anchor_slope,
            "direct_median_tail_rmse_slope": readout_direct_slope,
            "anchored_maximum_branch_failure_rate": readout_failure,
            "verdict": (
                "CALIBRATED_POST_CIRCUIT_SCALING_CONTROL_PASSES"
                if readout_scaling_control_passes
                else "GLOBAL_ESTIMATOR_STILL_FAILS_FROZEN_GATE"
            ),
        },
        "gate_model": {
            "oracle_median_tail_rmse_slope": gate_oracle_slope,
            "anchored_median_tail_rmse_slope": gate_anchor_slope,
            "anchored_maximum_branch_failure_rate": gate_failure,
            "verdict": "DEPTH_NOISE_SQL_KILL_UNCHANGED",
        },
        "astar_verdict": "KILL_BROAD_DRIFT_ASTAR_UNCHANGED",
        "hardware_spending_authorized": False,
    }
    write_csv(OUT / "strong_estimator_raw.csv", raw)
    write_csv(OUT / "strong_estimator_aggregate.csv", aggregate)
    (OUT / "strong_estimator_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    report = f"""# Strong global-likelihood estimator control

This preregistered follow-up checks that the Phase-0 closure is not an artifact
of the minimal sequential alias resolver.

## Results

- Readout nuisance-oracle median tail RMSE slope: `{readout_oracle_slope:.4f}`
- Readout anchored median tail RMSE slope: `{readout_anchor_slope:.4f}`
- Equal-budget direct median tail RMSE slope: `{readout_direct_slope:.4f}`
- Readout anchored maximum alias-failure rate: `{readout_failure:.3%}`
- Gate nuisance-oracle median tail RMSE slope: `{gate_oracle_slope:.4f}`
- Gate anchored median tail RMSE slope: `{gate_anchor_slope:.4f}`
- Gate anchored maximum alias-failure rate: `{gate_failure:.3%}`

Readout control verdict: **{summary['readout_model']['verdict']}**.

Gate control verdict: **DEPTH_NOISE_SQL_KILL_UNCHANGED**.  Its analytic Fisher
ceiling is independent of this estimator.

## Interpretation

Even a successful post-circuit control is not a new A* drift result: its matched
anchors make the per-round visibility an ordinary calibrated nuisance.  The
physically depth-accumulating model remains limited to `Q^-1/2` for fixed
nonzero noise.  Therefore the broad Phase-0 verdict remains
**KILL_BROAD_DRIFT_ASTAR_UNCHANGED**, and no QPU run is authorised.
"""
    (OUT / "STRONG_ESTIMATOR_REPORT.md").write_text(report, encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

