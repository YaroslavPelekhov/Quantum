"""Run development or held-out GDBC protocol stage."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from time import perf_counter

import numpy as np
from qiskit.quantum_info import Statevector


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULTS = REPO / "results" / "global_decision_balanced_contraction"
sys.path[:0] = [
    str(HERE),
    str(REPO / "experiments" / "contrastive_tensor_simulation"),
    str(REPO / "experiments" / "evoq_mis_full_qoblib"),
]

import run_expanded_qoblib_pilot as expanded
import run_resource_aware_cycle as resource
from contrastive_core import atomic_json, sha256
from gdbc_core import run_global_pair


PROTOCOL = HERE / "PROTOCOL.md"
CASES = ("es60fst01", "es60fst03", "mammalia-kangaroo-interactions")
ORDERINGS = ("sorted", "spectral")
GENOME_A = np.asarray(expanded.METHODS["published_lr"], dtype=float)
PAIR_METHODS = {
    "development": "prior_matched_random",
    "transfer": "prior_evolutionary",
}
DEPTH = 15
CUT = 4


def bks_indices(case) -> list[int]:
    output = []
    for index in range(1 << case.qubits):
        bitstring = f"{index:0{case.qubits}b}"
        decoded = case.decoder.decode(resource.canonical_bitstring(case, bitstring[::-1]))
        if decoded.raw_feasible and int(decoded.raw_selected) >= case.bks:
            output.append(index)
    if not output:
        raise AssertionError("Empty BKS support")
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=tuple(PAIR_METHODS))
    args = parser.parse_args()
    stage = args.stage
    method_b = PAIR_METHODS[stage]
    genome_b = np.asarray(expanded.METHODS[method_b], dtype=float)
    output_path = RESULTS / f"{stage}.json"
    cases, _ = expanded.configuration()
    payload = {
        "complete": False,
        "stage": stage,
        "protocol_sha256": sha256(PROTOCOL),
        "schedule_pair": ["published_lr", method_b],
        "rows": [],
    }
    for name in CASES:
        for ordering in ORDERINGS:
            case = resource.prepare_case(name, cases[name], ordering)
            indices = bks_indices(case)
            circuit_a = resource.circuit_for(case, GENOME_A, DEPTH).remove_final_measurements(inplace=False)
            circuit_b = resource.circuit_for(case, genome_b, DEPTH).remove_final_measurements(inplace=False)
            exact_a = np.asarray(Statevector.from_instruction(circuit_a).data)
            exact_b = np.asarray(Statevector.from_instruction(circuit_b).data)
            exact_delta = float((np.abs(exact_b[indices]) ** 2 - np.abs(exact_a[indices]) ** 2).sum())
            started = perf_counter()
            reduced = run_global_pair(circuit_a, circuit_b, indices, CUT)
            methods = reduced.pop("methods")
            for values in methods.values():
                values["absolute_error"] = abs(values["delta"] - exact_delta)
                values["sign_correct"] = bool(np.sign(values["delta"]) == np.sign(exact_delta))
            candidate = methods["global_balanced"]
            baseline = methods["orthogonal_baseline"]
            row = {
                "case": name,
                "ordering": ordering,
                "qubits": case.qubits,
                "support": len(indices),
                "exact_delta": exact_delta,
                "methods": methods,
                **reduced,
                "candidate_better": candidate["absolute_error"] < baseline["absolute_error"],
                "candidate_pass": candidate["sign_correct"] and candidate["absolute_error"] < baseline["absolute_error"],
                "error_improvement_factor": baseline["absolute_error"] / candidate["absolute_error"] if candidate["absolute_error"] else None,
                "runtime_seconds": perf_counter() - started,
            }
            payload["rows"].append(row)
            atomic_json(output_path, payload)
            print(json.dumps({
                "case": row["case"],
                "ordering": row["ordering"],
                "exact_delta": row["exact_delta"],
                "candidate_error": candidate["absolute_error"],
                "baseline_error": baseline["absolute_error"],
                "candidate_sign_correct": candidate["sign_correct"],
                "candidate_pass": row["candidate_pass"],
                "rank_min": row["rank_min"],
                "rank_max": row["rank_max"],
                "rank_mean": row["rank_mean"],
                "runtime_seconds": row["runtime_seconds"],
            }, indent=2), flush=True)
    payload["passed_rows"] = sum(row["candidate_pass"] for row in payload["rows"])
    payload["success"] = payload["passed_rows"] == len(payload["rows"])
    payload["complete"] = True
    atomic_json(output_path, payload)
    print(json.dumps({
        "output": str(output_path),
        "stage": stage,
        "passed": payload["passed_rows"],
        "total": len(payload["rows"]),
        "success": payload["success"],
    }, indent=2))


if __name__ == "__main__":
    main()
