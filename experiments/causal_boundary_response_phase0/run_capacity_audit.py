"""Deep optimizer restart and four-atom capacity audit at the frozen near miss."""

from __future__ import annotations

import csv
import json

import numpy as np

from .run_phase0 import OUT, REGIMES, onsite_detunings, response_on_grid
from .run_physical_surrogate import (
    Topology,
    enumerate_topologies,
    fit_topology,
    surrogate_response,
)


HORIZON = 5.0
TARGET_K = 13
TRAIN_COUNT = 129
SCREEN_COUNT = 65
VALIDATION_COUNT = 1023
EXPANDED_BOUNDS = (-6.0, 6.0)
MASTER_SEED = 20260902


def prefix_topology(atoms: int) -> Topology:
    return Topology(
        atoms=atoms,
        internal_edges=tuple((node, node + 1) for node in range(atoms - 1)),
        port_blocked=(0,),
        canonical_code="path_prefix",
    )


def audit_budget(atoms: int, regime: str) -> tuple[dict[str, object], list[dict[str, object]]]:
    screen_times = np.linspace(0.0, HORIZON, SCREEN_COUNT)
    train_times = np.linspace(0.0, HORIZON, TRAIN_COUNT)
    validation_times = np.linspace(0.0, HORIZON, VALIDATION_COUNT)
    screen_target = response_on_grid(TARGET_K, HORIZON, regime, SCREEN_COUNT)
    train_target = response_on_grid(TARGET_K, HORIZON, regime, TRAIN_COUNT)
    validation_target = response_on_grid(TARGET_K, HORIZON, regime, VALIDATION_COUNT)
    topologies = enumerate_topologies(atoms)
    screen_rows: list[tuple[float, Topology, np.ndarray, int]] = []
    screen_maxiter = 70 if atoms == 3 else 42
    screen_popsize = 10 if atoms == 3 else 8

    for index, topology in enumerate(topologies):
        parameters, loss, evaluations = fit_topology(
            topology,
            screen_times,
            screen_target,
            seed=MASTER_SEED + 1000 * atoms + 29 * index + (1 if regime == "perturbed" else 0),
            maxiter=screen_maxiter,
            popsize=screen_popsize,
            detuning_bounds=EXPANDED_BOUNDS,
            port_phase_bounds=EXPANDED_BOUNDS,
        )
        screen_rows.append((loss, topology, parameters, evaluations))
    screen_rows.sort(key=lambda item: item[0])

    retain = 4 if atoms == 3 else 5
    restarts = 4 if atoms == 3 else 3
    refine_rows: list[dict[str, object]] = []
    for candidate_index, (screen_loss, topology, screen_parameters, screen_evaluations) in enumerate(
        screen_rows[:retain]
    ):
        for restart in range(restarts):
            parameters, loss, evaluations = fit_topology(
                topology,
                train_times,
                train_target,
                seed=(
                    MASTER_SEED
                    + 100000 * atoms
                    + 1000 * candidate_index
                    + 43 * restart
                    + (1 if regime == "perturbed" else 0)
                ),
                maxiter=240 if atoms == 3 else 190,
                popsize=18 if atoms == 3 else 14,
                x0=screen_parameters,
                detuning_bounds=EXPANDED_BOUNDS,
                port_phase_bounds=EXPANDED_BOUNDS,
            )
            prediction = surrogate_response(topology, parameters, validation_times)
            difference = prediction - validation_target
            refine_rows.append(
                {
                    "regime": regime,
                    "atoms": atoms,
                    "candidate_index": candidate_index,
                    "restart": restart,
                    "topology_code": topology.canonical_code,
                    "internal_edges": json.dumps(topology.internal_edges),
                    "port_blocked": json.dumps(topology.port_blocked),
                    "parameters": json.dumps(parameters.tolist()),
                    "screen_relative_mse": screen_loss,
                    "train_relative_mse": loss,
                    "validation_relative_l2_error": float(
                        np.linalg.norm(difference) / np.linalg.norm(validation_target)
                    ),
                    "validation_max_error": float(np.max(np.abs(difference))),
                    "optimizer_evaluations": screen_evaluations + evaluations,
                }
            )
    refine_rows.sort(key=lambda row: float(row["train_relative_mse"]))
    best = refine_rows[0]
    prefix_parameters = np.concatenate((onsite_detunings(atoms, regime), np.asarray([0.0])))
    prefix = surrogate_response(prefix_topology(atoms), prefix_parameters, validation_times)
    prefix_error = float(np.max(np.abs(prefix - validation_target)))
    improvement = prefix_error / max(float(best["validation_max_error"]), 1e-15)
    passes = (
        float(best["validation_max_error"]) <= 0.02
        and float(best["validation_relative_l2_error"]) <= 0.01
        and improvement >= 5.0
    )
    decision = {
        "horizon": HORIZON,
        "regime": regime,
        "atoms": atoms,
        "topologies_screened": len(topologies),
        "refined_runs": len(refine_rows),
        "best_topology_code": best["topology_code"],
        "best_parameters": best["parameters"],
        "validation_max_error": best["validation_max_error"],
        "validation_relative_l2_error": best["validation_relative_l2_error"],
        "same_budget_prefix_max_error": prefix_error,
        "prefix_improvement_factor": improvement,
        "case_passes": passes,
    }
    return decision, refine_rows


def main() -> None:
    decisions: list[dict[str, object]] = []
    all_refines: list[dict[str, object]] = []
    for regime in REGIMES:
        for atoms in (3, 4):
            decision, refines = audit_budget(atoms, regime)
            decisions.append(decision)
            all_refines.extend(refines)
            print(json.dumps(decision, sort_keys=True), flush=True)

    three_atom_recovers = all(
        bool(row["case_passes"]) for row in decisions if int(row["atoms"]) == 3
    )
    four_atom_survives = all(
        bool(row["case_passes"]) for row in decisions if int(row["atoms"]) == 4
    )
    summary = {
        "decisions": decisions,
        "three_atom_optimizer_recovery": three_atom_recovers,
        "four_atom_capacity_survives": four_atom_survives,
        "static_branch_survives": three_atom_recovers or four_atom_survives,
        "verdict": (
            "ADVANCE_TO_AQUILA_PROJECTION"
            if three_atom_recovers or four_atom_survives
            else "STATIC_PHYSICAL_REALIZATION_GAP_CONFIRMED"
        ),
    }
    with (OUT / "capacity_audit_refines.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(all_refines[0]))
        writer.writeheader()
        writer.writerows(all_refines)
    (OUT / "capacity_audit_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
