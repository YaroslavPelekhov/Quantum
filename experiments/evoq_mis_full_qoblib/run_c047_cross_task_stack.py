"""Frozen task-and-stack triangulation of the QAOA ranking certificate."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from importlib.metadata import version
from pathlib import Path
from time import perf_counter

import networkx as nx
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator


HERE = Path(__file__).resolve().parent
PROTOCOL = HERE / "C047_CROSS_TASK_STACK_PROTOCOL.md"
RESULT = HERE / "results" / "c047_cross_task_stack.json"
DEPTH = 15
METHODS = {
    "linear_ramp": (0.7, 0.4, 1.0, 1.0),
    "matched_random": (0.6424738670407446, 0.7593921349176262,
                       1.776791693083474, 0.9917239502490107),
}
SETTINGS = (
    ("bond4_cut1e-2", 4, 1e-2),
    ("bond8_cut1e-3", 8, 1e-3),
    ("bond16_cut1e-4", 16, 1e-4),
    ("bond32_cut1e-6", 32, 1e-6),
    ("bond128_cut1e-12", 128, 1e-12),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def graph_cases() -> dict[str, nx.Graph]:
    return {
        "cubic10": nx.random_regular_graph(3, 10, seed=47010),
        "erdos12": nx.gnp_random_graph(12, 0.32, seed=47012),
        "watts14": nx.watts_strogatz_graph(14, 4, 0.25, seed=47014),
        "cubic16": nx.random_regular_graph(3, 16, seed=47016),
    }


def schedule(genome: tuple[float, ...]) -> tuple[np.ndarray, np.ndarray]:
    db, dg, pb, pg = genome
    k = np.arange(1, DEPTH + 1, dtype=float)
    betas = db * ((DEPTH - k + 1.0) / DEPTH) ** pb
    gammas = dg * (k / DEPTH) ** pg
    return betas, gammas


def placements(n: int, seed: int) -> dict[str, tuple[int, ...]]:
    rng = np.random.default_rng(seed)
    return {"identity": tuple(range(n)), "seeded": tuple(map(int, rng.permutation(n)))}


def qiskit_circuit(graph: nx.Graph, placement: tuple[int, ...], genome) -> QuantumCircuit:
    n = graph.number_of_nodes()
    circuit = QuantumCircuit(n)
    circuit.h(range(n))
    betas, gammas = schedule(genome)
    for beta, gamma in zip(betas, gammas):
        for u, v in sorted(graph.edges()):
            circuit.rzz(-float(gamma), placement[u], placement[v])
        for q in range(n):
            circuit.rx(2.0 * float(beta), q)
    return circuit


def braket_state(graph: nx.Graph, placement: tuple[int, ...], genome) -> np.ndarray:
    from braket.circuits import Circuit
    from braket.devices import LocalSimulator

    n = graph.number_of_nodes()
    circuit = Circuit()
    for q in range(n):
        circuit.h(q)
    betas, gammas = schedule(genome)
    for beta, gamma in zip(betas, gammas):
        for u, v in sorted(graph.edges()):
            circuit.zz(placement[u], placement[v], -float(gamma))
        for q in range(n):
            circuit.rx(q, 2.0 * float(beta))
    circuit.state_vector()
    raw = np.asarray(
        LocalSimulator("braket_sv").run(circuit, shots=0).result().result_types[0].value,
        dtype=np.complex128,
    )
    # Braket indexes q0 as the most-significant axis; Qiskit uses q0 as the
    # least-significant bit. Reverse tensor axes before direct comparison.
    return raw.reshape((2,) * n).transpose(tuple(reversed(range(n)))).reshape(-1)


def normalize(state: np.ndarray) -> tuple[np.ndarray, float]:
    norm = float(np.vdot(state, state).real)
    if not np.isfinite(norm) or norm <= 0.0:
        raise AssertionError(f"invalid state norm {norm}")
    return state / np.sqrt(norm), norm


def mps_state(circuit: QuantumCircuit, bond: int, cutoff: float) -> tuple[np.ndarray, float, float]:
    saved = circuit.copy()
    saved.save_statevector()
    backend = AerSimulator(
        method="matrix_product_state",
        matrix_product_state_max_bond_dimension=bond,
        matrix_product_state_truncation_threshold=cutoff,
        max_parallel_experiments=1,
    )
    started = perf_counter()
    result = backend.run(saved).result()
    elapsed = perf_counter() - started
    state, raw_norm = normalize(np.asarray(result.get_statevector(saved), dtype=np.complex128))
    return state, raw_norm, elapsed


def cut_scores(graph: nx.Graph, placement: tuple[int, ...]) -> np.ndarray:
    n = graph.number_of_nodes()
    indices = np.arange(1 << n, dtype=np.uint64)
    scores = np.zeros(indices.size, dtype=np.int16)
    for u, v in graph.edges():
        scores += ((indices >> placement[u]) & 1 != (indices >> placement[v]) & 1)
    return scores


def metrics(state: np.ndarray, optimum_mask: np.ndarray) -> dict:
    probabilities = state.real * state.real + state.imag * state.imag
    return {
        "optimum_probability": float(probabilities[optimum_mask].sum(dtype=np.float64)),
        "normalization": float(probabilities.sum(dtype=np.float64)),
    }


def compare(reference: np.ndarray, candidate: np.ndarray) -> dict:
    p = reference.real * reference.real + reference.imag * reference.imag
    q = candidate.real * candidate.real + candidate.imag * candidate.imag
    return {
        "tvd": float(0.5 * np.abs(p - q).sum(dtype=np.float64)),
        "fidelity": float(abs(np.vdot(reference, candidate)) ** 2),
    }


def sign(value: float, tolerance: float = 1e-14) -> int:
    return int(value > tolerance) - int(value < -tolerance)


def main() -> None:
    import braket
    import qiskit
    import qiskit_aer

    exact_rows = []
    mps_rows = []
    exact_states: dict[tuple[str, str, str], np.ndarray] = {}
    masks: dict[tuple[str, str], np.ndarray] = {}
    graphs = graph_cases()
    for case_index, (case, graph) in enumerate(graphs.items()):
        n = graph.number_of_nodes()
        edges = [list(map(int, edge)) for edge in sorted(graph.edges())]
        graph_hash = hashlib.sha256(json.dumps(edges).encode()).hexdigest()
        for ordering, placement in placements(n, 47100 + case_index).items():
            scores = cut_scores(graph, placement)
            maximum_cut = int(scores.max())
            optimum_mask = scores == maximum_cut
            masks[(case, ordering)] = optimum_mask
            for method, genome in METHODS.items():
                q_circuit = qiskit_circuit(graph, placement, genome)
                q_state, _ = normalize(np.asarray(Statevector.from_instruction(q_circuit).data))
                started = perf_counter()
                b_state, _ = normalize(braket_state(graph, placement, genome))
                braket_seconds = perf_counter() - started
                cross = compare(q_state, b_state)
                if cross["tvd"] > 1e-10:
                    raise AssertionError(f"cross-SDK exact mismatch {case}/{ordering}/{method}: {cross}")
                row = {
                    "case": case,
                    "vertices": n,
                    "edges": graph.number_of_edges(),
                    "edge_list_sha256": graph_hash,
                    "maximum_cut": maximum_cut,
                    "optimal_bitstrings": int(optimum_mask.sum()),
                    "ordering": ordering,
                    "placement": list(placement),
                    "method": method,
                    "qiskit_metrics": metrics(q_state, optimum_mask),
                    "braket_metrics": metrics(b_state, optimum_mask),
                    "cross_sdk": cross,
                    "braket_seconds": braket_seconds,
                }
                exact_rows.append(row)
                exact_states[(case, ordering, method)] = q_state
                print("exact", case, ordering, method, cross["tvd"], flush=True)
                for setting, bond, cutoff in SETTINGS:
                    approx, raw_norm, elapsed = mps_state(q_circuit, bond, cutoff)
                    comparison = compare(q_state, approx)
                    mps_rows.append({
                        "case": case,
                        "ordering": ordering,
                        "method": method,
                        "setting": setting,
                        "bond": bond,
                        "cutoff": cutoff,
                        "metrics": metrics(approx, optimum_mask),
                        "comparison": comparison,
                        "raw_norm": raw_norm,
                        "elapsed_seconds": elapsed,
                    })
                    print("mps", case, ordering, method, setting, comparison["tvd"], flush=True)

    exact_index = {(r["case"], r["ordering"], r["method"]): r for r in exact_rows}
    mps_index = {(r["case"], r["ordering"], r["method"], r["setting"]): r for r in mps_rows}
    cohorts = []
    for case in graphs:
        for ordering in ("identity", "seeded"):
            exact_lr = exact_index[(case, ordering, "linear_ramp")]["qiskit_metrics"]["optimum_probability"]
            exact_nl = exact_index[(case, ordering, "matched_random")]["qiskit_metrics"]["optimum_probability"]
            exact_effect = exact_nl - exact_lr
            for setting, bond, cutoff in SETTINGS:
                lr = mps_index[(case, ordering, "linear_ramp", setting)]
                nl = mps_index[(case, ordering, "matched_random", setting)]
                effect = nl["metrics"]["optimum_probability"] - lr["metrics"]["optimum_probability"]
                bound = lr["comparison"]["tvd"] + nl["comparison"]["tvd"]
                error = abs(effect - exact_effect)
                certified = abs(exact_effect) > bound
                row = {
                    "case": case,
                    "ordering": ordering,
                    "setting": setting,
                    "bond": bond,
                    "cutoff": cutoff,
                    "exact_effect": exact_effect,
                    "mps_effect": effect,
                    "effect_error": error,
                    "tvd_bound": bound,
                    "inequality_holds": error <= bound + 2e-12,
                    "certified": certified,
                    "sign_correct": sign(effect) == sign(exact_effect),
                }
                if not row["inequality_holds"]:
                    raise AssertionError(f"TVD inequality failed: {row}")
                cohorts.append(row)

    ordering_residuals = []
    for case in graphs:
        for method in METHODS:
            p0 = exact_index[(case, "identity", method)]["qiskit_metrics"]["optimum_probability"]
            p1 = exact_index[(case, "seeded", method)]["qiskit_metrics"]["optimum_probability"]
            ordering_residuals.append(abs(p0 - p1))
    summary = {
        "exact_rows": len(exact_rows),
        "mps_rows": len(mps_rows),
        "cohorts": len(cohorts),
        "maximum_cross_sdk_tvd": max(r["cross_sdk"]["tvd"] for r in exact_rows),
        "maximum_exact_ordering_residual": max(ordering_residuals),
        "inequalities_holding": sum(r["inequality_holds"] for r in cohorts),
        "certified_cohorts": sum(r["certified"] for r in cohorts),
        "certified_sign_correct": sum(r["certified"] and r["sign_correct"] for r in cohorts),
        "all_sign_correct": sum(r["sign_correct"] for r in cohorts),
        "sign_failures": sum(not r["sign_correct"] for r in cohorts),
    }
    if summary["maximum_exact_ordering_residual"] > 1e-10:
        raise AssertionError(f"exact ordering invariance failed: {summary}")
    payload = {
        "stage": "c047_cross_task_cross_stack_external_validation",
        "complete": True,
        "protocol_sha256": sha256(PROTOCOL),
        "runner_sha256": sha256(Path(__file__)),
        "provenance": {
            "python": sys.version,
            "platform": platform.platform(),
            "numpy": np.__version__,
            "networkx": nx.__version__,
            "qiskit": qiskit.__version__,
            "qiskit_aer": qiskit_aer.__version__,
            "braket_sdk": version("amazon-braket-sdk"),
        },
        "design": {"depth": DEPTH, "methods": METHODS, "settings": SETTINGS},
        "summary": summary,
        "exact_rows": exact_rows,
        "mps_rows": mps_rows,
        "cohorts": cohorts,
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
