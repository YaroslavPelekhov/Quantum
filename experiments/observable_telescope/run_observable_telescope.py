"""Exact-backward BKS telescope feasibility pilot on frozen 7-qubit circuits."""

from __future__ import annotations

import csv
import gc
import hashlib
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import numpy as np


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RANK_CODE = REPO / "experiments" / "rankcert_mps"
PROJECT = REPO / "experiments" / "evoq_mis_full_qoblib"
RESULTS = REPO / "results" / "observable_telescope"
RUNS = RESULTS / "runs"
CHECKPOINT = RESULTS / "schedule_rows.json"
PAIR_OUTPUT = RESULTS / "pair_rows.json"
SUMMARY = RESULTS / "summary.json"
REPORT = RESULTS / "REPORT.md"
RANKCERT_SCHEDULE = REPO / "results" / "rankcert_mps" / "rankcert_schedule_rows.json"
RANKCERT_PAIRS = REPO / "results" / "rankcert_mps" / "rankcert_pair_rows.json"

sys.path.insert(0, str(RANK_CODE))
sys.path.insert(0, str(PROJECT))
from rankcert_inputs import METHODS, ORDERINGS, SETTINGS, atomic_json, load_specs, sha256
import run_independent_ladder_audit as frozen_audit


CASES = ("chesapeake", "football")
NUMERICAL_TOLERANCE = 1e-9


def bks_basis_indices(scorer: dict) -> list[int]:
    result = []
    for index in range(1 << len(scorer["weights"])):
        selected = scorer["constant_selected"] + sum(
            weight * ((index >> qubit) & 1)
            for qubit, weight in enumerate(scorer["weights"])
        )
        feasible = not scorer["impossible"] and all(
            (index & mask) != pattern for mask, pattern in scorer["forbidden"]
        )
        if feasible and selected >= scorer["bks"]:
            result.append(index)
    if not result:
        raise AssertionError("BKS projector has zero rank")
    return result


def checkpoint_counts(circuit) -> list[int]:
    counts = [0]
    counts.extend(
        index + 1 for index, item in enumerate(circuit.data)
        if len(item.qubits) >= 2
    )
    if counts[-1] != len(circuit.data):
        counts.append(len(circuit.data))
    return counts


def instrumented_circuit(circuit, counts: list[int]):
    from qiskit import QuantumCircuit

    result = QuantumCircuit(circuit.num_qubits)
    labels = {count: f"checkpoint_{position:04d}" for position, count in enumerate(counts)}
    result.save_statevector(label=labels[0])
    for index, item in enumerate(circuit.data):
        qubits = [result.qubits[circuit.find_bit(qubit).index] for qubit in item.qubits]
        clbits = [result.clbits[circuit.find_bit(clbit).index] for clbit in item.clbits]
        result.append(item.operation, qubits, clbits)
        count = index + 1
        if count in labels:
            result.save_statevector(label=labels[count])
    return result, labels


def normalize_copy(value) -> np.ndarray:
    state = np.asarray(value, dtype=np.complex128).copy()
    norm = float(np.vdot(state, state).real)
    if not np.isfinite(norm) or norm <= 0:
        raise AssertionError(norm)
    state /= math.sqrt(norm)
    return state


def backward_bks_vectors(circuit, counts: list[int], basis_indices: list[int]) -> dict[int, np.ndarray]:
    """Exact low-rank representation of U_suffix^dagger Pi_BKS U_suffix."""
    from qiskit.quantum_info import Statevector

    dimension = 1 << circuit.num_qubits
    vectors = np.zeros((dimension, len(basis_indices)), dtype=np.complex128)
    for column, index in enumerate(basis_indices):
        vectors[index, column] = 1.0
    wanted = set(counts)
    result = {len(circuit.data): vectors.copy()} if len(circuit.data) in wanted else {}
    current = vectors
    for operation_index in range(len(circuit.data) - 1, -1, -1):
        item = circuit.data[operation_index]
        qargs = [circuit.find_bit(qubit).index for qubit in item.qubits]
        inverse = item.operation.inverse()
        for column in range(current.shape[1]):
            current[:, column] = np.asarray(
                Statevector(current[:, column]).evolve(inverse, qargs=qargs).data
            )
        if operation_index in wanted:
            result[operation_index] = current.copy()
    if set(result) != wanted:
        raise AssertionError(f"Missing backward checkpoints: {wanted - set(result)}")
    return result


