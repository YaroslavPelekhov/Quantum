"""Local decision-optimal Schmidt-subset kill-test on frozen ibm32 data."""

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

from cot_core import terminal_basis_vectors
from rankcert_inputs import SETTINGS, atomic_json, load_specs
import run_independent_ladder_audit as frozen_audit
from run_observable_telescope import bks_basis_indices, checkpoint_counts, normalize_copy
from run_observable_telescope_18q import run_segment
from audit_forward_groups import exact_evolve_segment
from run_backward_feasibility import apply_inverse_segment


RESULTS = REPO / "results" / "dot_mps_kill_test"
PRIMARY_POSITION = 502
PRIMARY_CUT = 11
PRIMARY_CHI = 40
RANKS = (8, 16, 32, 40, 64)
RANDOM_SEEDS = tuple(range(24))


def exact_backward_vectors(spec: dict, circuit, counts: list[int], position: int) -> np.ndarray:
    vectors = terminal_basis_vectors(circuit.num_qubits, bks_basis_indices(spec["scorer"]))
    for current in range(len(counts) - 2, position - 1, -1):
        vectors = apply_inverse_segment(
            vectors, circuit, counts[current], counts[current + 1]
        )
    return vectors


def schmidt_observable_data(
    state: np.ndarray, backward: np.ndarray, cut: int
) -> tuple[np.ndarray, np.ndarray, dict]:
    left = 1 << cut
    matrix = state.reshape(left, -1, order="F")
    u, singular, vh = np.linalg.svd(matrix, full_matrices=False)
    active = singular > 1e-14
    singular = singular[active]
    u = u[:, active]
    vh = vh[active, :]
    amplitudes = []
    for column in range(backward.shape[1]):
        observable_vector = backward[:, column].reshape(left, -1, order="F")
        projected = u.conj().T @ observable_vector
        overlaps = np.sum(projected * np.conj(vh), axis=1)
        amplitudes.append(singular * overlaps)
    amplitudes = np.asarray(amplitudes)
    reconstruction = (u * singular[None, :]) @ vh
    reconstruction_error = float(np.linalg.norm(matrix - reconstruction))
    direct_value = float(np.sum(np.abs(backward.conj().T @ state) ** 2))
    schmidt_value = float(np.sum(np.abs(np.sum(amplitudes, axis=1)) ** 2))
    if abs(direct_value - schmidt_value) > 2e-10:
        raise AssertionError((direct_value, schmidt_value))
    return singular, amplitudes, {
        "exact_bks_value": direct_value,
        "schmidt_rank": int(singular.size),
        "schmidt_reconstruction_error": reconstruction_error,
    }


def subset_metrics(
    singular: np.ndarray,
    amplitudes: np.ndarray,
    indices: np.ndarray,
    target: float,
) -> dict:
    mass = float(np.sum(np.square(singular[indices])))
    summed = np.sum(amplitudes[:, indices], axis=1)
    value = float(np.sum(np.abs(summed) ** 2) / mass)
    return {
        "bks_value": value,
        "absolute_bks_error": abs(value - target),
        "state_fidelity": mass,
        "discarded_mass": 1.0 - mass,
        "indices": [int(index) for index in np.sort(indices)],
    }


def local_swap_search(
    singular: np.ndarray,
    amplitudes: np.ndarray,
    initial: np.ndarray,
    target: float,
    max_iterations: int = 256,
) -> tuple[dict, int]:
    rank = singular.size
    selected = np.zeros(rank, dtype=bool)
    selected[initial] = True
    mass_terms = np.square(singular)
    mass = float(np.sum(mass_terms[selected]))
    summed = np.sum(amplitudes[:, selected], axis=1)

    def objective(current_mass: float, current_sum: np.ndarray) -> float:
        return abs(float(np.sum(np.abs(current_sum) ** 2) / current_mass) - target)

    current_objective = objective(mass, summed)
    iterations = 0
    for iterations in range(1, max_iterations + 1):
        inside = np.flatnonzero(selected)
        outside = np.flatnonzero(~selected)
        best = None
        best_objective = current_objective
        for removed in inside:
            candidate_mass = mass - mass_terms[removed] + mass_terms[outside]
            candidate_sum = (
                summed[:, None]
                - amplitudes[:, removed, None]
                + amplitudes[:, outside]
            )
            candidate_values = np.sum(np.abs(candidate_sum) ** 2, axis=0) / candidate_mass
            candidate_objectives = np.abs(candidate_values - target)
            location = int(np.argmin(candidate_objectives))
            value = float(candidate_objectives[location])
            if value < best_objective - 1e-16:
                best_objective = value
                best = (removed, int(outside[location]), float(candidate_mass[location]), candidate_sum[:, location])
        if best is None:
            iterations -= 1
            break
        removed, added, mass, summed = best
        selected[removed] = False
        selected[added] = True
        current_objective = best_objective
    return subset_metrics(singular, amplitudes, np.flatnonzero(selected), target), iterations


