"""Audit grouped Aer 2*sqrt(w_t) against exact checkpoint trace norms on 18q."""

from __future__ import annotations

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

from rankcert_inputs import SETTINGS, atomic_json, load_specs
import run_independent_ladder_audit as frozen_audit
from run_observable_telescope import checkpoint_counts, normalize_copy
from run_observable_telescope_18q import run_segment
from run_backward_feasibility import forward_group_rows, rankcert_index


RESULTS = REPO / "results" / "compressed_observable_telescope"
OUTPUT = RESULTS / "forward_group_audit_ibm32_confirm_sorted.json"
BLOCK = 64
TOLERANCE = 1e-8


def exact_evolve_segment(state: np.ndarray, circuit, start: int, end: int) -> np.ndarray:
    from qiskit.quantum_info import Statevector

    current = Statevector(state)
    for operation_index in range(start, end):
        item = circuit.data[operation_index]
        qargs = [circuit.find_bit(qubit).index for qubit in item.qubits]
        current = current.evolve(item.operation, qargs=qargs)
    return normalize_copy(current.data)


def pure_projector_trace_norm(first: np.ndarray, second: np.ndarray) -> float:
    overlap = min(1.0, max(0.0, float(abs(np.vdot(first, second)))))
    return 2.0 * math.sqrt(max(0.0, 1.0 - overlap * overlap))


def audit_method(spec: dict, rank_row: dict, setting: dict) -> dict:
    circuit = frozen_audit.load_circuit(Path(spec["circuit_file"]))
    counts = checkpoint_counts(circuit)
    grouped = {
        row["checkpoint_position"]: row
        for row in forward_group_rows(circuit, counts, Path(rank_row["raw_log_path"]))
    }
    positions = list(range(0, len(counts) - 1, BLOCK))
    if positions[-1] != len(counts) - 1:
        positions.append(len(counts) - 1)
    rows = []
    started = perf_counter()
    for block_number, (left, right) in enumerate(zip(positions, positions[1:]), start=1):
        block_counts = counts[left:right + 1]
        data, labels = run_segment(
            circuit, 0, block_counts[-1], setting, dense_counts=block_counts
        )
        states = {count: normalize_copy(data[labels[count]]) for count in block_counts}
        for position in range(left + 1, right + 1):
            previous = states[counts[position - 1]]
            post = states[counts[position]]
            pre = exact_evolve_segment(previous, circuit, counts[position - 1], counts[position])
            actual = pure_projector_trace_norm(pre, post)
            bound = grouped[position]["forward_trace_norm_radius"]
            violation = actual - bound
            if violation > TOLERANCE:
                raise AssertionError((spec["method"], position, actual, bound))
            rows.append({
                **grouped[position],
                "actual_checkpoint_trace_norm": actual,
                "group_radius_slack": bound - actual,
                "group_radius_over_actual": bound / actual if actual > 0 else None,
            })
        print(
            f"[forward audit] {spec['method']} block={block_number}/{len(positions)-1}",
            flush=True,
        )
        del data, states
        gc.collect()
    return {
        "case": spec["case"], "method": spec["method"], "setting": setting["name"],
        "ordering": spec["ordering"], "runtime_seconds": perf_counter() - started,
        "maximum_group_radius_violation": max(row["actual_checkpoint_trace_norm"] - row["forward_trace_norm_radius"] for row in rows),
        "sum_group_radius": math.fsum(row["forward_trace_norm_radius"] for row in rows),
        "sum_actual_checkpoint_trace_norm": math.fsum(row["actual_checkpoint_trace_norm"] for row in rows),
        "rows": rows,
    }


def main() -> None:
    setting = next(item for item in SETTINGS if item["name"] == "confirm")
    specs = {
        row["method"]: row for row in load_specs()
        if row["case"] == "ibm32" and row["ordering"] == "sorted"
        and row["method"] in ("published_lr", "prior_matched_random")
    }
    frozen = rankcert_index()
    rows = []
    for method in ("published_lr", "prior_matched_random"):
        rows.append(audit_method(
            specs[method], frozen[("ibm32", "confirm", method, "sorted")], setting
        ))
        atomic_json(OUTPUT, {
            "stage": "compressed_observable_telescope_forward_group_audit",
            "complete": False, "created_at": datetime.now(timezone.utc).isoformat(),
            "rows": rows,
        })
    payload = {
        "stage": "compressed_observable_telescope_forward_group_audit",
        "complete": True, "created_at": datetime.now(timezone.utc).isoformat(),
        "rows": rows,
    }
    atomic_json(OUTPUT, payload)
    print(json.dumps({row["method"]: {
        "sum_group_radius": row["sum_group_radius"],
        "sum_actual_checkpoint_trace_norm": row["sum_actual_checkpoint_trace_norm"],
        "maximum_violation": row["maximum_group_radius_violation"],
    } for row in rows}, indent=2))


if __name__ == "__main__":
    main()
