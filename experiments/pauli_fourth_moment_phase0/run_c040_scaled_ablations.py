"""C040: scaled baseline and ablation campaign for the C038 line-graph theorem.

The finite atlas in C039 is replaced by preregistered sparse graph ensembles,
four weight regimes, a hierarchy of bounded odd-cycle constraints, and
structured obstruction families whose behavior persists with graph size.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools as it
import json
import math
import time
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from scipy.optimize import linprog


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results" / "pauli_fourth_moment_phase0"
FIGURES = Path(__file__).resolve().parent / "paper_c038" / "figures"
SEED = 20260917
ORDERS = (10, 14, 18, 22, 26, 30)
REPLICATES = 6
WEIGHT_MODELS = ("uniform", "integer", "lognormal", "pareto")
BASELINES = ("degree", "clique", "odd5", "odd7", "odd9")


def edges_of(graph: nx.Graph) -> tuple[tuple[int, int], ...]:
    return tuple(sorted(tuple(sorted(edge)) for edge in graph.edges()))


def graph_ensembles(rng: np.random.Generator):
    for order in ORDERS:
        for replicate in range(REPLICATES):
            for family in ("erdos_renyi", "random_regular", "small_world", "geometric", "preferential"):
                seed = int(rng.integers(1, 2**31 - 1))
                if family == "erdos_renyi":
                    graph = nx.gnp_random_graph(order, 4.0 / (order - 1), seed=seed)
                elif family == "random_regular":
                    graph = nx.random_regular_graph(3, order, seed=seed)
                elif family == "small_world":
                    graph = nx.watts_strogatz_graph(order, 4, 0.2, seed=seed)
                elif family == "geometric":
                    radius = math.sqrt(4.5 / (math.pi * order))
                    graph = nx.random_geometric_graph(order, radius, seed=seed)
                else:
                    graph = nx.barabasi_albert_graph(order, 2, seed=seed)
                graph = nx.convert_node_labels_to_integers(graph, ordering="sorted")
                if not graph.number_of_edges():
                    raise AssertionError((family, order, replicate, "empty graph"))
                yield family, order, replicate, seed, graph


def weight_vectors(edge_count: int, rng: np.random.Generator) -> dict[str, np.ndarray]:
    raw_lognormal = rng.lognormal(mean=0.0, sigma=1.0, size=edge_count)
    raw_pareto = rng.pareto(a=2.0, size=edge_count) + 1.0
    return {
        "uniform": np.ones(edge_count),
        "integer": rng.integers(1, 10, size=edge_count).astype(float),
        "lognormal": np.clip(raw_lognormal, 0.1, 20.0),
        "pareto": np.clip(raw_pareto, 1.0, 20.0),
    }


def odd_cycles_by_length(graph: nx.Graph, maximum: int = 9):
    cycles: dict[int, set[tuple[tuple[int, int], ...]]] = defaultdict(set)
    for cycle in nx.simple_cycles(graph, length_bound=maximum):
        length = len(cycle)
        if length < 5 or length % 2 == 0:
            continue
        cycle_edges = tuple(sorted(tuple(sorted((cycle[i], cycle[(i + 1) % length])))
                                   for i in range(length)))
        cycles[length].add(cycle_edges)
    return {length: tuple(sorted(values)) for length, values in cycles.items()}


def constraint_hierarchy(graph: nx.Graph, edges: tuple[tuple[int, int], ...]):
    index = {edge: i for i, edge in enumerate(edges)}
    degree_rows, degree_rhs = [], []
    for vertex in sorted(graph):
        row = np.zeros(len(edges))
        for edge in graph.edges(vertex):
            row[index[tuple(sorted(edge))]] = 1.0
        degree_rows.append(row)
        degree_rhs.append(1.0)

    triangle_rows, triangle_rhs = [], []
    for triple in nx.enumerate_all_cliques(graph):
        if len(triple) < 3:
            continue
        if len(triple) > 3:
            break
        row = np.zeros(len(edges))
        for edge in it.combinations(sorted(triple), 2):
            row[index[tuple(sorted(edge))]] = 1.0
        triangle_rows.append(row)
        triangle_rhs.append(1.0)

    cycles = odd_cycles_by_length(graph)
    cycle_rows: dict[int, list[np.ndarray]] = defaultdict(list)
    for length, values in cycles.items():
        for cycle in values:
            row = np.zeros(len(edges))
            for edge in cycle:
                row[index[edge]] = 1.0
            cycle_rows[length].append(row)

    systems = {}
    base_rows = list(degree_rows)
    base_rhs = list(degree_rhs)
    systems["degree"] = (np.asarray(base_rows), np.asarray(base_rhs))
    base_rows += triangle_rows
    base_rhs += triangle_rhs
    systems["clique"] = (np.asarray(base_rows), np.asarray(base_rhs))
    for cutoff in (5, 7, 9):
        rows = list(base_rows)
        rhs = list(base_rhs)
        for length in (5, 7, 9):
            if length <= cutoff:
                rows += cycle_rows.get(length, [])
                rhs += [(length - 1) / 2] * len(cycle_rows.get(length, []))
        systems[f"odd{cutoff}"] = (np.asarray(rows), np.asarray(rhs))
    counts = {
        "degree": len(degree_rows),
        "triangles": len(triangle_rows),
        "cycles5": len(cycle_rows.get(5, [])),
        "cycles7": len(cycle_rows.get(7, [])),
        "cycles9": len(cycle_rows.get(9, [])),
    }
    return systems, counts


def lp_value(weights: np.ndarray, system) -> float:
    matrix, rhs = system
    result = linprog(-weights, A_ub=matrix, b_ub=rhs,
                     bounds=[(0.0, None)] * len(weights), method="highs")
    if not result.success:
        raise RuntimeError(result.message)
    return float(-result.fun)


def exact_matching(graph: nx.Graph, edges, weights: np.ndarray):
    weighted = graph.copy()
    lookup = {edge: i for i, edge in enumerate(edges)}
    for edge in edges:
        weighted.edges[edge]["weight"] = float(weights[lookup[edge]])
    chosen = {tuple(sorted(edge)) for edge in nx.max_weight_matching(weighted, weight="weight")}
    return sum(float(weights[lookup[edge]]) for edge in chosen), chosen


def full_blossom_lp(graph: nx.Graph, edges, weights: np.ndarray) -> float:
    index = {edge: i for i, edge in enumerate(edges)}
    rows, rhs = [], []
    for vertex in sorted(graph):
        row = np.zeros(len(edges))
        for edge in graph.edges(vertex):
            row[index[tuple(sorted(edge))]] = 1.0
        rows.append(row)
        rhs.append(1.0)
    nodes = tuple(sorted(graph))
    for size in range(3, len(nodes) + 1, 2):
        for subset_tuple in it.combinations(nodes, size):
            subset = set(subset_tuple)
            row = np.zeros(len(edges))
            for edge in edges:
                if edge[0] in subset and edge[1] in subset:
                    row[index[edge]] = 1.0
            rows.append(row)
            rhs.append((size - 1) / 2)
    return lp_value(weights, (np.asarray(rows), np.asarray(rhs)))


def skew_matrix(order: int, edges, coefficients: np.ndarray) -> np.ndarray:
    matrix = np.zeros((order, order))
    for (u, v), value in zip(edges, coefficients):
        matrix[u, v] = value
        matrix[v, u] = -value
    return matrix


def summary(values: list[float]) -> dict:
    array = np.asarray(values)
    return {
        "count": int(array.size),
        "mean": float(array.mean()),
        "median": float(np.median(array)),
        "p95": float(np.quantile(array, 0.95)),
        "max": float(array.max()),
        "exact_fraction": float(np.mean(array <= 1.0 + 1e-8)),
    }


def disjoint_union(component: nx.Graph, copies: int) -> nx.Graph:
    return nx.disjoint_union_all([component.copy() for _ in range(copies)])


def structured_ablations() -> list[dict]:
    specs = [
        ("triangles", nx.complete_graph(3), "clique"),
        ("C5", nx.cycle_graph(5), "odd5"),
        ("C7", nx.cycle_graph(7), "odd7"),
        ("C9", nx.cycle_graph(9), "odd9"),
        ("C11", nx.cycle_graph(11), "full_cycle_beyond_cutoff"),
        ("K5", nx.complete_graph(5), "full_blossom"),
    ]
    rows = []
    for family, component, repairing_constraint in specs:
        for copies in (1, 2, 4, 8, 12):
            graph = disjoint_union(component, copies)
            edges = edges_of(graph)
            weights = np.ones(len(edges))
            systems, counts = constraint_hierarchy(graph, edges)
            exact, _ = exact_matching(graph, edges, weights)
            values = {name: lp_value(weights, systems[name]) for name in BASELINES}
            rows.append({
                "family": family,
                "copies": copies,
                "root_order": graph.number_of_nodes(),
                "root_edges": graph.number_of_edges(),
                "repairing_constraint": repairing_constraint,
                "matching": exact,
                **{f"{name}_ratio": value / exact for name, value in values.items()},
                **counts,
            })
    return rows


def non_skew_scaling() -> list[dict]:
    rows = []
    for blocks in (1, 2, 4, 8, 16, 32):
        rows.append({
            "triangle_blocks": blocks,
            "order": 3 * blocks,
            "max_degree_sum": 8 / 9,
            "odd_set_square_sum": 4 * blocks / 3,
            "matching_bound": blocks,
            "violation_ratio": 4 / 3,
            "construction": "block diagonal copies of Q=I-(2/3)J",
        })
    return rows


def write_csv(path: Path, rows: list[dict]):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def aggregate(records: list[dict], fields: tuple[str, ...]) -> list[dict]:
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for row in records:
        groups[tuple(row[field] for field in fields)].append(row)
    output = []
    for key, selected in sorted(groups.items()):
        row = {field: value for field, value in zip(fields, key)}
        row["instances"] = len(selected)
        for baseline in BASELINES:
            values = [item[f"{baseline}_ratio"] for item in selected]
            row[f"{baseline}_mean"] = float(np.mean(values))
            row[f"{baseline}_max"] = max(values)
            row[f"{baseline}_exact_fraction"] = float(np.mean(np.asarray(values) <= 1 + 1e-8))
        output.append(row)
    return output


def make_figures(records, by_order, by_weight, structured, random_ratios, sharp_ratios):
    FIGURES.mkdir(parents=True, exist_ok=True)
    colors = {"degree": "#d95f02", "clique": "#e6ab02", "odd5": "#7570b3",
              "odd7": "#66a61e", "odd9": "#1b9e77"}
    labels = {"degree": "degree", "clique": "+ cliques", "odd5": "+ odd <=5",
              "odd7": "+ odd <=7", "odd9": "+ odd <=9"}
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), constrained_layout=True)
    for baseline in BASELINES:
        xs, ys = [], []
        for order in ORDERS:
            selected = [row for row in records if row["root_order"] == order]
            xs.append(order)
            ys.append(np.mean([row[f"{baseline}_ratio"] for row in selected]))
        axes[0].plot(xs, ys, "o-", color=colors[baseline], label=labels[baseline])
    axes[0].axhline(1, color="black", linestyle="--", linewidth=1)
    axes[0].set(xlabel="root order", ylabel="mean LP / matching", title="Scaled sparse ensembles")
    axes[0].legend(frameon=False, fontsize=8)

    positions = np.arange(len(WEIGHT_MODELS))
    width = 0.16
    for offset, baseline in enumerate(BASELINES):
        values = []
        for model in WEIGHT_MODELS:
            selected = [row for row in records if row["weight_model"] == model]
            values.append(np.mean([row[f"{baseline}_ratio"] > 1 + 1e-8 for row in selected]))
        axes[1].bar(positions + (offset - 2) * width, values, width=width,
                    color=colors[baseline], label=labels[baseline])
    axes[1].set_xticks(positions, WEIGHT_MODELS, rotation=18)
    axes[1].set(ylabel="strict-gap fraction", title="Weight heterogeneity ablation", ylim=(0, 1))
    axes[1].legend(frameon=False, fontsize=8)
    fig.savefig(FIGURES / "c040_scaled_random_ablations.png", dpi=220)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), constrained_layout=True)
    for family in ("triangles", "C5", "C7", "C9", "C11", "K5"):
        selected = [row for row in structured if row["family"] == family]
        axes[0].plot([row["root_order"] for row in selected],
                     [row["odd9_ratio"] for row in selected], "o-", label=family)
    axes[0].axhline(1, color="black", linestyle="--", linewidth=1)
    axes[0].set(xlabel="root order", ylabel="odd<=9 LP / matching",
                title="Persistent structured obstructions")
    axes[0].legend(frameon=False, ncol=2, fontsize=8)

    bins = np.linspace(0, 1, 26)
    axes[1].hist(random_ratios, bins=bins, density=True, alpha=0.75,
                 color="#377eb8", label="random directions")
    axes[1].axvline(np.median(random_ratios), color="#08519c", linewidth=2,
                    label="random median")
    axes[1].axvline(min(sharp_ratios), color="#e41a1c", linestyle="--", linewidth=2,
                    label="matching-supported")
    axes[1].set(xlabel="matrix side / exact bound", ylabel="density",
                title="Sharpness at orders 10--30")
    axes[1].legend(frameon=False, fontsize=8)
    fig.savefig(FIGURES / "c040_structured_and_tightness.png", dpi=220)
    plt.close(fig)


def main(overwrite: bool = False):
    started = time.perf_counter()
    RESULTS.mkdir(parents=True, exist_ok=True)
    output = RESULTS / "c040_scaled_ablations.json"
    if output.exists() and not overwrite:
        raise FileExistsError(f"Use --overwrite to replace {output}")
    rng = np.random.default_rng(SEED)
    records, graph_records, spot_checks = [], [], []
    random_ratios, sharp_ratios = [], []
    total_constraint_counts = defaultdict(int)
    for graph_index, (family, order, replicate, graph_seed, graph) in enumerate(graph_ensembles(rng)):
        edges = edges_of(graph)
        systems, counts = constraint_hierarchy(graph, edges)
        for name, count in counts.items():
            total_constraint_counts[name] += count
        graph6 = nx.to_graph6_bytes(graph, header=False).decode().strip()
        graph_records.append({"graph_index": graph_index, "family": family, "root_order": order,
                              "replicate": replicate, "seed": graph_seed, "graph6": graph6,
                              "root_edges": len(edges), "bipartite": nx.is_bipartite(graph), **counts})
        vectors = weight_vectors(len(edges), rng)
        for model, weights in vectors.items():
            exact, chosen = exact_matching(graph, edges, weights)
            values = {name: lp_value(weights, systems[name]) for name in BASELINES}
            ratios = {name: values[name] / exact for name in BASELINES}
            if any(ratios[BASELINES[i]] + 2e-8 < ratios[BASELINES[i + 1]]
                   for i in range(len(BASELINES) - 1)):
                raise AssertionError((family, order, replicate, model, ratios))
            record = {
                "graph_index": graph_index, "graph6": graph6, "graph_family": family,
                "root_order": order, "root_edges": len(edges), "replicate": replicate,
                "weight_model": model, "matching": exact,
                "weight_min": float(weights.min()), "weight_max": float(weights.max()),
                "weight_cv": float(weights.std() / weights.mean()),
                **{f"{name}_lp": values[name] for name in BASELINES},
                **{f"{name}_ratio": ratios[name] for name in BASELINES},
            }
            records.append(record)
            if order in (10, 14) and replicate == 0:
                full = full_blossom_lp(graph, edges, weights)
                if not math.isclose(full, exact, rel_tol=2e-8, abs_tol=2e-8):
                    raise AssertionError((family, order, model, full, exact))
                spot_checks.append({"graph_index": graph_index, "family": family, "root_order": order,
                                    "weight_model": model, "matching": exact, "full_blossom_lp": full,
                                    "ratio": full / exact})

            if model == "integer":
                for _ in range(3):
                    coefficients = rng.normal(size=len(edges))
                    matrix = skew_matrix(order, edges, coefficients)
                    half_nuclear = np.linalg.svd(matrix, compute_uv=False).sum() / 2
                    denominator = exact * float(np.sum(coefficients**2 / weights))
                    ratio = float(half_nuclear**2 / denominator)
                    if ratio > 1 + 3e-10:
                        raise AssertionError((family, order, ratio))
                    random_ratios.append(ratio)
                lookup = {edge: i for i, edge in enumerate(edges)}
                coefficients = np.asarray([weights[i] if edge in chosen else 0.0
                                           for i, edge in enumerate(edges)])
                matrix = skew_matrix(order, edges, coefficients)
                half_nuclear = np.linalg.svd(matrix, compute_uv=False).sum() / 2
                denominator = exact * float(np.sum(coefficients**2 / weights))
                sharp = float(half_nuclear**2 / denominator)
                if not math.isclose(sharp, 1.0, abs_tol=3e-10):
                    raise AssertionError((family, order, sharp, lookup))
                sharp_ratios.append(sharp)

    structured = structured_ablations()
    non_skew = non_skew_scaling()
    baseline_summary = {name: summary([row[f"{name}_ratio"] for row in records]) for name in BASELINES}
    by_order = aggregate(records, ("root_order",))
    by_family = aggregate(records, ("graph_family",))
    by_weight = aggregate(records, ("weight_model",))
    tightness = {"random": summary(random_ratios), "matching_supported": summary(sharp_ratios),
                 "random_directions_per_graph": 3}
    make_figures(records, by_order, by_weight, structured, random_ratios, sharp_ratios)
    tables = {
        RESULTS / "c040_baseline_summary.csv": [{"baseline": name, **values}
                                                 for name, values in baseline_summary.items()],
        RESULTS / "c040_by_order.csv": by_order,
        RESULTS / "c040_by_family.csv": by_family,
        RESULTS / "c040_by_weight.csv": by_weight,
        RESULTS / "c040_structured_ablations.csv": structured,
    }
    for path, rows in tables.items():
        write_csv(path, rows)
    artifacts = list(tables) + [FIGURES / "c040_scaled_random_ablations.png",
                                FIGURES / "c040_structured_and_tightness.png"]
    report = {
        "experiment": "C040_scaled_baselines_and_ablations",
        "seed": SEED,
        "protocol": {"orders": list(ORDERS), "replicates": REPLICATES,
                     "graph_families": 5, "weight_models": list(WEIGHT_MODELS),
                     "baselines": list(BASELINES)},
        "graph_count": len(graph_records), "weighted_instances": len(records),
        "baseline_summary": baseline_summary, "by_order": by_order,
        "by_family": by_family, "by_weight": by_weight,
        "full_blossom_spot_checks": spot_checks,
        "structured_ablations": structured, "non_skew_scaling": non_skew,
        "theorem_tightness": tightness,
        "constraint_counts": dict(total_constraint_counts),
        "runtime_seconds": time.perf_counter() - started,
        "scope": (
            "The 180 sparse graphs are seeded draws from five generators, not an exhaustive census or "
            "application distribution. Odd-cycle baselines are deliberately truncated at lengths 5, 7, "
            "and 9; only the structured K5 unions make the odd<=9 row equal the complete h-relaxation."
        ),
        "claims": {"experiments_replace_theorem": False,
                   "full_blossom_spot_checks_all_exact": True,
                   "bounded_local_constraints_can_leave_persistent_gaps": True,
                   "non_skew_failure_scales_by_direct_sum": True},
        "graphs": graph_records, "records": records,
        "artifacts": {str(path.relative_to(ROOT)).replace("\\", "/"):
                      hashlib.sha256(path.read_bytes()).hexdigest() for path in artifacts},
    }
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    result = main(overwrite=args.overwrite)
    print(json.dumps({key: value for key, value in result.items()
                      if key not in {"graphs", "records", "structured_ablations"}}, indent=2))
