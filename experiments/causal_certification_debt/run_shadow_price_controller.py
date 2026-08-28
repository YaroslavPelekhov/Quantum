"""Oracle-free causal shadow-price controller for residual COT bond choices."""

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
    str(REPO / "experiments" / "compressed_observable_telescope"),
    str(REPO / "experiments" / "observable_telescope"),
    str(REPO / "experiments" / "rankcert_mps"),
    str(REPO / "experiments" / "evoq_mis_full_qoblib"),
]

from cot_core import projector_operator_norm_difference, terminal_basis_vectors
from rankcert_inputs import atomic_json, load_specs
import run_independent_ladder_audit as frozen_audit
from run_observable_telescope import bks_basis_indices, checkpoint_counts
from run_backward_feasibility import apply_inverse_segment, forward_group_rows, rankcert_index
from run_residual_cot import (
    AUDIT_TOLERANCE,
    NUMERICAL_RESIDUAL_NORM_PER_CHECKPOINT,
    SELECTED,
    compress_columns_normalized,
    compress_residual_columns,
    parse_primary_schedule,
    scheduled_bond,
)


RESULTS = REPO / "results" / "causal_certification_debt"


def controller_candidates(
    vectors: np.ndarray,
    tails: list[float],
    bonds: tuple[int, ...],
    causal_price: float,
    shadow_price: float,
) -> tuple[int, dict, list[dict]]:
    maximum_bond = max(bonds)
    candidates = []
    payloads = {}
    for bond in bonds:
        approximation, updated_tails, infos = compress_residual_columns(
            vectors, bond, tails
        )
        local_increment = math.fsum(
            info["discarded_norm_upper_bound"]
            + NUMERICAL_RESIDUAL_NORM_PER_CHECKPOINT
            for info in infos
        )
        normalized_cubic_cost = (bond / maximum_bond) ** 3
        debt_increment = causal_price * local_increment
        score = normalized_cubic_cost + shadow_price * debt_increment
        candidate = {
            "bond": bond,
            "normalized_cubic_cost": normalized_cubic_cost,
            "local_tail_increment": local_increment,
            "causal_price": causal_price,
            "causal_debt_increment": debt_increment,
            "score": score,
            "per_vector_discard_bounds": [
                info["discarded_norm_upper_bound"] for info in infos
            ],
        }
        candidates.append(candidate)
        payloads[bond] = (approximation, updated_tails, infos)
    chosen = min(candidates, key=lambda row: (row["score"], row["bond"]))["bond"]
    return chosen, payloads[chosen], candidates


