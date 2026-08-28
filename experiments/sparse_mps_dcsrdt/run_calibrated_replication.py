"""Run the untouched large cohort under the calibrated replication protocol."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from time import perf_counter


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULTS = REPO / "results" / "sparse_mps_dcsrdt"
sys.path[:0] = [
    str(HERE),
    str(REPO / "experiments" / "rankcert_mps"),
    str(REPO / "experiments" / "contrastive_tensor_simulation"),
    str(REPO / "experiments" / "evoq_mis_full_qoblib"),
]

import rankcert_inputs
import run_independent_ladder_audit as frozen_audit
from certificate import NUMERICAL_SIMULATION_TOLERANCE
from contrastive_core import atomic_json, sha256
from run_sparse_mps import METHODS, archived_gap, archived_rows, simulate_mps
from sparse_mps_core import (
    decision_operator_from_mps_pair,
    enumerate_bks_support,
    spectral_summary,
)


PROTOCOL = HERE / "CALIBRATED_REPLICATION_PROTOCOL.md"
OUTPUT = RESULTS / "calibrated_replication.json"
CASES = ("ibm32", "aves-sparrow-social")
ORDERINGS = ("sorted", "spectral")
BOND = 128
CUTOFF = 1e-4
CUT = 5
RANK = 8


def main() -> None:
    specs = {
        (row["case"], row["ordering"], row["method"]): row
        for row in rankcert_inputs.load_specs()
    }
    archive = archived_rows()
    payload = {
        "complete": False,
        "stage": "calibrated_replication",
        "primary_protocol_success": False,
        "protocol_sha256": sha256(PROTOCOL),
        "bond": BOND,
        "cutoff": CUTOFF,
        "cut": CUT,
        "rank": RANK,
        "rows": [],
    }
    for case in CASES:
        for ordering in ORDERINGS:
            pair = []
            simulation = {}
            for method in METHODS:
                spec = specs[(case, ordering, method)]
                circuit = frozen_audit.load_circuit(Path(spec["circuit_file"]))
                mps, info = simulate_mps(circuit, BOND, CUTOFF)
                pair.append(mps)
                simulation[method] = info
            support = enumerate_bks_support(specs[(case, ordering, METHODS[0])]["scorer"])
            started = perf_counter()
            operator, construction = decision_operator_from_mps_pair(
                pair[0], pair[1], support, CUT
            )
            construction_seconds = perf_counter() - started
            spectral = spectral_summary(operator, RANK)
            epsilon_pair = sum(info["epsilon_mps"] for info in simulation.values())
            combined_bound = min(
                2.0,
                epsilon_pair
                + spectral["tail_trace_norm"]
                + 2.0 * NUMERICAL_SIMULATION_TOLERANCE,
            )
            archived = archived_gap(archive, case, ordering)
            qubits = specs[(case, ordering, METHODS[0])]["qubits"]
            dense_bytes = 2 * (1 << qubits) * 16
            resident_bytes = (
                sum(info["storage_bytes"] for info in simulation.values())
                + operator.nbytes
                + (1 << CUT) * 16
            )
            exact_delta = (
                float(specs[(case, ordering, "prior_matched_random")]["exact_metrics"]["bks_rate"])
                - float(specs[(case, ordering, "published_lr")]["exact_metrics"]["bks_rate"])
            )
            row = {
                "case": case,
                "ordering": ordering,
                "qubits": qubits,
                "support_rank": len(support),
                "simulation": simulation,
                "construction": construction,
                "construction_seconds": construction_seconds,
                "spectral": spectral,
                "direct_mps_delta": spectral["operator_trace"],
                "archived_mps_delta": archived,
                "archived_gap_match_error": abs(spectral["operator_trace"] - archived),
                "exact_delta_audit": exact_delta,
                "actual_mps_gap_error_audit": abs(spectral["operator_trace"] - exact_delta),
                "epsilon_pair": epsilon_pair,
                "combined_rank_bound": combined_bound,
                "rank_estimate_sign_certified": abs(spectral["estimate"]) > combined_bound,
                "dense_pair_bytes": dense_bytes,
                "resident_algorithm_bytes": resident_bytes,
                "storage_reduction_factor": dense_bytes / resident_bytes,
            }
            row["pass"] = bool(
                row["archived_gap_match_error"] < 1e-7
                and row["storage_reduction_factor"] >= 10.0
            )
            payload["rows"].append(row)
            atomic_json(OUTPUT, payload)
            print(json.dumps({
                "case": case,
                "ordering": ordering,
                "support": len(support),
                "direct_delta": row["direct_mps_delta"],
                "archive_error": row["archived_gap_match_error"],
                "tail": spectral["tail_trace_norm"],
                "combined_bound": combined_bound,
                "storage_reduction": row["storage_reduction_factor"],
                "pass": row["pass"],
            }, indent=2), flush=True)
    payload["passed_rows"] = sum(row["pass"] for row in payload["rows"])
    payload["success"] = payload["passed_rows"] == len(payload["rows"])
    payload["complete"] = True
    atomic_json(OUTPUT, payload)
    print(json.dumps({
        "output": str(OUTPUT),
        "passed_rows": payload["passed_rows"],
        "success": payload["success"],
    }, indent=2))


if __name__ == "__main__":
    main()
