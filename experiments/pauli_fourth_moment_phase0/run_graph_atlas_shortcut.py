"""Exhaustive small-graph falsification of the proof-shortcut conjecture."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import networkx as nx
import numpy as np


SINGLE_PAULI = (
    np.eye(2, dtype=complex),
    np.asarray([[0, 1], [1, 0]], dtype=complex),
    np.asarray([[0, -1j], [1j, 0]], dtype=complex),
    np.diag([1, -1]).astype(complex),
)


def anticommutes(left, right):
    return bool(sum(a and b and a != b for a, b in zip(left, right)) & 1)


def standard_representation(graph: nx.Graph):
    nodes = list(graph.nodes())
    edge = next(iter(graph.edges()), None)
    if edge is None:
        return [[] for _ in nodes]
    left, right = edge
    remainder = [node for node in nodes if node not in (left, right)]
    groups = {
        node: 2 * int(graph.has_edge(node, left)) + int(graph.has_edge(node, right))
        for node in remainder
    }
    induced = graph.subgraph(remainder).copy()
    for index, first in enumerate(remainder):
        for second in remainder[index + 1 :]:
            if groups[first] and groups[second] and groups[first] != groups[second]:
                if induced.has_edge(first, second):
                    induced.remove_edge(first, second)
                else:
                    induced.add_edge(first, second)
    suffixes = dict(zip(remainder, standard_representation(induced)))
    suffix_length = len(next(iter(suffixes.values()))) if suffixes else 0
    words = {left: [1] + [0] * suffix_length, right: [3] + [0] * suffix_length}
    for prefix in ({0: 0, 1: 1, 2: 3, 3: 2}, {0: 0, 1: 1, 2: 2, 3: 3}):
        for node in remainder:
            words[node] = [prefix[groups[node]]] + suffixes[node]
        ordered = [words[node] for node in nodes]
        if all(
            anticommutes(ordered[i], ordered[j]) == graph.has_edge(nodes[i], nodes[j])
            for i in range(len(nodes))
            for j in range(i + 1, len(nodes))
        ):
            return ordered
    raise RuntimeError("Pauli representation recursion failed")


def matrix(word):
    output = np.asarray([[1.0 + 0.0j]])
    for symbol in word:
        output = np.kron(output, SINGLE_PAULI[symbol])
    return output


def expectations(state, operators):
    return np.real(np.einsum("i,kij,j->k", state.conj(), operators, state))


def weighted_alpha(graph, weights):
    return max(float(weights[clique].sum()) for clique in nx.find_cliques(nx.complement(graph)))


def maximize(operators, weights, rng, restarts=16, iterations=220):
    dimension = operators.shape[1]
    starts = []
    for _ in range(restarts):
        state = rng.normal(size=dimension) + 1j * rng.normal(size=dimension)
        starts.append(state / np.linalg.norm(state))
    best = -math.inf
    for state in starts:
        old = -math.inf
        for _ in range(iterations):
            profile = expectations(state, operators)
            squares = profile**2
            pivot = int(np.argmax(squares))
            first = float(squares[pivot])
            second = float(np.dot(weights, squares))
            value = first * second
            best = max(best, value)
            if value <= old + 1e-13:
                break
            old = value
            coefficients = first * weights * profile
            coefficients[pivot] += second * profile[pivot]
            hamiltonian = np.einsum("k,kij->ij", coefficients, operators)
            _, vectors = np.linalg.eigh(hamiltonian)
            candidate = vectors[:, -1]
            overlap = np.vdot(state, candidate)
            if overlap:
                candidate *= np.exp(-1j * np.angle(overlap))
            state = 0.65 * candidate + 0.35 * state
            state /= np.linalg.norm(state)
    return best


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=2026090313)
    args = parser.parse_args()
    rng = np.random.default_rng(args.seed)
    graphs = [graph for graph in nx.graph_atlas_g() if 1 <= len(graph) <= 7]
    best = (-np.inf, None)
    tests = 0
    for graph_index, graph in enumerate(graphs):
        words = standard_representation(graph)
        operators = np.stack([matrix(word) for word in words])
        for weight_index, weights in enumerate(
            (np.ones(len(graph)), rng.lognormal(0.0, 1.8, len(graph)))
        ):
            alpha = weighted_alpha(graph, weights)
            ratio = maximize(operators, weights, rng) / alpha
            tests += 1
            if ratio > best[0]:
                best = (ratio, {"graph_index": graph_index, "vertices": len(graph), "weight_index": weight_index})
            if ratio > 1.0 + 1e-8:
                break
        if best[0] > 1.0 + 1e-8:
            break
    payload = {
        "claim": "max(r_i^2) sum_i w_i r_i^2 <= alpha(G,w)",
        "status": "counterexample" if best[0] > 1.0 + 1e-8 else "no_violation",
        "graphs": len(graphs),
        "tests": tests,
        "seed": args.seed,
        "best_ratio": best[0],
        "best_case": best[1],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
