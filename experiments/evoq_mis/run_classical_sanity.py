from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from qaoa_mis import GraphInstance, enumerate_exact_space
from run_confirmatory import frozen_graphs as confirmatory_graphs
from run_random_subset_robustness import frozen_graphs as random_subset_graphs
from run_scaleup_audit import build_scale_graphs as scaleup_graphs


OUTPUT_DIR = Path(__file__).resolve().parent / "results_classical_sanity"


def greedy_from_order(graph: GraphInstance, order: np.ndarray) -> int:
    neighbors = [set() for _ in range(graph.n)]
    for u, v in graph.edges:
        neighbors[u].add(v)
        neighbors[v].add(u)
    selected: set[int] = set()
    for vertex in order:
        vertex = int(vertex)
        if not (neighbors[vertex] & selected):
            selected.add(vertex)
    return len(selected)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    suites = {
        "scaleup_first_k": scaleup_graphs(),
        "confirmatory_first_k": confirmatory_graphs(),
        "random_induced": random_subset_graphs(),
    }
    started = time.perf_counter()
    rows = []
    for suite_name, graphs in suites.items():
        for graph_index, graph in enumerate(graphs):
            exact = enumerate_exact_space(graph)
            degrees = graph.degrees
            degree_order = np.lexsort((np.arange(graph.n), degrees))
            deterministic = greedy_from_order(graph, degree_order)
            rng = np.random.default_rng(20261200 + graph_index + 100 * len(rows))
            restart_values = [greedy_from_order(graph, rng.permutation(graph.n)) for _ in range(1000)]
            uniform = np.full(1 << graph.n, 1.0 / (1 << graph.n), dtype=float)
            feasible_probability = float(uniform[exact.feasible].sum())
            expected_feasible_size = float(np.dot(uniform[exact.feasible], exact.sizes[exact.feasible]))
            rows.append({
                "suite": suite_name,
                "graph": graph.name,
                "vertices": graph.n,
                "edges": len(graph.edges),
                "exact_optimum": exact.optimum,
                "minimum_degree_greedy_size": deterministic,
                "minimum_degree_greedy_ratio": deterministic / exact.optimum,
                "random_order_greedy_1000_best_size": max(restart_values),
                "random_order_greedy_1000_best_ratio": max(restart_values) / exact.optimum,
                "random_order_greedy_1000_mean_ratio": float(np.mean(restart_values) / exact.optimum),
                "uniform_feasible_probability": feasible_probability,
                "uniform_approximation_ratio_unconditional": expected_feasible_size / exact.optimum,
            })
    report = {
        "experiment": "Classical and uniform-state sanity controls",
        "warning": "Classical greedy heuristics are not runtime-matched QAOA baselines; they bound interpretation and rule out quantum-advantage claims.",
        "random_restarts_per_graph": 1000,
        "seconds": time.perf_counter() - started,
        "rows": rows,
        "summary": {
            "graphs": len(rows),
            "minimum_degree_greedy_optimal_count": sum(row["minimum_degree_greedy_ratio"] == 1.0 for row in rows),
            "random_order_1000_optimal_count": sum(row["random_order_greedy_1000_best_ratio"] == 1.0 for row in rows),
            "minimum_degree_greedy_mean_ratio": float(np.mean([row["minimum_degree_greedy_ratio"] for row in rows])),
            "random_order_1000_best_mean_ratio": float(np.mean([row["random_order_greedy_1000_best_ratio"] for row in rows])),
        },
    }
    (OUTPUT_DIR / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