def run_method(
    spec: dict,
    setting_row: dict,
    primary_schedule: list[tuple[int, int, int]],
    bonds: tuple[int, ...],
    shadow_price: float,
) -> dict:
    circuit = frozen_audit.load_circuit(Path(spec["circuit_file"]))
    counts = checkpoint_counts(circuit)
    forward_rows = forward_group_rows(circuit, counts, Path(setting_row["raw_log_path"]))
    radii = {
        row["checkpoint_position"]: row["forward_trace_norm_radius"]
        for row in forward_rows
        if 1 <= row["checkpoint_position"] < len(counts) - 1
    }
    causal_prices = {}
    running = 0.0
    for position in sorted(radii):
        running += radii[position]
        causal_prices[position] = running

    terminal = terminal_basis_vectors(circuit.num_qubits, bks_basis_indices(spec["scorer"]))
    exact = terminal.copy()
    primary = terminal.copy()
    residual_state = np.zeros_like(terminal)
    tails = [0.0] * terminal.shape[1]
    eta_by_position = {len(counts) - 1: 0.0}
    checkpoint_rows = []
    cumulative_debt = 0.0
    started = perf_counter()

    for position in range(len(counts) - 2, 0, -1):
        start, end = counts[position], counts[position + 1]
        exact = apply_inverse_segment(exact, circuit, start, end)
        propagated_primary = apply_inverse_segment(primary, circuit, start, end)
        primary_bond = scheduled_bond(position, primary_schedule)
        primary, local_primary_residual, primary_infos = compress_columns_normalized(
            propagated_primary, primary_bond
        )
        propagated_residual = apply_inverse_segment(residual_state, circuit, start, end)
        residual_candidate = propagated_residual + local_primary_residual
        chosen_bond, chosen_payload, candidate_rows = controller_candidates(
            residual_candidate,
            tails,
            bonds,
            causal_prices[position],
            shadow_price,
        )
        residual_state, tails, residual_infos = chosen_payload
        chosen_diagnostic = next(row for row in candidate_rows if row["bond"] == chosen_bond)
        cumulative_debt += chosen_diagnostic["causal_debt_increment"]
        vector_bounds = [
            float(np.linalg.norm(residual_state[:, column])) + tails[column]
            for column in range(terminal.shape[1])
        ]
        eta = math.fsum(min(1.0, value) for value in vector_bounds)
        eta_by_position[position] = eta
        checkpoint = {
            "checkpoint_position": position,
            "operation_count": counts[position],
            "primary_backward_bond": primary_bond,
            "chosen_residual_bond": chosen_bond,
            "causal_price": causal_prices[position],
            "chosen_causal_debt_increment": chosen_diagnostic["causal_debt_increment"],
            "cumulative_debt_in_backward_execution_order": cumulative_debt,
            "candidate_diagnostics": candidate_rows,
            "eta_operator_norm_upper_bound": eta,
            "residual_vector_norm_bounds": vector_bounds,
            "compressed_residual_norms": [
                float(np.linalg.norm(residual_state[:, column]))
                for column in range(terminal.shape[1])
            ],
            "discarded_residual_tail_bounds": tails.copy(),
            "primary_local_norm_errors": [
                info["phase_aligned_norm_error"] for info in primary_infos
            ],
            "residual_local_discard_bounds": [
                info["discarded_norm_upper_bound"] for info in residual_infos
            ],
        }
        if position in SELECTED or circuit.num_qubits <= 8:
            actual_residual_representation_errors = [
                float(np.linalg.norm(
                    exact[:, column] - primary[:, column] - residual_state[:, column]
                ))
                for column in range(terminal.shape[1])
            ]
            actual_operator_error = projector_operator_norm_difference(exact, primary)
            if any(
                actual_residual_representation_errors[column]
                > tails[column] + AUDIT_TOLERANCE
                for column in range(terminal.shape[1])
            ):
                raise AssertionError((
                    spec["method"], chosen_bond, position,
                    actual_residual_representation_errors, tails,
                ))
            if actual_operator_error > eta + AUDIT_TOLERANCE:
                raise AssertionError((spec["method"], chosen_bond, position, actual_operator_error, eta))
            checkpoint.update({
                "oracle_residual_representation_errors": actual_residual_representation_errors,
                "oracle_actual_operator_error": actual_operator_error,
            })
        checkpoint_rows.append(checkpoint)
        if position % 64 == 0 or position == 1:
            print(
                f"[debt controller] {spec['case']} {spec['method']} t={position} "
                f"bond={chosen_bond} Lambda={causal_prices[position]:.6g} "
                f"debt={cumulative_debt:.6g}",
                flush=True,
            )

    correction = math.fsum(
        radii[position] * eta_by_position[position] for position in radii
    )
    counts_by_bond = {
        str(bond): sum(row["chosen_residual_bond"] == bond for row in checkpoint_rows)
        for bond in bonds
    }
    cubic_work_vs_fixed_256 = math.fsum(
        (row["chosen_residual_bond"] / 256) ** 3 for row in checkpoint_rows
    ) / len(checkpoint_rows)
    del exact, primary, residual_state
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
        "candidate_residual_bonds": list(bonds),
        "shadow_price": shadow_price,
        "bond_counts": counts_by_bond,
        "cubic_work_ratio_vs_fixed_R256": cubic_work_vs_fixed_256,
        "causal_debt": cumulative_debt,
        "operator_correction_sum": correction,
        "maximum_eta": max(eta_by_position.values()),
        "forward_groups": forward_rows,
        "checkpoints": sorted(checkpoint_rows, key=lambda row: row["checkpoint_position"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", default="ibm32")
    parser.add_argument("--setting", default="confirm")
    parser.add_argument("--ordering", default="sorted")
    parser.add_argument("--primary-bond", type=int, default=64)
    parser.add_argument("--primary-schedule")
    parser.add_argument("--candidate-bonds", default="128,256,512")
    parser.add_argument("--shadow-price", type=float, default=500.0)
    parser.add_argument("--methods", default="published_lr,prior_matched_random")
    args = parser.parse_args()
    bonds = tuple(sorted({int(item) for item in args.candidate_bonds.split(",")}))
    methods = tuple(item.strip() for item in args.methods.split(",") if item.strip())
    primary_schedule = parse_primary_schedule(args.primary_schedule, args.primary_bond)
    frozen = rankcert_index()
    specs = {
        row["method"]: row for row in load_specs()
        if row["case"] == args.case and row["ordering"] == args.ordering
        and row["method"] in methods
    }
    if set(specs) != set(methods):
        raise ValueError(f"Missing specs: requested={methods}, found={tuple(specs)}")
    output = RESULTS / f"controller_{args.case}_{args.setting}_{args.ordering}.json"
    rows = []
    for method in methods:
        print(f"[debt controller start] {args.case} {args.ordering} {method}", flush=True)
        rows.append(run_method(
            specs[method],
            frozen[(args.case, args.setting, method, args.ordering)],
            primary_schedule,
            bonds,
            args.shadow_price,
        ))
        atomic_json(output, {
            "stage": "causal_certification_debt_controller",
            "complete": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "rows": rows,
        })
    atomic_json(output, {
        "stage": "causal_certification_debt_controller",
        "complete": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "controller": {
            "candidate_bonds": list(bonds),
            "shadow_price": args.shadow_price,
            "cost": "(bond/max_candidate_bond)^3",
            "objective": "cost + shadow_price * causal_price * sum(local certified tail increments)",
            "tie_break": "smallest bond",
            "uses_dense_exact_errors_for_selection": False,
        },
        "case": args.case,
        "setting": args.setting,
        "ordering": args.ordering,
        "primary_backward_schedule": primary_schedule,
        "rows": rows,
    })
    print(json.dumps({
        row["method"]: {
            "bond_counts": row["bond_counts"],
            "work_vs_R256": row["cubic_work_ratio_vs_fixed_R256"],
            "debt": row["causal_debt"],
            "correction": row["operator_correction_sum"],
        }
        for row in rows
    }, indent=2))


if __name__ == "__main__":
    main()
