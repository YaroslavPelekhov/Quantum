"""Run the frozen constant-deficit connected-family follow-up."""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

import networkx as nx
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from experiments.dynamical_kernel_geometry_phase0.run_family import (  # noqa: E402
    STEPS,
    TIMES,
    geometry_integrals,
    linear_fit,
)
from experiments.quantum_safe_kernelization_phase0.qdk_core import (  # noqa: E402
    HardBlockadeSystem,
    evolve_success,
    gap_distortion,
    graph6,
    leaf_reduction,
    minimum_gap,
    minimum_gap_window,
)


OUT = ROOT / "results" / "dynamical_kernel_geometry_phase0"


def constant_deficit_graph(k: int) -> nx.Graph:
    graph = nx.Graph()
    leaf, hub, sibling = 0, 1, 2
    graph.add_edges_from(((leaf, hub), (sibling, hub)))
    for index in range(k):
        first = 3 + 2 * index
        second = first + 1
        graph.add_edges_from(((first, second), (hub, first)))
    return graph


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    spectra = []
    dynamics = []
    geometry = []
    k1_success: dict[float, tuple[float, float]] = {}

    for k in range(1, 5):
        graph = constant_deficit_graph(k)
        reduction = leaf_reduction(graph, 0)
        original = HardBlockadeSystem(graph)
        reduced = HardBlockadeSystem(reduction.graph)
        if original.alpha != k + 2 or reduced.alpha + 1 != original.alpha:
            raise AssertionError("constant-deficit family MIS value mismatch")
        if len(original.optimum_masks) != 2**k or len(reduced.optimum_masks) != 2**k:
            raise AssertionError("constant-deficit family endpoint lift is not bijective")
        full_original, full_original_s = minimum_gap(original)
        full_reduced, full_reduced_s = minimum_gap(reduced)
        interior_original, interior_original_s = minimum_gap_window(original, 0.1, 0.9, points=41)
        interior_reduced, interior_reduced_s = minimum_gap_window(reduced, 0.1, 0.9, points=41)
        spectra.append(
            {
                "k": k,
                "n": original.n,
                "graph6": graph6(graph),
                "reduced_graph6": graph6(reduction.graph),
                "hilbert_dimension": len(original.masks),
                "reduced_hilbert_dimension": len(reduced.masks),
                "alpha": original.alpha,
                "optimum_degeneracy": len(original.optimum_masks),
                "hub_sector_classical_deficit": 1,
                "full_original_gap": full_original,
                "full_original_argmin_s": full_original_s,
                "full_reduced_gap": full_reduced,
                "full_reduced_argmin_s": full_reduced_s,
                "full_gap_distortion": gap_distortion(full_original, full_reduced),
                "interior_original_gap": interior_original,
                "interior_original_argmin_s": interior_original_s,
                "interior_reduced_gap": interior_reduced,
                "interior_reduced_argmin_s": interior_reduced_s,
                "interior_gap_distortion": gap_distortion(interior_original, interior_reduced),
            }
        )
        for total_time in TIMES:
            original_success = evolve_success(original, total_time, steps=STEPS)
            reduced_success = evolve_success(reduced, total_time, steps=STEPS)
            if k == 1:
                k1_success[total_time] = (original_success, reduced_success)
            product_original = k1_success[total_time][0] ** k
            product_reduced = k1_success[total_time][1] ** k
            dynamics.append(
                {
                    "k": k,
                    "total_time": total_time,
                    "original_success": original_success,
                    "reduced_success": reduced_success,
                    "absolute_difference": abs(reduced_success - original_success),
                    "log_success_ratio": math.log(max(reduced_success, 1e-300) / max(original_success, 1e-300)),
                    "disconnected_log_success_ratio": math.log(
                        max(product_reduced, 1e-300) / max(product_original, 1e-300)
                    ),
                }
            )
        if k <= 3:
            original_geometry = geometry_integrals(original)
            reduced_geometry = geometry_integrals(reduced)
            row: dict[str, object] = {"k": k}
            for key in original_geometry:
                row[f"original_{key}"] = original_geometry[key]
                row[f"reduced_{key}"] = reduced_geometry[key]
                row[f"absolute_{key}_difference"] = abs(original_geometry[key] - reduced_geometry[key])
            geometry.append(row)

    fits = {
        str(total_time): linear_fit(
            [float(row["log_success_ratio"]) for row in dynamics if row["total_time"] == total_time]
        )
        for total_time in TIMES
    }
    best_time = max(TIMES, key=lambda total_time: fits[str(total_time)]["slope"])
    best_fit = fits[str(best_time)]
    k4 = next(row for row in dynamics if row["k"] == 4 and row["total_time"] == best_time)
    product_fraction = abs(float(k4["log_success_ratio"]) - float(k4["disconnected_log_success_ratio"])) / max(
        abs(float(k4["disconnected_log_success_ratio"])), 1e-15
    )
    action_differences = [float(row["absolute_sweep_transition_action_difference"]) for row in geometry]
    success_differences = [
        float(row["absolute_difference"])
        for row in dynamics
        if row["total_time"] == best_time and int(row["k"]) <= 3
    ]
    action_monotone_same_direction = bool(
        np.all(np.diff(action_differences) >= 0) == np.all(np.diff(success_differences) >= 0)
        and (np.all(np.diff(action_differences) >= 0) or np.all(np.diff(action_differences) <= 0))
        and (np.all(np.diff(success_differences) >= 0) or np.all(np.diff(success_differences) <= 0))
    )
    criteria = {
        "interior_gap_at_most_1p25": max(float(row["interior_gap_distortion"]) for row in spectra) <= 1.25,
        "log_ratio_slope_and_r2": best_fit["slope"] >= 0.15 and best_fit["r2"] >= 0.95,
        "k4_absolute_difference_at_least_0p25": float(k4["absolute_difference"]) >= 0.25,
        "geometry_monotone_with_success": action_monotone_same_direction,
        "beats_disconnected_product_baseline": product_fraction >= 0.20,
    }
    criteria["phase0_survives"] = all(criteria.values())
    summary = {
        "family": "constant-deficit hub with two leaves and k one-sided edges",
        "fits": fits,
        "best_time": best_time,
        "best_fit": best_fit,
        "k4_at_best_time": k4,
        "k4_product_fractional_separation": product_fraction,
        "maximum_interior_gap_distortion": max(float(row["interior_gap_distortion"]) for row in spectra),
        "action_differences_k1_to_k3": action_differences,
        "success_differences_k1_to_k3": success_differences,
        "criteria": criteria,
        "verdict": "CONTINUE" if criteria["phase0_survives"] else "KILL_CONSTANT_DEFICIT_FAMILY",
    }
    write_csv(OUT / "constant_deficit_spectra.csv", spectra)
    write_csv(OUT / "constant_deficit_dynamics.csv", dynamics)
    write_csv(OUT / "constant_deficit_geometry.csv", geometry)
    (OUT / "constant_deficit_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
