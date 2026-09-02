"""Run the frozen sequential-reference curvature-boundary Phase 0."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from .core import (
    affine_drift,
    compact_bump_second_derivative,
    compact_bump_target_average,
    compact_target_bump,
    fit_log_slope,
    interval_average,
    phasor_probabilities,
    physical_depth_cost,
    quadratic_drift,
    rtr_drift_averages,
    rtr_interpolation_bias,
    simulate_rtr_local_estimator,
)


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = Path(__file__).resolve().parent
OUT = ROOT / "results" / "interleaved_drift_boundary_phase0"
PROTOCOL_PATH = EXPERIMENT / "protocol.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def analytic_audit(protocol: dict[str, object]) -> dict[str, object]:
    duration = 17.0
    offset = 0.037
    slope = -0.0041
    curvature = 2.3e-5
    affine_bias = rtr_interpolation_bias(affine_drift(offset, slope), duration)
    quadratic_bias = rtr_interpolation_bias(quadratic_drift(curvature), duration)
    quadratic_ratio = quadratic_bias / (curvature * duration**2)

    bump = compact_target_bump(curvature, duration)
    left, target, right = rtr_drift_averages(bump, duration)
    expected_target = compact_bump_target_average(curvature, duration)
    grid = np.linspace(-0.5 * duration, 0.5 * duration, 100_001)
    maximum_second_derivative = float(
        np.max(np.abs(compact_bump_second_derivative(grid, curvature, duration)))
    )
    theta_first = 0.231
    theta_second = theta_first + target
    depth = 31
    reference_theta = float(protocol["reference_theta"])
    world_zero_phases = (
        2.0 * depth * reference_theta,
        2.0 * depth * theta_second,
        2.0 * depth * reference_theta,
    )
    world_one_phases = (
        2.0 * depth * (reference_theta + left),
        2.0 * depth * (theta_first + target),
        2.0 * depth * (reference_theta + right),
    )
    probability_gap = max(
        abs(first - second)
        for phase_zero, phase_one in zip(world_zero_phases, world_one_phases, strict=True)
        for first, second in zip(
            phasor_probabilities(phase_zero, float(protocol["visibility"])),
            phasor_probabilities(phase_one, float(protocol["visibility"])),
            strict=True,
        )
    )
    return {
        "affine": {
            "duration": duration,
            "offset": offset,
            "slope": slope,
            "interpolation_bias": affine_bias,
        },
        "quadratic": {
            "curvature": curvature,
            "interpolation_bias": quadratic_bias,
            "bias_over_kappa_T_squared": quadratic_ratio,
            "exact_prediction": -0.5,
        },
        "compact_bump": {
            "reference_averages": [left, right],
            "target_average": target,
            "exact_target_average": expected_target,
            "target_average_over_kappa_T_squared": target / (curvature * duration**2),
            "maximum_absolute_second_derivative": maximum_second_derivative,
            "registered_curvature_bound": curvature,
            "theta_separation": target,
            "minimax_absolute_risk_lower_bound": 0.5 * target,
            "maximum_two_quadrature_probability_gap": probability_gap,
        },
        "deterministic_upper_bound": {
            "statement": "|RTR interpolation bias| <= kappa T^2 / 2",
            "quadratic_saturates_bound": True,
        },
    }


def simulate(protocol: dict[str, object]) -> list[dict[str, object]]:
    rng = np.random.default_rng(int(protocol["seed"]))
    visibility = float(protocol["visibility"])
    shots = int(protocol["shots_per_quadrature_per_circuit"])
    trials = int(protocol["monte_carlo_trials"])
    layer_time = float(protocol["layer_time"])
    reference_theta = float(protocol["reference_theta"])
    rows: list[dict[str, object]] = []
    for theta in protocol["theta_values"]:
        for curvature in protocol["curvatures"]:
            for depth in protocol["depths"]:
                duration = layer_time * int(depth)
                drift = quadratic_drift(float(curvature))
                estimates = simulate_rtr_local_estimator(
                    rng,
                    float(theta),
                    reference_theta,
                    int(depth),
                    duration,
                    drift,
                    visibility,
                    shots,
                    trials,
                )
                errors = estimates - float(theta)
                deterministic_bias = rtr_interpolation_bias(drift, duration)
                budget = physical_depth_cost(int(depth), shots)
                rows.append(
                    {
                        "estimator": "amplified_rtr",
                        "theta": float(theta),
                        "curvature": float(curvature),
                        "depth": int(depth),
                        "duration": duration,
                        "physical_depth_budget": budget,
                        "trials": trials,
                        "bias": float(np.mean(errors)),
                        "deterministic_bias": deterministic_bias,
                        "rmse": float(np.sqrt(np.mean(errors**2))),
                        "median_absolute_error": float(np.median(np.abs(errors))),
                        "q90_absolute_error": float(np.quantile(np.abs(errors), 0.9)),
                        "crossover_xi": float(curvature) * layer_time**2 * int(depth) ** 3,
                        "normalized_absolute_deterministic_bias": abs(deterministic_bias) * int(depth),
                    }
                )

        # Equal-cost direct control is a zero-drift scaling baseline.  Depth one
        # receives D times as many repetitions as the amplified depth-D block.
        for depth in protocol["depths"]:
            direct_shots = shots * int(depth)
            estimates = simulate_rtr_local_estimator(
                rng,
                float(theta),
                reference_theta,
                1,
                layer_time,
                affine_drift(0.0, 0.0),
                visibility,
                direct_shots,
                trials,
            )
            errors = estimates - float(theta)
            rows.append(
                {
                    "estimator": "direct_depth1_equal_cost",
                    "theta": float(theta),
                    "curvature": 0.0,
                    "depth": int(depth),
                    "duration": layer_time,
                    "physical_depth_budget": physical_depth_cost(1, direct_shots),
                    "trials": trials,
                    "bias": float(np.mean(errors)),
                    "deterministic_bias": 0.0,
                    "rmse": float(np.sqrt(np.mean(errors**2))),
                    "median_absolute_error": float(np.median(np.abs(errors))),
                    "q90_absolute_error": float(np.quantile(np.abs(errors), 0.9)),
                    "crossover_xi": 0.0,
                    "normalized_absolute_deterministic_bias": 0.0,
                }
            )
    return rows


def fit_summary(protocol: dict[str, object], analytic: dict[str, object], rows: list[dict[str, object]]) -> dict[str, object]:
    amplified_slopes = []
    direct_slopes = []
    for theta in protocol["theta_values"]:
        amplified = sorted(
            (
                row
                for row in rows
                if row["estimator"] == "amplified_rtr"
                and row["theta"] == theta
                and row["curvature"] == 0.0
            ),
            key=lambda row: row["physical_depth_budget"],
        )
        direct = sorted(
            (
                row
                for row in rows
                if row["estimator"] == "direct_depth1_equal_cost" and row["theta"] == theta
            ),
            key=lambda row: row["physical_depth_budget"],
        )
        amplified_slopes.append(
            fit_log_slope(
                np.asarray([row["physical_depth_budget"] for row in amplified[-5:]]),
                np.asarray([row["rmse"] for row in amplified[-5:]]),
            )[0]
        )
        direct_slopes.append(
            fit_log_slope(
                np.asarray([row["physical_depth_budget"] for row in direct[-5:]]),
                np.asarray([row["rmse"] for row in direct[-5:]]),
            )[0]
        )

    collapse_rows = [
        row
        for row in rows
        if row["estimator"] == "amplified_rtr" and row["curvature"] > 0
    ]
    x = np.asarray([row["crossover_xi"] for row in collapse_rows])
    y = np.asarray([row["normalized_absolute_deterministic_bias"] for row in collapse_rows])
    collapse_slope, collapse_intercept = np.polyfit(x, y, 1)
    prediction = collapse_slope * x + collapse_intercept
    residual = float(np.sum((y - prediction) ** 2))
    total = float(np.sum((y - float(np.mean(y))) ** 2))
    collapse_r_squared = 1.0 - residual / total

    gates = protocol["gates"]
    criteria = {
        "affine_cancels": abs(float(analytic["affine"]["interpolation_bias"]))
        <= float(gates["affine_cancellation_tolerance"]),
        "quadratic_ratio_exact": abs(
            float(analytic["quadratic"]["bias_over_kappa_T_squared"]) + 0.5
        )
        <= float(gates["quadratic_ratio_tolerance"]),
        "compact_bump_is_admissible": float(analytic["compact_bump"]["maximum_absolute_second_derivative"])
        <= float(analytic["compact_bump"]["registered_curvature_bound"]) * (1.0 + 1e-10),
        "compact_bump_is_indistinguishable": float(
            analytic["compact_bump"]["maximum_two_quadrature_probability_gap"]
        )
        <= float(gates["bump_probability_tolerance"]),
        "ideal_amplified_slope": all(
            float(gates["ideal_amplified_slope_range"][0]) <= value <= float(gates["ideal_amplified_slope_range"][1])
            for value in amplified_slopes
        ),
        "direct_slope": all(
            float(gates["direct_slope_range"][0]) <= value <= float(gates["direct_slope_range"][1])
            for value in direct_slopes
        ),
        "curvature_collapse": collapse_r_squared >= float(gates["minimum_collapse_r_squared"]),
    }
    mechanism_passes = all(criteria.values())
    return {
        "schema_version": 1,
        "protocol_sha256": sha256(PROTOCOL_PATH),
        "mechanism_verdict": "PASSES_MATHEMATICAL_PHASE0" if mechanism_passes else "FAILS_MATHEMATICAL_PHASE0",
        "astar_novelty_verdict": "PENDING_PRIMARY_SOURCE_AUDIT",
        "hardware_spending_authorized": False,
        "criteria": criteria,
        "amplified_zero_curvature_tail_slopes": amplified_slopes,
        "direct_equal_cost_tail_slopes": direct_slopes,
        "median_amplified_slope": float(np.median(amplified_slopes)),
        "median_direct_slope": float(np.median(direct_slopes)),
        "curvature_collapse": {
            "slope": float(collapse_slope),
            "intercept": float(collapse_intercept),
            "r_squared": collapse_r_squared,
            "prediction": "|bias|*D = 0.5*kappa*tau^2*D^3 for quadratic drift",
        },
        "correct_scope": (
            "The cube-root scale is the crossover where a D~1/epsilon Heisenberg-depth "
            "schedule ceases to be valid. It is not a universal accuracy floor: below it, "
            "one can reduce depth and use more shots, eventually returning toward SQL scaling."
        ),
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_report(summary: dict[str, object], analytic: dict[str, object]) -> None:
    bump = analytic["compact_bump"]
    collapse = summary["curvature_collapse"]
    report = f"""# Sequential-reference curvature boundary: Phase-0 report

