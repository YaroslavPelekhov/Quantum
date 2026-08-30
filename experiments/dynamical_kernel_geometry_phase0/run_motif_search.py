"""Exhaustive rooted-petal search for a scalable dynamical-kernel separation."""

from __future__ import annotations

import csv
import itertools
import json
import math
import sys
from pathlib import Path

import networkx as nx
import numpy as np
from scipy.sparse.linalg import eigsh


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from experiments.dynamical_kernel_geometry_phase0.run_family import linear_fit  # noqa: E402
from experiments.quantum_safe_kernelization_phase0.qdk_core import (  # noqa: E402
    HardBlockadeSystem,
    evolve_success,
    gap_distortion,
    graph6,
    leaf_reduction,
    schedule,
)


OUT = ROOT / "results" / "dynamical_kernel_geometry_phase0"
SCREEN_STEPS = 120
CONFIRM_STEPS = 480
TIMES = (5.0, 10.0)
TOP_COUNT = 12


def petal_templates(size: int):
    pairs = list(itertools.combinations(range(size), 2))
    for edge_mask in range(1 << len(pairs)):
        internal_edges = tuple(pairs[index] for index in range(len(pairs)) if edge_mask & (1 << index))
        for hub_mask in range(1, 1 << size):
            hub_neighbors = tuple(index for index in range(size) if hub_mask & (1 << index))
            rooted = nx.Graph()
            rooted.add_nodes_from(range(size + 1))
            rooted.add_edges_from((first + 1, second + 1) for first, second in internal_edges)
            rooted.add_edges_from((0, node + 1) for node in hub_neighbors)
            if nx.is_connected(rooted):
                yield internal_edges, hub_neighbors


def compose_family(size: int, internal_edges, hub_neighbors, leaf_count: int, k: int) -> nx.Graph:
    graph = nx.Graph()
    hub = 0
    graph.add_nodes_from(range(1 + leaf_count + k * size))
    graph.add_edges_from((hub, leaf) for leaf in range(1, leaf_count + 1))
    for copy in range(k):
        offset = 1 + leaf_count + copy * size
        graph.add_edges_from((offset + first, offset + second) for first, second in internal_edges)
        graph.add_edges_from((hub, offset + node) for node in hub_neighbors)
    return graph


class PhysicsCache:
    def __init__(self):
        self.systems: dict[str, HardBlockadeSystem] = {}
        self.success: dict[tuple[str, float, int], float] = {}

    def system(self, graph: nx.Graph) -> HardBlockadeSystem:
        key = graph6(graph)
        if key not in self.systems:
            self.systems[key] = HardBlockadeSystem(graph)
        return self.systems[key]

    def evolve(self, graph: nx.Graph, total_time: float, steps: int) -> float:
        key = (graph6(graph), total_time, steps)
        if key not in self.success:
            self.success[key] = evolve_success(self.system(graph), total_time, steps=steps)
        return self.success[key]


def sparse_minimum_gap(system: HardBlockadeSystem) -> tuple[float, float]:
    grid = np.linspace(0.1, 0.9, 33)
    gaps = []
    for s in grid:
        omega, delta = schedule(float(s))
        hamiltonian = system.hamiltonian(omega, delta)
        if hamiltonian.shape[0] <= 256:
            values = np.linalg.eigvalsh(hamiltonian.toarray())[:2]
        else:
            values = np.sort(eigsh(hamiltonian, k=2, which="SA", return_eigenvectors=False, tol=1e-10))
        gaps.append(float(values[1] - values[0]))
    index = int(np.argmin(gaps))
    return gaps[index], float(grid[index])


