"""Run the frozen contrastive tensor simulation kill tests."""

from __future__ import annotations

import argparse
import gc
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import numpy as np
from qiskit import qpy
from qiskit.quantum_info import DensityMatrix, Operator


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULTS = REPO / "results" / "contrastive_tensor_simulation"
sys.path[:0] = [
    str(HERE),
    str(REPO / "experiments" / "rankcert_mps"),
    str(REPO / "experiments" / "observable_telescope"),
]

import rankcert_inputs
from contrastive_core import (
    atomic_json,
    canonical_parameter_count,
    compress_density_operator,
    contrastive_operator_spectrum,
    matched_contrast_bond,
    sha256,
    signed_tensor_tt_metrics,
    state_tt_metrics,
    tensor_cut_spectrum,
    trace_norm,
)
from run_observable_telescope import bks_basis_indices


PROTOCOL = HERE / "PROTOCOL.md"
SMALL_PATH = RESULTS / "small_md_dynamics.json"
DIAGNOSTICS_PATH = RESULTS / "structural_diagnostics.json"
BENCHMARK_PATH = RESULTS / "equal_budget_benchmark.json"
STATE_BONDS = (4, 8, 16, 32, 64)
OPERATOR_BONDS = ((4, 4), (2, 8), (4, 8), (4, 16))
CASES = ("ibm32", "aves-sparrow-social")
ORDERINGS = ("sorted", "spectral")
METHOD_A = "published_lr"
METHOD_B = "prior_matched_random"


def provenance() -> dict:
    import qiskit
    import scipy

    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "qiskit": qiskit.__version__,
        "protocol_sha256": sha256(PROTOCOL),
        "runner_sha256": sha256(Path(__file__)),
    }


def pair_specs(case: str, ordering: str) -> tuple[dict, dict]:
    rows = rankcert_inputs.load_specs()
    a = next(
        row for row in rows
        if (row["case"], row["method"], row["ordering"])
        == (case, METHOD_A, ordering)
    )
    b = next(
        row for row in rows
        if (row["case"], row["method"], row["ordering"])
        == (case, METHOD_B, ordering)
    )
    return a, b


def load_circuit(path: str):
    with Path(path).open("rb") as handle:
        circuit = qpy.load(handle)[0]
    return circuit.remove_final_measurements(inplace=False)


def load_state(spec: dict) -> np.ndarray:
    state = np.asarray(np.load(spec["reference_file"], mmap_mode="r", allow_pickle=False))
    norm = float(np.vdot(state, state).real)
    if abs(norm - 1.0) > 1e-10:
        state = np.array(state, dtype=np.complex128, copy=True) / np.sqrt(norm)
    return state


def paired_circuits(spec_a: dict, spec_b: dict):
    circuit_a = load_circuit(spec_a["circuit_file"])
    circuit_b = load_circuit(spec_b["circuit_file"])
    if circuit_a.num_qubits != circuit_b.num_qubits or len(circuit_a.data) != len(circuit_b.data):
        raise AssertionError("Paired circuits have different shapes")
    for index, (item_a, item_b) in enumerate(zip(circuit_a.data, circuit_b.data)):
        qa = tuple(circuit_a.find_bit(qubit).index for qubit in item_a.qubits)
        qb = tuple(circuit_b.find_bit(qubit).index for qubit in item_b.qubits)
        if (item_a.operation.name, qa) != (item_b.operation.name, qb):
            raise AssertionError((index, item_a.operation.name, qa, item_b.operation.name, qb))
    return circuit_a, circuit_b


def evolve(matrix: np.ndarray, operation, qargs: tuple[int, ...]) -> np.ndarray:
    return np.asarray(DensityMatrix(matrix).evolve(operation, qargs=list(qargs)).data)


def channel_epsilon(operation_a, operation_b) -> float:
    unitary_a = np.asarray(Operator(operation_a).data)
    unitary_b = np.asarray(Operator(operation_b).data)
    return float(min(1.0, linalg_norm(unitary_a - unitary_b)))


def linalg_norm(matrix: np.ndarray) -> float:
    return float(np.linalg.norm(matrix, ord=2))


def projector(sites: int, indices: list[int]) -> np.ndarray:
    diagonal = np.zeros(2**sites, dtype=np.float64)
    diagonal[indices] = 1.0
    return np.diag(diagonal)


def exact_md_step(
    mean: np.ndarray,
    difference: np.ndarray,
    operation_a,
    operation_b,
    qargs: tuple[int, ...],
) -> tuple[np.ndarray, np.ndarray]:
    a_mean = evolve(mean, operation_a, qargs)
    b_mean = evolve(mean, operation_b, qargs)
    a_difference = evolve(difference, operation_a, qargs)
    b_difference = evolve(difference, operation_b, qargs)
    return (
        0.5 * (a_mean + b_mean + b_difference - a_difference),
        0.5 * (b_mean - a_mean + b_difference + a_difference),
    )


