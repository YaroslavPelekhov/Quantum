"""Backward-bond feasibility ladder for the proposed certified COT bound."""

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
    str(REPO / "experiments" / "observable_telescope"),
    str(REPO / "experiments" / "rankcert_mps"),
    str(REPO / "experiments" / "evoq_mis_full_qoblib"),
]

from cot_core import (
    compress_statevector_ttsvd,
    group_aer_weights_by_instruction,
    grouped_angle_and_effective_weight,
    terminal_basis_vectors,
)
from rankcert_inputs import atomic_json, load_specs
import run_independent_ladder_audit as frozen_audit
from run_observable_telescope import bks_basis_indices, checkpoint_counts


RESULTS = REPO / "results" / "compressed_observable_telescope"
RANKCERT = REPO / "results" / "rankcert_mps" / "rankcert_schedule_rows.json"
NUMERICAL_ANGLE_PER_COMPRESSION = 1e-12
FORWARD_NUMERICAL_TRACE_NORM_FLOOR = 1e-7


def rankcert_index() -> dict[tuple[str, str, str, str], dict]:
    rows = json.loads(RANKCERT.read_text(encoding="utf-8"))["rows"]
    return {
        (row["case"], row["setting"], row["method"], row["ordering"]): row
        for row in rows
    }


def apply_inverse_segment(vectors: np.ndarray, circuit, start: int, end: int) -> np.ndarray:
    from qiskit.quantum_info import Statevector

    current = vectors
    for operation_index in range(end - 1, start - 1, -1):
        item = circuit.data[operation_index]
        qargs = [circuit.find_bit(qubit).index for qubit in item.qubits]
        inverse = item.operation.inverse()
        for column in range(current.shape[1]):
            current[:, column] = np.asarray(
                Statevector(current[:, column]).evolve(inverse, qargs=qargs).data
            )
    return current


def forward_group_rows(circuit, counts: list[int], raw_log_path: Path) -> list[dict]:
    groups = group_aer_weights_by_instruction(raw_log_path.read_text(encoding="utf-8"))
    two_qubit_counts = [count for count in counts[1:] if len(circuit.data[count - 1].qubits) >= 2]
    if len(groups) != len(two_qubit_counts):
        raise AssertionError((len(groups), len(two_qubit_counts)))
    by_count = {}
    for instruction, operation_count in enumerate(two_qubit_counts):
        angle, effective_weight, radius = grouped_angle_and_effective_weight(groups[instruction])
        by_count[operation_count] = {
            "aer_instruction": instruction,
            "number_of_internal_truncations": len(groups[instruction]),
            "forward_group_angle": angle,
            "forward_effective_weight": effective_weight,
            "aer_group_trace_norm_radius": radius,
            "forward_trace_norm_radius": min(2.0, radius + FORWARD_NUMERICAL_TRACE_NORM_FLOOR),
        }
    rows = []
    for position in range(1, len(counts)):
        operation_count = counts[position]
        row = {
            "checkpoint_position": position,
            "prior_operation_count": counts[position - 1],
            "operation_count": operation_count,
        }
        row.update(by_count.get(operation_count, {
            "aer_instruction": None,
            "number_of_internal_truncations": 0,
            "forward_group_angle": 0.0,
            "forward_effective_weight": 0.0,
            "aer_group_trace_norm_radius": 0.0,
            "forward_trace_norm_radius": FORWARD_NUMERICAL_TRACE_NORM_FLOOR,
        }))
        rows.append(row)
    return rows