def endpoint_bijective(original: HardBlockadeSystem, reduced: HardBlockadeSystem) -> bool:
    return original.alpha == reduced.alpha + 1 and len(original.optimum_masks) == len(reduced.optimum_masks)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    physics = PhysicsCache()
    families = []
    seen = set()
    for size in (2, 3):
        for internal_edges, hub_neighbors in petal_templates(size):
            for leaf_count in (1, 2):
                graphs = [compose_family(size, internal_edges, hub_neighbors, leaf_count, k) for k in (1, 2, 3)]
                signature = tuple(graph6(graph) for graph in graphs)
                if signature in seen:
                    continue
                seen.add(signature)
                reductions = [leaf_reduction(graph, 1) for graph in graphs]
                originals = [physics.system(graph) for graph in graphs]
                reduced_systems = [physics.system(reduction.graph) for reduction in reductions]
                if not all(endpoint_bijective(original, reduced) for original, reduced in zip(originals, reduced_systems)):
                    continue
                time_records = {}
                for total_time in TIMES:
                    log_ratios = []
                    differences = []
                    for graph, reduction in zip(graphs, reductions):
                        original_success = physics.evolve(graph, total_time, SCREEN_STEPS)
                        reduced_success = physics.evolve(reduction.graph, total_time, SCREEN_STEPS)
                        log_ratios.append(math.log(max(reduced_success, 1e-300) / max(original_success, 1e-300)))
                        differences.append(abs(reduced_success - original_success))
                    fit = linear_fit(log_ratios)
                    time_records[str(total_time)] = {
                        "log_ratios": log_ratios,
                        "absolute_differences": differences,
                        "fit": fit,
                    }
                best_time = max(TIMES, key=lambda value: time_records[str(value)]["fit"]["slope"])
                families.append(
                    {
                        "petal_size": size,
                        "internal_edges": [list(edge) for edge in internal_edges],
                        "hub_neighbors": list(hub_neighbors),
                        "leaf_count": leaf_count,
                        "signatures": list(signature),
                        "best_time": best_time,
                        "best_slope": time_records[str(best_time)]["fit"]["slope"],
                        "best_r2": time_records[str(best_time)]["fit"]["r2"],
                        "k3_difference": time_records[str(best_time)]["absolute_differences"][2],
                        "screen_records": time_records,
                    }
                )
    families.sort(key=lambda row: (float(row["best_slope"]), float(row["best_r2"])), reverse=True)
    confirmed = []
    for rank, family in enumerate(families[:TOP_COUNT]):
        size = int(family["petal_size"])
        internal_edges = tuple(tuple(edge) for edge in family["internal_edges"])
        hub_neighbors = tuple(family["hub_neighbors"])
        leaf_count = int(family["leaf_count"])
        total_time = float(family["best_time"])
        graphs = [compose_family(size, internal_edges, hub_neighbors, leaf_count, k) for k in (1, 2, 3)]
        reductions = [leaf_reduction(graph, 1) for graph in graphs]
        log_ratios = []
        differences = []
        gaps = []
        for graph, reduction in zip(graphs, reductions):
            original_success = physics.evolve(graph, total_time, CONFIRM_STEPS)
            reduced_success = physics.evolve(reduction.graph, total_time, CONFIRM_STEPS)
            log_ratios.append(math.log(max(reduced_success, 1e-300) / max(original_success, 1e-300)))
            differences.append(abs(reduced_success - original_success))
            original_gap, original_s = sparse_minimum_gap(physics.system(graph))
            reduced_gap, reduced_s = sparse_minimum_gap(physics.system(reduction.graph))
            gaps.append(
                {
                    "distortion": gap_distortion(original_gap, reduced_gap),
                    "original_gap": original_gap,
                    "original_s": original_s,
                    "reduced_gap": reduced_gap,
                    "reduced_s": reduced_s,
                }
            )
        fit = linear_fit(log_ratios)
        disconnected_k3 = 3.0 * log_ratios[0]
        product_fraction = abs(log_ratios[2] - disconnected_k3) / max(abs(disconnected_k3), 1e-15)
        passes = (
            fit["slope"] >= 0.15
            and fit["r2"] >= 0.95
            and differences[2] >= 0.25
            and max(record["distortion"] for record in gaps) <= 1.25
            and product_fraction >= 0.20
        )
        confirmed.append(
            {
                "rank": rank,
                "petal_size": size,
                "internal_edges": family["internal_edges"],
                "hub_neighbors": family["hub_neighbors"],
                "leaf_count": leaf_count,
                "best_time": total_time,
                "confirmed_log_ratios": log_ratios,
                "confirmed_differences": differences,
                "confirmed_slope": fit["slope"],
                "confirmed_r2": fit["r2"],
                "gap_records": gaps,
                "product_fractional_separation": product_fraction,
                "passes_all_gates": passes,
            }
        )
    serializable_families = []
    for family in families:
        serializable_families.append({**family, "screen_records": json.dumps(family["screen_records"], sort_keys=True)})
    write_csv(OUT / "motif_search_screen.csv", serializable_families)
    (OUT / "motif_search_confirmed.json").write_text(json.dumps(confirmed, indent=2, sort_keys=True), encoding="utf-8")
    summary = {
        "unique_grammar_families": len(seen),
        "endpoint_bijective_families": len(families),
        "confirmed_count": len(confirmed),
        "survivor_count": sum(bool(row["passes_all_gates"]) for row in confirmed),
        "best_screen_candidate": families[0] if families else None,
        "best_confirmed_candidate": max(confirmed, key=lambda row: float(row["confirmed_slope"]), default=None),
        "verdict": "CONTINUE" if any(row["passes_all_gates"] for row in confirmed) else "KILL_ROOTED_PETAL_GRAMMAR",
    }
    (OUT / "motif_search_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
