"""Diagnose terminal snapshot-path dependence on one frozen 18q pair."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np


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
from contrastive_core import atomic_json
from run_sparse_mps import METHODS, archived_rows, simulate_mps
from sparse_mps_core import decision_contribution_from_mps, enumerate_bks_support


OUTPUT = RESULTS / "snapshot_semantics.json"


def main() -> None:
    from qiskit_aer import AerSimulator

    specs = {
        (row["case"], row["ordering"], row["method"]): row
        for row in rankcert_inputs.load_specs()
    }
    archive = archived_rows()
    rows = {}
    for method in METHODS:
        spec = specs[("ibm32", "sorted", method)]
        support = enumerate_bks_support(spec["scorer"])
        circuit = frozen_audit.load_circuit(Path(spec["circuit_file"]))
        state_executable = circuit.copy()
        state_executable.save_statevector()
        backend = AerSimulator(
            method="matrix_product_state",
            matrix_product_state_max_bond_dimension=128,
            matrix_product_state_truncation_threshold=1e-4,
            max_parallel_experiments=1,
            max_parallel_threads=1,
            mps_omp_threads=1,
            mps_log_data=True,
            chop_threshold=0.0,
        )
        state = np.asarray(backend.run(state_executable).result().get_statevector(state_executable))
        statevector_probability = float(np.sum(np.abs(state[support]) ** 2))
        mps, mps_info = simulate_mps(circuit, 128, 1e-4)
        contribution, _ = decision_contribution_from_mps(mps, support, cut=5)
        mps_probability = float(np.trace(contribution).real)
        archived = next(
            row
            for row in archive
            if row["case"] == "ibm32"
            and row["ordering"] == "sorted"
            and row["setting"] == "confirm"
            and row["method"] == method
        )
        rows[method] = {
            "save_statevector_probability": statevector_probability,
            "save_matrix_product_state_probability": mps_probability,
            "archived_save_statevector_probability": archived["p_bks_mps"],
            "fresh_vs_archive_error": abs(statevector_probability - archived["p_bks_mps"]),
            "snapshot_path_difference": abs(statevector_probability - mps_probability),
            "mps_info": mps_info,
        }
    payload = {
        "complete": True,
        "case": "ibm32",
        "ordering": "sorted",
        "bond": 128,
        "cutoff": 1e-4,
        "rows": rows,
        "save_statevector_gap": rows["prior_matched_random"]["save_statevector_probability"]
        - rows["published_lr"]["save_statevector_probability"],
        "save_matrix_product_state_gap": rows["prior_matched_random"]["save_matrix_product_state_probability"]
        - rows["published_lr"]["save_matrix_product_state_probability"],
    }
    payload["gap_difference"] = abs(
        payload["save_statevector_gap"] - payload["save_matrix_product_state_gap"]
    )
    atomic_json(OUTPUT, payload)
    print(json.dumps({"output": str(OUTPUT), **payload}, indent=2))


if __name__ == "__main__":
    main()
