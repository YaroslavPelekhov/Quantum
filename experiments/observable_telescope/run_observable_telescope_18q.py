"""Memory-bounded exact-backward observable telescope pilot on ibm32 (18q)."""

from __future__ import annotations

import argparse
import gc
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import numpy as np


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path[:0] = [
    str(HERE),
    str(REPO / "experiments" / "rankcert_mps"),
    str(REPO / "experiments" / "evoq_mis_full_qoblib"),
]

from rankcert_inputs import SETTINGS, atomic_json, load_specs
import run_independent_ladder_audit as frozen_audit
from run_observable_telescope import (
    bks_basis_indices,
    checkpoint_counts,
    event_probability,
    normalize_copy,
)


RESULTS = REPO / "results" / "observable_telescope"
RANKCERT_ROWS = REPO / "results" / "rankcert_mps" / "rankcert_schedule_rows.json"
CASE = "ibm32"
METHODS = ("published_lr", "prior_matched_random")
DEFAULT_BLOCK_CHECKPOINTS = 64
NUMERICAL_TOLERANCE = 1e-8
# Prefix replay can choose a different, but physically equivalent, SVD gauge from
# the frozen uninterrupted RankCert run.  Keep this reproducibility guard
# separate from the numerical slack used by the certificate itself.
FROZEN_REGRESSION_TOLERANCE = 1e-6


def append_slice(target, source, start: int, end: int) -> None:
    for item in source.data[start:end]:
        qargs = [target.qubits[source.find_bit(qubit).index] for qubit in item.qubits]
        cargs = [target.clbits[source.find_bit(clbit).index] for clbit in item.clbits]
        target.append(item.operation, qargs, cargs)


def simulator(setting: dict):
    from qiskit_aer import AerSimulator

    return AerSimulator(
        method="matrix_product_state",
        matrix_product_state_max_bond_dimension=setting["bond"],
        matrix_product_state_truncation_threshold=setting["cutoff"],
        max_parallel_experiments=1,
        max_parallel_threads=1,
        mps_omp_threads=1,
    )


def run_segment(circuit, start: int, end: int, setting: dict,
                dense_counts: list[int] | None = None):
    import qiskit_aer  # Registers Aer save instructions on QuantumCircuit.
    from qiskit import QuantumCircuit

    dense_counts = dense_counts or []
    wanted = set(dense_counts)
    segment = QuantumCircuit(circuit.num_qubits)
    labels = {count: f"state_{count:04d}" for count in dense_counts}
    if start in wanted:
        segment.save_statevector(labels[start])
    for operation_index in range(start, end):
        append_slice(segment, circuit, operation_index, operation_index + 1)
        count = operation_index + 1
        if count in wanted:
            segment.save_statevector(labels[count])
    result = simulator(setting).run(segment).result()
    return result.data(0), labels


def terminal_bks_vectors(qubits: int, indices: list[int]) -> np.ndarray:
    vectors = np.zeros((1 << qubits, len(indices)), dtype=np.complex128)
    for column, index in enumerate(indices):
        vectors[index, column] = 1.0
    return vectors


def backward_block(circuit, checkpoint_counts_in_block: list[int], current: np.ndarray):
    from qiskit.quantum_info import Statevector

    start = checkpoint_counts_in_block[0]
    end = checkpoint_counts_in_block[-1]
    wanted = set(checkpoint_counts_in_block)
    vectors = {end: current.copy()}
    for operation_index in range(end - 1, start - 1, -1):
        item = circuit.data[operation_index]
        qargs = [circuit.find_bit(qubit).index for qubit in item.qubits]
        inverse = item.operation.inverse()
        for column in range(current.shape[1]):
            current[:, column] = np.asarray(
                Statevector(current[:, column]).evolve(inverse, qargs=qargs).data
            )
        if operation_index in wanted:
            vectors[operation_index] = current.copy()
    if set(vectors) != wanted:
        raise AssertionError(f"Missing block environments: {wanted - set(vectors)}")
    return vectors, current


