"""Residual-aware Certified Compressed Observable Telescope on frozen ibm32.

For every backward BKS basis vector, this tracks

    r_t = v_t - z_t = U_t^dagger r_{t+1} + (U_t^dagger z_{t+1} - z_t).

The residual itself is TT-SVD compressed.  A scalar tail ``xi`` accumulates
the certified norm of discarded residual pieces, giving

    ||r_t||_2 <= ||rhat_t||_2 + xi_t.

Consequently the observable error is bounded by the sum over BKS basis
vectors of min(1, ||rhat_t||_2 + xi_t).  Dense exact vectors are propagated
only as an oracle audit; they are not used to construct the bound.
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

from cot_core import (
    compress_statevector_ttsvd,
    compress_vector_ttsvd_unnormalized,
    projector_operator_norm_difference,
    terminal_basis_vectors,
)
from rankcert_inputs import atomic_json, load_specs
import run_independent_ladder_audit as frozen_audit
from run_observable_telescope import bks_basis_indices, checkpoint_counts
from run_backward_feasibility import (
    apply_inverse_segment,
    forward_group_rows,
    rankcert_index,
)


RESULTS = REPO / "results" / "compressed_observable_telescope"
SELECTED = {512, 448, 384, 320, 256, 192, 128, 64, 1}
NUMERICAL_RESIDUAL_NORM_PER_CHECKPOINT = 1e-10
AUDIT_TOLERANCE = 2e-8


def parse_primary_schedule(text: str | None, default_bond: int) -> list[tuple[int, int, int]]:
    if not text:
        return [(1, 10**9, default_bond)]
    rows = []
    for item in text.split(","):
        interval, bond_text = item.split(":", 1)
        start_text, end_text = interval.split("-", 1)
        rows.append((int(start_text), int(end_text), int(bond_text)))
    rows.sort()
    for previous, current in zip(rows, rows[1:]):
        if previous[1] + 1 != current[0]:
            raise ValueError("Primary schedule must be contiguous")
    return rows


def scheduled_bond(position: int, schedule: list[tuple[int, int, int]]) -> int:
    for start, end, bond in schedule:
        if start <= position <= end:
            return bond
    raise ValueError(f"No primary bond assigned to checkpoint {position}")


def compress_columns_normalized(vectors: np.ndarray, bond: int) -> tuple[np.ndarray, np.ndarray, list[dict]]:
    compressed = []
    residuals = []
    infos = []
    for column in range(vectors.shape[1]):
        approximation, info = compress_statevector_ttsvd(vectors[:, column], bond)
        compressed.append(approximation)
        residuals.append(vectors[:, column] - approximation)
        infos.append(info)
    return np.column_stack(compressed), np.column_stack(residuals), infos


def compress_residual_columns(
    candidates: np.ndarray, bond: int, tails: list[float]
) -> tuple[np.ndarray, list[float], list[dict]]:
    compressed = []
    updated_tails = []
    infos = []
    for column in range(candidates.shape[1]):
        approximation, info = compress_vector_ttsvd_unnormalized(candidates[:, column], bond)
        actual_local_error = float(np.linalg.norm(candidates[:, column] - approximation))
        theorem_bound = info["discarded_norm_upper_bound"]
        if actual_local_error > theorem_bound + 1e-9:
            raise AssertionError((bond, column, actual_local_error, theorem_bound))
        info = {
            **info,
            "dense_oracle_local_error": actual_local_error,
            "floating_slack": theorem_bound + NUMERICAL_RESIDUAL_NORM_PER_CHECKPOINT - actual_local_error,
        }
        compressed.append(approximation)
        updated_tails.append(
            tails[column] + theorem_bound + NUMERICAL_RESIDUAL_NORM_PER_CHECKPOINT
        )
        infos.append(info)
    return np.column_stack(compressed), updated_tails, infos


def run_method(
    spec: dict,
    setting_row: dict,
    primary_bond: int,
    primary_schedule: list[tuple[int, int, int]],
    residual_bonds: list[int],
    residual_schedule: list[tuple[int, int, int]] | None = None,
    forward_rows_override: list[dict] | None = None,
    residual_configs_override: list[dict] | None = None,
) -> dict:
    circuit = frozen_audit.load_circuit(Path(spec["circuit_file"]))
    counts = checkpoint_counts(circuit)
    forward_rows = (
        forward_rows_override
        if forward_rows_override is not None
        else forward_group_rows(circuit, counts, Path(setting_row["raw_log_path"]))
    )
    terminal = terminal_basis_vectors(circuit.num_qubits, bks_basis_indices(spec["scorer"]))
    exact = terminal.copy()
    primary = terminal.copy()
    residual_configs = residual_configs_override or (
        [{"key": "adaptive", "constant_bond": None, "schedule": residual_schedule}]
        if residual_schedule is not None else [
            {
                "key": f"R{bond}",
                "constant_bond": bond,
                "schedule": [(1, 10**9, bond)],
            }
            for bond in residual_bonds
        ]
    )
    residual_states = {
        config["key"]: np.zeros_like(terminal) for config in residual_configs
    }
    tails = {
        config["key"]: [0.0] * terminal.shape[1] for config in residual_configs
    }
    eta_by_config = {
        config["key"]: {len(counts) - 1: 0.0} for config in residual_configs
    }
    rows_by_config = {config["key"]: [] for config in residual_configs}
    started = perf_counter()

    for position in range(len(counts) - 2, 0, -1):
        start, end = counts[position], counts[position + 1]
        exact = apply_inverse_segment(exact, circuit, start, end)
        propagated_primary = apply_inverse_segment(primary, circuit, start, end)
        active_primary_bond = scheduled_bond(position, primary_schedule)
        primary, local_primary_residual, primary_infos = compress_columns_normalized(
            propagated_primary, active_primary_bond
        )

        for config in residual_configs:
            key = config["key"]
            bond = scheduled_bond(position, config["schedule"])
            propagated_residual = apply_inverse_segment(residual_states[key], circuit, start, end)
            candidates = propagated_residual + local_primary_residual
            residual_states[key], tails[key], residual_infos = compress_residual_columns(
                candidates, bond, tails[key]
            )
            vector_bounds = [
                float(np.linalg.norm(residual_states[key][:, column])) + tails[key][column]
                for column in range(terminal.shape[1])
            ]
            eta = math.fsum(min(1.0, value) for value in vector_bounds)
            eta_by_config[key][position] = eta
            row = {
                "checkpoint_position": position,
                "operation_count": counts[position],
                "primary_backward_bond": active_primary_bond,
                "residual_backward_bond": bond,
                "eta_operator_norm_upper_bound": eta,
                "residual_vector_norm_bounds": vector_bounds,
                "compressed_residual_norms": [
                    float(np.linalg.norm(residual_states[key][:, column]))
                    for column in range(terminal.shape[1])
                ],
                "discarded_residual_tail_bounds": tails[key].copy(),
                "primary_local_norm_errors": [
                    info["phase_aligned_norm_error"] for info in primary_infos
                ],
                "residual_local_discard_bounds": [
                    info["discarded_norm_upper_bound"] for info in residual_infos
                ],
            }
            if position in SELECTED:
                exact_vector_errors = [
                    float(np.linalg.norm(exact[:, column] - primary[:, column]))
                    for column in range(terminal.shape[1])
                ]
                actual_residual_representation_errors = [
                    float(np.linalg.norm(
                        exact[:, column] - primary[:, column] - residual_states[key][:, column]
                    ))
                    for column in range(terminal.shape[1])
                ]
                actual_operator_error = projector_operator_norm_difference(exact, primary)
                if any(
                    actual_residual_representation_errors[column] > tails[key][column] + AUDIT_TOLERANCE
                    for column in range(terminal.shape[1])
                ):
                    raise AssertionError((
                        spec["method"], bond, position,
                        actual_residual_representation_errors, tails[key],
                    ))
                if actual_operator_error > eta + AUDIT_TOLERANCE:
                    raise AssertionError((spec["method"], bond, position, actual_operator_error, eta))
                row.update({
                    "oracle_exact_vector_errors": exact_vector_errors,
                    "oracle_residual_representation_errors": actual_residual_representation_errors,
                    "oracle_actual_operator_error": actual_operator_error,
                    "oracle_eta_over_actual": eta / actual_operator_error if actual_operator_error > 0 else None,
                })
            rows_by_config[key].append(row)

        if position % 64 == 0 or position == 1:
            message = " ".join(
                f"{config['key']}@{scheduled_bond(position, config['schedule'])}:"
                f"eta={eta_by_config[config['key']][position]:.6g}"
                for config in residual_configs
            )
            print(f"[residual COT] {spec['method']} t={position} {message}", flush=True)

    results = []
    for config in residual_configs:
        key = config["key"]
        correction = math.fsum(
            row["forward_trace_norm_radius"]
            * eta_by_config[key].get(row["checkpoint_position"], 0.0)
            for row in forward_rows
        )
        results.append({
            "residual_config_key": key,
            "primary_backward_bond": primary_bond,
            "primary_backward_schedule": primary_schedule,
            "residual_backward_bond": config["constant_bond"],
            "residual_backward_schedule": config["schedule"],
            "operator_correction_sum": correction,
            "maximum_eta": max(eta_by_config[key].values()),
            "eta_by_position": eta_by_config[key],
            "checkpoints": sorted(
                rows_by_config[key], key=lambda item: item["checkpoint_position"]
            ),
        })
    del exact, primary, residual_states
    gc.collect()
    return {
        "case": spec["case"],
        "method": spec["method"],
        "schedule": spec["schedule"],
        "ordering": spec["ordering"],
        "setting": setting_row["setting"],
        "qubits": spec["qubits"],
        "checkpoint_count": len(counts),
        "bks_projector_rank": terminal.shape[1],
        "runtime_seconds": perf_counter() - started,
        "primary_backward_schedule": primary_schedule,
        "forward_groups": forward_rows,
        "residual_ladder": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--primary-bond", type=int, default=64)
    parser.add_argument(
        "--primary-schedule",
        help="Comma-separated inclusive position ranges, e.g. 1-319:512,320-555:64",
    )
    parser.add_argument("--residual-bonds", default="32,64,128")
    parser.add_argument(
        "--residual-schedule",
        help="Optional variable residual bond schedule using inclusive position ranges",
    )
    parser.add_argument("--setting", default="confirm")
    parser.add_argument("--ordering", default="sorted")
    parser.add_argument(
        "--methods",
        default="published_lr,prior_matched_random",
        help="Comma-separated subset of published_lr,prior_matched_random",
    )
    parser.add_argument("--output-tag", default="")
    args = parser.parse_args()
    residual_bonds = [int(item) for item in args.residual_bonds.split(",")]
    primary_schedule = parse_primary_schedule(args.primary_schedule, args.primary_bond)
    residual_schedule = (
        parse_primary_schedule(args.residual_schedule, residual_bonds[0])
        if args.residual_schedule else None
    )
    methods = tuple(item.strip() for item in args.methods.split(",") if item.strip())
    allowed_methods = {"published_lr", "prior_matched_random"}
    if not methods or not set(methods) <= allowed_methods:
        raise ValueError(f"Invalid methods: {methods}")
    frozen = rankcert_index()
    specs = {
        row["method"]: row for row in load_specs()
        if row["case"] == "ibm32" and row["ordering"] == args.ordering
        and row["method"] in methods
    }
    schedule_label = "adaptive" if args.primary_schedule else f"D{args.primary_bond}"
    residual_label = "_residual-adaptive" if residual_schedule is not None else ""
    tag_label = f"_{args.output_tag}" if args.output_tag else ""
    output = RESULTS / (
        f"residual_cot_ibm32_{args.setting}_{args.ordering}_"
        f"{schedule_label}{residual_label}{tag_label}.json"
    )
    archived_forward_rows = {}
    archived_path = RESULTS / (
        f"residual_cot_ibm32_{args.setting}_{args.ordering}_{schedule_label}.json"
    )
    if archived_path.exists():
        archived_payload = json.loads(archived_path.read_text(encoding="utf-8"))
        archived_forward_rows = {
            row["method"]: row["forward_groups"] for row in archived_payload.get("rows", [])
        }
    rows = []
    for method in methods:
        print(f"[residual COT start] {method}", flush=True)
        rows.append(run_method(
            specs[method],
            frozen[("ibm32", args.setting, method, args.ordering)],
            args.primary_bond,
            primary_schedule,
            residual_bonds,
            residual_schedule,
            archived_forward_rows.get(method),
        ))
        atomic_json(output, {
            "stage": "residual_aware_compressed_observable_telescope",
            "complete": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "rows": rows,
        })
    payload = {
        "stage": "residual_aware_compressed_observable_telescope",
        "complete": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "construction": "rhat_t=TT_R(Udagger rhat_{t+1}+Udagger z_{t+1}-z_t); xi_t=xi_{t+1}+TT_error+numeric_floor",
        "eta_definition": "sum_k min(1, ||rhat_t,k||_2 + xi_t,k)",
        "numeric_floor_per_residual_vector_per_checkpoint": NUMERICAL_RESIDUAL_NORM_PER_CHECKPOINT,
        "dense_exact_vectors_used_for_oracle_audit_only": True,
        "primary_backward_schedule": primary_schedule,
        "residual_backward_schedule": residual_schedule,
        "methods": list(methods),
        "rows": rows,
    }
    atomic_json(output, payload)
    print(json.dumps({
        row["method"]: {
            (
                f"R{item['residual_backward_bond']}"
                if item["residual_backward_bond"] is not None else "adaptive"
            ): item["operator_correction_sum"]
            for item in row["residual_ladder"]
        } for row in rows
    }, indent=2))


if __name__ == "__main__":
    main()
