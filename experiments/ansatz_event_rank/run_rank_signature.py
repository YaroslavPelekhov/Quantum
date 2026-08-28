"""Synthetic frozen test of parameter-invariant ansatz-event rank signatures."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import networkx as nx
import numpy as np


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULTS = REPO / "results" / "ansatz_event_rank"
sys.path[:0] = [
    str(REPO / "experiments" / "dcsrdt_structural_audit"),
    str(REPO / "experiments" / "contrastive_tensor_simulation"),
]

from contrastive_core import atomic_json, sha256
from structural_core import (
    RANK_TOLERANCE,
    deterministic_seed,
    frontier_profile,
    low_rank_spectrum,
    tensor_train_ranks,
)


SCHEDULES = (
    (np.asarray([0.23, 0.51, 0.77]), np.asarray([0.61, 0.42, 0.19])),
    (np.asarray([0.37, 0.68, 0.91]), np.asarray([0.49, 0.31, 0.11])),
    (np.asarray([0.16, 0.44, 0.83]), np.asarray([0.72, 0.38, 0.24])),
)
PAIRS = ((0, 1), (0, 2), (1, 2))


def graph_for(name: str) -> nx.Graph:
    if name == "chorded_cycle12":
        graph = nx.cycle_graph(12)
        graph.add_edges_from((i, (i + 4) % 12) for i in range(12))
        return nx.Graph(graph)
    if name == "regular14":
        return nx.random_regular_graph(3, 14, seed=14028)
    if name == "erdos16":
        graph = nx.gnp_random_graph(16, 0.24, seed=16028)
        if not nx.is_connected(graph):
            raise AssertionError("frozen held-out graph unexpectedly disconnected")
        return graph
    raise KeyError(name)


def order_for(graph: nx.Graph, ordering: str) -> list[int]:
    nodes = sorted(graph.nodes())
    if ordering == "natural":
        return nodes
    adjacency = nx.to_numpy_array(graph, nodelist=nodes, dtype=float)
    laplacian = np.diag(adjacency.sum(axis=1)) - adjacency
    values, vectors = np.linalg.eigh(laplacian)
    fiedler = vectors[:, np.argsort(values)[1]]
    return [nodes[index] for index in np.argsort(fiedler)]


def ordered_edges(graph: nx.Graph, order: list[int]) -> list[tuple[int, int]]:
    position = {node: index for index, node in enumerate(order)}
    return [(position[u], position[v]) for u, v in graph.edges()]


def maxcut_energies(qubits: int, edges: list[tuple[int, int]]) -> np.ndarray:
    indices = np.arange(1 << qubits, dtype=np.uint32)
    energy = np.zeros(indices.size, dtype=np.int16)
    for u, v in edges:
        energy += (
            ((indices >> u) & 1) ^ ((indices >> v) & 1)
        ).astype(np.int16)
    return energy


def apply_rx_layer(state: np.ndarray, qubits: int, beta: float) -> None:
    cosine = np.cos(beta)
    sine = -1j * np.sin(beta)
    for qubit in range(qubits):
        stride = 1 << qubit
        view = state.reshape(-1, 2 * stride)
        zero = view[:, :stride].copy()
        one = view[:, stride:].copy()
        view[:, :stride] = cosine * zero + sine * one
        view[:, stride:] = sine * zero + cosine * one


def qaoa_state(energy: np.ndarray, schedule) -> np.ndarray:
    qubits = int(round(np.log2(energy.size)))
    state = np.ones(energy.size, dtype=np.complex128) / np.sqrt(energy.size)
    gammas, betas = schedule
    for gamma, beta in zip(gammas, betas, strict=True):
        state *= np.exp(-1j * gamma * energy)
        apply_rx_layer(state, qubits, float(beta))
    return state


def run_case(name: str, ordering: str) -> dict:
    graph = graph_for(name)
    order = order_for(graph, ordering)
    edges = ordered_edges(graph, order)
    qubits = graph.number_of_nodes()
    energy = maxcut_energies(qubits, edges)
    threshold = int(energy.max()) - 1
    events = np.flatnonzero(energy >= threshold).astype(np.int64)
    structure = frontier_profile(events, qubits)
    states = [qaoa_state(energy, schedule) for schedule in SCHEDULES]
    schmidt = [tensor_train_ranks(state) for state in states]
    pair_profiles = {
        f"{a}-{b}": [
            low_rank_spectrum(states[a], states[b], events, cut)["numerical_rank"]
            for cut in range(1, qubits)
        ]
        for a, b in PAIRS
    }
    rng = np.random.default_rng(deterministic_seed(name, ordering, "phase"))
    scrambled = []
    for index in (0, 1):
        phase = np.exp(1j * rng.uniform(-np.pi, np.pi, energy.size))
        scrambled.append(np.abs(states[index]) * phase)
    phase_profile = [
        low_rank_spectrum(scrambled[0], scrambled[1], events, cut)["numerical_rank"]
        for cut in range(1, qubits)
    ]
    signatures_equal = len({tuple(value) for value in pair_profiles.values()}) == 1
    primary = pair_profiles["0-1"]
    eligible = [
        index for index, row in enumerate(structure)
        if row["structural_bound"] < row["left_dimension"]
    ]
    phase_saturates = all(
        phase_profile[index] == structure[index]["structural_bound"]
        for index in eligible
    )
    deficit_cuts = [
        index for index in eligible
        if primary[index] <= 0.75 * structure[index]["structural_bound"]
    ]
    schmidt_separated = [
        index for index in deficit_cuts
        if schmidt[0][index] > primary[index] / 2
        and schmidt[1][index] > primary[index] / 2
    ]
    return {
        "case": name,
        "ordering": ordering,
        "qubits": qubits,
        "edges": graph.number_of_edges(),
        "order": order,
        "event_threshold": threshold,
        "event_support": int(events.size),
        "structure": structure,
        "pair_rank_profiles": pair_profiles,
        "phase_scrambled_profile": phase_profile,
        "schmidt_rank_profiles": schmidt,
        "signatures_equal": signatures_equal,
        "phase_saturates": phase_saturates,
        "deficit_cuts": [index + 1 for index in deficit_cuts],
        "schmidt_separated_cuts": [index + 1 for index in schmidt_separated],
        "pass": bool(
            signatures_equal and phase_saturates
            and deficit_cuts and schmidt_separated
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("development", "transfer"))
    args = parser.parse_args()
    cases = (
        ("chorded_cycle12", "regular14")
        if args.stage == "development" else ("erdos16",)
    )
    output = RESULTS / f"{args.stage}.json"
    payload = {
        "complete": False,
        "stage": args.stage,
        "protocol_sha256": sha256(HERE / "PROTOCOL.md"),
        "rank_tolerance": RANK_TOLERANCE,
        "rows": [],
    }
    for case in cases:
        for ordering in ("natural", "spectral"):
            row = run_case(case, ordering)
            payload["rows"].append(row)
            atomic_json(output, payload)
            print(json.dumps({
                key: row[key] for key in (
                    "case", "ordering", "event_support", "signatures_equal",
                    "phase_saturates", "deficit_cuts",
                    "schmidt_separated_cuts", "pass"
                )
            }), flush=True)
    payload["passed_rows"] = sum(row["pass"] for row in payload["rows"])
    payload["success"] = payload["passed_rows"] == len(payload["rows"])
    payload["complete"] = True
    atomic_json(output, payload)
    print(json.dumps({
        "stage": args.stage,
        "passed_rows": payload["passed_rows"],
        "rows": len(payload["rows"]),
        "success": payload["success"],
    }, indent=2))


if __name__ == "__main__":
    main()
