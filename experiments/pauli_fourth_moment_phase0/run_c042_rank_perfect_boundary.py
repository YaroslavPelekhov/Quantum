"""C042: locate the rank-perfect boundary beyond line graphs.

The analytic result tested here is simple but broad: the previously proved
SCF rank bound implies hbar-perfectness for every rank-perfect SCF graph.
This script audits strictness, an exhaustive order-nine quasi-line boundary,
web controls, and larger seeded proper-circular-arc samples.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import random
import time

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from scipy.spatial import ConvexHull


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results" / "pauli_fourth_moment_phase0"
FIGURES = Path(__file__).with_name("paper_c038") / "figures"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def graph6(graph: nx.Graph) -> str:
    graph = nx.convert_node_labels_to_integers(graph, ordering="sorted")
    return nx.to_graph6_bytes(graph, header=False).decode().strip()


def is_clique(graph: nx.Graph, nodes) -> bool:
    nodes = list(nodes)
    return graph.subgraph(nodes).number_of_edges() == len(nodes) * (len(nodes) - 1) // 2


def simplicial_cliques(graph: nx.Graph) -> list[list[int]]:
    output = []
    for clique in nx.find_cliques(graph):
        selected = set(clique)
        if all(is_clique(graph, set(graph.neighbors(v)) - selected) for v in selected):
            output.append(sorted(selected))
    return sorted(output, key=lambda row: (len(row), row))


def is_quasi_line(graph: nx.Graph) -> bool:
    for vertex in graph:
        neighborhood = graph.subgraph(list(graph.neighbors(vertex)))
        if not nx.is_bipartite(nx.complement(neighborhood)):
            return False
    return True


def is_line_graph(graph: nx.Graph) -> bool:
    try:
        nx.inverse_line_graph(graph)
        return True
    except nx.NetworkXError:
        return False


def stable_masks(graph: nx.Graph) -> list[int]:
    edges = list(graph.edges())
    return [
        mask
        for mask in range(1 << len(graph))
        if all(not (mask >> left & 1 and mask >> right & 1) for left, right in edges)
    ]


def exact_rank(rows: list[list[int]]) -> int:
    if not rows:
        return 0
    matrix = [[Fraction(value) for value in row] for row in rows]
    rank = 0
    columns = len(matrix[0])
    for column in range(columns):
        pivot = next((row for row in range(rank, len(matrix)) if matrix[row][column]), None)
        if pivot is None:
            continue
        matrix[rank], matrix[pivot] = matrix[pivot], matrix[rank]
        scale = matrix[rank][column]
        matrix[rank] = [value / scale for value in matrix[rank]]
        for row in range(len(matrix)):
            if row != rank and matrix[row][column]:
                scale = matrix[row][column]
                matrix[row] = [a - scale * b for a, b in zip(matrix[row], matrix[rank])]
        rank += 1
        if rank == len(matrix):
            break
    return rank


def rank_facet_masks(graph: nx.Graph, masks: list[int]) -> list[dict]:
    n = len(graph)
    output = []
    for support in range(1, 1 << n):
        alpha = max((mask & support).bit_count() for mask in masks)
        roots = [mask for mask in masks if (mask & support).bit_count() == alpha]
        rows = [[1] + [(mask >> index) & 1 for index in range(n)] for mask in roots]
        if exact_rank(rows) == n:
            output.append({"support_mask": support, "alpha": alpha, "roots": len(roots)})
    return output


def is_odd_hole(graph: nx.Graph) -> bool:
    return len(graph) >= 5 and len(graph) % 2 == 1 and nx.is_connected(graph) and all(
        graph.degree(vertex) == 2 for vertex in graph
    )


def hperfect_exception(graph: nx.Graph, facets: list[dict]) -> dict | None:
    nodes = list(range(len(graph)))
    for facet in facets:
        support = [node for node in nodes if facet["support_mask"] >> node & 1]
        induced = graph.subgraph(support)
        if not is_clique(graph, support) and not is_odd_hole(induced):
            return {
                **facet,
                "support_nodes": support,
                "support_graph6": graph6(induced),
                "support_edges": induced.number_of_edges(),
            }
    return None


def numerical_facets(graph: nx.Graph, masks: list[int]) -> tuple[list[dict], list[dict]]:
    points = np.asarray(
        [[(mask >> index) & 1 for index in range(len(graph))] for mask in masks], dtype=float
    )
    hull = ConvexHull(points)
    rank_supports = set()
    nonrank = {}
    for equation in hull.equations:
        normal = equation[:-1]
        if normal.max() <= 1e-8 or normal.min() < -1e-7:
            continue
        normal = np.maximum(normal, 0.0)
        positive = normal > 1e-7
        values = normal[positive]
        if values.max() - values.min() <= 2e-6:
            support = sum(1 << index for index, selected in enumerate(positive) if selected)
            rank_supports.add(support)
        else:
            scale = values.max()
            key = tuple(np.round(normal / scale, 7)) + (round(float(-equation[-1] / scale), 7),)
            nonrank[key] = {
                "normalized_weights": list(key[:-1]),
                "normalized_rhs": key[-1],
            }
    rank = []
    for support in sorted(rank_supports):
        alpha = max((mask & support).bit_count() for mask in masks)
        roots = [mask for mask in masks if (mask & support).bit_count() == alpha]
        rows = [[1] + [(mask >> index) & 1 for index in range(len(graph))] for mask in roots]
        if exact_rank(rows) != len(graph):
            raise AssertionError("numerical rank facet failed exact affine-rank check")
        rank.append({"support_mask": support, "alpha": alpha, "roots": len(roots)})
    return rank, list(nonrank.values())


def unit_circular_arc_graph(order: int, rng: random.Random) -> tuple[nx.Graph, list[int], int]:
    circumference = 4096
    points = sorted(rng.sample(range(circumference), order))
    threshold = rng.randint(320, 1220)
    graph = nx.Graph()
    graph.add_nodes_from(range(order))
    for left, right in itertools.combinations(range(order), 2):
        distance = abs(points[left] - points[right])
        distance = min(distance, circumference - distance)
        if distance <= threshold:
            graph.add_edge(left, right)
    return graph, points, threshold


def alpha_number(graph: nx.Graph) -> int:
    return max(mask.bit_count() for mask in stable_masks(graph))


def web_graph(order: int, power: int) -> nx.Graph:
    graph = nx.Graph()
    graph.add_nodes_from(range(order))
    for vertex in range(order):
        for distance in range(1, power + 1):
            graph.add_edge(vertex, (vertex + distance) % order)
    return graph


def web_simplicial_cliques(graph: nx.Graph, power: int) -> list[list[int]]:
    """Check the explicit maximal cliques of a web, avoiding generic enumeration."""
    order = len(graph)
    if 2 * power + 1 >= order:
        candidates = [list(range(order))]
    else:
        candidates = [sorted((start + offset) % order for offset in range(power + 1)) for start in range(order)]
    output = []
    for clique in candidates:
        selected = set(clique)
        if all(is_clique(graph, set(graph.neighbors(v)) - selected) for v in selected):
            output.append(clique)
    return sorted(output, key=lambda row: (len(row), row))


def write_csv(path: Path, columns: list[str], rows: list[dict]) -> None:
    lines = [",".join(columns)]
    for row in rows:
        lines.append(",".join(str(row[column]) for column in columns))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20260919)
    parser.add_argument("--samples-per-order", type=int, default=20)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    output = RESULTS / "c042_rank_perfect_boundary.json"
    if output.exists() and not args.overwrite:
        raise SystemExit(f"refusing to overwrite {output}; pass --overwrite")
    started = time.monotonic()
    census_path = RESULTS / "scf_order9_census.json"
    facets_path = RESULTS / "scf_exact_facet_census.json"
    census = json.loads(census_path.read_text(encoding="utf-8"))
    exact = json.loads(facets_path.read_text(encoding="utf-8"))
    exact_by_graph = {row["graph6"]: row for row in exact["records"]}

    census_rows = []
    quasi_line_graphs = quasi_line_nonline = quasi_line_nonrank = 0
    nonrank_quasi_line = []
    for row in census["SCF_records"]:
        graph = nx.from_graph6_bytes(row["graph6"].encode())
        quasi = is_quasi_line(graph)
        exact_row = exact_by_graph.get(row["graph6"])
        nonrank = len(exact_row["nonrank_facets"]) if exact_row is not None else 0
        quasi_line_graphs += int(quasi)
        quasi_line_nonline += int(quasi and not row["line_graph"])
        quasi_line_nonrank += int(quasi and nonrank > 0)
        if quasi and nonrank:
            nonrank_quasi_line.append(row["graph6"])
    for label, condition in (
        ("line", lambda row, quasi: row["line_graph"]),
        ("quasi_line_non_line", lambda row, quasi: quasi and not row["line_graph"]),
        ("SCF_not_quasi_line", lambda row, quasi: not quasi),
    ):
        count = nonrank_count = 0
        for row in census["SCF_records"]:
            graph = nx.from_graph6_bytes(row["graph6"].encode())
            quasi = is_quasi_line(graph)
            if condition(row, quasi):
                count += 1
                exact_row = exact_by_graph.get(row["graph6"])
                nonrank_count += int(exact_row is not None and bool(exact_row["nonrank_facets"]))
        census_rows.append({"class": label, "graphs": count, "graphs_with_nonrank_facets": nonrank_count})

    if nonrank_quasi_line:
        raise AssertionError(f"order-nine SCF quasi-line nonrank examples: {nonrank_quasi_line[:3]}")

    strict_witness = None
    for row in census["SCF_records"]:
        if row["line_graph"]:
            continue
        graph = nx.from_graph6_bytes(row["graph6"].encode())
        if not is_quasi_line(graph):
            continue
        exact_row = exact_by_graph[row["graph6"]]
        if exact_row["nonrank_facets"]:
            continue
        masks = stable_masks(graph)
        facets = rank_facet_masks(graph, masks)
        exception = hperfect_exception(graph, facets)
        if exception is None:
            continue
        if len(facets) + len(graph) != exact_row["facets"]:
            raise AssertionError("rank-facet enumeration does not match frozen exact facet count")
        strict_witness = {
            "graph6": row["graph6"],
            "vertices": len(graph),
            "edges": graph.number_of_edges(),
            "quasi_line": True,
            "SCF": True,
            "simplicial_cliques": simplicial_cliques(graph),
            "line_graph": is_line_graph(graph),
            "stable_sets": len(masks),
            "exact_facets": exact_row["facets"],
            "nonrank_facets": 0,
            "rank_facet_count_excluding_nonnegativity": len(facets),
            "not_hperfect_facet": exception,
            "interpretation": "rank-perfect SCF, but neither line nor h-perfect",
        }
        break
    if strict_witness is None or strict_witness["line_graph"]:
        raise AssertionError("no strict non-line/non-h-perfect witness found")

    web_rows = []
    web_scf = 0
    web_bad = []
    for order in range(5, 61):
        for power in range(1, (order - 1) // 2 + 1):
            graph = web_graph(order, power)
            cliques = web_simplicial_cliques(graph, power)
            alpha = order // (power + 1)
            is_scf = bool(cliques)
            web_scf += int(is_scf)
            allowed = power == 1 or alpha <= 2
            if is_scf and not allowed:
                web_bad.append((order, power))
            web_rows.append(
                {
                    "order": order,
                    "power": power,
                    "alpha": alpha,
                    "SCF": int(is_scf),
                    "simplicial_clique_size": len(cliques[0]) if cliques else 0,
                    "cycle_or_alpha_le_2": int(allowed),
                }
            )
    if web_bad:
        raise AssertionError(f"unexpected SCF webs outside proved regimes: {web_bad[:3]}")

    rng = random.Random(args.seed)
    sampled = []
    seen = set()
    for order in (10, 11, 12):
        attempts = 0
        while sum(row["order"] == order for row in sampled) < args.samples_per_order:
            attempts += 1
            if attempts > 100000:
                raise RuntimeError("could not generate enough adversarial circular-arc samples")
            graph, points, threshold = unit_circular_arc_graph(order, rng)
            code = graph6(graph)
            if code in seen or not nx.is_connected(graph):
                continue
            if not is_quasi_line(graph) or not simplicial_cliques(graph):
                continue
            if is_line_graph(graph):
                continue
            masks = stable_masks(graph)
            if max(mask.bit_count() for mask in masks) < 3 or len(masks) > 120:
                continue
            seen.add(code)
            rank_facets, nonrank_facets = numerical_facets(graph, masks)
            sampled.append(
                {
                    "order": order,
                    "graph6": code,
                    "edges": graph.number_of_edges(),
                    "alpha": max(mask.bit_count() for mask in masks),
                    "points": points,
                    "threshold": threshold,
                    "stable_sets": len(masks),
                    "rank_facets": len(rank_facets),
                    "rank_facet_certificates": rank_facets,
                    "nonrank_facets": len(nonrank_facets),
                    "nonrank_candidates": nonrank_facets,
                }
            )

    RESULTS.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    census_csv = RESULTS / "c042_order9_boundary.csv"
    sample_csv = RESULTS / "c042_circular_arc_stress.csv"
    web_csv = RESULTS / "c042_web_boundary.csv"
    figure_path = FIGURES / "c042_rank_perfect_boundary.png"
    write_csv(census_csv, ["class", "graphs", "graphs_with_nonrank_facets"], census_rows)
    write_csv(
        sample_csv,
        ["order", "graph6", "edges", "alpha", "stable_sets", "rank_facets", "nonrank_facets"],
        sampled,
    )
    write_csv(
        web_csv,
        ["order", "power", "alpha", "SCF", "simplicial_clique_size", "cycle_or_alpha_le_2"],
        web_rows,
    )

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.2))
    axes[0].bar([row["class"] for row in census_rows], [row["graphs"] for row in census_rows], color=["#4c78a8", "#59a14f", "#e15759"])
    axes[0].bar([row["class"] for row in census_rows], [row["graphs_with_nonrank_facets"] for row in census_rows], color="#f28e2b", label="non-rank facet")
    axes[0].set_ylabel("order-nine SCF graphs")
    axes[0].tick_params(axis="x", rotation=20)
    axes[0].legend(frameon=False)
    by_order = {order: [row for row in sampled if row["order"] == order] for order in (10, 11, 12)}
    axes[1].boxplot([[row["rank_facets"] for row in by_order[order]] for order in (10, 11, 12)], tick_labels=["10", "11", "12"])
    axes[1].set_xlabel("sampled circular-arc order")
    axes[1].set_ylabel("detected rank facets")
    web_orders = sorted({row["order"] for row in web_rows})
    axes[2].plot(web_orders, [sum(row["SCF"] for row in web_rows if row["order"] == order) for order in web_orders], color="#b07aa1")
    axes[2].set_xlabel("web order")
    axes[2].set_ylabel("SCF web powers")
    axes[2].set_ylim(bottom=0)
    fig.suptitle("C042: the rank-perfect boundary beyond line graphs")
    fig.tight_layout()
    fig.savefig(figure_path, dpi=190)
    plt.close(fig)

    artifacts = {}
    for path in (census_csv, sample_csv, web_csv, figure_path):
        artifacts[str(path.relative_to(ROOT)).replace("\\", "/")] = sha256(path)
    payload = {
        "experiment": "C042_rank_perfect_boundary",
        "seed": args.seed,
        "analytic_result": {
            "theorem": "Every rank-perfect simplicial-claw-free graph is hbar-perfect.",
            "proof": "BETA satisfies every induced-subgraph rank inequality by the SCF rank theorem; rank-perfectness identifies their intersection with STAB; the universal reverse inclusion STAB subset BETA gives equality.",
            "semi_line_corollary": "Every SCF semi-line graph is hbar-perfect, using the classical rank-perfectness of semi-line graphs.",
        },
        "upstream": {
            "scf_order9_census": {"path": str(census_path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha256(census_path)},
            "exact_facet_census": {"path": str(facets_path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha256(facets_path)},
        },
        "order9": {
            "SCF_graphs": census["SCF_graphs"],
            "line_graphs": sum(row["line_graph"] for row in census["SCF_records"]),
            "quasi_line_graphs": quasi_line_graphs,
            "quasi_line_non_line_graphs": quasi_line_nonline,
            "quasi_line_graphs_with_nonrank_facets": quasi_line_nonrank,
            "all_nonrank_graphs_outside_quasi_line": exact["graphs_with_nonrank_facets"],
            "classes": census_rows,
        },
        "strict_witness": strict_witness,
        "web_stress": {
            "orders": [5, 60],
            "cases": len(web_rows),
            "SCF_cases": web_scf,
            "SCF_outside_cycles_or_alpha_le_2": len(web_bad),
        },
        "sampled_circular_arc_stress": {
            "orders": [10, 11, 12],
            "samples_per_order": args.samples_per_order,
            "graphs": len(sampled),
            "all_connected_SCF_quasi_line_non_line_alpha_ge_3": True,
            "graphs_with_detected_nonrank_facets": sum(row["nonrank_facets"] > 0 for row in sampled),
            "method": "seeded equal-length circular-arc graphs conditioned on at most 120 stable sets; Qhull discovery with exact integer validity and affine-rank checks for every reported rank facet",
            "records": sampled,
        },
        "scope": {
            "proved": ["SCF intersect rank-perfect implies hbar-perfect", "SCF semi-line corollary", "strict finite separation from line and h-perfect classes"],
            "not_proved": ["all SCF quasi-line graphs are rank-perfect", "all SCF graphs are hbar-perfect", "publication priority"],
            "order9_exhaustive": True,
            "larger_sampling_exhaustive": False,
        },
        "runtime_seconds": time.monotonic() - started,
        "source_sha256": sha256(Path(__file__)),
        "artifacts": artifacts,
    }
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(output),
        "order9_quasi_line": quasi_line_graphs,
        "order9_quasi_line_non_line": quasi_line_nonline,
        "order9_quasi_line_nonrank": quasi_line_nonrank,
        "strict_witness": strict_witness["graph6"],
        "sampled_graphs": len(sampled),
        "sampled_nonrank": sum(row["nonrank_facets"] > 0 for row in sampled),
        "seconds": payload["runtime_seconds"],
    }, indent=2))


if __name__ == "__main__":
    main()