def event_probability(state: np.ndarray, backward_vectors: np.ndarray) -> float:
    overlaps = backward_vectors.conj().T @ state
    value = float(np.vdot(overlaps, overlaps).real)
    if not -1e-10 <= value <= 1.0 + 1e-10:
        raise AssertionError(value)
    return min(1.0, max(0.0, value))


def run_trajectory(spec: dict, setting: dict, backward: dict[int, np.ndarray], counts: list[int]) -> dict:
    from qiskit_aer import AerSimulator

    circuit = frozen_audit.load_circuit(Path(spec["circuit_file"]))
    executable, labels = instrumented_circuit(circuit, counts)
    backend = AerSimulator(
        method="matrix_product_state",
        matrix_product_state_max_bond_dimension=setting["bond"],
        matrix_product_state_truncation_threshold=setting["cutoff"],
        max_parallel_experiments=1,
        max_parallel_threads=1,
        mps_omp_threads=1,
    )
    started = perf_counter()
    result = backend.run(executable).result()
    simulation_seconds = perf_counter() - started
    data = result.data(0)
    probabilities = []
    for count in counts:
        state = normalize_copy(data[labels[count]])
        probabilities.append(event_probability(state, backward[count]))
    contributions = [
        probabilities[index] - probabilities[index - 1]
        for index in range(1, len(probabilities))
    ]
    absolute_contributions = [abs(value) for value in contributions]
    exact_bks = float(spec["exact_metrics"]["bks_rate"])
    approximate_bks = probabilities[-1]
    actual_error = abs(approximate_bks - exact_bks)
    telescope_sum = math.fsum(contributions)
    bound = math.fsum(absolute_contributions)
    if abs(probabilities[0] - exact_bks) > NUMERICAL_TOLERANCE:
        raise AssertionError((probabilities[0], exact_bks))
    if abs(telescope_sum - (approximate_bks - exact_bks)) > NUMERICAL_TOLERANCE:
        raise AssertionError("Telescope identity failed")
    if actual_error > bound + NUMERICAL_TOLERANCE:
        raise AssertionError("Observable telescope bound failed")
    details = []
    for position, value in enumerate(contributions, start=1):
        operation_count = counts[position]
        prior_count = counts[position - 1]
        terminal = operation_count == len(circuit.data) and len(circuit.data[operation_count - 1].qubits) < 2
        if terminal:
            gate_index = None
            gate = "exact_tail_after_last_two_qubit_gate"
            qubits = []
        else:
            gate_index = operation_count - 1
            item = circuit.data[gate_index]
            gate = item.operation.name
            qubits = [circuit.find_bit(qubit).index for qubit in item.qubits]
        details.append({
            "segment_index": position - 1,
            "prior_operation_count": prior_count,
            "operation_count": operation_count,
            "gate_index": gate_index,
            "gate": gate,
            "qubits": qubits,
            "signed_bks_contribution": value,
            "absolute_bks_contribution": abs(value),
        })
    del result, data, executable, backend
    gc.collect()
    return {
        "case": spec["case"], "qubits": spec["qubits"], "method": spec["method"],
        "schedule": spec["schedule"], "ordering": spec["ordering"],
        "setting": setting["name"], "bond": setting["bond"], "cutoff": setting["cutoff"],
        "circuit_file": spec["circuit_file"], "circuit_sha256": spec["circuit_sha256"],
        "bks_projector_rank": backward[counts[-1]].shape[1],
        "native_gate_count": len(circuit.data), "checkpoint_count": len(counts),
        "p_bks_exact": exact_bks, "p_bks_mps": approximate_bks,
        "actual_bks_error": actual_error,
        "observable_telescope_bound": bound,
        "telescope_signed_sum": telescope_sum,
        "telescope_identity_error": abs(telescope_sum - (approximate_bks - exact_bks)),
        "bound_slack": bound - actual_error,
        "cancellation_ratio": bound / actual_error if actual_error > 0 else None,
        "simulation_seconds": simulation_seconds,
        "top_contributions": sorted(details, key=lambda row: row["absolute_bks_contribution"], reverse=True)[:20],
        "contributions": details,
    }


