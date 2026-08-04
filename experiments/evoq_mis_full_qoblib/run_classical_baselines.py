"""Exact and randomized classical baselines for the held-out QOBLIB MIS case."""

from __future__ import annotations

import platform
from collections import Counter
from time import perf_counter

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_array

import run_cycle as rc


REPLICATES = 15
STARTS_PER_REPLICATE = 1_000
SEEDS = [21_160_804 + 10_007 * replicate for replicate in range(REPLICATES)]


def is_independent(graph, selected) -> bool:
    chosen = set(selected)
    return all(u not in chosen or v not in chosen for u, v in graph.edges())


def randomized_min_degree(graph, rng: np.random.Generator) -> set:
    """Randomized tie-breaking in the minimum residual-degree heuristic."""
    remaining = set(graph.nodes())
    selected = set()
    adjacency = {node: set(graph[node]) for node in graph.nodes()}
    while remaining:
        residual_degree = {
            node: len(adjacency[node].intersection(remaining)) for node in remaining
        }
        minimum = min(residual_degree.values())
        tied = [node for node, degree in residual_degree.items() if degree == minimum]
        node = tied[int(rng.integers(len(tied)))]
        selected.add(node)
        remaining.discard(node)
        remaining.difference_update(adjacency[node])
    return selected


def distribution_summary(sizes: list[int], bks: int) -> dict:
    total = len(sizes)
    distribution = Counter(sizes)
    bks_hits = sum(size >= bks for size in sizes)
    near_hits = sum(size >= bks - 1 for size in sizes)
    return {
        "total_runs": total,
        "bks_hits": bks_hits,
        "bks_rate": bks_hits / total,
        "near_bks_hits": near_hits,
        "near_bks_rate": near_hits / total,
        "feasible_rate": 1.0,
        "mean_size": float(np.mean(sizes)),
        "median_size": float(np.median(sizes)),
        "best_size": max(sizes),
        "distribution": {str(size): count for size, count in sorted(distribution.items())},
        "wilson_bks": rc.wilson_lower(bks_hits, total),
        "wilson_near_bks": rc.wilson_lower(near_hits, total),
    }


def solve_highs_exact(case) -> dict:
    graph = case.graph
    nodes = sorted(graph.nodes())
    index = {node: i for i, node in enumerate(nodes)}
    rows, cols, data = [], [], []
    for row, (u, v) in enumerate(graph.edges()):
        rows.extend((row, row))
        cols.extend((index[u], index[v]))
        data.extend((1.0, 1.0))
    matrix = coo_array(
        (data, (rows, cols)), shape=(graph.number_of_edges(), len(nodes))
    ).tocsr()
    start = perf_counter()
    result = milp(
        -np.ones(len(nodes)),
        integrality=np.ones(len(nodes)),
        bounds=Bounds(0, 1),
        constraints=LinearConstraint(matrix, -np.inf, 1),
        options={"time_limit": 7_200, "mip_rel_gap": 0.0, "presolve": True},
    )
    elapsed = perf_counter() - start
    selected = [node for node, value in zip(nodes, result.x) if value > 0.5]
    if not result.success or not is_independent(graph, selected):
        raise RuntimeError(f"HiGHS failed to return a valid optimum: {result.message}")
    return {
        "solver": "scipy.optimize.milp/HiGHS",
        "success": bool(result.success),
        "status": int(result.status),
        "message": result.message,
        "objective_size": len(selected),
        "selected_vertices": selected,
        "elapsed_seconds": elapsed,
        "mip_node_count": int(result.mip_node_count),
        "mip_gap": float(result.mip_gap),
    }