def run_small_ordering(ordering: str) -> dict:
    spec_a, spec_b = pair_specs("chesapeake", ordering)
    circuit_a, circuit_b = paired_circuits(spec_a, spec_b)
    sites = circuit_a.num_qubits
    indices = bks_basis_indices(spec_a["scorer"])
    observable = projector(sites, indices)
    dimension = 2**sites
    initial = np.zeros((dimension, dimension), dtype=np.complex128)
    initial[0, 0] = 1.0
    rho_a = initial.copy()
    rho_b = initial.copy()
    mean = initial.copy()
    difference = np.zeros_like(initial)
    approximations = {
        f"M{mean_bond}_D{difference_bond}": {
            "mean": initial.copy(),
            "difference": np.zeros_like(initial),
            "e_mean": 0.0,
            "e_difference": 0.0,
            "mean_bond": mean_bond,
            "difference_bond": difference_bond,
            "maximum_actual_over_bound": 0.0,
            "maximum_mean_parameters": 0,
            "maximum_difference_parameters": 0,
        }
        for mean_bond, difference_bond in OPERATOR_BONDS
    }
    max_identity_error = 0.0
    epsilons = []
    audit_rows = []
    started = perf_counter()
    for position, (item_a, item_b) in enumerate(zip(circuit_a.data, circuit_b.data), start=1):
        qargs = tuple(circuit_a.find_bit(qubit).index for qubit in item_a.qubits)
        next_rho_a = evolve(rho_a, item_a.operation, qargs)
        next_rho_b = evolve(rho_b, item_b.operation, qargs)
        next_mean, next_difference = exact_md_step(
            mean, difference, item_a.operation, item_b.operation, qargs
        )
        max_identity_error = max(
            max_identity_error,
            float(np.linalg.norm(next_mean - 0.5 * (next_rho_a + next_rho_b))),
            float(np.linalg.norm(next_difference - 0.5 * (next_rho_b - next_rho_a))),
        )
        rho_a, rho_b, mean, difference = (
            next_rho_a, next_rho_b, next_mean, next_difference
        )
        epsilon = channel_epsilon(item_a.operation, item_b.operation)
        epsilons.append(epsilon)
        for key, row in approximations.items():
            propagated_mean, propagated_difference = exact_md_step(
                row["mean"], row["difference"], item_a.operation, item_b.operation, qargs
            )
            compressed_mean, mean_info = compress_density_operator(
                propagated_mean, sites, row["mean_bond"]
            )
            compressed_difference, difference_info = compress_density_operator(
                propagated_difference, sites, row["difference_bond"]
            )
            previous_mean = row["e_mean"]
            previous_difference = row["e_difference"]
            row["e_mean"] = (
                previous_mean + epsilon * previous_difference
                + mean_info["trace_norm_residual"]
            )
            row["e_difference"] = (
                previous_difference + epsilon * previous_mean
                + difference_info["trace_norm_residual"]
            )
            row["mean"] = compressed_mean
            row["difference"] = compressed_difference
            row["maximum_mean_parameters"] = max(
                row["maximum_mean_parameters"], mean_info["parameter_count"]
            )
            row["maximum_difference_parameters"] = max(
                row["maximum_difference_parameters"], difference_info["parameter_count"]
            )
            if position % 64 == 0 or position == len(circuit_a.data):
                actual_mean = trace_norm(mean - compressed_mean)
                actual_difference = trace_norm(difference - compressed_difference)
                if actual_mean > row["e_mean"] + 2e-8 or actual_difference > row["e_difference"] + 2e-8:
                    raise AssertionError((ordering, position, key, actual_mean, actual_difference))
                ratios = [
                    actual_mean / row["e_mean"] if row["e_mean"] else 0.0,
                    actual_difference / row["e_difference"] if row["e_difference"] else 0.0,
                ]
                row["maximum_actual_over_bound"] = max(
                    row["maximum_actual_over_bound"], *ratios
                )
        if position % 64 == 0 or position == len(circuit_a.data):
            audit_rows.append({
                "position": position,
                "epsilon": epsilon,
                "exact_identity_error": max_identity_error,
            })
            print(f"[small M/D] {ordering} {position}/{len(circuit_a.data)}", flush=True)

    exact_delta = float(np.trace(observable @ (rho_b - rho_a)).real)
    md_delta = float(2.0 * np.trace(observable @ difference).real)
    rows = []
    for key, row in approximations.items():
        estimate = float(2.0 * np.trace(observable @ row["difference"]).real)
        radius = 2.0 * row["e_difference"]
        lower, upper = estimate - radius, estimate + radius
        rows.append({
            "policy": key,
            "mean_bond": row["mean_bond"],
            "difference_bond": row["difference_bond"],
            "estimate": estimate,
            "absolute_error": abs(estimate - exact_delta),
            "certified_radius": radius,
            "interval_lower": lower,
            "interval_upper": upper,
            "sign_certified": lower > 0.0 or upper < 0.0,
            "final_e_mean": row["e_mean"],
            "final_e_difference": row["e_difference"],
            "maximum_actual_over_bound": row["maximum_actual_over_bound"],
            "maximum_mean_parameters": row["maximum_mean_parameters"],
            "maximum_difference_parameters": row["maximum_difference_parameters"],
        })
    return {
        "case": "chesapeake",
        "ordering": ordering,
        "qubits": sites,
        "paired_gates": len(circuit_a.data),
        "exact_delta": exact_delta,
        "md_delta": md_delta,
        "maximum_exact_identity_error": max_identity_error,
        "epsilon": {
            "maximum": max(epsilons),
            "mean": float(np.mean(epsilons)),
            "zero_count": sum(value <= 1e-15 for value in epsilons),
            "one_count": sum(value >= 1.0 - 1e-15 for value in epsilons),
        },
        "audit_rows": audit_rows,
        "policies": rows,
        "runtime_seconds": perf_counter() - started,
    }