def identity(row: dict) -> tuple[str, str, str, str]:
    return row["case"], row["setting"], row["method"], row["ordering"]


def load_completed() -> dict[tuple[str, str, str, str], dict]:
    if not CHECKPOINT.exists():
        return {}
    payload = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
    return {identity(row): row for row in payload.get("rows", [])}


def save_checkpoint(rows: dict) -> None:
    ordered = sorted(rows.values(), key=identity)
    atomic_json(CHECKPOINT, {
        "stage": "observable_telescope_7q", "complete": len(ordered) == 40,
        "created_at": datetime.now(timezone.utc).isoformat(), "expected_rows": 40,
        "rows": ordered,
    })


def analyze_pairs(rows: list[dict]) -> tuple[list[dict], dict]:
    index = {identity(row): row for row in rows}
    old_pair_index = {
        (row["case"], row["setting"], row["ordering"]): row
        for row in json.loads(RANKCERT_PAIRS.read_text(encoding="utf-8"))["rows"]
    }
    old_schedule_index = {
        (row["case"], row["setting"], row["method"], row["ordering"]): row
        for row in json.loads(RANKCERT_SCHEDULE.read_text(encoding="utf-8"))["rows"]
    }
    regression_errors = [
        abs(row["p_bks_mps"] - old_schedule_index[identity(row)]["p_bks_mps"])
        for row in rows
    ]
    pair_rows = []
    for case in CASES:
        for setting in SETTINGS:
            for ordering in ORDERINGS:
                lr = index[(case, setting["name"], "published_lr", ordering)]
                mr = index[(case, setting["name"], "prior_matched_random", ordering)]
                mps_delta = mr["p_bks_mps"] - lr["p_bks_mps"]
                exact_delta = mr["p_bks_exact"] - lr["p_bks_exact"]
                width = lr["observable_telescope_bound"] + mr["observable_telescope_bound"] + 2 * NUMERICAL_TOLERANCE
                certified = abs(mps_delta) > width
                old = old_pair_index[(case, setting["name"], ordering)]
                pair_rows.append({
                    "case": case, "setting": setting["name"], "ordering": ordering,
                    "exact_delta": exact_delta, "mps_delta": mps_delta,
                    "telescope_pair_width": width, "certified": certified,
                    "correct_sign": (mps_delta > 0) == (exact_delta > 0),
                    "certified_correct": certified and (mps_delta > 0) == (exact_delta > 0),
                    "accumulated_angle_certified": old["certified"],
                    "accumulated_angle_pair_width": old["epsilon_pair"],
                })
    old_certified = sum(row["accumulated_angle_certified"] for row in pair_rows)
    new_certified = sum(row["certified"] for row in pair_rows)
    summary = {
        "stage": "observable_telescope_7q_summary", "complete": True,
        "schedule_rows": len(rows), "pair_rows": len(pair_rows),
        "telescope_certified": new_certified,
        "accumulated_angle_certified_same_cohort": old_certified,
        "newly_certified_over_accumulated_angle": sum(
            row["certified"] and not row["accumulated_angle_certified"] for row in pair_rows
        ),
        "telescope_wrong_certified": sum(row["certified"] and not row["correct_sign"] for row in pair_rows),
        "per_case": {
            case: {
                "certified": sum(row["certified"] for row in pair_rows if row["case"] == case),
                "total": sum(row["case"] == case for row in pair_rows),
            } for case in CASES
        },
        "maximum_telescope_identity_error": max(row["telescope_identity_error"] for row in rows),
        "maximum_bound_violation": max(row["actual_bks_error"] - row["observable_telescope_bound"] for row in rows),
        "maximum_frozen_rankcert_regression_error": max(regression_errors),
        "median_bound_over_actual_error": float(np.median([
            row["cancellation_ratio"] for row in rows if row["cancellation_ratio"] is not None
        ])),
    }
    return pair_rows, summary