def run_full_graph_heuristic(case) -> dict:
    rows = []
    all_sizes = []
    first_bks_global = None
    global_start = perf_counter()
    for replicate, seed in enumerate(SEEDS):
        rng = np.random.default_rng(seed)
        sizes = []
        first_bks = None
        start = perf_counter()
        for trial in range(STARTS_PER_REPLICATE):
            selected = randomized_min_degree(case.graph, rng)
            if not is_independent(case.graph, selected):
                raise AssertionError("full-graph greedy returned an infeasible set")
            size = len(selected)
            sizes.append(size)
            if size >= case.bks and first_bks is None:
                first_bks = trial + 1
            if size >= case.bks and first_bks_global is None:
                first_bks_global = len(all_sizes) + len(sizes)
        elapsed = perf_counter() - start
        all_sizes.extend(sizes)
        rows.append(
            {
                "replicate": replicate,
                "seed": seed,
                "elapsed_seconds": elapsed,
                "first_bks_trial": first_bks,
                "metrics": distribution_summary(sizes, case.bks),
            }
        )
    return {
        "method": "randomized_min_residual_degree_full_graph",
        "rows": rows,
        "summary": distribution_summary(all_sizes, case.bks),
        "elapsed_seconds": perf_counter() - global_start,
        "first_bks_global_trial": first_bks_global,
    }


def run_reduced_graph_heuristic(case) -> dict:
    reduced = case.reduction.reduced_graph
    reduced_nodes = sorted(reduced.nodes())
    rows = []
    all_sizes = []
    first_bks_global = None
    global_start = perf_counter()
    for replicate, seed in enumerate(SEEDS):
        rng = np.random.default_rng(seed)
        sizes = []
        first_bks = None
        start = perf_counter()
        for trial in range(STARTS_PER_REPLICATE):
            selected = randomized_min_degree(reduced, rng)
            bitstring = "".join("1" if node in selected else "0" for node in reduced_nodes)
            decoded = case.decoder.decode(bitstring)
            if not decoded.raw_feasible:
                raise AssertionError("reduced-graph greedy decoded to an infeasible set")
            size = int(decoded.raw_selected)
            sizes.append(size)
            if size >= case.bks and first_bks is None:
                first_bks = trial + 1
            if size >= case.bks and first_bks_global is None:
                first_bks_global = len(all_sizes) + len(sizes)
        elapsed = perf_counter() - start
        all_sizes.extend(sizes)
        rows.append(
            {
                "replicate": replicate,
                "seed": seed,
                "elapsed_seconds": elapsed,
                "first_bks_trial": first_bks,
                "metrics": distribution_summary(sizes, case.bks),
            }
        )
    return {
        "method": "randomized_min_residual_degree_qoblib_kernel",
        "rows": rows,
        "summary": distribution_summary(all_sizes, case.bks),
        "elapsed_seconds": perf_counter() - global_start,
        "first_bks_global_trial": first_bks_global,
    }


def main() -> None:
    preparation_start = perf_counter()
    case = rc.prepare_case(rc.TEST_NAME)
    preparation_elapsed = perf_counter() - preparation_start
    payload = {
        "stage": "classical_baselines",
        "created_at": rc.utc_now(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": __import__("scipy").__version__,
        "case": rc.case_metadata(case),
        "preparation_elapsed_seconds": preparation_elapsed,
        "replicates": REPLICATES,
        "starts_per_replicate": STARTS_PER_REPLICATE,
        "seeds": SEEDS,
        "exact": solve_highs_exact(case),
        "full_graph_heuristic": run_full_graph_heuristic(case),
        "reduced_graph_heuristic": run_reduced_graph_heuristic(case),
    }
    rc.write_json(rc.RESULTS / "classical_baselines.json", payload)
    exact = payload["exact"]
    full = payload["full_graph_heuristic"]["summary"]
    kernel = payload["reduced_graph_heuristic"]["summary"]
    print(
        f"HiGHS optimum={exact['objective_size']} in {exact['elapsed_seconds']:.6f}s; "
        f"full greedy BKS={full['bks_rate']:.4%}; "
        f"kernel greedy BKS={kernel['bks_rate']:.4%}"
    )


if __name__ == "__main__":
    main()
