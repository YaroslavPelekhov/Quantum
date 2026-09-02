"""Diagnose the frozen held-out collision with a disclosed 0.001 um shift."""

from __future__ import annotations

import argparse
import json
import math
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
from experiments.aquila_gauge_resource_phase0.run_phase0 import (
    atomic_write_csv,
    atomic_write_json,
    finite_median,
    load_rows,
    serializable_row,
)


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = ROOT / "experiments" / "aquila_gauge_resource_phase0"
OUTPUT = ROOT / "results" / "aquila_gauge_resource_phase0"


def run(resume: bool = False) -> None:
    protocol = json.loads((EXPERIMENT / "protocol.json").read_text(encoding="utf-8"))
    cohort = protocol["heldout"]
    model = protocol["model"]
    optimizer = protocol["circular_milp"]
    positions = np.asarray(cohort["positions_um"], dtype=float)
    positions[4, 0] += 0.001
    mask = np.asarray(cohort["mask"], dtype=float)
    result_path = OUTPUT / "posthoc_milp_instances.csv"
    existing = load_rows(result_path) if resume else []
    existing_by_key = {(row["cohort"], row["n"], row["target_id"]): row for row in existing}
    rows: list[dict] = []

    for n in (5, 6, 7, 8):
        complex_ = cube_complex(n)
        _, normalized, width = transition_frequencies(
            n,
            positions,
            mask,
            model["c6_rad_per_us_um6"],
            model["local_detuning_span_rad_per_us"],
            complex_.edges,
        )
        order, gaps = adjacent_spectral_data(normalized)
        for target_id in cohort["target_ids"]:
            key = ("posthoc", n, target_id)
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
                "cohort": "posthoc",
                "geometry": "geometry_B_site4_x_plus_0p001um",
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
            result_row["gauge_to_raw_ratio_upper"] = result_row["objective_upper"] / raw_cost
            result_row["certified_time_width_lower_rho_0p2"] = (
                2.0 * optimizer["response_margin_rho_for_bound"] / math.pi * lower
                if math.isfinite(lower)
                else math.nan
            )
            rows.append(result_row)
            atomic_write_csv(result_path, rows)
            print(json.dumps(result_row), flush=True)

    aggregates = []
    for n in (5, 6, 7, 8):
        selected = [row for row in rows if row["n"] == n]
        aggregates.append(
            {
                "n": n,
                "instances": len(selected),
                "median_objective_lower": finite_median(selected, "objective_lower"),
                "median_objective_upper": finite_median(selected, "objective_upper"),
                "median_raw_cost": finite_median(selected, "raw_spectral_cost"),
                "median_gauge_to_raw_ratio_upper": finite_median(
                    selected, "gauge_to_raw_ratio_upper"
                ),
                "median_max_abs_flux_rad": finite_median(selected, "max_abs_flux_rad"),
                "max_mip_gap": max(row["mip_gap"] for row in selected),
                "optimal_instances": sum(row["success"] for row in selected),
            }
        )
    atomic_write_csv(OUTPUT / "posthoc_scaling_aggregate.csv", aggregates)
    fit = fit_log2_scaling(
        np.asarray([row["n"] for row in aggregates]),
        np.asarray([row["median_objective_lower"] for row in aggregates]),
    )
    summary = {
        "posthoc": True,
        "change": "geometry B site 4 x coordinate +0.001 um",
        "does_not_change_frozen_verdict": True,
        "instances": len(rows),
        "optimal_instances": sum(row["success"] for row in rows),
        "fit_log2_median_dual_lower": fit,
        "qpu_tasks_submitted": 0,
    }
    atomic_write_json(OUTPUT / "posthoc_summary.json", summary)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true")
    arguments = parser.parse_args()
    run(resume=arguments.resume)