## Mathematical verdict

**{summary['mechanism_verdict']}**.  A* novelty remains
**{summary['astar_novelty_verdict']}**.  No QPU run is authorised.

## Exact results

- Affine RTR interpolation bias: `{analytic['affine']['interpolation_bias']:.3g}`.
- Quadratic ratio `bias/(kappa T^2)`:
  `{analytic['quadratic']['bias_over_kappa_T_squared']:.12f}` (exact prediction `-0.5`).
- Compact-bump target shift: `{bump['theta_separation']:.12g}`.
- Compact-bump maximum `|d''|`: `{bump['maximum_absolute_second_derivative']:.12g}`
  against registered bound `{bump['registered_curvature_bound']:.12g}`.
- Maximum two-quadrature probability gap between the two lower-bound worlds:
  `{bump['maximum_two_quadrature_probability_gap']:.3g}`.
- Resulting two-point minimax absolute-risk lower bound:
  `{bump['minimax_absolute_risk_lower_bound']:.12g}`.

For every common drift with `|d''|<=kappa`, sequential equal-duration RTR
interpolation has error at most `kappa T^2/2`; quadratic drift saturates the
constant.  The compact target-only C2 bump establishes a matching
`Omega(kappa T^2)` indistinguishability lower bound.

## Shot-noise and resource controls