def stage_small() -> dict:
    payload = {
        "stage": "exact_small_md_dynamics",
        "complete": False,
        "provenance": provenance(),
        "rows": [],
    }
    for ordering in ORDERINGS:
        payload["rows"].append(run_small_ordering(ordering))
        atomic_json(SMALL_PATH, payload)
    payload["complete"] = True
    atomic_json(SMALL_PATH, payload)
    return payload


def run_diagnostics_cohort(case: str, ordering: str) -> dict:
    spec_a, spec_b = pair_specs(case, ordering)
    state_a = load_state(spec_a)
    state_b = load_state(spec_b)
    sites = spec_a["qubits"]
    probability_a = np.square(np.abs(state_a))
    probability_b = np.square(np.abs(state_b))
    mean_probability = 0.5 * (probability_a + probability_b)
    signed_probability = probability_b - probability_a
    cuts = sorted(set((3, 5, 7, sites // 2)))
    tensor_spectra = {}
    for name, values in (
        ("state_a", state_a), ("state_b", state_b),
        ("probability_a", probability_a), ("probability_b", probability_b),
        ("mean_probability", mean_probability),
        ("signed_probability_contrast", signed_probability),
    ):
        tensor_spectra[name] = [
            tensor_cut_spectrum(values, sites, cut, top=64) for cut in cuts
        ]
    operator_spectra = []
    for cut in (3, 5, 7):
        for kind in ("rho_a", "rho_b", "mean", "difference"):
            print(f"[operator spectrum] {case}/{ordering} cut={cut} {kind}", flush=True)
            operator_spectra.append(
                contrastive_operator_spectrum(
                    state_a, state_b, sites, cut, kind=kind, top=32
                )
            )
    result = {
        "case": case,
        "ordering": ordering,
        "qubits": sites,
        "state_overlap_squared": float(abs(np.vdot(state_a, state_b)) ** 2),
        "tensor_spectra": tensor_spectra,
        "operator_spectra": operator_spectra,
    }
    del state_a, state_b, probability_a, probability_b, mean_probability, signed_probability
    gc.collect()
    return result


def stage_diagnostics() -> dict:
    payload = {
        "stage": "contrastive_structural_diagnostics",
        "complete": False,
        "provenance": provenance(),
        "rows": [],
    }
    for case in CASES:
        for ordering in ORDERINGS:
            payload["rows"].append(run_diagnostics_cohort(case, ordering))
            atomic_json(DIAGNOSTICS_PATH, payload)
    payload["complete"] = True
    atomic_json(DIAGNOSTICS_PATH, payload)
    return payload


def run_benchmark_cohort(case: str, ordering: str) -> list[dict]:
    spec_a, spec_b = pair_specs(case, ordering)
    state_a = load_state(spec_a)
    state_b = load_state(spec_b)
    sites = spec_a["qubits"]
    indices = bks_basis_indices(spec_a["scorer"])
    probability_a = np.square(np.abs(state_a))
    probability_b = np.square(np.abs(state_b))
    signed_probability = probability_b - probability_a
    exact_a = float(probability_a[indices].sum(dtype=np.float64))
    exact_b = float(probability_b[indices].sum(dtype=np.float64))
    exact_delta = exact_b - exact_a
    rows = []
    for bond in STATE_BONDS:
        started = perf_counter()
        separate_a = state_tt_metrics(state_a, sites, indices, bond)
        separate_b = state_tt_metrics(state_b, sites, indices, bond)
        separate_delta = separate_b["probability"] - separate_a["probability"]
        contrast_bond = matched_contrast_bond(sites, bond)
        contrast = signed_tensor_tt_metrics(
            signed_probability, sites, indices, contrast_bond
        )
        separate_parameters = (
            canonical_parameter_count(sites, 2, bond) * 2
        )
        contrast_parameters = canonical_parameter_count(sites, 2, contrast_bond)
        if contrast_parameters > separate_parameters:
            raise AssertionError((sites, bond, contrast_bond, separate_parameters, contrast_parameters))
        separate_error = abs(separate_delta - exact_delta)
        contrast_error = abs(contrast["delta"] - exact_delta)
        separate_radius = (
            np.sqrt(max(0.0, 1.0 - separate_a["fidelity"]))
            + np.sqrt(max(0.0, 1.0 - separate_b["fidelity"]))
        )
        contrast_l2_bound = np.sqrt(
            max(0.0, contrast["discarded_frobenius_sq_sum"])
        )
        contrast_radius = np.sqrt(len(indices)) * contrast_l2_bound
        separate_lower = separate_delta - separate_radius
        separate_upper = separate_delta + separate_radius
        contrast_lower = contrast["delta"] - contrast_radius
        contrast_upper = contrast["delta"] + contrast_radius
        row = {
            "case": case,
            "ordering": ordering,
            "qubits": sites,
            "state_bond": bond,
            "contrast_bond": contrast_bond,
            "separate_parameter_budget": separate_parameters,
            "contrast_parameter_budget": contrast_parameters,
            "exact_p_a": exact_a,
            "exact_p_b": exact_b,
            "exact_delta": exact_delta,
            "separate_p_a": separate_a["probability"],
            "separate_p_b": separate_b["probability"],
            "separate_delta": separate_delta,
            "contrast_delta": contrast["delta"],
            "separate_absolute_error": separate_error,
            "contrast_absolute_error": contrast_error,
            "separate_certified_radius": separate_radius,
            "separate_interval_lower": separate_lower,
            "separate_interval_upper": separate_upper,
            "separate_sign_certified": separate_lower > 0.0 or separate_upper < 0.0,
            "contrast_l2_error_bound": contrast_l2_bound,
            "contrast_certified_radius": contrast_radius,
            "contrast_interval_lower": contrast_lower,
            "contrast_interval_upper": contrast_upper,
            "contrast_sign_certified": contrast_lower > 0.0 or contrast_upper < 0.0,
            "error_improvement_factor": (
                separate_error / contrast_error if contrast_error > 0.0 else None
            ),
            "separate_sign_correct": np.sign(separate_delta) == np.sign(exact_delta),
            "contrast_sign_correct": np.sign(contrast["delta"]) == np.sign(exact_delta),
            "state_a_fidelity": separate_a["fidelity"],
            "state_b_fidelity": separate_b["fidelity"],
            "separate_actual_parameters": (
                separate_a["parameter_count"] + separate_b["parameter_count"]
            ),
            "contrast_actual_parameters": contrast["parameter_count"],
            "runtime_seconds": perf_counter() - started,
        }
        rows.append(row)
        print(
            f"[equal budget] {case}/{ordering} R={bond} K={contrast_bond} "
            f"separate_err={separate_error:.6g} contrast_err={contrast_error:.6g}",
            flush=True,
        )
    del state_a, state_b, probability_a, probability_b, signed_probability
    gc.collect()
    return rows


def stage_benchmark() -> dict:
    payload = {
        "stage": "equal_budget_contrastive_benchmark",
        "complete": False,
        "provenance": provenance(),
        "state_bonds": STATE_BONDS,
        "rows": [],
    }
    for case in CASES:
        for ordering in ORDERINGS:
            payload["rows"].extend(run_benchmark_cohort(case, ordering))
            atomic_json(BENCHMARK_PATH, payload)
    payload["complete"] = True
    atomic_json(BENCHMARK_PATH, payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stage", choices=("small", "diagnostics", "benchmark", "all"), default="all"
    )
    args = parser.parse_args()
    if args.stage in ("small", "all"):
        stage_small()
    if args.stage in ("diagnostics", "all"):
        stage_diagnostics()
    if args.stage in ("benchmark", "all"):
        stage_benchmark()


if __name__ == "__main__":
    main()
