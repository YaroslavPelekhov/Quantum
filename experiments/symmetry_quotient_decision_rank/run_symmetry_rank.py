"""Frozen symmetry-rich MIS rank-signature development and transfer."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import networkx as nx
import numpy as np


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULTS = REPO / "results" / "symmetry_quotient_decision_rank"
sys.path[:0] = [
    str(REPO / "experiments" / "ansatz_event_rank"),
    str(REPO / "experiments" / "dcsrdt_structural_audit"),
    str(REPO / "experiments" / "contrastive_tensor_simulation"),
]

from contrastive_core import atomic_json, sha256
from run_rank_signature import apply_rx_layer
from structural_core import (
    RANK_TOLERANCE,
    deterministic_seed,
    frontier_profile,
    low_rank_spectrum,
    tensor_train_ranks,
)


GENOMES = (
    (0.70, 0.40, 1.00, 1.00),
    (0.64, 0.76, 1.77, 0.99),
    (0.42, 0.63, 1.20, 0.80),
)
PAIRS = ((0, 1), (0, 2), (1, 2))
DEPTH = 15


def triangle_graph(triangles: int, ring: bool) -> nx.Graph:
    graph = nx.Graph()
    for triangle in range(triangles):
        base = 3 * triangle
        graph.add_edges_from((
            (base, base + 1), (base + 1, base + 2), (base + 2, base)
        ))
    for triangle in range(triangles - 1):
        graph.add_edge(3 * triangle, 3 * (triangle + 1))
    if ring:
        graph.add_edge(0, 3 * (triangles - 1))
    return graph


def order_for(graph: nx.Graph, ordering: str) -> list[int]:
    nodes = sorted(graph.nodes())
    if ordering == "natural":
        return nodes
    adjacency = nx.to_numpy_array(graph, nodelist=nodes)
    laplacian = np.diag(adjacency.sum(axis=1)) - adjacency
    values, vectors = np.linalg.eigh(laplacian)
    fiedler = vectors[:, np.argsort(values)[1]]
    return [nodes[index] for index in np.argsort(fiedler)]


def energy_and_event(graph: nx.Graph, order: list[int]):
    position = {node: index for index, node in enumerate(order)}
    qubits = len(order)
    indices = np.arange(1 << qubits, dtype=np.uint32)
    selected = np.zeros(indices.size, dtype=np.int16)
    violations = np.zeros_like(selected)
    for qubit in range(qubits):
        selected += ((indices >> qubit) & 1).astype(np.int16)
    for u, v in graph.edges():
        left, right = position[u], position[v]
        violations += (
            ((indices >> left) & 1) & ((indices >> right) & 1)
        ).astype(np.int16)
    feasible = violations == 0
    alpha = int(selected[feasible].max())
    events = np.flatnonzero(feasible & (selected == alpha)).astype(np.int64)
    return selected - 2 * violations, events, alpha


def schedule(genome):
    delta_beta, delta_gamma, beta_power, gamma_power = genome
    layer = np.arange(1, DEPTH + 1, dtype=float)
    betas = delta_beta * ((DEPTH - layer + 1) / DEPTH) ** beta_power
    gammas = delta_gamma * (layer / DEPTH) ** gamma_power
    return gammas, betas


def state_for(energy: np.ndarray, genome) -> np.ndarray:
    qubits = int(round(np.log2(energy.size)))
    state = np.ones(energy.size, dtype=np.complex128) / np.sqrt(energy.size)
    gammas, betas = schedule(genome)
    for gamma, beta in zip(gammas, betas, strict=True):
        state *= np.exp(-1j * gamma * energy)
        apply_rx_layer(state, qubits, float(beta))
    return state


def audit(name: str, triangles: int, ring: bool, ordering: str) -> dict:
    graph = triangle_graph(triangles, ring)
    order = order_for(graph, ordering)
    energy, events, alpha = energy_and_event(graph, order)
    qubits = graph.number_of_nodes()
    structure = frontier_profile(events, qubits)
    states = [state_for(energy, genome) for genome in GENOMES]
    schmidt = [tensor_train_ranks(state) for state in states]
    pairs = {
        f"{a}-{b}": [
            low_rank_spectrum(states[a], states[b], events, cut)["numerical_rank"]
            for cut in range(1, qubits)
        ] for a, b in PAIRS
    }
    rng = np.random.default_rng(deterministic_seed(name, ordering, "phase"))
    scrambled = [
        np.abs(states[index])
        * np.exp(1j * rng.uniform(-np.pi, np.pi, energy.size))
        for index in (0, 1)
    ]
    phase = [
        low_rank_spectrum(scrambled[0], scrambled[1], events, cut)["numerical_rank"]
        for cut in range(1, qubits)
    ]
    signatures_equal = len({tuple(value) for value in pairs.values()}) == 1
    primary = pairs["0-1"]
    eligible = [
        i for i, row in enumerate(structure)
        if row["structural_bound"] < row["left_dimension"]
    ]
    phase_saturates = all(
        phase[i] == structure[i]["structural_bound"] for i in eligible
    )
    deficit = [
        i for i in eligible
        if primary[i] <= 0.75 * structure[i]["structural_bound"]
    ]
    separated = [
        i for i in deficit
        if schmidt[0][i] > primary[i] / 2
        and schmidt[1][i] > primary[i] / 2
    ]
    return {
        "case": name, "ordering": ordering, "qubits": qubits,
        "edges": graph.number_of_edges(), "automorphisms": sum(
            1 for _ in nx.algorithms.isomorphism.GraphMatcher(graph, graph)
            .isomorphisms_iter()
        ),
        "order": order, "independence_number": alpha,
        "event_support": int(events.size), "structure": structure,
        "pair_rank_profiles": pairs, "phase_scrambled_profile": phase,
        "schmidt_rank_profiles": schmidt,
        "signatures_equal": signatures_equal,
        "phase_saturates": phase_saturates,
        "deficit_cuts": [i + 1 for i in deficit],
        "schmidt_separated_cuts": [i + 1 for i in separated],
        "pass": bool(
            signatures_equal and phase_saturates
            and len(deficit) >= 3 and separated
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("development", "transfer"))
    args = parser.parse_args()
    cases = (
        (("triangle_chain4", 4, False), ("triangle_chain5", 5, False))
        if args.stage == "development"
        else (("triangle_ring6", 6, True),)
    )
    output = RESULTS / f"{args.stage}.json"
    payload = {
        "complete": False, "stage": args.stage,
        "protocol_sha256": sha256(HERE / "PROTOCOL.md"), "rows": []
    }
    for name, count, ring in cases:
        for ordering in ("natural", "spectral"):
            row = audit(name, count, ring, ordering)
            payload["rows"].append(row)
            atomic_json(output, payload)
            print(json.dumps({key: row[key] for key in (
                "case", "ordering", "qubits", "event_support",
                "automorphisms", "deficit_cuts", "pass"
            )}), flush=True)
    payload["passed_rows"] = sum(row["pass"] for row in payload["rows"])
    payload["success"] = payload["passed_rows"] == len(payload["rows"])
    payload["complete"] = True
    atomic_json(output, payload)
    print(json.dumps({"stage": args.stage, "passed_rows": payload["passed_rows"],
        "rows": len(payload["rows"]), "success": payload["success"]}, indent=2))


if __name__ == "__main__":
    main()

