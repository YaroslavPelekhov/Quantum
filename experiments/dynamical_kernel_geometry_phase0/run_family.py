"""Run the frozen connected windmill-leaf separation-family experiment."""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

import networkx as nx
import numpy as np
from scipy.linalg import eigh


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from experiments.quantum_safe_kernelization_phase0.qdk_core import (  # noqa: E402
    HardBlockadeSystem,
    evolve_success,
    gap_distortion,
    graph6,
    leaf_reduction,
    minimum_gap,
    minimum_gap_window,
    schedule,
)


OUT = ROOT / "results" / "dynamical_kernel_geometry_phase0"
TIMES = (5.0, 10.0, 20.0)
STEPS = 480


def windmill_leaf(k: int) -> nx.Graph:
    graph = nx.Graph()
    leaf, hub = 0, 1
    graph.add_edge(leaf, hub)
    for index in range(k):
        first = 2 + 2 * index
        second = first + 1
        graph.add_edges_from(((hub, first), (hub, second), (first, second)))
    return graph


def unit_disk_positions(k: int) -> dict[int, tuple[float, float]]:
    if k > 4:
        raise ValueError("the direct unit-disk construction supports k <= 4")
    positions = {1: (0.0, 0.0)}
    radius = 0.98
    half_pair_angle = math.radians(2.0)
    cluster_count = k + 1
    positions[0] = (radius, 0.0)
    for index in range(k):
        angle = 2.0 * math.pi * (index + 1) / cluster_count
        for offset, node in ((-half_pair_angle, 2 + 2 * index), (half_pair_angle, 3 + 2 * index)):
            positions[node] = (radius * math.cos(angle + offset), radius * math.sin(angle + offset))
    return positions


def layout_is_exact(graph: nx.Graph, positions: dict[int, tuple[float, float]], threshold: float = 1.0) -> bool:
    nodes = list(graph.nodes())
    realised = set()
    for first_index, first in enumerate(nodes):
        for second in nodes[first_index + 1 :]:
            distance = math.dist(positions[first], positions[second])
            if distance <= threshold + 1e-12:
                realised.add(tuple(sorted((first, second))))
    expected = {tuple(sorted(edge)) for edge in graph.edges()}
    return realised == expected


def hprime(system: HardBlockadeSystem, s: float) -> np.ndarray:
    if s < 0.1:
        return -5.0 * system.flip.toarray()
    if s < 0.9:
        return np.diag(-5.0 * system.counts)
    return 5.0 * system.flip.toarray()


def geometry_at(system: HardBlockadeSystem, s: float) -> tuple[float, float]:
    omega, delta = schedule(s)
    values, vectors = eigh(system.hamiltonian(omega, delta).toarray())
    gaps = values[1:] - values[0]
    source = hprime(system, s) @ vectors[:, 0]
    couplings = vectors[:, 1:].T @ source
    metric = float(np.sum(np.abs(couplings) ** 2 / gaps**2))
    action = float(np.sum(np.abs(couplings) ** 2 / gaps**4))
    return metric, action


def geometry_integrals(system: HardBlockadeSystem) -> dict[str, float]:
    segments = {
        "ramp_up": np.linspace(0.02, 0.08, 4),
        "sweep": np.linspace(0.12, 0.88, 20),
        "ramp_down": np.linspace(0.92, 0.98, 4),
    }
    output = {}
    for name, grid in segments.items():
        metrics = []
        actions = []
        for s in grid:
            metric, action = geometry_at(system, float(s))
            metrics.append(math.sqrt(metric))
            actions.append(math.sqrt(action))
        output[f"{name}_path_length"] = float(np.trapezoid(metrics, grid))
        output[f"{name}_transition_action"] = float(np.trapezoid(actions, grid))
    return output