def run_ladder(spec: dict, setting_row: dict, bonds: list[int]) -> dict:
    circuit = frozen_audit.load_circuit(Path(spec["circuit_file"]))
    counts = checkpoint_counts(circuit)
    forward_rows = forward_group_rows(circuit, counts, Path(setting_row["raw_log_path"]))
    results = []
    for bond in bonds:
        print(f"[COT backward] {spec['method']} bond={bond}", flush=True)
        started = perf_counter()
        vectors = terminal_basis_vectors(circuit.num_qubits, bks_basis_indices(spec["scorer"]))
        accumulated_angles = [0.0] * vectors.shape[1]
        eta_by_position = {len(counts) - 1: 0.0}
        checkpoint_rows = []
        for position in range(len(counts) - 2, 0, -1):
            vectors = apply_inverse_segment(vectors, circuit, counts[position], counts[position + 1])
            compressed_columns = []
            local_angles = []
            max_rank = 1
            for column in range(vectors.shape[1]):
                compressed, info = compress_statevector_ttsvd(vectors[:, column], bond)
                compressed_columns.append(compressed)
                local_angles.append(info["compression_angle_from_residual"])
                max_rank = max(max_rank, info["max_retained_rank"])
                accumulated_angles[column] = min(
                    math.pi / 2,
                    accumulated_angles[column]
                    + info["compression_angle_from_residual"]
                    + NUMERICAL_ANGLE_PER_COMPRESSION,
                )
            vectors = np.column_stack(compressed_columns)
            eta = math.fsum(math.sin(angle) for angle in accumulated_angles)
            eta_by_position[position] = eta
            checkpoint_rows.append({
                "checkpoint_position": position,
                "operation_count": counts[position],
                "eta_operator_norm_upper_bound": eta,
                "accumulated_vector_angles": accumulated_angles.copy(),
                "local_compression_angles": local_angles,
                "max_backward_bond_seen": max_rank,
            })
            if position % 64 == 0:
                print(f"  checkpoint={position}/{len(counts)-1} eta={eta:.6g}", flush=True)
        correction = math.fsum(
            row["forward_trace_norm_radius"] * eta_by_position.get(row["checkpoint_position"], 0.0)
            for row in forward_rows
        )
        results.append({
            "backward_bond": bond,
            "runtime_seconds": perf_counter() - started,
            "operator_correction_sum": correction,
            "maximum_eta": max(eta_by_position.values()),
            "eta_by_position": eta_by_position,
            "checkpoints": sorted(checkpoint_rows, key=lambda row: row["checkpoint_position"]),
        })
        del vectors
        gc.collect()
        print(f"[COT complete] bond={bond} correction={correction:.6g}", flush=True)
    return {
        "case": spec["case"], "method": spec["method"], "schedule": spec["schedule"],
        "ordering": spec["ordering"], "setting": setting_row["setting"],
        "qubits": spec["qubits"], "native_gate_count": len(circuit.data),
        "checkpoint_count": len(counts), "bks_projector_rank": len(bks_basis_indices(spec["scorer"])),
        "forward_groups": forward_rows, "bond_ladder": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bonds", default="2,4,8,16,32")
    parser.add_argument("--setting", default="confirm")
    parser.add_argument("--ordering", default="sorted")
    args = parser.parse_args()
    bonds = [int(item) for item in args.bonds.split(",")]
    frozen = rankcert_index()
    specs = {
        row["method"]: row for row in load_specs()
        if row["case"] == "ibm32" and row["ordering"] == args.ordering
        and row["method"] in ("published_lr", "prior_matched_random")
    }
    rows = []
    output = RESULTS / f"backward_feasibility_ibm32_{args.setting}_{args.ordering}.json"
    for method in ("published_lr", "prior_matched_random"):
        rows.append(run_ladder(
            specs[method], frozen[("ibm32", args.setting, method, args.ordering)], bonds
        ))
        atomic_json(output, {
            "stage": "compressed_observable_telescope_backward_feasibility",
            "complete": False, "created_at": datetime.now(timezone.utc).isoformat(),
            "proposed_bound": "sum_t(|Tr(O_t_tilde Delta_rho_t)| + 2 sqrt(w_t) eta_t)",
            "rows": rows,
        })
    payload = {
        "stage": "compressed_observable_telescope_backward_feasibility",
        "complete": True, "created_at": datetime.now(timezone.utc).isoformat(),
        "proposed_bound": "sum_t(|Tr(O_t_tilde Delta_rho_t)| + 2 sqrt(w_t) eta_t)",
        "forward_weight_definition": "w_t=sin(sum_j asin(sqrt(upper-rounded Aer w_tj)))^2 within checkpoint group",
        "eta_definition": "sum_k sin(accumulated TT-SVD angle for backward BKS vector k)",
        "rows": rows,
    }
    atomic_json(output, payload)
    print(json.dumps({
        row["method"]: {
            item["backward_bond"]: item["operator_correction_sum"]
            for item in row["bond_ladder"]
        } for row in rows
    }, indent=2))


if __name__ == "__main__":
    main()
