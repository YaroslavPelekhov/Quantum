"""Evaluate the first term of the adaptive Certified Observable Telescope.

This streams adaptive compressed backward observables in reverse blocks and
replays the frozen Aer MPS prefix trajectory in forward blocks.  It computes

    sum_t |Tr(Otilde_t Delta rho_t)|

without retaining all dense checkpoint states at once.
"""

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

from cot_core import compress_statevector_ttsvd, terminal_basis_vectors
from rankcert_inputs import SETTINGS, atomic_json, load_specs
import run_independent_ladder_audit as frozen_audit
from run_observable_telescope import bks_basis_indices, checkpoint_counts, normalize_copy
from run_observable_telescope_18q import run_segment
from audit_forward_groups import exact_evolve_segment
from run_backward_feasibility import apply_inverse_segment, rankcert_index
from run_residual_cot import parse_primary_schedule, scheduled_bond


RESULTS = REPO / "results" / "compressed_observable_telescope"
TOLERANCE = 2e-8


def observable_value(vectors: np.ndarray, state: np.ndarray) -> float:
    overlaps = vectors.conj().T @ state
    return float(np.vdot(overlaps, overlaps).real)


def compress_normalized_columns(vectors: np.ndarray, bond: int) -> np.ndarray:
    return np.column_stack([
        compress_statevector_ttsvd(vectors[:, column], bond)[0]
        for column in range(vectors.shape[1])
    ])


def backward_adaptive_block(
    circuit,
    counts: list[int],
    left: int,
    right: int,
    current: np.ndarray,
    schedule: list[tuple[int, int, int]],
) -> tuple[dict[int, np.ndarray], np.ndarray]:
    environments = {right: current.copy()}
    for position in range(right - 1, max(0, left - 1), -1):
        if position == 0:
            break
        current = apply_inverse_segment(
            current, circuit, counts[position], counts[position + 1]
        )
        current = compress_normalized_columns(current, scheduled_bond(position, schedule))
        environments[position] = current.copy()
    return environments, current