def linear_fit(values: list[float]) -> dict[str, float]:
    x = np.arange(1, len(values) + 1, dtype=float)
    y = np.asarray(values, dtype=float)
    slope, intercept = np.polyfit(x, y, 1)
    predicted = slope * x + intercept
    residual = float(np.sum((y - predicted) ** 2))
    total = float(np.sum((y - np.mean(y)) ** 2))
    return {"slope": float(slope), "intercept": float(intercept), "r2": 1.0 if total == 0 else 1.0 - residual / total}


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    family_rows = []
    dynamics_rows = []
    geometry_rows = []
    k1_success: dict[float, tuple[float, float]] = {}

    for k in range(1, 6):
        graph = windmill_leaf(k)
        positions = unit_disk_positions(k) if k <= 4 else None
        reduction = leaf_reduction(graph, 0)
        original = HardBlockadeSystem(graph)
        reduced = HardBlockadeSystem(reduction.graph)
        if original.alpha != reduced.alpha + 1 or len(original.optimum_masks) != len(reduced.optimum_masks):
            raise AssertionError("family endpoint lift is not value- and degeneracy-preserving")
        full_original, full_original_s = minimum_gap(original)
        full_reduced, full_reduced_s = minimum_gap(reduced)
        interior_original, interior_original_s = minimum_gap_window(original, 0.1, 0.9, points=41)
        interior_reduced, interior_reduced_s = minimum_gap_window(reduced, 0.1, 0.9, points=41)
        family_rows.append(
            {
                "k": k,
                "n": original.n,
                "removed_vertices": 2,
                "graph6": graph6(graph),
                "reduced_graph6": graph6(reduction.graph),
                "hilbert_dimension": len(original.masks),
                "reduced_hilbert_dimension": len(reduced.masks),
                "alpha": original.alpha,
                "optimum_degeneracy": len(original.optimum_masks),
                "unit_disk_layout_exact": layout_is_exact(graph, positions) if positions is not None else False,
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
            disconnected_original = k1_success[total_time][0] ** k
            disconnected_reduced = k1_success[total_time][1] ** k
            dynamics_rows.append(
                {
                    "k": k,
                    "total_time": total_time,
                    "steps": STEPS,
                    "original_success": original_success,
                    "reduced_success": reduced_success,
                    "absolute_difference": abs(reduced_success - original_success),
                    "log_success_ratio": math.log(max(reduced_success, 1e-300) / max(original_success, 1e-300)),
                    "disconnected_original_success": disconnected_original,
                    "disconnected_reduced_success": disconnected_reduced,
                    "disconnected_log_success_ratio": math.log(
                        max(disconnected_reduced, 1e-300) / max(disconnected_original, 1e-300)
                    ),
                }
            )
        if k <= 4:
            original_geometry = geometry_integrals(original)
            reduced_geometry = geometry_integrals(reduced)
            row: dict[str, object] = {"k": k}
            for key in original_geometry:
                row[f"original_{key}"] = original_geometry[key]
                row[f"reduced_{key}"] = reduced_geometry[key]
                row[f"absolute_{key}_difference"] = abs(original_geometry[key] - reduced_geometry[key])
            geometry_rows.append(row)

    fits = {}
    for total_time in TIMES:
        values = [
            float(row["log_success_ratio"])
            for row in dynamics_rows
            if float(row["total_time"]) == total_time
        ]
        fits[str(total_time)] = linear_fit(values)
    best_time = max(TIMES, key=lambda value: fits[str(value)]["slope"])
    best_fit = fits[str(best_time)]
    k5_row = next(row for row in dynamics_rows if row["k"] == 5 and row["total_time"] == best_time)
    product_separation = abs(float(k5_row["log_success_ratio"]) - float(k5_row["disconnected_log_success_ratio"]))
    product_reference = abs(float(k5_row["disconnected_log_success_ratio"]))
    product_fraction = product_separation / product_reference if product_reference else 0.0
    criteria = {
        "interior_gap_at_most_1p25": max(float(row["interior_gap_distortion"]) for row in family_rows) <= 1.25,
        "log_ratio_slope_and_r2": best_fit["slope"] >= 0.15 and best_fit["r2"] >= 0.95,
        "beats_disconnected_product_baseline": product_fraction >= 0.20,
        "geometry_monotone_while_gap_flat": False,
        "prior_art_clear": True,
    }
    criteria["phase0_survives"] = all(criteria.values())
    summary = {
        "family": "shared-hub windmill plus one leaf",
        "k_range": [1, 5],
        "fits": fits,
        "best_time": best_time,
        "best_fit": best_fit,
        "k5_product_log_ratio_fractional_separation": product_fraction,
        "maximum_interior_gap_distortion": max(float(row["interior_gap_distortion"]) for row in family_rows),
        "criteria_before_geometry_analysis": criteria,
    }
    write_csv(OUT / "family_spectra.csv", family_rows)
    write_csv(OUT / "family_dynamics.csv", dynamics_rows)
    write_csv(OUT / "family_geometry.csv", geometry_rows)
    (OUT / "summary_preanalysis.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    (OUT / "unit_disk_layouts.json").write_text(
        json.dumps({str(k): unit_disk_positions(k) for k in range(1, 5)}, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