def main() -> None:
    specs = [row for row in load_specs() if row["case"] in CASES]
    spec_index = {(row["case"], row["method"], row["ordering"]): row for row in specs}
    completed = load_completed()
    environment_cache = {}
    for case in CASES:
        for method in METHODS:
            for ordering in ORDERINGS:
                spec = spec_index[(case, method, ordering)]
                circuit = frozen_audit.load_circuit(Path(spec["circuit_file"]))
                counts = checkpoint_counts(circuit)
                cache_key = (case, method, ordering)
                print(f"[backward] {cache_key}; gates={len(circuit.data)} checkpoints={len(counts)}", flush=True)
                backward = backward_bks_vectors(circuit, counts, bks_basis_indices(spec["scorer"]))
                environment_cache[cache_key] = (counts, backward)
                for setting in SETTINGS:
                    key = (case, setting["name"], method, ordering)
                    if key in completed:
                        print(f"[resume] {key}", flush=True)
                        continue
                    print(f"[run] {key}", flush=True)
                    row = run_trajectory(spec, setting, backward, counts)
                    completed[key] = row
                    save_checkpoint(completed)
                    print(
                        f"[complete] bound={row['observable_telescope_bound']:.6g} "
                        f"error={row['actual_bks_error']:.6g}", flush=True
                    )
    save_checkpoint(completed)
    rows = sorted(completed.values(), key=identity)
    if len(rows) != 40:
        raise AssertionError(len(rows))
    pairs, summary = analyze_pairs(rows)
    atomic_json(PAIR_OUTPUT, {"stage": "observable_telescope_7q_pairs", "rows": pairs})
    atomic_json(SUMMARY, summary)
    write_csv(RESULTS / "schedule_rows.csv", rows, exclude=("contributions", "top_contributions"))
    write_csv(RESULTS / "pair_rows.csv", pairs)
    write_report(summary, rows)
    print(json.dumps(summary, indent=2))


def write_csv(path: Path, rows: list[dict], exclude: tuple[str, ...] = ()) -> None:
    fields = [field for field in rows[0] if field not in exclude]
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
        handle.flush(); os.fsync(handle.fileno())
    os.replace(temporary, path)


def write_report(summary: dict, rows: list[dict]) -> None:
    case_lines = "\n".join(
        f"| {case} | {stats['certified']} / {stats['total']} |"
        for case, stats in summary["per_case"].items()
    )
    REPORT.write_text(f"""# Exact-backward observable telescope pilot

## Result

The 7q pilot completed 40 approximate schedule trajectories and 20 LR-vs-MR
cohorts. The BKS-specific telescope certified
{summary['telescope_certified']} / {summary['pair_rows']} rankings with
{summary['telescope_wrong_certified']} wrong certified signs.
On this identical cohort, accumulated-angle RankCert certified
{summary['accumulated_angle_certified_same_cohort']} / {summary['pair_rows']};
the observable telescope added
{summary['newly_certified_over_accumulated_angle']} strict decisions.

| Case | Certified |
|---|---:|
{case_lines}

The exact telescope identity held to maximum absolute error
{summary['maximum_telescope_identity_error']:.3e}. The maximum value of
`actual_BKS_error - telescope_bound` was
{summary['maximum_bound_violation']:.3e}. Median bound / actual error was
{summary['median_bound_over_actual_error']:.3f}.
Instrumented final BKS probabilities match the frozen RankCert runs to
{summary['maximum_frozen_rankcert_regression_error']:.3e} maximum absolute error.

## Method

Aer MPS states were snapshotted after every two-qubit native gate. The BKS
projector has rank one for chesapeake and rank four for football. Its basis
vectors were propagated backward exactly through every frozen suffix. For
checkpoint state phi_t this gives

`q_t = <phi_t| U_suffix^dagger Pi_BKS U_suffix |phi_t>`.

The identity `p_MPS-p_exact = sum_t(q_t-q_(t-1))` is exact up to numerical
roundoff. Therefore `sum_t |q_t-q_(t-1)|` is a rigorous BKS-specific bound for
the captured approximate trajectory.

## Interpretation and 18q feasibility

This is a feasibility oracle, not yet a scalable internal certificate: exact
backward vectors cost exponential memory. It is nevertheless much more
informative than the global angle because it retains the signed orientation of
every local perturbation relative to BKS.

The ibm32 BKS projector rank is only two, which makes a streamed backward-vector
prototype plausible. The main scaling obstacle is storing hundreds of dense
18q forward snapshots (several GiB), not projector rank. The next implementation
should process two-qubit checkpoints in blocks or recompute prefix blocks, keep
only current backward vectors, and validate one setting before any full sweep.
""", encoding="utf-8")


if __name__ == "__main__":
    main()
