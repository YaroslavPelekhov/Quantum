"""Exact 18q oracle audit: intrinsic TT compressibility of backward BKS vectors."""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

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
    projector_operator_norm_difference,
    terminal_basis_vectors,
)
from rankcert_inputs import atomic_json, load_specs
import run_independent_ladder_audit as frozen_audit
from run_observable_telescope import bks_basis_indices, checkpoint_counts
from run_backward_feasibility import apply_inverse_segment


RESULTS = REPO / "results" / "compressed_observable_telescope"
NUMERICAL_ANGLE = 1e-12


def audit_method(spec: dict, bonds: list[int], selected: set[int]) -> dict:
    circuit = frozen_audit.load_circuit(Path(spec["circuit_file"]))
    counts = checkpoint_counts(circuit)
    exact = terminal_basis_vectors(circuit.num_qubits, bks_basis_indices(spec["scorer"]))
    rows = []
    for position in range(len(counts) - 2, 0, -1):
        exact = apply_inverse_segment(exact, circuit, counts[position], counts[position + 1])
        if position not in selected:
            continue
        print(f"[oracle] {spec['method']} checkpoint={position}", flush=True)
        for bond in bonds:
            approximate_columns = []
            angles = []
            for column in range(exact.shape[1]):
                approximate, info = compress_statevector_ttsvd(exact[:, column], bond)
                approximate_columns.append(approximate)
                angles.append(info["compression_angle_from_residual"] + NUMERICAL_ANGLE)
            approximate = np.column_stack(approximate_columns)
            eta = math.fsum(math.sin(min(math.pi / 2, angle)) for angle in angles)
            actual = projector_operator_norm_difference(exact, approximate)
            if actual > eta + 1e-9:
                raise AssertionError((position, bond, actual, eta))
            rows.append({
                "checkpoint_position": position,
                "operation_count": counts[position],
                "backward_bond": bond,
                "direct_vector_angles": angles,
                "direct_eta_upper_bound": eta,
                "actual_projector_operator_norm_error": actual,
            })
    return {
        "case": spec["case"], "method": spec["method"], "ordering": spec["ordering"],
        "qubits": spec["qubits"], "checkpoint_count": len(counts), "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bonds", default="4,8,16,32,64,128")
    parser.add_argument("--positions", default="512,448,384,320,256,192,128,64")
    parser.add_argument("--output", default="backward_oracle_ibm32_sorted.json")
    args = parser.parse_args()
    bonds = [int(item) for item in args.bonds.split(",")]
    selected = {int(item) for item in args.positions.split(",")}
    specs = {
        row["method"]: row for row in load_specs()
        if row["case"] == "ibm32" and row["ordering"] == "sorted"
        and row["method"] in ("published_lr", "prior_matched_random")
    }
    rows = [audit_method(specs[method], bonds, selected) for method in specs]
    payload = {
        "stage": "compressed_observable_telescope_backward_oracle_audit",
        "complete": True, "created_at": datetime.now(timezone.utc).isoformat(),
        "interpretation": "Direct compression of exact backward vectors; diagnostic oracle, not scalable certificate",
        "rows": rows,
    }
    output = RESULTS / args.output
    atomic_json(output, payload)
    print(json.dumps({
        row["method"]: {
            str(position): {
                str(bond): next(
                    item["direct_eta_upper_bound"] for item in row["rows"]
                    if item["checkpoint_position"] == position and item["backward_bond"] == bond
                ) for bond in bonds
            } for position in sorted(selected, reverse=True)
        } for row in rows
    }, indent=2))


if __name__ == "__main__":
    main()