def run_method(
    spec: dict,
    setting: dict,
    schedule: list[tuple[int, int, int]],
    block_checkpoints: int,
) -> dict:
    circuit = frozen_audit.load_circuit(Path(spec["circuit_file"]))
    counts = checkpoint_counts(circuit)
    boundaries = list(range(0, len(counts) - 1, block_checkpoints))
    if boundaries[-1] != len(counts) - 1:
        boundaries.append(len(counts) - 1)
    current = terminal_basis_vectors(circuit.num_qubits, bks_basis_indices(spec["scorer"]))
    contributions = []
    peak_environment_bytes = 0
    backward_seconds = 0.0
    forward_seconds = 0.0

    for block_number in range(len(boundaries) - 2, -1, -1):
        left, right = boundaries[block_number], boundaries[block_number + 1]
        started = perf_counter()
        environments, current = backward_adaptive_block(
            circuit, counts, left, right, current, schedule
        )
        backward_seconds += perf_counter() - started
        peak_environment_bytes = max(
            peak_environment_bytes, sum(value.nbytes for value in environments.values())
        )

        block_counts = counts[left:right + 1]
        started = perf_counter()
        data, labels = run_segment(
            circuit, 0, block_counts[-1], setting, dense_counts=block_counts
        )
        forward_seconds += perf_counter() - started
        states = {count: normalize_copy(data[labels[count]]) for count in block_counts}
        for position in range(left + 1, right + 1):
            post = states[counts[position]]
            pre = exact_evolve_segment(
                states[counts[position - 1]],
                circuit,
                counts[position - 1],
                counts[position],
            )
            vectors = environments[position]
            signed = observable_value(vectors, post) - observable_value(vectors, pre)
            contributions.append({
                "checkpoint_position": position,
                "prior_operation_count": counts[position - 1],
                "operation_count": counts[position],
                "primary_backward_bond": scheduled_bond(position, schedule)
                if position < len(counts) - 1 else 1,
                "compressed_signed_contribution": signed,
                "compressed_absolute_contribution": abs(signed),
            })
        print(
            f"[compressed first term] {spec['method']} block={block_number + 1}/"
            f"{len(boundaries)-1} positions={left + 1}:{right}",
            flush=True,
        )
        del data, states, environments
        gc.collect()

    contributions.sort(key=lambda row: row["checkpoint_position"])
    first_term = math.fsum(row["compressed_absolute_contribution"] for row in contributions)
    return {
        "case": spec["case"],
        "method": spec["method"],
        "schedule": spec["schedule"],
        "setting": setting["name"],
        "ordering": spec["ordering"],
        "primary_backward_schedule": schedule,
        "checkpoint_count": len(counts),
        "compressed_first_term_sum": first_term,
        "compressed_signed_sum_diagnostic": math.fsum(
            row["compressed_signed_contribution"] for row in contributions
        ),
        "backward_seconds": backward_seconds,
        "prefix_replay_seconds": forward_seconds,
        "peak_block_environment_bytes": peak_environment_bytes,
        "top_contributions": sorted(
            contributions,
            key=lambda row: row["compressed_absolute_contribution"],
            reverse=True,
        )[:30],
        "contributions": contributions,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--primary-schedule",
        default="1-319:512,320-383:384,384-447:256,448-511:128,512-555:64",
    )
    parser.add_argument("--block-checkpoints", type=int, default=64)
    parser.add_argument("--ordering", default="sorted", choices=("sorted", "spectral"))
    parser.add_argument("--residual-result")
    args = parser.parse_args()
    schedule = parse_primary_schedule(args.primary_schedule, 64)
    setting = next(item for item in SETTINGS if item["name"] == "confirm")
    specs = {
        row["method"]: row for row in load_specs()
        if row["case"] == "ibm32" and row["ordering"] == args.ordering
        and row["method"] in ("published_lr", "prior_matched_random")
    }
    output = RESULTS / f"compressed_first_term_ibm32_confirm_{args.ordering}_adaptive.json"
    rows = []
    for method in ("published_lr", "prior_matched_random"):
        rows.append(run_method(specs[method], setting, schedule, args.block_checkpoints))
        atomic_json(output, {
            "stage": "compressed_observable_telescope_first_term",
            "complete": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "rows": rows,
        })

    residual_name = args.residual_result or f"residual_cot_ibm32_confirm_{args.ordering}_adaptive.json"
    residual = json.loads((RESULTS / residual_name).read_text(encoding="utf-8"))
    residual_index = {row["method"]: row for row in residual["rows"]}
    frozen = rankcert_index()
    lr_reference = frozen[("ibm32", "confirm", "published_lr", args.ordering)]
    mr_reference = frozen[("ibm32", "confirm", "prior_matched_random", args.ordering)]
    mps_delta = mr_reference["p_bks_mps"] - lr_reference["p_bks_mps"]
    exact_delta = mr_reference["p_bks_exact"] - lr_reference["p_bks_exact"]
    first_index = {row["method"]: row for row in rows}
    residual_pair_rows = []
    for residual_bond in (128, 256, 512):
        corrections = {}
        for method in first_index:
            item = next(
                value for value in residual_index[method]["residual_ladder"]
                if value["residual_backward_bond"] == residual_bond
            )
            corrections[method] = item["operator_correction_sum"]
        first_sum = math.fsum(
            first_index[method]["compressed_first_term_sum"] for method in first_index
        )
        correction_sum = math.fsum(corrections.values())
        width = first_sum + correction_sum + 2 * TOLERANCE
        residual_pair_rows.append({
            "residual_backward_bond": residual_bond,
            "compressed_first_term_pair_sum": first_sum,
            "operator_correction_pair_sum": correction_sum,
            "certified_pair_width": width,
            "mps_gap_absolute": abs(mps_delta),
            "certified": abs(mps_delta) > width,
            "certificate_margin": abs(mps_delta) - width,
            "correct_sign": (mps_delta > 0) == (exact_delta > 0),
        })
    payload = {
        "stage": "compressed_observable_telescope_first_term",
        "complete": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "primary_backward_schedule": schedule,
        "rows": rows,
        "pair_rows": residual_pair_rows,
    }
    atomic_json(output, payload)
    print(json.dumps({
        "first_terms": {row["method"]: row["compressed_first_term_sum"] for row in rows},
        "pair_rows": residual_pair_rows,
    }, indent=2))


if __name__ == "__main__":
    main()
