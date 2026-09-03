"""Audit the exact exponent-two theorem for line-graph Pauli scenarios.

The filename is retained from the weaker cubic conjecture that led to the
free-fermion strengthening.
"""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import networkx as nx
import numpy as np

from stabilizer_core import random_state


I = np.eye(2, dtype=complex)
X = np.asarray([[0, 1], [1, 0]], dtype=complex)
Y = np.asarray([[0, -1j], [1j, 0]], dtype=complex)
Z = np.diag([1, -1]).astype(complex)


def tensor(factors):
    output = np.asarray([[1.0 + 0.0j]])
    for factor in factors:
        output = np.kron(output, factor)
    return output


def majoranas(count: int):
    qubits = (count + 1) // 2
    output = []
    for pivot in range(qubits):
        output.append(tensor([Z] * pivot + [X] + [I] * (qubits - pivot - 1)))
        output.append(tensor([Z] * pivot + [Y] + [I] * (qubits - pivot - 1)))
    return output[:count]


def maximum_weight(graph: nx.Graph, weights: dict[tuple[int, int], float]) -> float:
    weighted = graph.copy()
    nx.set_edge_attributes(weighted, weights, "weight")
    matching = nx.max_weight_matching(weighted, maxcardinality=False, weight="weight")
    return float(sum(weights[tuple(sorted(edge))] for edge in matching))


def blossom_excess(graph: nx.Graph, y: dict[tuple[int, int], float]) -> float:
    nodes = list(graph.nodes())
    maximum = -np.inf
    for size in range(3, len(nodes) + 1, 2):
        for subset in itertools.combinations(nodes, size):
            induced_sum = sum(y[tuple(sorted(edge))] for edge in graph.subgraph(subset).edges())
            maximum = max(maximum, induced_sum - (size - 1) / 2)
    return float(maximum)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--graphs-per-size", type=int, default=12)
    parser.add_argument("--states-per-graph", type=int, default=40)
    parser.add_argument("--atlas-states-per-graph", type=int, default=4)
    parser.add_argument("--seed", type=int, default=660157)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rng = np.random.default_rng(args.seed)
    worst_blossom = -np.inf
    worst_degree = -np.inf
    largest_weighted_ratio = 0.0
    instances = 0
    boundary_controls = 0
    atlas_graphs = [
        nx.convert_node_labels_to_integers(graph)
        for graph in nx.graph_atlas_g()
        if 2 <= len(graph) <= 7 and graph.number_of_edges() > 0
    ]
    random_graphs = []
    for vertices in range(3, 10):
        for _ in range(args.graphs_per_size):
            graph = nx.gnp_random_graph(
                vertices,
                float(rng.uniform(0.15, 0.85)),
                seed=int(rng.integers(2**31)),
            )
            if graph.number_of_edges() > 0:
                random_graphs.append(graph)

    graph_cases = [
        (graph, args.atlas_states_per_graph, "atlas") for graph in atlas_graphs
    ] + [(graph, args.states_per_graph, "random") for graph in random_graphs]
    for graph, state_count, source in graph_cases:
        vertices = len(graph)
        gamma = majoranas(vertices)
        dimension = gamma[0].shape[0]
        edges = [tuple(sorted(edge)) for edge in graph.edges()]
        operators = np.stack([1j * gamma[u] @ gamma[v] for u, v in edges])
        weights = {
            edge: float(value)
            for edge, value in zip(edges, rng.lognormal(0, 1.2, len(edges)))
        }
        alpha = maximum_weight(graph, weights)
        for _state_index in range(state_count):
            state = random_state(dimension, rng)
            expectations = np.real(
                np.einsum("i,kij,j->k", state.conj(), operators, state)
            )
            y = {
                edge: float(abs(value) ** 2)
                for edge, value in zip(edges, expectations)
            }
            degree = max(
                sum(y[tuple(sorted(edge))] for edge in graph.edges(node)) - 1.0
                for node in graph.nodes()
            )
            worst_degree = max(worst_degree, degree)
            worst_blossom = max(worst_blossom, blossom_excess(graph, y))
            objective = sum(weights[edge] * y[edge] for edge in edges)
            largest_weighted_ratio = max(largest_weighted_ratio, objective / alpha)
            instances += 1

        weighted = graph.copy()
        nx.set_edge_attributes(weighted, weights, "weight")
        matching = nx.max_weight_matching(
            weighted, maxcardinality=False, weight="weight"
        )
        if matching:
            hamiltonian = sum(
                operators[edges.index(tuple(sorted(edge)))] for edge in matching
            )
            _, vectors = np.linalg.eigh(hamiltonian)
            state = vectors[:, -1]
            profile = np.real(
                np.einsum("i,kij,j->k", state.conj(), operators, state)
            )
            y = {
                edge: float(abs(value) ** 2)
                for edge, value in zip(edges, profile)
            }
            weighted_ratio = sum(weights[edge] * y[edge] for edge in edges) / alpha
            if abs(weighted_ratio - 1.0) > 1e-8:
                raise AssertionError((source, vertices, weighted_ratio))
            boundary_controls += 1

    payload = {
        "experiment": "line_graph_Pauli_exponent_two_matching_polytope",
        "seed": args.seed,
        "random_state_instances": instances,
        "boundary_controls": boundary_controls,
        "atlas_root_graphs": len(atlas_graphs),
        "random_root_graphs": len(random_graphs),
        "base_vertex_sizes": [3, 4, 5, 6, 7, 8, 9],
        "maximum_degree_constraint_excess": worst_degree,
        "maximum_blossom_constraint_excess": worst_blossom,
        "largest_weighted_objective_ratio": largest_weighted_ratio,
        "status": "violation" if max(worst_degree, worst_blossom, largest_weighted_ratio - 1) > 1e-9 else "no_violation",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    if payload["status"] == "violation":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
