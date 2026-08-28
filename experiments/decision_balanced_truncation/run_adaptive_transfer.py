"""Run the frozen adaptive DBT transfer to a held-out schedule pair."""

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
from contrastive_core import atomic_json, sha256
from dbt_core import backward_observability
from run_adaptive_exploratory import adaptive_candidate, matched_baseline
from run_prospective import CASES, CUT, DEPTH, GENOME_A, ORDERINGS, bks_indices


PROTOCOL = HERE / "ADAPTIVE_TRANSFER_PROTOCOL.md"
OUTPUT = RESULTS / "adaptive_transfer.json"
GENOME_B = np.asarray(expanded.METHODS["prior_evolutionary"], dtype=float)


def main() -> None:
    cases, _ = expanded.configuration()
    payload = {
        "complete": False,
        "protocol_sha256": sha256(PROTOCOL),
        "schedule_pair": ["published_lr", "prior_evolutionary"],
        "energy_fraction": 0.99,
        "allowed_ranks": list(range(1, 9)),
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
            candidate_error = abs(candidate_delta - exact_delta)
            baseline_error = abs(baseline_delta - exact_delta)
            row = {
                "case": name,
                "ordering": ordering,
                "qubits": case.qubits,
                "support": len(indices),
                "exact_delta": exact_delta,
                "candidate_delta": candidate_delta,
                "baseline_delta": baseline_delta,
                "candidate_error": candidate_error,
                "baseline_error": baseline_error,
                "error_improvement_factor": baseline_error / candidate_error if candidate_error else None,
                "candidate_sign_correct": bool(np.sign(candidate_delta) == np.sign(exact_delta)),
                "baseline_sign_correct": bool(np.sign(baseline_delta) == np.sign(exact_delta)),
                "candidate_better": candidate_error < baseline_error,
                "rank_min": min(schedule),
                "rank_max": max(schedule),
                "rank_mean": float(np.mean(schedule)),
                "rank_histogram": {str(rank): schedule.count(rank) for rank in sorted(set(schedule))},
                "equal_rank_cubed_work": int(sum(rank ** 3 for rank in schedule)),
                "max_biorthogonality_error": biorthogonality,
                "runtime_seconds": perf_counter() - started,
            }
            row["pass"] = row["candidate_sign_correct"] and row["candidate_better"]
            payload["rows"].append(row)
            atomic_json(OUTPUT, payload)
            print(json.dumps(row, indent=2), flush=True)
    payload["passed_rows"] = sum(row["pass"] for row in payload["rows"])
    payload["success"] = payload["passed_rows"] == len(payload["rows"])
    payload["complete"] = True
    atomic_json(OUTPUT, payload)
    print(json.dumps({
        "output": str(OUTPUT),
        "success": payload["success"],
        "passed": payload["passed_rows"],
        "total": len(payload["rows"]),
    }, indent=2))


if __name__ == "__main__":
    main()