def deterministic_starts(
    singular: np.ndarray, amplitudes: np.ndarray, chi: int
) -> list[tuple[str, np.ndarray]]:
    rank = singular.size
    starts = [("top_schmidt", np.arange(chi, dtype=int))]
    individual = np.sum(np.abs(amplitudes) ** 2, axis=0)
    coherent = np.abs(np.sum(amplitudes, axis=0))
    starts.append(("top_individual_observable", np.argsort(individual)[-chi:]))
    starts.append(("top_coherent_amplitude", np.argsort(coherent)[-chi:]))
    weights = np.square(singular)
    weights /= np.sum(weights)
    for seed in RANDOM_SEEDS:
        rng = np.random.default_rng(seed)
        starts.append((f"weighted_random_{seed}", rng.choice(rank, chi, replace=False, p=weights)))
    return starts


def run_rank(singular: np.ndarray, amplitudes: np.ndarray, chi: int, target: float) -> dict:
    if chi >= singular.size:
        raise ValueError("chi must be smaller than the exact Schmidt rank")
    standard = subset_metrics(singular, amplitudes, np.arange(chi), target)
    trials = []
    for name, initial in deterministic_starts(singular, amplitudes, chi):
        result, iterations = local_swap_search(singular, amplitudes, initial, target)
        trials.append({"start": name, "iterations": iterations, **result})
    best = min(trials, key=lambda row: (row["absolute_bks_error"], row["state_fidelity"]))
    standard_set = set(standard["indices"])
    best_set = set(best["indices"])
    return {
        "chi": chi,
        "standard_top_schmidt": standard,
        "goal_aware_subset": best,
        "bks_error_improvement_factor": (
            standard["absolute_bks_error"] / best["absolute_bks_error"]
            if best["absolute_bks_error"] > 0 else None
        ),
        "goal_aware_fidelity_minus_standard": best["state_fidelity"] - standard["state_fidelity"],
        "selected_mode_overlap": len(standard_set & best_set),
        "all_starts": trials,
    }


