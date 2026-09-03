"""Falsify weighted hbar-perfectness beyond generator-level free fermions."""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import networkx as nx
import numpy as np


I = np.eye(2, dtype=complex)
X = np.asarray([[0, 1], [1, 0]], dtype=complex)
Y = np.asarray([[0, -1j], [1j, 0]], dtype=complex)
Z = np.diag([1, -1]).astype(complex)
PAULI = {(0, 0): I, (1, 0): X, (0, 1): Z, (1, 1): Y}


def is_clique(graph: nx.Graph, nodes) -> bool:
    nodes = list(nodes)
    return graph.subgraph(nodes).number_of_edges() == len(nodes) * (len(nodes) - 1) // 2


def has_claw(graph: nx.Graph) -> bool:
    return any(
        graph.subgraph(leaves).number_of_edges() == 0
        for center in graph
        for leaves in itertools.combinations(graph.neighbors(center), 3)
    )


def simplicial_cliques(graph: nx.Graph) -> list[list[int]]:
    output = []
    for clique in nx.enumerate_all_cliques(graph):
        selected = set(clique)
        if all(is_clique(graph, set(graph.neighbors(v)) - selected) for v in selected):
            output.append(sorted(clique))
    return output


def is_scf(graph: nx.Graph) -> bool:
    return nx.is_connected(graph) and not has_claw(graph) and bool(simplicial_cliques(graph))


def is_line_graph(graph: nx.Graph) -> bool:
    try:
        nx.inverse_line_graph(graph)
        return True
    except nx.NetworkXError:
        return False


def standard_saur(graph: nx.Graph) -> tuple[list[tuple[int, int]], int]:
    """Return compact binary (x,z) labels from the recursive standard SAUR."""
    nodes = sorted(graph.nodes())
    if graph.number_of_edges() == 0:
        return [(0, 0) for _ in nodes], 0
    left, right = sorted(next(iter(graph.edges())))
    remainder = [node for node in nodes if node not in (left, right)]
    groups = {}
    for node in remainder:
        groups[node] = 2 * int(graph.has_edge(node, left)) + int(
            graph.has_edge(node, right)
        )
    reduced = graph.subgraph(remainder).copy()
    for first, second in itertools.combinations(remainder, 2):
        if groups[first] and groups[second] and groups[first] != groups[second]:
            if reduced.has_edge(first, second):
                reduced.remove_edge(first, second)
            else:
                reduced.add_edge(first, second)
    reduced_labels, qubits = standard_saur(reduced)
    by_node = dict(zip(sorted(reduced.nodes()), reduced_labels))
    prefix = {0: (0, 0), 1: (1, 0), 2: (0, 1), 3: (1, 1)}
    labels = {}
    for node in remainder:
        old_x, old_z = by_node[node]
        new_x, new_z = prefix[groups[node]]
        labels[node] = (old_x | (new_x << qubits), old_z | (new_z << qubits))
    labels[left] = (1 << qubits, 0)
    labels[right] = (0, 1 << qubits)
    return [labels[node] for node in nodes], qubits + 1


def matrices_for_graph(graph: nx.Graph) -> np.ndarray:
    labels, qubits = standard_saur(graph)
    output = []
    for x_label, z_label in labels:
        matrix = np.asarray([[1.0 + 0.0j]])
        for bit in range(qubits):
            matrix = np.kron(matrix, PAULI[((x_label >> bit) & 1, (z_label >> bit) & 1)])
        output.append(matrix)
    matrices = np.stack(output)
    for i, j in itertools.combinations(range(len(graph)), 2):
        anticommutes = np.linalg.norm(matrices[i] @ matrices[j] + matrices[j] @ matrices[i]) < 1e-8
        if anticommutes != graph.has_edge(i, j):
            raise AssertionError((i, j, anticommutes, graph.has_edge(i, j)))
    return matrices


def independent_masks(graph: nx.Graph) -> list[int]:
    count = len(graph)
    return [
        mask
        for mask in range(1 << count)
        if all(
            not ((mask >> left) & 1 and (mask >> right) & 1)
            for left, right in graph.edges()
        )
    ]


def weighted_alpha(masks: list[int], weights: np.ndarray) -> float:
    return max(
        sum(weights[index] for index in range(len(weights)) if (mask >> index) & 1)
        for mask in masks
    )


