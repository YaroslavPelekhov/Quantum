"""Benchmark the quotient backend against an optimized Aer statevector."""

from __future__ import annotations

import json
import os
import platform
import sys
import time
from pathlib import Path

import numpy as np
import qiskit
import qiskit_aer
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULTS = REPO / "results" / "symmetry_claim_falsification"
sys.path[:0] = [
    str(REPO / "experiments" / "rankcert_mps"),
    str(REPO / "experiments" / "sparse_mps_dcsrdt"),
    str(REPO / "experiments" / "symmetry_quotient_backend"),
    str(REPO / "experiments" / "symmetry_quotient_decision_rank"),
    str(REPO / "experiments" / "contrastive_tensor_simulation"),
]

import rankcert_inputs
from contrastive_core import atomic_json, sha256
from quotient_core import (
    compile_twin_quotient,
    evolve_twin_quotient,
    quotient_decision_spectrum,
)
from run_backend import graph_from_scorer, schedule
from sparse_mps_core import enumerate_bks_support


AER_REPETITIONS = 3
QUOTIENT_REPETITIONS = 7
SAMPLE_SIZE = 20_000
CUTS = (5, 9, 12)


def circuit_for(graph, gammas: np.ndarray, betas: np.ndarray) -> QuantumCircuit:
    qubits = graph.number_of_nodes()
    circuit = QuantumCircuit(qubits)
    circuit.h(range(qubits))
    # E = (4/1.5) (-sum x_i + 1.5 sum_edges x_i x_j).
    # Up to a global constant this is sum_i h_i Z_i + sum_edges Z_i Z_j,
    # with h_i = 4/(2*1.5) - degree(i).
    fields = [4.0 / 3.0 - graph.degree(qubit) for qubit in range(qubits)]
    for gamma, beta in zip(gammas, betas, strict=True):
        for qubit, field in enumerate(fields):
            circuit.rz(2.0 * float(gamma) * field, qubit)
        for left, right in graph.edges():
            circuit.rzz(2.0 * float(gamma), left, right)
        for qubit in range(qubits):
            circuit.rx(2.0 * float(beta), qubit)
    circuit.save_statevector()
    return circuit


def aligned_errors(actual: np.ndarray, reference: np.ndarray, sample: np.ndarray):
    left = np.asarray(actual[sample])
    right = np.asarray(reference[sample])
    overlap = np.vdot(left, right)
    phase = overlap / abs(overlap)
    return {
        "amplitude": float(np.max(np.abs(phase * left - right))),
        "probability": float(np.max(np.abs(np.abs(left) ** 2 - np.abs(right) ** 2))),
    }


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    specs = {
        (row["case"], row["ordering"], row["method"]): row
        for row in rankcert_inputs.load_specs()
    }
    spec = specs[("aves-sparrow-social", "sorted", "published_lr")]
    comparison = specs[(
        "aves-sparrow-social", "sorted", "prior_matched_random"
    )]
    graph = graph_from_scorer(spec["scorer"])
    gammas, betas = schedule(spec["schedule_parameters"])
    reference = np.load(spec["reference_file"], mmap_mode="r", allow_pickle=False)
    rng = np.random.default_rng(20260828)
    sample = rng.choice(reference.size, size=SAMPLE_SIZE, replace=False)

    start = time.perf_counter()
    architecture = compile_twin_quotient(
        graph, list(range(24)), penalty=1.5, normalized_ising=True
    )
    quotient_compile = time.perf_counter() - start
    quotient_times = []
    quotient_state = None
    for _ in range(QUOTIENT_REPETITIONS):
        start = time.perf_counter()
        quotient_state = evolve_twin_quotient(architecture, gammas, betas)
        quotient_times.append(time.perf_counter() - start)
    quotient_errors = aligned_errors(
        quotient_state.amplitudes(sample), np.asarray(reference[sample]),
        np.arange(SAMPLE_SIZE),
    )

    start = time.perf_counter()
    circuit = circuit_for(graph, gammas, betas)
    simulator = AerSimulator(method="statevector")
    compiled = transpile(circuit, simulator, optimization_level=3)
    aer_compile = time.perf_counter() - start
    aer_times = []
    aer_state = None
    for _ in range(AER_REPETITIONS):
        start = time.perf_counter()
        result = simulator.run(compiled).result()
        aer_times.append(time.perf_counter() - start)
        aer_state = np.asarray(result.get_statevector(compiled))
    aer_errors = aligned_errors(aer_state, reference, sample)

    other_gammas, other_betas = schedule(comparison["schedule_parameters"])
    other_state = evolve_twin_quotient(
        architecture, other_gammas, other_betas
    )
    events = np.asarray(enumerate_bks_support(spec["scorer"]), dtype=np.int64)
    decision_times = []
    for _ in range(QUOTIENT_REPETITIONS):
        start = time.perf_counter()
        for cut in CUTS:
            quotient_decision_spectrum(
                quotient_state, other_state, events, cut
            )
        decision_times.append(time.perf_counter() - start)

    quotient_median = float(np.median(quotient_times))
    aer_median = float(np.median(aer_times))
    ratio = aer_median / quotient_median
    conservative = min(aer_times) / max(quotient_times)
    old_ratio = 23.90407527830599
    payload = {
        "complete": True,
        "protocol_sha256": sha256(HERE / "PERFORMANCE_PROTOCOL.md"),
        "platform": platform.platform(),
        "logical_cpus": os.cpu_count(),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "qiskit": qiskit.__version__,
        "qiskit_aer": qiskit_aer.__version__,
        "aer_repetitions": AER_REPETITIONS,
        "quotient_repetitions": QUOTIENT_REPETITIONS,
        "aer_transpile_seconds": aer_compile,
        "quotient_compile_seconds": quotient_compile,
        "aer_seconds": aer_times,
        "quotient_seconds": quotient_times,
        "decision_three_cut_seconds": decision_times,
        "aer_median_seconds": aer_median,
        "quotient_median_seconds": quotient_median,
        "decision_median_seconds": float(np.median(decision_times)),
        "median_steady_speedup": ratio,
        "conservative_speedup": conservative,
        "old_reported_speedup": old_ratio,
        "old_numeric_claim_survives": abs(ratio - old_ratio) <= 0.2 * old_ratio,
        "weaker_practical_speedup_survives": ratio > 2.0 and conservative > 2.0,
        "aer_errors": aer_errors,
        "quotient_errors": quotient_errors,
        "exactness_pass": max(
            aer_errors["probability"], quotient_errors["probability"]
        ) < 1e-12,
        "dense_state_bytes": int(reference.nbytes),
        "quotient_state_bytes": int(quotient_state.coefficients.nbytes),
        "representation_compression": reference.nbytes / quotient_state.coefficients.nbytes,
    }
    atomic_json(RESULTS / "performance.json", payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