def mode_diagnostics(singular: np.ndarray, amplitudes: np.ndarray, target: float) -> dict:
    from scipy.stats import spearmanr

    mass = np.square(singular)
    full_sum = np.sum(amplitudes, axis=1)
    leave_one_values = []
    for index in range(singular.size):
        remaining_mass = 1.0 - mass[index]
        remaining_sum = full_sum - amplitudes[:, index]
        leave_one_values.append(float(np.sum(np.abs(remaining_sum) ** 2) / remaining_mass))
    decision_importance = np.abs(np.asarray(leave_one_values) - target)
    correlation = spearmanr(mass, decision_importance)
    return {
        "schmidt_mass_vs_leave_one_decision_importance_spearman": float(correlation.statistic),
        "spearman_pvalue": float(correlation.pvalue),
        "top_mass_indices": [int(value) for value in np.argsort(mass)[-20:][::-1]],
        "top_decision_importance_indices": [
            int(value) for value in np.argsort(decision_importance)[-20:][::-1]
        ],
        "modes": [{
            "index": index,
            "singular_value": float(singular[index]),
            "schmidt_mass": float(mass[index]),
            "leave_one_bks_error": float(decision_importance[index]),
            "observable_amplitude_norm": float(np.linalg.norm(amplitudes[:, index])),
        } for index in range(singular.size)],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--position", type=int, default=PRIMARY_POSITION)
    parser.add_argument("--cut", type=int, default=PRIMARY_CUT)
    parser.add_argument("--ranks", default=",".join(str(value) for value in RANKS))
    args = parser.parse_args()
    ranks = [int(value) for value in args.ranks.split(",")]
    setting = next(item for item in SETTINGS if item["name"] == "confirm")
    spec = next(
        row for row in load_specs()
        if row["case"] == "ibm32" and row["method"] == "published_lr"
        and row["ordering"] == "sorted"
    )
    circuit = frozen_audit.load_circuit(Path(spec["circuit_file"]))
    counts = checkpoint_counts(circuit)
    if not 1 <= args.position < len(counts):
        raise ValueError(args.position)
    started = perf_counter()
    data, labels = run_segment(
        circuit,
        0,
        counts[args.position],
        setting,
        dense_counts=[counts[args.position - 1], counts[args.position]],
    )
    previous = normalize_copy(data[labels[counts[args.position - 1]]])
    actual_post = normalize_copy(data[labels[counts[args.position]]])
    pre_truncation = exact_evolve_segment(
        previous, circuit, counts[args.position - 1], counts[args.position]
    )
    backward = exact_backward_vectors(spec, circuit, counts, args.position)
    singular, amplitudes, audit = schmidt_observable_data(
        pre_truncation, backward, args.cut
    )
    target = audit["exact_bks_value"]
    actual_post_bks = float(np.sum(np.abs(backward.conj().T @ actual_post) ** 2))
    rows = [run_rank(singular, amplitudes, chi, target) for chi in ranks]
    primary = next(row for row in rows if row["chi"] == PRIMARY_CHI)
    is_protocol_primary = args.position == PRIMARY_POSITION and args.cut == PRIMARY_CUT
    payload = {
        "stage": "dot_mps_local_kill_test",
        "complete": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "protocol": "experiments/compressed_observable_telescope/DOT_KILL_TEST_PROTOCOL.md",
        "case": "ibm32",
        "setting": "confirm",
        "method": "published_lr",
        "ordering": "sorted",
        "checkpoint_position": args.position,
        "prior_operation_count": counts[args.position - 1],
        "operation_count": counts[args.position],
        "cut": args.cut,
        "protocol_primary_configuration": is_protocol_primary,
        "left_qubits": list(range(args.cut)),
        "right_qubits": list(range(args.cut, circuit.num_qubits)),
        "exact_pre_truncation_bks": target,
        "actual_aer_post_checkpoint_bks": actual_post_bks,
        "actual_aer_local_bks_error": abs(actual_post_bks - target),
        "audit": audit,
        "mode_diagnostics": mode_diagnostics(singular, amplitudes, target),
        "rank_rows": rows,
        "primary_chi": PRIMARY_CHI,
        "primary_success_criterion": "goal-aware absolute BKS error <= standard error / 10",
        "primary_success": (
            primary["goal_aware_subset"]["absolute_bks_error"]
            <= primary["standard_top_schmidt"]["absolute_bks_error"] / 10
        ),
        "primary_worse_fidelity_better_answer": (
            primary["goal_aware_subset"]["state_fidelity"]
            < primary["standard_top_schmidt"]["state_fidelity"]
            and primary["goal_aware_subset"]["absolute_bks_error"]
            < primary["standard_top_schmidt"]["absolute_bks_error"]
        ),
        "runtime_seconds": perf_counter() - started,
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    output = RESULTS / f"ibm32_confirm_sorted_lr_position{args.position}_cut{args.cut}.json"
    atomic_json(output, payload)
    print(json.dumps({
        "primary_success": payload["primary_success"],
        "primary_worse_fidelity_better_answer": payload["primary_worse_fidelity_better_answer"],
        "exact_bks": target,
        "actual_aer_local_bks_error": payload["actual_aer_local_bks_error"],
        "spearman": payload["mode_diagnostics"]["schmidt_mass_vs_leave_one_decision_importance_spearman"],
        "rank_rows": [{
            "chi": row["chi"],
            "svd_error": row["standard_top_schmidt"]["absolute_bks_error"],
            "dot_error": row["goal_aware_subset"]["absolute_bks_error"],
            "improvement": row["bks_error_improvement_factor"],
            "svd_fidelity": row["standard_top_schmidt"]["state_fidelity"],
            "dot_fidelity": row["goal_aware_subset"]["state_fidelity"],
            "overlap": row["selected_mode_overlap"],
        } for row in rows],
    }, indent=2))
    del data, previous, actual_post, pre_truncation, backward
    gc.collect()


if __name__ == "__main__":
    main()