- Median zero-curvature amplified RMSE slope versus fully counted physical
  depth: `{summary['median_amplified_slope']:.4f}`.
- Median equal-cost direct-depth-one slope: `{summary['median_direct_slope']:.4f}`.
- Curvature collapse `R^2`: `{collapse['r_squared']:.12f}`.
- Fitted collapse slope: `{collapse['slope']:.12f}` (prediction `0.5`).

Thus the mechanism produces the crossover
`kappa tau^2 D^3 = Theta(1)` when a local Heisenberg schedule uses
`D=Theta(1/epsilon)`.  This is not an absolute estimation floor.  Below that
crossover a protocol may shorten coherent depth and buy more repetitions,
progressively reverting toward standard-quantum-limit scaling.

## Novelty boundary

Correct mathematics is necessary but not sufficient.  If the result is already
an immediate consequence of established sequential-reference interpolation or
clock/metrology bounds, this branch must be closed as A* novelty even though
the Phase-0 theorem mechanism passes.  Hardware work remains forbidden until
that independent literature gate is resolved.
"""
    (OUT / "FINAL_REPORT.md").write_text(report, encoding="utf-8")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    analytic = analytic_audit(protocol)
    rows = simulate(protocol)
    summary = fit_summary(protocol, analytic, rows)
    (OUT / "analytic_audit.json").write_text(json.dumps(analytic, indent=2), encoding="utf-8")
    write_csv(OUT / "monte_carlo.csv", rows)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUT / "run_manifest.json").write_text(
        json.dumps(
            {
                "created_utc": datetime.now(timezone.utc).isoformat(),
                "python": sys.version,
                "platform": platform.platform(),
                "numpy": np.__version__,
                "command": "python -m experiments.interleaved_drift_boundary_phase0.run_phase0",
                "protocol_sha256": sha256(PROTOCOL_PATH),
                "hardware_queries": 0,
                "qpu_observations": 0,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    write_report(summary, analytic)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