def beta_from_coefficients(
    operators: np.ndarray,
    weights: np.ndarray,
    initial_coefficients,
    iterations: int,
) -> float:
    count = len(operators)
    root_weight = np.sqrt(weights)
    best = 0.0
    for coefficients in initial_coefficients:
        coefficients = coefficients / np.linalg.norm(coefficients)
        value = 0.0
        for _ in range(iterations):
            hamiltonian = np.einsum(
                "i,ijk->jk", coefficients * root_weight, operators
            )
            eigenvalues, eigenvectors = np.linalg.eigh(hamiltonian)
            location = int(np.argmax(abs(eigenvalues)))
            state = eigenvectors[:, location]
            expectations = np.real(
                np.einsum("i,kij,j->k", state.conj(), operators, state)
            )
            update = root_weight * expectations
            value = float(update @ update)
            norm = np.linalg.norm(update)
            if norm < 1e-14:
                break
            new_coefficients = update / norm
            if min(
                np.linalg.norm(new_coefficients - coefficients),
                np.linalg.norm(new_coefficients + coefficients),
            ) < 1e-11:
                break
            coefficients = new_coefficients
        best = max(best, value)
    return best


def beta_lower_bound(
    operators: np.ndarray,
    weights: np.ndarray,
    rng: np.random.Generator,
    starts: int,
    iterations: int,
) -> float:
    count = len(operators)
    initial = [np.ones(count) / np.sqrt(count)]
    initial.extend(rng.normal(size=count) for _ in range(starts - 1))
    return beta_from_coefficients(operators, weights, initial, iterations)


def weight_family(count: int, rng: np.random.Generator, random_weights: int):
    yield "uniform", np.ones(count)
    for index in range(random_weights):
        yield f"lognormal_{index}", rng.lognormal(0.0, 1.5, count)
        yield f"integer_{index}", rng.choice([0.25, 0.5, 1.0, 2.0, 4.0], count)
        sparse = rng.lognormal(0.0, 1.0, count)
        sparse[rng.random(count) < 0.45] = 1e-3
        yield f"sparse_{index}", sparse


def canonical_graph(graph: nx.Graph) -> nx.Graph:
    return nx.convert_node_labels_to_integers(graph, ordering="sorted")


def anti_cycle(order: int) -> nx.Graph:
    return canonical_graph(nx.complement(nx.cycle_graph(order)))


def published_scf_example() -> nx.Graph:
    edges = [
        (0, 1), (1, 2), (0, 3), (2, 3), (0, 4), (1, 4), (0, 5),
        (2, 5), (3, 5), (4, 5), (0, 6), (2, 6), (3, 6), (5, 6),
        (0, 7), (1, 7), (3, 7), (4, 7), (6, 7),
    ]
    graph = nx.Graph()
    graph.add_nodes_from(range(8))
    graph.add_edges_from(edges)
    return graph


def completed_neighborhood(graph: nx.Graph, vertex: int) -> nx.Graph:
    output = graph.copy()
    closed = list(output.neighbors(vertex)) + [vertex]
    output.add_edges_from(itertools.combinations(closed, 2))
    return canonical_graph(output)


