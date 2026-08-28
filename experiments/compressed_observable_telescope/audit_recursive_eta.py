"""Compare certified recursive eta with exact projector error at selected 18q checkpoints."""

from __future__ import annotations

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
from run_backward_feasibility import apply_inverse_segment, NUMERICAL_ANGLE_PER_COMPRESSION


RESULTS = REPO / "results" / "compressed_observable_telescope"
BOND = 64
SELECTED = {512, 448, 384, 320, 256, 192, 128, 64}


def audit(spec: dict) -> dict:
    circuit = frozen_audit.load_circuit(Path(spec["circuit_file"]))
    counts = checkpoint_counts(circuit)
    indices = bks_basis_indices(spec["scorer"])
    exact = terminal_basis_vectors(circuit.num_qubits, indices)
    approximate = exact.copy()
    accumulated = [0.0] * exact.shape[1]
    rows = []
    for position in range(len(counts) - 2, 0, -1):
        exact = apply_inverse_segment(exact, circuit, counts[position], counts[position + 1])
        approximate = apply_inverse_segment(
            approximate, circuit, counts[position], counts[position + 1]
        )
        columns = []
        local = []
        for column in range(approximate.shape[1]):
            compressed, info = compress_statevector_ttsvd(approximate[:, column], BOND)
            columns.append(compressed)
            angle = info["compression_angle_from_residual"]
            local.append(angle)
            accumulated[column] = min(
                math.pi / 2,
                accumulated[column] + angle + NUMERICAL_ANGLE_PER_COMPRESSION,
            )
        approximate = np.column_stack(columns)
        if position not in SELECTED:
            continue
        eta = math.fsum(math.sin(angle) for angle in accumulated)
        actual = projector_operator_norm_difference(exact, approximate)
        if actual > eta + 1e-8:
            raise AssertionError((spec["method"], position, actual, eta))
        rows.append({
            "checkpoint_position": position,
            "operation_count": counts[position],
            "backward_bond": BOND,
            "certified_eta": eta,
            "actual_recursive_projector_error": actual,
            "eta_over_actual": eta / actual if actual > 0 else None,
            "accumulated_vector_angles": accumulated.copy(),
            "local_compression_angles": local,
        })
        print(
            f"[recursive oracle] {spec['method']} checkpoint={position} "
            f"eta={eta:.6g} actual={actual:.6g}", flush=True,
        )
    return {"method": spec["method"], "rows": sorted(rows, key=lambda row: row["checkpoint_position"])}


def main() -> None:
    specs = {
        row["method"]: row for row in load_specs()
        if row["case"] == "ibm32" and row["ordering"] == "sorted"
        and row["method"] in ("published_lr", "prior_matched_random")
    }
    rows = [audit(specs[method]) for method in ("published_lr", "prior_matched_random")]
    payload = {
        "stage": "compressed_observable_telescope_recursive_eta_oracle_audit",
        "complete": True, "created_at": datetime.now(timezone.utc).isoformat(),
        "backward_bond": BOND, "rows": rows,
    }
    atomic_json(RESULTS / "recursive_eta_oracle_ibm32_sorted_bond64.json", payload)
    print(json.dumps({row["method"]: {
        item["checkpoint_position"]: item["eta_over_actual"] for item in row["rows"]
    } for row in rows}, indent=2))


if __name__ == "__main__":
    main()
