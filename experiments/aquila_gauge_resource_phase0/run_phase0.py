"""Run the frozen gauge-quotient resource screen with atomic checkpoints."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from pathlib import Path

import numpy as np

from experiments.aquila_gauge_resource_phase0.gauge_core import (
    adjacent_spectral_data,
    circular_gauge_cost,
    cube_complex,
    fit_log2_scaling,
    hashed_edge_phases,
    spectral_cost,
    transition_frequencies,
    wrap_angle,
)


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = ROOT / "experiments" / "aquila_gauge_resource_phase0"
OUTPUT = ROOT / "results" / "aquila_gauge_resource_phase0"

INTEGER_FIELDS = {"n", "target_id", "vertices", "edges", "faces", "status", "mip_node_count"}
FLOAT_FIELDS = {
    "physical_frequency_width_rad_per_us",
    "normalized_min_gap",
    "raw_spectral_cost",
    "max_abs_flux_rad",
    "median_abs_flux_rad",
    "elapsed_seconds",
    "objective_upper",
    "objective_lower",
    "mip_gap",
    "achieved_cost",
    "circular_total_variation",
    "constraint_error",
    "gauge_to_raw_ratio_upper",
    "certified_time_width_lower_rho_0p2",
}


def atomic_write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def atomic_write_json(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(json_safe(payload), indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def json_safe(value):
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, np.generic):
        return json_safe(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def serializable_row(row: dict) -> dict:
    return {
        key: value.item() if isinstance(value, np.generic) else value
        for key, value in row.items()
        if key not in {"theta", "representative", "order", "frequency_gaps"}
    }


def load_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        for key in INTEGER_FIELDS:
            row[key] = int(row[key])
        for key in FLOAT_FIELDS:
            row[key] = float(row[key])
        row["success"] = row["success"].lower() == "true"
    return rows


def finite_median(rows: list[dict], key: str) -> float:
    values = [row[key] for row in rows if math.isfinite(row[key])]
    return float(np.median(values)) if values else math.nan


def run(resume: bool = False) -> None:
    protocol = json.loads((EXPERIMENT / "protocol.json").read_text(encoding="utf-8"))
    OUTPUT.mkdir(parents=True, exist_ok=True)
    result_path = OUTPUT / "milp_instances.csv"
    existing = load_rows(result_path) if resume else []
    existing_by_key = {(row["cohort"], row["n"], row["target_id"]): row for row in existing}
    rows: list[dict] = []
    model = protocol["model"]
    optimizer = protocol["circular_milp"]

    for cohort_name in ("development", "heldout"):
        cohort = protocol[cohort_name]
        positions = np.asarray(cohort["positions_um"], dtype=float)
        mask = np.asarray(cohort["mask"], dtype=float)
        for n in cohort["n_values"]:
            complex_ = cube_complex(n)
            physical, normalized, width = transition_frequencies(
                n,
                positions,
                mask,
                model["c6_rad_per_us_um6"],
                model["local_detuning_span_rad_per_us"],
                complex_.edges,
            )
            try:
                order, gaps = adjacent_spectral_data(normalized)
                collision = False
            except ValueError:
                order = np.argsort(normalized, kind="stable")
                gaps = np.diff(normalized[order])
                collision = True
            for target_id in cohort["target_ids"]:
                key = (cohort_name, n, target_id)
                if key in existing_by_key:
                    rows.append(existing_by_key[key])
                    print(json.dumps({"resumed": key}), flush=True)
                    continue
                phases = hashed_edge_phases(
                    cohort["target_tag"],
                    n,
                    target_id,
                    complex_.edges,
                    protocol["targets"]["edge_phase_half_range_rad"],
                )
                flux = wrap_angle(complex_.curl @ phases)
                if collision:
                    result_row = {
                        "cohort": cohort_name,
                        "geometry": cohort["name"],
                        "n": n,
                        "target_id": target_id,
                        "vertices": len(complex_.vertices),
                        "edges": len(complex_.edges),
                        "faces": len(complex_.faces),
                        "physical_frequency_width_rad_per_us": width,
                        "normalized_min_gap": float(np.min(gaps)),
                        "raw_spectral_cost": math.nan,
                        "max_abs_flux_rad": float(np.max(np.abs(flux))),
                        "median_abs_flux_rad": float(np.median(np.abs(flux))),
                        "success": False,
                        "status": 4,
                        "message": "exact transition-frequency collision; MILP not defined",
                        "elapsed_seconds": 0.0,
                        "objective_upper": math.nan,
                        "objective_lower": math.nan,
                        "mip_gap": math.nan,
                        "mip_node_count": 0,
                        "achieved_cost": math.nan,
                        "circular_total_variation": math.nan,
                        "constraint_error": math.nan,
                        "gauge_to_raw_ratio_upper": math.nan,
                        "certified_time_width_lower_rho_0p2": math.nan,
                    }
                    rows.append(result_row)
                    atomic_write_csv(result_path, rows)
                    print(json.dumps(result_row), flush=True)
                    continue
                quotient = circular_gauge_cost(
                    phases,
                    complex_.gradient,
                    normalized,
                    winding_bound=optimizer["winding_bounds"][1],
                    relative_mip_gap=optimizer["relative_mip_gap"],
                    time_limit_seconds=optimizer["time_limit_seconds_per_instance"],
                )
                raw_cost = spectral_cost(phases, order, gaps)
                result_row = {
                    "cohort": cohort_name,
                    "geometry": cohort["name"],
                    "n": n,
                    "target_id": target_id,
                    "vertices": len(complex_.vertices),
                    "edges": len(complex_.edges),
                    "faces": len(complex_.faces),
                    "physical_frequency_width_rad_per_us": width,
                    "normalized_min_gap": float(np.min(gaps)),
                    "raw_spectral_cost": raw_cost,
                    "max_abs_flux_rad": float(np.max(np.abs(flux))),
                    "median_abs_flux_rad": float(np.median(np.abs(flux))),
                    **serializable_row(quotient),
                }
                lower = result_row["objective_lower"]
                result_row["gauge_to_raw_ratio_upper"] = (
                    result_row["objective_upper"] / raw_cost if raw_cost > 0 else math.nan
                )
                result_row["certified_time_width_lower_rho_0p2"] = (
                    2.0 * optimizer["response_margin_rho_for_bound"] / math.pi * lower
                    if math.isfinite(lower)
                    else math.nan
                )
                rows.append(result_row)
                atomic_write_csv(result_path, rows)
                print(json.dumps(result_row), flush=True)

    aggregates = []
    for cohort_name in ("development", "heldout"):
        n_values = protocol[cohort_name]["n_values"]
        for n in n_values:
            selected = [row for row in rows if row["cohort"] == cohort_name and row["n"] == n]
            aggregates.append(
                {
                    "cohort": cohort_name,
                    "n": n,
                    "instances": len(selected),
                    "median_objective_lower": finite_median(selected, "objective_lower"),
                    "median_objective_upper": finite_median(selected, "objective_upper"),
                    "median_raw_cost": finite_median(selected, "raw_spectral_cost"),
                    "median_gauge_to_raw_ratio_upper": finite_median(
                        selected, "gauge_to_raw_ratio_upper"
                    ),
                    "median_max_abs_flux_rad": finite_median(selected, "max_abs_flux_rad"),
                    "max_mip_gap": (
                        max(row["mip_gap"] for row in selected if math.isfinite(row["mip_gap"]))
                        if any(math.isfinite(row["mip_gap"]) for row in selected)
                        else math.nan
                    ),
                    "all_success": all(row["success"] for row in selected),
                }
            )
    atomic_write_csv(OUTPUT / "scaling_aggregate.csv", aggregates)

    fits = {}
    fit_ranges = {"development": (4, 7), "heldout": (5, 8)}
    for cohort_name, (minimum_n, maximum_n) in fit_ranges.items():
        selected = [
            row
            for row in aggregates
            if row["cohort"] == cohort_name and minimum_n <= row["n"] <= maximum_n
            and math.isfinite(row["median_objective_lower"])
            and row["median_objective_lower"] > 0
        ]
        fits[cohort_name] = (
            fit_log2_scaling(
                np.asarray([row["n"] for row in selected]),
                np.asarray([row["median_objective_lower"] for row in selected]),
            )
            if len(selected) >= 2
            else {"slope": math.nan, "intercept": math.nan, "r_squared": math.nan}
        )

    gates = protocol["registered_numerical_gates"]
    finite_gaps = [row["mip_gap"] for row in rows if math.isfinite(row["mip_gap"])]
    gate_results = {
        "all_frequency_collisions_absent": all(
            math.isfinite(row["normalized_min_gap"]) and row["normalized_min_gap"] > 0
            for row in rows
        ),
        "all_solver_relative_gaps_at_most": (
            len(finite_gaps) == len(rows) and max(finite_gaps) <= gates["all_solver_relative_gaps_at_most"]
        ),
        "development_log2_median_cost_slope_min": (
            fits["development"]["slope"] >= gates["development_log2_median_cost_slope_min"]
        ),
        "development_log2_fit_r2_min": (
            fits["development"]["r_squared"] >= gates["development_log2_fit_r2_min"]
        ),
        "heldout_log2_median_cost_slope_min": (
            fits["heldout"]["slope"] >= gates["heldout_log2_median_cost_slope_min"]
        ),
        "heldout_log2_fit_r2_min": (
            fits["heldout"]["r_squared"] >= gates["heldout_log2_fit_r2_min"]
        ),
        "median_max_abs_flux_rad_min": (
            all(math.isfinite(row["median_max_abs_flux_rad"]) for row in aggregates)
            and min(row["median_max_abs_flux_rad"] for row in aggregates)
            >= gates["median_max_abs_flux_rad_min"]
        ),
    }
    summary = {
        "protocol_version": protocol["version"],
        "instances": len(rows),
        "fits": fits,
        "gate_results": gate_results,
        "all_numerical_gates_pass": all(gate_results.values()),
        "astar_status": "NOT_EVALUATED_BY_NUMERICS_ALONE",
        "qpu_eligible": False,
        "qpu_tasks_submitted": 0,
        "failure_counts": {
            "frequency_collision_instances": sum(row["status"] == 4 for row in rows),
            "solver_nonoptimal_instances": sum(row["status"] not in {0, 4} for row in rows),
        },
    }
    atomic_write_json(OUTPUT / "phase0_summary.json", summary)
    print(json.dumps(json_safe(summary), indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true", help="reuse atomic completed rows")
    arguments = parser.parse_args()
    run(resume=arguments.resume)
