"""Run the frozen expanded-QOBLIB decision-balanced truncation cohort."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
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
from dbt_core import evolve_reduced_pair


PROTOCOL = HERE / "PROTOCOL.md"
OUTPUT = RESULTS / "prospective.json"
CASES = ("es60fst01", "es60fst03", "mammalia-kangaroo-interactions")
ORDERINGS = ("sorted", "spectral")
GENOME_A = np.asarray(expanded.METHODS["published_lr"], dtype=float)
GENOME_B = np.asarray(expanded.METHODS["prior_matched_random"], dtype=float)
DEPTH = 15
CUT = 4
RANK = 2


def bks_indices(case) -> list[int]:
    indices = []
    for index in range(1 << case.qubits):
        bitstring = f"{index:0{case.qubits}b}"
        decoded = case.decoder.decode(resource.canonical_bitstring(case, bitstring[::-1]))
        if decoded.raw_feasible and int(decoded.raw_selected) >= case.bks:
            indices.append(index)
    if not indices:
        raise AssertionError(f"No BKS support for {case.name}/{case.ordering}")
    return indices


def exact_state(circuit) -> np.ndarray:
    return np.asarray(Statevector.from_instruction(circuit).data)


def main() -> None:
    cases, _ = expanded.configuration()
    payload = {
        "complete": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "protocol_sha256": sha256(PROTOCOL),
        "cut": CUT,
        "rank": RANK,
        "depth": DEPTH,
        "rows": [],
    }
    for name in CASES:
        cap = cases[name]
        for ordering in ORDERINGS:
            case = resource.prepare_case(name, cap, ordering)
            indices = bks_indices(case)
            circuit_a = resource.circuit_for(case, GENOME_A, DEPTH).remove_final_measurements(inplace=False)
            circuit_b = resource.circuit_for(case, GENOME_B, DEPTH).remove_final_measurements(inplace=False)
            exact_a = exact_state(circuit_a)
            exact_b = exact_state(circuit_b)
            exact_delta = float((np.abs(exact_b[indices]) ** 2 - np.abs(exact_a[indices]) ** 2).sum())
            methods = {}
            for method in ("state_averaged", "decision_balanced"):
                started = perf_counter()
                states, diagnostics = evolve_reduced_pair(
                    circuit_a, circuit_b, indices, cut=CUT, rank=RANK, method=method
                )
                delta = float((np.abs(states[indices, 1]) ** 2 - np.abs(states[indices, 0]) ** 2).sum())
                methods[method] = {
                    "delta": delta,
                    "absolute_error": abs(delta - exact_delta),
                    "sign_correct": bool(np.sign(delta) == np.sign(exact_delta)),
                    "runtime_seconds": perf_counter() - started,
                    **diagnostics,
                }
            candidate = methods["decision_balanced"]
            baseline = methods["state_averaged"]
            row = {
                "case": name,
                "ordering": ordering,
                "qubits": case.qubits,
                "bks_support_size": len(indices),
                "paired_gates": len(circuit_a.data),
                "exact_delta": exact_delta,
                "methods": methods,
                "candidate_strictly_better": candidate["absolute_error"] < baseline["absolute_error"],
                "candidate_pass": candidate["sign_correct"] and candidate["absolute_error"] < baseline["absolute_error"],
            }
            payload["rows"].append(row)
            atomic_json(OUTPUT, payload)
            print(json.dumps(row, indent=2), flush=True)
    payload["success"] = all(row["candidate_pass"] for row in payload["rows"])
    payload["passed_rows"] = sum(row["candidate_pass"] for row in payload["rows"])
    payload["complete"] = True
    atomic_json(OUTPUT, payload)
    print(json.dumps({
        "output": str(OUTPUT),
        "success": payload["success"],
        "passed_rows": payload["passed_rows"],
        "total_rows": len(payload["rows"]),
    }, indent=2))


if __name__ == "__main__":
    main()