def frozen_rankcert_index() -> dict[tuple[str, str, str, str], dict]:
    rows = json.loads(RANKCERT_ROWS.read_text(encoding="utf-8"))["rows"]
    return {
        (row["case"], row["setting"], row["method"], row["ordering"]): row
        for row in rows
    }


def run_method(spec: dict, setting: dict, expected: dict, block_checkpoints: int) -> dict:
    circuit = frozen_audit.load_circuit(Path(spec["circuit_file"]))
    counts = checkpoint_counts(circuit)
    boundary_positions = list(range(0, len(counts) - 1, block_checkpoints))
    if boundary_positions[-1] != len(counts) - 1:
        boundary_positions.append(len(counts) - 1)
    probabilities: dict[int, float] = {}
    current = terminal_bks_vectors(circuit.num_qubits, bks_basis_indices(spec["scorer"]))
    backward_seconds = 0.0
    dense_seconds = 0.0
    peak_block_environment_bytes = 0

    for block_number in range(len(boundary_positions) - 2, -1, -1):
        left = boundary_positions[block_number]
        right = boundary_positions[block_number + 1]
        block_counts = counts[left:right + 1]
        started = perf_counter()
        environments, current = backward_block(circuit, block_counts, current)
        backward_seconds += perf_counter() - started
        peak_block_environment_bytes = max(
            peak_block_environment_bytes,
            sum(value.nbytes for value in environments.values()),
        )
        started = perf_counter()
        # Replay from |0> so every checkpoint belongs to the original uninterrupted
        # Aer trajectory. Restarting from save_matrix_product_state can change SVD
        # gauge choices and therefore later truncations.
        data, labels = run_segment(
            circuit, 0, block_counts[-1], setting, dense_counts=block_counts,
        )
        dense_seconds += perf_counter() - started
        for count in block_counts:
            value = event_probability(normalize_copy(data[labels[count]]), environments[count])
            if count in probabilities and abs(probabilities[count] - value) > NUMERICAL_TOLERANCE:
                raise AssertionError("Block boundary restart changed the trajectory")
            probabilities[count] = value
        print(
            f"[18q block] {spec['method']} {block_number + 1}/"
            f"{len(boundary_positions) - 1}; checkpoints={left}:{right}",
            flush=True,
        )
        del data, environments
        gc.collect()

    ordered = [probabilities[count] for count in counts]
    contributions = [ordered[index] - ordered[index - 1] for index in range(1, len(ordered))]
    exact_bks = float(spec["exact_metrics"]["bks_rate"])
    approximate_bks = ordered[-1]
    signed_sum = math.fsum(contributions)
    bound = math.fsum(abs(value) for value in contributions)
    identity_error = abs(signed_sum - (approximate_bks - exact_bks))
    regression_error = abs(approximate_bks - expected["p_bks_mps"])
    if abs(ordered[0] - exact_bks) > NUMERICAL_TOLERANCE:
        raise AssertionError((ordered[0], exact_bks))
    if identity_error > NUMERICAL_TOLERANCE:
        raise AssertionError(("telescope", identity_error))
    if abs(approximate_bks - exact_bks) > bound + NUMERICAL_TOLERANCE:
        raise AssertionError("Observable bound violated")
    if regression_error > FROZEN_REGRESSION_TOLERANCE:
        raise AssertionError(("frozen RankCert regression", regression_error))
    details = []
    for position, value in enumerate(contributions, start=1):
        operation_count = counts[position]
        prior_count = counts[position - 1]
        item = circuit.data[operation_count - 1] if operation_count > 0 else None
        details.append({
            "segment_index": position - 1,
            "prior_operation_count": prior_count,
            "operation_count": operation_count,
            "gate": item.operation.name if item is not None else None,
            "qubits": [circuit.find_bit(qubit).index for qubit in item.qubits]
            if item is not None else [],
            "signed_bks_contribution": value,
            "absolute_bks_contribution": abs(value),
        })
    del current
    gc.collect()
    return {
        "case": spec["case"], "qubits": spec["qubits"], "method": spec["method"],
        "schedule": spec["schedule"], "ordering": spec["ordering"],
        "setting": setting["name"], "bond": setting["bond"], "cutoff": setting["cutoff"],
        "circuit_file": spec["circuit_file"], "circuit_sha256": spec["circuit_sha256"],
        "native_gate_count": len(circuit.data), "checkpoint_count": len(counts),
        "bks_projector_rank": len(bks_basis_indices(spec["scorer"])),
        "block_checkpoints": block_checkpoints,
        "p_bks_exact": exact_bks, "p_bks_mps": approximate_bks,
        "frozen_rankcert_p_bks_mps": expected["p_bks_mps"],
        "frozen_rankcert_regression_error": regression_error,
        "actual_bks_error": abs(approximate_bks - exact_bks),
        "observable_telescope_bound": bound,
        "telescope_signed_sum": signed_sum,
        "telescope_identity_error": identity_error,
        "cancellation_ratio": bound / abs(approximate_bks - exact_bks),
        "prefix_replay_seconds": dense_seconds,
        "backward_seconds": backward_seconds,
        "peak_block_environment_bytes": peak_block_environment_bytes,
        "top_contributions": sorted(
            details, key=lambda row: row["absolute_bks_contribution"], reverse=True
        )[:30],
        "contributions": details,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--setting", default="released", choices=[item["name"] for item in SETTINGS])
    parser.add_argument("--ordering", default="sorted", choices=("sorted", "spectral"))
    parser.add_argument("--block-checkpoints", type=int, default=DEFAULT_BLOCK_CHECKPOINTS)
    args = parser.parse_args()
    setting_name = args.setting
    ordering = args.ordering
    output = RESULTS / f"ibm32_{setting_name}_{ordering}.json"
    setting = next(item for item in SETTINGS if item["name"] == setting_name)
    specs = {
        row["method"]: row for row in load_specs()
        if row["case"] == CASE and row["ordering"] == ordering and row["method"] in METHODS
    }
    frozen = frozen_rankcert_index()
    rows = []
    for method in METHODS:
        print(f"[18q method] {method}", flush=True)
        expected = frozen[(CASE, setting_name, method, ordering)]
        rows.append(run_method(specs[method], setting, expected, args.block_checkpoints))
        atomic_json(output, {
            "stage": "observable_telescope_18q_pilot", "complete": False,
            "created_at": datetime.now(timezone.utc).isoformat(), "rows": rows,
        })
    index = {row["method"]: row for row in rows}
    lr = index["published_lr"]
    mr = index["prior_matched_random"]
    lr_expected = frozen[(CASE, setting_name, "published_lr", ordering)]
    mr_expected = frozen[(CASE, setting_name, "prior_matched_random", ordering)]
    mps_delta = mr["p_bks_mps"] - lr["p_bks_mps"]
    exact_delta = mr["p_bks_exact"] - lr["p_bks_exact"]
    width = lr["observable_telescope_bound"] + mr["observable_telescope_bound"] + 2 * NUMERICAL_TOLERANCE
    pair = {
        "case": CASE, "setting": setting_name, "ordering": ordering,
        "exact_delta": exact_delta, "mps_delta": mps_delta,
        "observable_telescope_pair_width": width,
        "old_accumulated_angle_pair_width": min(
            2.0,
            lr_expected["epsilon_mps"] + mr_expected["epsilon_mps"] + 2e-7,
        ),
        "certified": abs(mps_delta) > width,
        "correct_sign": (mps_delta > 0) == (exact_delta > 0),
    }
    payload = {
        "stage": "observable_telescope_18q_pilot", "complete": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "memory_strategy": "independent uninterrupted prefix replay plus reverse dense blocks",
        "rows": rows, "pair": pair,
    }
    atomic_json(output, payload)
    print(json.dumps({
        "complete": True, "pair": pair,
        "max_telescope_identity_error": max(row["telescope_identity_error"] for row in rows),
        "max_frozen_regression_error": max(row["frozen_rankcert_regression_error"] for row in rows),
        "max_peak_block_environment_bytes": max(row["peak_block_environment_bytes"] for row in rows),
    }, indent=2))


if __name__ == "__main__":
    main()
