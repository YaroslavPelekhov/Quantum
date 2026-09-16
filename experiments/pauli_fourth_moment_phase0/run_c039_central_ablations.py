"""C039: baseline and mechanism ablations for the line-graph theorem.

This campaign asks which ingredients are actually necessary:
  * degree-only fractional matching versus h-perfect-style constraints;
  * full blossom/odd-set constraints versus those baselines;
  * skew versus general operator-norm contractions;
  * random Hamiltonian directions versus the matching-supported sharp case.
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
SEED = 20260916


def edges_of(graph: nx.Graph) -> tuple[tuple[int, int], ...]:
    return tuple(sorted(tuple(sorted(edge)) for edge in graph.edges()))


def odd_cycle_edge_sets(graph: nx.Graph) -> tuple[tuple[tuple[int, int], ...], ...]:
    """All simple odd root cycles of length at least five, without duplicates."""
    nodes = tuple(sorted(graph))
    found: set[tuple[tuple[int, int], ...]] = set()
    for size in range(5, len(nodes) + 1, 2):
        for subset in it.combinations(nodes, size):
            anchor = subset[0]
            for tail in it.permutations(subset[1:]):
                if tail[0] > tail[-1]:  # identify reverse orientations
                    continue
                cycle = (anchor,) + tail
                cycle_edges = tuple(
                    sorted(
                        tuple(sorted((cycle[i], cycle[(i + 1) % size])))
                        for i in range(size)
                    )
                )
                if all(graph.has_edge(*edge) for edge in cycle_edges):
                    found.add(cycle_edges)
    return tuple(sorted(found))


def constraint_systems(graph: nx.Graph, edges: tuple[tuple[int, int], ...]):
    index = {edge: i for i, edge in enumerate(edges)}
    degree_rows = []
    degree_rhs = []
    for vertex in sorted(graph):
        row = np.zeros(len(edges))
        for edge in edges:
            if vertex in edge:
                row[index[edge]] = 1.0
        degree_rows.append(row)
        degree_rhs.append(1.0)

    h_rows = list(degree_rows)
    h_rhs = list(degree_rhs)
    triangle_count = 0
    for triple in it.combinations(sorted(graph), 3):
        triangle = tuple(sorted(tuple(sorted(e)) for e in it.combinations(triple, 2)))
        if all(graph.has_edge(*edge) for edge in triangle):
            row = np.zeros(len(edges))
            for edge in triangle:
                row[index[edge]] = 1.0
            h_rows.append(row)
            h_rhs.append(1.0)
            triangle_count += 1
    cycles = odd_cycle_edge_sets(graph)
    for cycle in cycles:
        row = np.zeros(len(edges))
        for edge in cycle:
            row[index[edge]] = 1.0
        h_rows.append(row)
        h_rhs.append((len(cycle) - 1) / 2)

    full_rows = list(degree_rows)
    full_rhs = list(degree_rhs)
    odd_set_count = 0
    nodes = tuple(sorted(graph))
    for size in range(3, len(nodes) + 1, 2):
        for subset in it.combinations(nodes, size):
            subset = set(subset)
            row = np.zeros(len(edges))
            for edge in edges:
                if edge[0] in subset and edge[1] in subset:
                    row[index[edge]] = 1.0
            full_rows.append(row)
            full_rhs.append((size - 1) / 2)
            odd_set_count += 1

    def packed(rows, rhs):
        return np.asarray(rows, dtype=float), np.asarray(rhs, dtype=float)

    return {
        "degree": packed(degree_rows, degree_rhs),
        "h_relaxation": packed(h_rows, h_rhs),
        "full_matching": packed(full_rows, full_rhs),
        "counts": {
            "degree": len(degree_rows),
            "root_triangles": triangle_count,
            "root_odd_cycles_ge5": len(cycles),
            "odd_vertex_sets": odd_set_count,
        },
    }


def lp_value(weights: np.ndarray, system) -> float:
    matrix, rhs = system
    result = linprog(
        -weights,
        A_ub=matrix,
        b_ub=rhs,
        bounds=[(0.0, None)] * len(weights),
        method="highs",
    )
    if not result.success:
        raise RuntimeError(result.message)
    return float(-result.fun)


def matching(graph: nx.Graph, edges, weights: np.ndarray):
    weighted = graph.copy()
    for edge, weight in zip(edges, weights):
        weighted.edges[edge]["campaign_weight"] = float(weight)
    chosen = nx.max_weight_matching(weighted, weight="campaign_weight")
    normalized = {tuple(sorted(edge)) for edge in chosen}
    value = sum(float(weights[edges.index(edge)]) for edge in normalized)
    return value, normalized


def skew_matrix(order: int, edges, coefficients: np.ndarray) -> np.ndarray:
    matrix = np.zeros((order, order), dtype=float)
    for (u, v), coefficient in zip(edges, coefficients):
        matrix[u, v] = coefficient
        matrix[v, u] = -coefficient
    return matrix


def ratio_summary(values: list[float]) -> dict:
    array = np.asarray(values, dtype=float)
    return {
        "count": int(array.size),
        "mean": float(array.mean()),
        "median": float(np.median(array)),
        "p95": float(np.quantile(array, 0.95)),
        "max": float(array.max()),
        "exact_fraction": float(np.mean(array <= 1.0 + 1e-8)),
    }


def family_rows() -> list[dict]:
    rows = []
    for order in (5, 7, 9, 11, 13):
        matching_value = (order - 1) / 2
        for family in ("odd_complete", "odd_cycle"):
            degree = order / 2
            h_value = order / 2 if family == "odd_complete" else matching_value
            rows.append(
                {
                    "family": family,
                    "root_order": order,
                    "matching": matching_value,
                    "degree_lp": degree,
                    "h_relaxation": h_value,
                    "full_matching": matching_value,
                    "degree_ratio": degree / matching_value,
                    "h_ratio": h_value / matching_value,
                    "missing_blossom_additive_gap": h_value - matching_value,
                }
            )
    return rows


def write_csv(path: Path, rows: list[dict]):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def make_figures(records: list[dict], by_order: list[dict], families: list[dict],
                 random_ratios: list[float], sharp_ratios: list[float]):
    FIGURES.mkdir(parents=True, exist_ok=True)
    degree = np.asarray([r["degree_ratio"] for r in records])
    h_ratio = np.asarray([r["h_ratio"] for r in records])
    full = np.asarray([r["full_ratio"] for r in records])

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.0), constrained_layout=True)
    for values, label, color in (
        (degree, "degree only", "#d95f02"),
        (h_ratio, "cliques + odd cycles", "#7570b3"),
        (full, "all odd sets", "#1b9e77"),
    ):
        ordered = np.sort(values)
        cdf = np.arange(1, len(ordered) + 1) / len(ordered)
        axes[0].plot(ordered, cdf, label=label, color=color, linewidth=2)
    axes[0].axvline(1, color="black", linewidth=1, linestyle="--")
    axes[0].set_xlabel("LP bound / exact matching")
    axes[0].set_ylabel("empirical CDF")
    axes[0].set_title("Weighted atlas instances")
    axes[0].legend(frameon=False)

    orders = [row["root_order"] for row in by_order]
    axes[1].plot(orders, [row["degree_max"] for row in by_order], "o-",
                 label="degree only", color="#d95f02")
    axes[1].plot(orders, [row["h_max"] for row in by_order], "s-",
                 label="cliques + odd cycles", color="#7570b3")
    axes[1].plot(orders, [row["full_max"] for row in by_order], "^-",
                 label="all odd sets", color="#1b9e77")
    axes[1].axhline(1, color="black", linewidth=1, linestyle="--")
    axes[1].set_xlabel("root order")
    axes[1].set_ylabel("maximum ratio")
    axes[1].set_title("Worst observed relaxation gap")
    axes[1].legend(frameon=False)
    fig.savefig(FIGURES / "c039_baseline_gaps.png", dpi=220)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.0), constrained_layout=True)
    styles = {
        ("odd_complete", "h_ratio"): ("#7570b3", "s-", "degree (both) = complete h-relaxation"),
        ("odd_cycle", "h_ratio"): ("#1b9e77", "^-", "cycle: clique + odd cycles"),
    }
    for (family, field), (color, style, label) in styles.items():
        selected = [row for row in families if row["family"] == family]
        axes[0].plot(
            [row["root_order"] for row in selected],
            [row[field] for row in selected],
            style,
            color=color,
            label=label,
        )
    axes[0].axhline(1, color="black", linewidth=1, linestyle=":")
    axes[0].set_xlabel("root order")
    axes[0].set_ylabel("bound / matching")
    axes[0].set_title("Which blossom constraints are missing?")
    axes[0].legend(frameon=False, fontsize=8)

    bins = np.linspace(0, 1, 26)
    axes[1].hist(random_ratios, bins=bins, density=True, alpha=0.75,
                 color="#377eb8", label="random directions")
    axes[1].axvline(np.median(random_ratios), color="#08519c", linewidth=2,
                    label="random median")
    axes[1].axvline(min(sharp_ratios), color="#e41a1c", linewidth=2,
                    linestyle="--", label="matching-supported")
    axes[1].set_xlabel("matrix left side / exact theorem bound")
    axes[1].set_ylabel("density")
    axes[1].set_title("Global sharpness vs typical directions")
    axes[1].legend(frameon=False, fontsize=8)
    fig.savefig(FIGURES / "c039_mechanism_ablations.png", dpi=220)
    plt.close(fig)


def main(overwrite: bool = False) -> dict:
    started = time.perf_counter()
    RESULTS.mkdir(parents=True, exist_ok=True)
    output = RESULTS / "c039_central_ablations.json"
    if output.exists() and not overwrite:
        raise FileExistsError(f"Use --overwrite to replace {output}")
    rng = np.random.default_rng(SEED)
    records = []
    random_ratios = []
    random_direction_records = []
    sharp_ratios = []
    constraint_counts = defaultdict(int)
    graphs = []
    for graph in nx.graph_atlas_g():
        if graph.number_of_edges():
            graphs.append(nx.convert_node_labels_to_integers(graph, ordering="sorted"))

    for graph_index, graph in enumerate(graphs):
        edges = edges_of(graph)
        systems = constraint_systems(graph, edges)
        for key, value in systems["counts"].items():
            constraint_counts[key] += value
        graph6 = nx.to_graph6_bytes(graph, header=False).decode().strip()
        weight_vectors = [np.ones(len(edges), dtype=float)]
        weight_vectors.extend(rng.integers(1, 10, size=len(edges)).astype(float) for _ in range(4))
        for weight_index, weights in enumerate(weight_vectors):
            exact, chosen = matching(graph, edges, weights)
            degree = lp_value(weights, systems["degree"])
            h_value = lp_value(weights, systems["h_relaxation"])
            full = lp_value(weights, systems["full_matching"])
            if abs(full - exact) > 2e-7 * max(1.0, exact):
                raise AssertionError((graph6, weights.tolist(), exact, full))
            record = {
                "graph6": graph6,
                "root_order": graph.number_of_nodes(),
                "root_edges": len(edges),
                "weight_index": weight_index,
                "uniform_weights": weight_index == 0,
                "bipartite_root": nx.is_bipartite(graph),
                "weights": [int(value) for value in weights],
                "matching": exact,
                "degree_lp": degree,
                "h_relaxation": h_value,
                "full_matching_lp": full,
                "degree_ratio": degree / exact,
                "h_ratio": h_value / exact,
                "full_ratio": full / exact,
            }
            records.append(record)

            if weight_index == 1:
                coefficient_norm = None
                for _ in range(4):
                    coefficients = rng.normal(size=len(edges))
                    matrix = skew_matrix(graph.number_of_nodes(), edges, coefficients)
                    half_nuclear = np.linalg.svd(matrix, compute_uv=False).sum() / 2
                    coefficient_norm = float(np.sum(coefficients**2 / weights))
                    ratio = float(half_nuclear**2 / (exact * coefficient_norm))
                    if ratio > 1 + 2e-10:
                        raise AssertionError((graph6, ratio))
                    random_ratios.append(ratio)
                    random_direction_records.append({
                        "graph6": graph6,
                        "root_order": graph.number_of_nodes(),
                        "root_edges": len(edges),
                        "matching": exact,
                        "ratio": ratio,
                    })
                sharp = np.asarray([weights[edges.index(e)] if e in chosen else 0.0 for e in edges])
                sharp_matrix = skew_matrix(graph.number_of_nodes(), edges, sharp)
                sharp_half_nuclear = np.linalg.svd(sharp_matrix, compute_uv=False).sum() / 2
                sharp_norm = float(np.sum(sharp**2 / weights))
                sharp_ratio = float(sharp_half_nuclear**2 / (exact * sharp_norm))
                if abs(sharp_ratio - 1) > 2e-10:
                    raise AssertionError((graph6, sharp_ratio))
                sharp_ratios.append(sharp_ratio)

    by_order = []
    for order in sorted({r["root_order"] for r in records}):
        selected = [r for r in records if r["root_order"] == order]
        by_order.append(
            {
                "root_order": order,
                "instances": len(selected),
                "degree_mean": float(np.mean([r["degree_ratio"] for r in selected])),
                "degree_max": max(r["degree_ratio"] for r in selected),
                "h_mean": float(np.mean([r["h_ratio"] for r in selected])),
                "h_max": max(r["h_ratio"] for r in selected),
                "full_mean": float(np.mean([r["full_ratio"] for r in selected])),
                "full_max": max(r["full_ratio"] for r in selected),
            }
        )

    families = family_rows()
    non_skew = {
        "matrix": [["1/3", "-2/3", "-2/3"], ["-2/3", "1/3", "-2/3"],
                   ["-2/3", "-2/3", "1/3"]],
        "construction": "Q=I-(2/3)J is a symmetric orthogonal Householder matrix",
        "operator_norm": "1",
        "edge_squares": ["4/9", "4/9", "4/9"],
        "max_degree_sum": "8/9",
        "K3_odd_set_sum": "4/3",
        "K3_matching_bound": "1",
        "conclusion": "skewness is essential even after all degree constraints pass",
    }
    skew_control = {
        "construction": "3x3 cross-product matrix for (1,1,1)/sqrt(3)",
        "operator_norm": "1",
        "edge_squares": ["1/3", "1/3", "1/3"],
        "max_degree_sum": "2/3",
        "K3_odd_set_sum": "1",
        "K3_matching_bound": "1",
    }

    baseline_summary = {
        "degree_only": ratio_summary([r["degree_ratio"] for r in records]),
        "h_relaxation": ratio_summary([r["h_ratio"] for r in records]),
        "full_matching": ratio_summary([r["full_ratio"] for r in records]),
    }
    class_summary = {}
    for name, predicate in (
        ("bipartite_roots", lambda r: r["bipartite_root"]),
        ("nonbipartite_roots", lambda r: not r["bipartite_root"]),
    ):
        selected = [r for r in records if predicate(r)]
        class_summary[name] = {
            "instances": len(selected),
            "degree_only": ratio_summary([r["degree_ratio"] for r in selected]),
            "h_relaxation": ratio_summary([r["h_ratio"] for r in selected]),
            "full_matching": ratio_summary([r["full_ratio"] for r in selected]),
        }
    graph_strictness = {}
    for baseline, field in (("degree_only", "degree_ratio"), ("h_relaxation", "h_ratio")):
        strict_graphs = {
            r["graph6"] for r in records if r[field] > 1 + 1e-8
        }
        graph_strictness[baseline] = {
            "strict_instances": sum(r[field] > 1 + 1e-8 for r in records),
            "strict_root_graphs": len(strict_graphs),
            "fraction_of_weighted_instances": len([r for r in records if r[field] > 1 + 1e-8]) / len(records),
        }
    nontrivial_random = [
        r["ratio"] for r in random_direction_records
        if r["root_edges"] >= 3 and r["matching"] >= 2
    ]
    tightness = {
        "random_directions": ratio_summary(random_ratios),
        "nontrivial_random_directions": ratio_summary(nontrivial_random),
        "matching_supported": ratio_summary(sharp_ratios),
        "random_draws_per_graph": 4,
    }
    report = {
        "experiment": "C039_central_mechanism_baselines_and_ablations",
        "seed": SEED,
        "atlas_root_graphs": len(graphs),
        "weight_vectors_per_graph": 5,
        "weighted_instances": len(records),
        "baseline_definitions": {
            "degree_only": "nonnegative edge variables and root-star degree constraints",
            "h_relaxation": "degree, root-triangle clique, and every simple odd-cycle constraint",
            "full_matching": "degree and every odd-root-vertex-set blossom constraint",
        },
        "baseline_summary": baseline_summary,
        "baseline_summary_by_graph_class": class_summary,
        "strictness_counts": graph_strictness,
        "maximum_gap_examples": {
            "degree_only": max(records, key=lambda r: r["degree_ratio"]),
            "h_relaxation": max(records, key=lambda r: r["h_ratio"]),
        },
        "by_root_order": by_order,
        "family_ablations": families,
        "skewness_ablation": non_skew,
        "skew_control": skew_control,
        "theorem_tightness": tightness,
        "constraint_counts_across_graphs": dict(constraint_counts),
        "runtime_seconds": time.perf_counter() - started,
        "claims": {
            "full_matching_matches_exact_every_instance": True,
            "degree_and_h_relaxations_can_be_strict": True,
            "skewness_is_necessary_for_the_contraction_lemma": True,
            "matching_supported_directions_attain_the_bound": True,
            "experiments_replace_analytic_proof": False,
        },
        "sampling_boundary": (
            "The atlas is exhaustive only over unlabeled roots of order at most seven; "
            "the four nonuniform integer-weight vectors per graph are seeded stress cases, "
            "not a probability model over applications."
        ),
        "records": records,
    }
    make_figures(records, by_order, families, random_ratios, sharp_ratios)
    summary_csv = RESULTS / "c039_baseline_summary.csv"
    order_csv = RESULTS / "c039_by_order.csv"
    family_csv = RESULTS / "c039_family_ablations.csv"
    write_csv(summary_csv, [
        {"baseline": name, **values} for name, values in baseline_summary.items()
    ])
    write_csv(order_csv, by_order)
    write_csv(family_csv, families)
    artifact_paths = (
        summary_csv,
        order_csv,
        family_csv,
        FIGURES / "c039_baseline_gaps.png",
        FIGURES / "c039_mechanism_ablations.png",
    )
    report["artifacts"] = {
        str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in artifact_paths
    }
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    result = main(overwrite=args.overwrite)
    compact = {key: value for key, value in result.items() if key != "records"}
    print(json.dumps(compact, indent=2))