def graph_key(graph: nx.Graph) -> str:
    return nx.weisfeiler_lehman_graph_hash(graph)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=771943)
    parser.add_argument("--random-weights", type=int, default=4)
    parser.add_argument("--starts", type=int, default=24)
    parser.add_argument("--iterations", type=int, default=120)
    parser.add_argument("--random-trials", type=int, default=12000)
    parser.add_argument("--random-cap", type=int, default=120)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rng = np.random.default_rng(args.seed)

    controls = [("anti_C7_positive_control", anti_cycle(7))]
    candidates: list[tuple[str, nx.Graph]] = [("published_2023_non_line", published_scf_example())]
    atlas_claw_free = []
    for graph in nx.graph_atlas_g():
        if len(graph) >= 2 and nx.is_connected(graph) and not has_claw(graph):
            graph = canonical_graph(graph)
            atlas_claw_free.append(graph)
            if is_scf(graph) and not is_line_graph(graph):
                candidates.append(("atlas_non_line_scf", graph))
    for order in (7, 9):
        seed_graph = anti_cycle(order)
        for vertex in seed_graph:
            completed = completed_neighborhood(seed_graph, vertex)
            if is_scf(completed) and not is_line_graph(completed):
                candidates.append((f"completed_anti_C{order}", completed))
    for graph in atlas_claw_free:
        for vertex in graph:
            completed = completed_neighborhood(graph, vertex)
            if is_scf(completed) and not is_line_graph(completed):
                candidates.append(("completed_atlas_claw_free", completed))

    random_accepted = 0
    for _ in range(args.random_trials):
        order = int(rng.integers(8, 11))
        probability = float(rng.uniform(0.18, 0.82))
        graph = nx.gnp_random_graph(order, probability, seed=int(rng.integers(2**31)))
        if is_scf(graph) and not is_line_graph(graph):
            candidates.append(("random_non_line_scf", canonical_graph(graph)))
            random_accepted += 1
            if random_accepted >= args.random_cap:
                break

    unique = []
    buckets: dict[tuple[int, str], list[nx.Graph]] = {}
    for source, graph in candidates:
        key = (len(graph), graph_key(graph))
        if any(nx.is_isomorphic(graph, old) for old in buckets.get(key, [])):
            continue
        buckets.setdefault(key, []).append(graph)
        unique.append((source, graph))

    records = []
    largest_ratio = 0.0
    largest_nonuniform_ratio = 0.0
    violation = None
    for source, graph in controls + unique:
        graph = canonical_graph(graph)
        operators = matrices_for_graph(graph)
        masks = independent_masks(graph)
        graph_best = 0.0
        graph_nonuniform_best = 0.0
        best_weight_name = None
        for weight_name, weights in weight_family(len(graph), rng, args.random_weights):
            alpha = weighted_alpha(masks, weights)
            beta = beta_lower_bound(
                operators, weights, rng, args.starts, args.iterations
            )
            ratio = beta / alpha
            graph_best = max(graph_best, ratio)
            if weight_name != "uniform":
                graph_nonuniform_best = max(graph_nonuniform_best, ratio)
            if ratio >= graph_best - 1e-15:
                best_weight_name = weight_name
            largest_ratio = max(largest_ratio, ratio)
            if weight_name != "uniform":
                largest_nonuniform_ratio = max(largest_nonuniform_ratio, ratio)
            if source != "anti_C7_positive_control" and ratio > 1.0 + 1e-7:
                violation = {
                    "source": source,
                    "graph6": nx.to_graph6_bytes(graph, header=False).decode().strip(),
                    "weight_name": weight_name,
                    "weights": weights.tolist(),
                    "alpha": alpha,
                    "beta_lower_bound": beta,
                    "ratio": ratio,
                }
                break
        records.append(
            {
                "source": source,
                "vertices": len(graph),
                "edges": graph.number_of_edges(),
                "graph6": nx.to_graph6_bytes(graph, header=False).decode().strip(),
                "claw_free": not has_claw(graph),
                "simplicial_cliques": simplicial_cliques(graph),
                "line_graph": is_line_graph(graph),
                "largest_ratio": graph_best,
                "largest_nonuniform_ratio": graph_nonuniform_best,
                "best_weight_name": best_weight_name,
            }
        )
        if violation:
            break

    positive = records[0]
    if positive["largest_ratio"] <= 1.0 + 1e-3:
        raise AssertionError("anti-C7 positive control did not reproduce")
    payload = {
        "experiment": "simplicial_claw_free_hbar_falsification",
        "seed": args.seed,
        "positive_control": positive,
        "unique_scf_non_line_graphs": len(unique),
        "random_trials": args.random_trials,
        "random_scf_non_line_accepted": random_accepted,
        "weight_vectors_per_graph": 1 + 3 * args.random_weights,
        "starts_per_weight": args.starts,
        "largest_ratio_including_control": largest_ratio,
        "largest_scf_nonuniform_ratio": max(
            (record["largest_nonuniform_ratio"] for record in records[1:]), default=0.0
        ),
        "violation": violation,
        "status": "weighted_claim_falsified" if violation else "no_violation_found",
        "records": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in payload.items() if key != "records"}, indent=2))


if __name__ == "__main__":
    main()
