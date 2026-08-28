"""Run frozen sparse-MPS DCS-RDT identity or large constructibility stage."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from time import perf_counter

import numpy as np


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULTS = REPO / "results" / "sparse_mps_dcsrdt"
sys.path[:0] = [
    str(HERE),
    str(REPO / "experiments" / "rankcert_mps"),
    str(REPO / "experiments" / "contrastive_tensor_simulation"),
    str(REPO / "experiments" / "evoq_mis_full_qoblib"),
    str(REPO / "experiments" / "decision_conditioned_srdt"),
]

import rankcert_inputs
import run_independent_ladder_audit as frozen_audit
from certificate import NUMERICAL_SIMULATION_TOLERANCE, accumulated_angle_certificate
from contrastive_core import atomic_json, sha256
from dcsrdt_core import decision_conditioned_operator
from parse_aer_mps_log import parse_mps_log
from sparse_mps_core import (
    decision_operator_from_mps_pair,
    enumerate_bks_support,
    maximum_mps_bond,
    mps_amplitude,
    mps_norm,
    mps_storage_bytes,
    spectral_summary,
)


PROTOCOL = HERE / "PROTOCOL.md"
ORDERINGS = ("sorted", "spectral")
METHODS = ("published_lr", "prior_matched_random")
CONFIG = {
    "development": {
        "cases": ("chesapeake", "football"), "bond": 128, "cutoff": 0.0,
        "cut": 3, "rank": 4,
    },
    "transfer": {
        "cases": ("ibm32", "aves-sparrow-social"), "bond": 128, "cutoff": 1e-4,
        "cut": 5, "rank": 8,
    },
}


def simulate_mps(circuit, bond: int, cutoff: float):
    from qiskit_aer import AerSimulator

    executable = circuit.copy()
    executable.save_matrix_product_state()
    backend = AerSimulator(
        method="matrix_product_state",
        matrix_product_state_max_bond_dimension=bond,
        matrix_product_state_truncation_threshold=cutoff,
        max_parallel_experiments=1,
        max_parallel_threads=1,
        mps_omp_threads=1,
        mps_log_data=True,
        chop_threshold=0.0,
    )
    started = perf_counter()
    result = backend.run(executable).result()
    if not result.success:
        raise RuntimeError(str(result.status))
    mps = result.data(0)["matrix_product_state"]
    parsed = parse_mps_log(
        result.results[0].metadata.get("MPS_log_data", ""), include_segments=False
    )
    certificate = accumulated_angle_certificate(parsed["certificate_weight_upper_bounds"])
    return mps, {
        "simulation_seconds": perf_counter() - started,
        "epsilon_mps": certificate.epsilon,
        "certificate_saturated": certificate.saturated,
        "number_of_truncations": parsed["number_of_truncations"],
        "maximum_bond": maximum_mps_bond(mps),
        "storage_bytes": mps_storage_bytes(mps),
        "norm": mps_norm(mps),
    }


def archived_rows() -> list[dict]:
    path = REPO / "results" / "rankcert_mps" / "rankcert_schedule_rows.json"
    return json.loads(path.read_text(encoding="utf-8"))["rows"]


def archived_gap(rows, case: str, ordering: str) -> float:
    selected = {
        row["method"]: row
        for row in rows
        if row["case"] == case
        and row["ordering"] == ordering
        and row["setting"] == "confirm"
        and row["method"] in METHODS
    }
    return float(selected["prior_matched_random"]["p_bks_mps"]) - float(
        selected["published_lr"]["p_bks_mps"]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=tuple(CONFIG))
    args = parser.parse_args()
    config = CONFIG[args.stage]
    output = RESULTS / f"{args.stage}.json"
    specs = {
        (row["case"], row["ordering"], row["method"]): row
        for row in rankcert_inputs.load_specs()
    }
    archive = archived_rows()
    payload = {
        "complete": False,
        "stage": args.stage,
        "protocol_sha256": sha256(PROTOCOL),
        **config,
        "rows": [],
    }
    for case in config["cases"]:
        for ordering in ORDERINGS:
            pair = []
            simulation = {}
            for method in METHODS:
                spec = specs[(case, ordering, method)]
                circuit = frozen_audit.load_circuit(Path(spec["circuit_file"]))
                mps, info = simulate_mps(circuit, config["bond"], config["cutoff"])
                pair.append(mps)
                simulation[method] = info
            support = enumerate_bks_support(specs[(case, ordering, METHODS[0])]["scorer"])
            started = perf_counter()
            operator, construction = decision_operator_from_mps_pair(
                pair[0], pair[1], support, config["cut"]
            )
            construction_seconds = perf_counter() - started
            spectral = spectral_summary(operator, config["rank"])
            epsilon_pair = sum(info["epsilon_mps"] for info in simulation.values())
            total_bound = min(
                2.0,
                epsilon_pair
                + spectral["tail_trace_norm"]
                + 2.0 * NUMERICAL_SIMULATION_TOLERANCE,
            )
            exact_delta = (
                float(specs[(case, ordering, "prior_matched_random")]["exact_metrics"]["bks_rate"])
                - float(specs[(case, ordering, "published_lr")]["exact_metrics"]["bks_rate"])
            )
            dense_bytes = 2 * (1 << specs[(case, ordering, METHODS[0])]["qubits"]) * 16
            resident_bytes = (
                sum(info["storage_bytes"] for info in simulation.values())
                + operator.nbytes
                + (1 << config["cut"]) * 16
            )
            row = {
                "case": case,
                "ordering": ordering,
                "qubits": specs[(case, ordering, METHODS[0])]["qubits"],
                "support_rank": len(support),
                "simulation": simulation,
                "construction": construction,
                "construction_seconds": construction_seconds,
                "spectral": spectral,
                "direct_mps_delta": spectral["operator_trace"],
                "exact_delta": exact_delta,
                "actual_mps_gap_error": abs(spectral["operator_trace"] - exact_delta),
                "epsilon_pair": epsilon_pair,
                "combined_rank_bound": total_bound,
                "rank_estimate_sign_certified": abs(spectral["estimate"]) > total_bound,
                "dense_pair_bytes": dense_bytes,
                "resident_algorithm_bytes": resident_bytes,
                "storage_reduction_factor": dense_bytes / resident_bytes,
            }
            if args.stage == "development":
                state_a = np.asarray(np.load(specs[(case, ordering, METHODS[0])]["reference_file"], allow_pickle=False))
                state_b = np.asarray(np.load(specs[(case, ordering, METHODS[1])]["reference_file"], allow_pickle=False))
                effect = np.zeros(state_a.size)
                effect[support] = 1.0
                dense = decision_conditioned_operator(
                    state_a, state_b, effect, config["cut"]
                )
                row["dense_operator_frobenius_error"] = float(np.linalg.norm(operator - dense))
                reconstructed_a = np.asarray(
                    [mps_amplitude(pair[0], index) for index in range(state_a.size)]
                )
                reconstructed_b = np.asarray(
                    [mps_amplitude(pair[1], index) for index in range(state_b.size)]
                )
                same_mps_dense = decision_conditioned_operator(
                    reconstructed_a, reconstructed_b, effect, config["cut"]
                )
                row["same_mps_representation_error"] = float(
                    np.linalg.norm(operator - same_mps_dense)
                )
                row["development_pass"] = bool(
                    row["dense_operator_frobenius_error"] < 1e-10
                    and abs(row["direct_mps_delta"] - exact_delta) < 1e-12
                )
            else:
                archived = archived_gap(archive, case, ordering)
                row["archived_mps_delta"] = archived
                row["archived_gap_match_error"] = abs(row["direct_mps_delta"] - archived)
                row["transfer_pass"] = bool(
                    row["archived_gap_match_error"] < 1e-8
                    and row["storage_reduction_factor"] >= 10.0
                )
            payload["rows"].append(row)
            atomic_json(output, payload)
            print(json.dumps({
                "case": case,
                "ordering": ordering,
                "support": len(support),
                "direct_delta": row["direct_mps_delta"],
                "tail": spectral["tail_trace_norm"],
                "combined_bound": total_bound,
                "storage_reduction": row["storage_reduction_factor"],
                "pass": row.get("development_pass", row.get("transfer_pass")),
            }, indent=2), flush=True)
    pass_key = f"{args.stage}_pass"
    payload["passed_rows"] = sum(row[pass_key] for row in payload["rows"])
    payload["success"] = payload["passed_rows"] == len(payload["rows"])
    payload["complete"] = True
    atomic_json(output, payload)
    print(json.dumps({
        "output": str(output),
        "passed_rows": payload["passed_rows"],
        "success": payload["success"],
    }, indent=2))


if __name__ == "__main__":
    main()
