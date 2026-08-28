"""Exploratory equal-schedule adaptive-rank successor on the inspected cohort."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from time import perf_counter

import numpy as np
from qiskit.quantum_info import Statevector


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULTS = REPO / "results" / "decision_balanced_truncation"
sys.path[:0] = [
    str(HERE),
    str(REPO / "experiments" / "contrastive_tensor_simulation"),
    str(REPO / "experiments" / "evoq_mis_full_qoblib"),
]

import run_expanded_qoblib_pilot as expanded
import run_resource_aware_cycle as resource
from contrastive_core import atomic_json
from dbt_core import (
    apply_gate_batch,
    apply_left_projector,
    backward_observability,
    balanced_projector,
    hankel_singular_values,
    reduced_gram,
    select_hankel_rank,
    state_averaged_projector,
)
from run_prospective import CASES, CUT, DEPTH, GENOME_A, GENOME_B, ORDERINGS, bks_indices


OUTPUT = RESULTS / "adaptive_exploratory.json"
ALLOWED_RANKS = tuple(range(1, 9))
ENERGY_FRACTION = 0.99


def advance(states, circuit_a, circuit_b, position: int) -> np.ndarray:
    item_a, item_b = circuit_a.data[position], circuit_b.data[position]
    qargs_a = tuple(circuit_a.find_bit(qubit).index for qubit in item_a.qubits)
    qargs_b = tuple(circuit_b.find_bit(qubit).index for qubit in item_b.qubits)
    sites = circuit_a.num_qubits
    states[:, 0] = apply_gate_batch(states[:, 0], item_a.operation, qargs_a, sites)
    states[:, 1] = apply_gate_batch(states[:, 1], item_b.operation, qargs_b, sites)
    return states


def adaptive_candidate(circuit_a, circuit_b, indices, obs_a, obs_b):
    states = np.zeros((1 << circuit_a.num_qubits, 2), dtype=np.complex128)
    states[0, :] = 1.0
    schedule = []
    maximum_biorthogonality = 0.0
    for position in range(len(circuit_a.data)):
        states = advance(states, circuit_a, circuit_b, position)
        reachability = 0.5 * reduced_gram(states, CUT)
        observability = 0.5 * (obs_a[position] + obs_b[position]) / len(indices)
        singular = hankel_singular_values(reachability, observability)
        rank = select_hankel_rank(singular, ALLOWED_RANKS, ENERGY_FRACTION)
        projector, info = balanced_projector(reachability, observability, rank)
        maximum_biorthogonality = max(maximum_biorthogonality, info["biorthogonality_error"])
        states = apply_left_projector(states, projector, CUT)
        schedule.append(rank)
    return states, schedule, maximum_biorthogonality


def matched_baseline(circuit_a, circuit_b, schedule):
    states = np.zeros((1 << circuit_a.num_qubits, 2), dtype=np.complex128)
    states[0, :] = 1.0
    for position, rank in enumerate(schedule):
        states = advance(states, circuit_a, circuit_b, position)
        reachability = 0.5 * reduced_gram(states, CUT)
        states = apply_left_projector(states, state_averaged_projector(reachability, rank), CUT)
    return states


def main() -> None:
    cases, _ = expanded.configuration()
    payload = {
        "complete": False,
        "inspected_exploratory": True,
        "energy_fraction": ENERGY_FRACTION,
        "allowed_ranks": ALLOWED_RANKS,
        "rows": [],
    }
    for name in CASES:
        for ordering in ORDERINGS:
            case = resource.prepare_case(name, cases[name], ordering)
            indices = bks_indices(case)
            circuit_a = resource.circuit_for(case, GENOME_A, DEPTH).remove_final_measurements(inplace=False)
            circuit_b = resource.circuit_for(case, GENOME_B, DEPTH).remove_final_measurements(inplace=False)
            exact_a = np.asarray(Statevector.from_instruction(circuit_a).data)
            exact_b = np.asarray(Statevector.from_instruction(circuit_b).data)
            exact_delta = float((np.abs(exact_b[indices]) ** 2 - np.abs(exact_a[indices]) ** 2).sum())
            started = perf_counter()
            obs_a = backward_observability(circuit_a, indices, CUT)
            obs_b = backward_observability(circuit_b, indices, CUT)
            candidate, schedule, biorthogonality = adaptive_candidate(
                circuit_a, circuit_b, indices, obs_a, obs_b
            )
            baseline = matched_baseline(circuit_a, circuit_b, schedule)
            candidate_delta = float((np.abs(candidate[indices, 1]) ** 2 - np.abs(candidate[indices, 0]) ** 2).sum())
            baseline_delta = float((np.abs(baseline[indices, 1]) ** 2 - np.abs(baseline[indices, 0]) ** 2).sum())
            row = {
                "case": name,
                "ordering": ordering,
                "qubits": case.qubits,
                "support": len(indices),
                "exact_delta": exact_delta,
                "candidate_delta": candidate_delta,
                "baseline_delta": baseline_delta,
                "candidate_error": abs(candidate_delta - exact_delta),
                "baseline_error": abs(baseline_delta - exact_delta),
                "candidate_sign_correct": bool(np.sign(candidate_delta) == np.sign(exact_delta)),
                "baseline_sign_correct": bool(np.sign(baseline_delta) == np.sign(exact_delta)),
                "candidate_better": abs(candidate_delta - exact_delta) < abs(baseline_delta - exact_delta),
                "rank_min": min(schedule),
                "rank_max": max(schedule),
                "rank_mean": float(np.mean(schedule)),
                "rank_histogram": {str(rank): schedule.count(rank) for rank in sorted(set(schedule))},
                "equal_rank_cubed_work": int(sum(rank ** 3 for rank in schedule)),
                "max_biorthogonality_error": biorthogonality,
                "runtime_seconds": perf_counter() - started,
            }
            payload["rows"].append(row)
            atomic_json(OUTPUT, payload)
            print(json.dumps(row, indent=2), flush=True)
    payload["candidate_better_rows"] = sum(row["candidate_better"] for row in payload["rows"])
    payload["candidate_correct_rows"] = sum(row["candidate_sign_correct"] for row in payload["rows"])
    payload["complete"] = True
    atomic_json(OUTPUT, payload)
    print(json.dumps({
        "output": str(OUTPUT),
        "better": payload["candidate_better_rows"],
        "correct": payload["candidate_correct_rows"],
        "total": len(payload["rows"]),
    }, indent=2))


if __name__ == "__main__":
    main()
