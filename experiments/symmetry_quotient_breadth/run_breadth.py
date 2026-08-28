"""All-case exact breadth validation on the pre-existing QOBLIB selection."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import networkx as nx
import numpy as np


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path[:0] = [
    str(REPO / "experiments" / "evoq_mis_full_qoblib"),
    str(REPO / "experiments" / "ansatz_event_rank"),
    str(REPO / "experiments" / "dcsrdt_structural_audit"),
    str(REPO / "experiments" / "symmetry_quotient_decision_rank"),
    str(REPO / "experiments" / "contrastive_tensor_simulation"),
]

import run_cycle as rc
from contrastive_core import atomic_json, sha256
from quotient_core import (
    compile_twin_quotient,
    evolve_twin_quotient,
    quotient_decision_spectrum,
)
from run_rank_signature import apply_rx_layer
from structural_core import low_rank_spectrum


DEPTH = 15
GENOMES = (
    (0.70, 0.40, 1.00, 1.00),
    (0.64, 0.76, 1.77, 0.99),
)


def schedule(genome):
    delta_beta, delta_gamma, beta_power, gamma_power = genome
    layer = np.arange(1, DEPTH + 1, dtype=float)
    betas = delta_beta * ((DEPTH - layer + 1) / DEPTH) ** beta_power
    gammas = delta_gamma * (layer / DEPTH) ** gamma_power
    return gammas, -betas


def basis_data(graph: nx.Graph):
    qubits = graph.number_of_nodes()
    indices = np.arange(1 << qubits, dtype=np.uint32)
    selected = np.zeros(indices.size, dtype=np.int16)
    violations = np.zeros_like(selected)
    for qubit in range(qubits):
        selected += ((indices >> qubit) & 1).astype(np.int16)
    for left, right in graph.edges():
        violations += (
            ((indices >> left) & 1) & ((indices >> right) & 1)
        ).astype(np.int16)
    energy = (-selected.astype(np.float64) + 1.5 * violations) * (4.0 / 1.5)
    feasible = violations == 0
    alpha = int(selected[feasible].max())
    events = np.flatnonzero(feasible & (selected == alpha)).astype(np.int64)
    return energy, events, alpha


def dense_state(energy: np.ndarray, genome) -> np.ndarray:
    qubits = int(round(np.log2(energy.size)))
    gammas, betas = schedule(genome)
    state = np.ones(energy.size, dtype=np.complex128) / np.sqrt(energy.size)
    for gamma, beta in zip(gammas, betas, strict=True):
        state *= np.exp(-1j * gamma * energy)
        apply_rx_layer(state, qubits, float(beta))
    return state


def main() -> None:
    selection = json.loads(
        (REPO / "experiments" / "evoq_mis_full_qoblib" / "results"
         / "qoblib_cohort_screen" / "selected_cases.json")
        .read_text(encoding="utf-8")
    )
    selected_rows = [
        row for row in selection["selected_cases"]
        if row["case"] != "aves-sparrow-social"
    ]
    output = REPO / "results" / "symmetry_quotient_breadth" / "breadth.json"
    payload = {
        "complete": False,
        "protocol_sha256": sha256(HERE / "PROTOCOL.md"),
        "selection_was_preexisting": True,
        "rows": [],
    }
    for selected in selected_rows:
        original = rc.parse_gph_file(
            rc.QOBLIB / "07-independentset" / "instances"
            / f"{selected['case']}.gph"
        )
        reduced = rc.reduce_graph_for_quantum(
            original, max_degree=selected["cap"]
        ).reduced_graph
        mapping = {node: index for index, node in enumerate(sorted(reduced.nodes()))}
        graph = nx.relabel_nodes(reduced, mapping)
        order = list(range(graph.number_of_nodes()))
        energy, events, alpha = basis_data(graph)
        start = time.perf_counter()
        architecture = compile_twin_quotient(
            graph, order, penalty=1.5, normalized_ising=True
        )
        compile_seconds = time.perf_counter() - start
        start = time.perf_counter()
        quotient_states = [
            evolve_twin_quotient(architecture, *schedule(genome))
            for genome in GENOMES
        ]
        quotient_seconds = time.perf_counter() - start
        start = time.perf_counter()
        dense_states = [dense_state(energy, genome) for genome in GENOMES]
        dense_seconds = time.perf_counter() - start
        amplitude_error = max(
            float(np.max(np.abs(quotient.dense() - dense)))
            for quotient, dense in zip(quotient_states, dense_states, strict=True)
        )
        cut = max(1, graph.number_of_nodes() // 2)
        quotient_spectrum = quotient_decision_spectrum(
            quotient_states[0], quotient_states[1], events, cut
        )
        dense_spectrum = low_rank_spectrum(
            dense_states[0], dense_states[1], events, cut
        )
        row = {
            "case": selected["case"], "family": selected["family"],
            "qubits": graph.number_of_nodes(), "edges": graph.number_of_edges(),
            "independence_number": alpha, "event_support": int(events.size),
            "nontrivial_twin_class_sizes": [
                len(group) for group in architecture.groups if len(group) > 1
            ],
            "full_dimension": int(energy.size),
            "quotient_dimension": architecture.orbit_count,
            "dimension_compression": energy.size / architecture.orbit_count,
            "compile_seconds": compile_seconds,
            "two_state_quotient_seconds": quotient_seconds,
            "two_state_dense_seconds": dense_seconds,
            "evolution_speedup_excluding_compile": dense_seconds / quotient_seconds,
            "amplitude_error": amplitude_error,
            "max_norm_error": max(
                abs(float(np.linalg.norm(state.coefficients)) - 1.0)
                for state in quotient_states
            ),
            "cut": cut,
            "quotient_rank": quotient_spectrum["numerical_rank"],
            "dense_rank": dense_spectrum["numerical_rank"],
            "trace_error": abs(quotient_spectrum["trace"] - dense_spectrum["trace"]),
            "trace_norm_error": abs(
                quotient_spectrum["trace_norm"] - dense_spectrum["trace_norm"]
            ),
        }
        row["pass"] = bool(
            amplitude_error < 1e-11 and row["max_norm_error"] < 1e-10
            and row["quotient_rank"] == row["dense_rank"]
            and row["trace_error"] < 1e-10
            and row["trace_norm_error"] < 1e-10
        )
        payload["rows"].append(row)
        atomic_json(output, payload)
        print(json.dumps(row, indent=2), flush=True)
    payload["passed_rows"] = sum(row["pass"] for row in payload["rows"])
    payload["success"] = payload["passed_rows"] == len(payload["rows"])
    payload["complete"] = True
    atomic_json(output, payload)
    print(json.dumps({"passed_rows": payload["passed_rows"],
        "rows": len(payload["rows"]), "success": payload["success"]}, indent=2))


if __name__ == "__main__":
    main()

