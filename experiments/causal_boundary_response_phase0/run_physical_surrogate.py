"""Fit the frozen optimistic one-to-three-atom physical surrogate envelope."""

from __future__ import annotations

import csv
import itertools
import json
import math
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from scipy.linalg import eigh
from scipy.optimize import differential_evolution

from experiments.quantum_safe_kernelization_phase0.qdk_core import independent_masks

from .run_phase0 import OMEGA, OUT, REGIMES, onsite_detunings, response_on_grid


TARGET_K = 13
HORIZONS = (5.0, 10.0, 20.0)
ATOM_BUDGETS = (1, 2, 3)
TRAIN_COUNT = 129
VALIDATION_COUNT = 1023
DETUNING_BOUNDS = (-3.0, 3.0)
PORT_PHASE_BOUNDS = (-3.0, 3.0)
COARSE_MAXITER = 32
COARSE_POPSIZE = 7
REFINE_MAXITER = 110
REFINE_POPSIZE = 11
MASTER_SEED = 20260901


@dataclass(frozen=True)
class Topology:
    atoms: int
    internal_edges: tuple[tuple[int, int], ...]
    port_blocked: tuple[int, ...]
    canonical_code: str


def canonical_code(atoms: int, internal_edges: tuple[tuple[int, int], ...], blocked: tuple[int, ...]) -> str:
    original_edges = {tuple(sorted(edge)) for edge in internal_edges}
    original_blocked = set(blocked)
    codes = []
    for permutation in itertools.permutations(range(atoms)):
        mapped_edges = {
            tuple(sorted((permutation[first], permutation[second]))) for first, second in original_edges
        }
        mapped_blocked = {permutation[node] for node in original_blocked}
        bits = []
        for first in range(atoms):
            bits.append("1" if first in mapped_blocked else "0")
            for second in range(first + 1, atoms):
                bits.append("1" if (first, second) in mapped_edges else "0")
        codes.append("".join(bits))
    return min(codes)


def enumerate_topologies(atoms: int) -> tuple[Topology, ...]:
    possible_edges = tuple(itertools.combinations(range(atoms), 2))
    unique: dict[str, Topology] = {}
    for edge_bits in range(1 << len(possible_edges)):
        edges = tuple(edge for index, edge in enumerate(possible_edges) if edge_bits & (1 << index))
        for blocked_bits in range(1, 1 << atoms):
            blocked = tuple(node for node in range(atoms) if blocked_bits & (1 << node))
            code = canonical_code(atoms, edges, blocked)
            unique.setdefault(code, Topology(atoms, edges, blocked, code))
    return tuple(unique[key] for key in sorted(unique))


def graph_from_topology(topology: Topology) -> nx.Graph:
    graph = nx.Graph()
    graph.add_nodes_from(range(topology.atoms))
    graph.add_edges_from(topology.internal_edges)
    return graph


def hamiltonian(
    topology: Topology, detunings: np.ndarray, port_occupied: bool
) -> tuple[tuple[int, ...], np.ndarray]:
    graph = graph_from_topology(topology)
    masks = independent_masks(graph)
    if port_occupied:
        blocked_mask = sum(1 << node for node in topology.port_blocked)
        masks = tuple(mask for mask in masks if not (mask & blocked_mask))
    index = {mask: position for position, mask in enumerate(masks)}
    matrix = np.zeros((len(masks), len(masks)), dtype=complex)
    for row, mask in enumerate(masks):
        matrix[row, row] = -sum(
            detunings[node] for node in range(topology.atoms) if mask & (1 << node)
        )
        for node in range(topology.atoms):
            col = index.get(mask ^ (1 << node))
            if col is not None:
                matrix[row, col] = -0.5 * OMEGA
    return masks, matrix


def trajectory(matrix: np.ndarray, empty_index: int, times: np.ndarray) -> np.ndarray:
    energies, vectors = eigh(matrix)
    initial_coefficients = np.conjugate(vectors[empty_index, :])
    spectral = np.exp(-1j * np.outer(times, energies)) * initial_coefficients[None, :]
    return spectral @ vectors.T


def surrogate_response(topology: Topology, parameters: np.ndarray, times: np.ndarray) -> np.ndarray:
    detunings = np.asarray(parameters[: topology.atoms], dtype=float)
    port_phase_rate = float(parameters[-1])
    masks0, h0 = hamiltonian(topology, detunings, port_occupied=False)
    masks1, h1 = hamiltonian(topology, detunings, port_occupied=True)
    states0 = trajectory(h0, masks0.index(0), times)
    states1 = trajectory(h1, masks1.index(0), times)
    embedded1 = np.zeros_like(states0)
    index0 = {mask: position for position, mask in enumerate(masks0)}
    for source, mask in enumerate(masks1):
        embedded1[:, index0[mask]] = states1[:, source]
    response = np.sum(np.conjugate(states0) * embedded1, axis=1)
    return response * np.exp(-1j * port_phase_rate * times)


def objective(parameters: np.ndarray, topology: Topology, times: np.ndarray, target: np.ndarray) -> float:
    prediction = surrogate_response(topology, parameters, times)
    return float(np.mean(np.abs(prediction - target) ** 2) / np.mean(np.abs(target) ** 2))


def fit_topology(
    topology: Topology,
    times: np.ndarray,
    target: np.ndarray,
    seed: int,
    maxiter: int,
    popsize: int,
    x0: np.ndarray | None = None,
    detuning_bounds: tuple[float, float] = DETUNING_BOUNDS,
    port_phase_bounds: tuple[float, float] = PORT_PHASE_BOUNDS,
) -> tuple[np.ndarray, float, int]:
    bounds = [detuning_bounds] * topology.atoms + [port_phase_bounds]
    result = differential_evolution(
        objective,
        bounds,
        args=(topology, times, target),
        seed=seed,
        maxiter=maxiter,
        popsize=popsize,
        tol=1e-9,
        polish=True,
        updating="immediate",
        workers=1,
        x0=x0,
    )
    return np.asarray(result.x), float(result.fun), int(result.nfev)


def fit_case(horizon: float, regime: str) -> tuple[list[dict[str, object]], dict[str, object]]:
    train_times = np.linspace(0.0, horizon, TRAIN_COUNT)
    validation_times = np.linspace(0.0, horizon, VALIDATION_COUNT)
    train_target = response_on_grid(TARGET_K, horizon, regime, TRAIN_COUNT)
    validation_target = response_on_grid(TARGET_K, horizon, regime, VALIDATION_COUNT)
    rows: list[dict[str, object]] = []
    best_by_budget: dict[int, tuple[Topology, np.ndarray, float]] = {}

    for atoms in ATOM_BUDGETS:
        screened: list[tuple[float, Topology, np.ndarray, int]] = []
        for topology_index, topology in enumerate(enumerate_topologies(atoms)):
            parameters, loss, evaluations = fit_topology(
                topology,
                train_times,
                train_target,
                seed=MASTER_SEED + 10000 * int(horizon) + 1000 * atoms + 31 * topology_index + (1 if regime == "perturbed" else 0),
                maxiter=COARSE_MAXITER,
                popsize=COARSE_POPSIZE,
            )
            screened.append((loss, topology, parameters, evaluations))
        screened.sort(key=lambda item: item[0])

        refined = []
        for refine_index, (coarse_loss, topology, coarse_parameters, coarse_evaluations) in enumerate(screened[:2]):
            parameters, loss, evaluations = fit_topology(
                topology,
                train_times,
                train_target,
                seed=MASTER_SEED + 20000 * int(horizon) + 2000 * atoms + 101 * refine_index + (1 if regime == "perturbed" else 0),
                maxiter=REFINE_MAXITER,
                popsize=REFINE_POPSIZE,
                x0=coarse_parameters,
            )
            refined.append((loss, topology, parameters, coarse_loss, coarse_evaluations + evaluations))
        refined.sort(key=lambda item: item[0])
        loss, topology, parameters, coarse_loss, evaluations = refined[0]
        prediction = surrogate_response(topology, parameters, validation_times)
        difference = prediction - validation_target
        max_error = float(np.max(np.abs(difference)))
        relative_l2 = float(np.linalg.norm(difference) / np.linalg.norm(validation_target))
        prefix_topology = Topology(
            atoms=atoms,
            internal_edges=tuple((node, node + 1) for node in range(atoms - 1)),
            port_blocked=(0,),
            canonical_code="path_prefix",
        )
        prefix_parameters = np.concatenate((onsite_detunings(atoms, regime), np.asarray([0.0])))
        prefix_prediction = surrogate_response(prefix_topology, prefix_parameters, validation_times)
        prefix_max_error = float(np.max(np.abs(prefix_prediction - validation_target)))
        improvement = prefix_max_error / max(max_error, 1e-15)
        row = {
            "horizon": horizon,
            "regime": regime,
            "atoms": atoms,
            "topology_code": topology.canonical_code,
            "internal_edges": json.dumps(topology.internal_edges),
            "port_blocked": json.dumps(topology.port_blocked),
            "detunings": json.dumps(parameters[:atoms].tolist()),
            "port_phase_rate": float(parameters[-1]),
            "coarse_relative_mse": coarse_loss,
            "train_relative_mse": loss,
            "validation_relative_l2_error": relative_l2,
            "validation_max_error": max_error,
            "prefix_validation_max_error": prefix_max_error,
            "prefix_improvement_factor": improvement,
            "optimizer_evaluations": evaluations,
            "topologies_screened": len(screened),
        }
        rows.append(row)
        best_by_budget[atoms] = (topology, parameters, loss)

    three = next(row for row in rows if row["atoms"] == 3)
    passes = (
        float(three["validation_max_error"]) <= 0.02
        and float(three["validation_relative_l2_error"]) <= 0.01
        and float(three["prefix_improvement_factor"]) >= 5.0
    )
    decision = {
        "horizon": horizon,
        "regime": regime,
        "three_atom_max_error": three["validation_max_error"],
        "three_atom_relative_l2_error": three["validation_relative_l2_error"],
        "three_atom_prefix_improvement": three["prefix_improvement_factor"],
        "case_passes": passes,
    }
    return rows, decision


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    decisions: list[dict[str, object]] = []
    for horizon in HORIZONS:
        for regime in REGIMES:
            case_rows, decision = fit_case(horizon, regime)
            rows.extend(case_rows)
            decisions.append(decision)
            print(json.dumps(decision, sort_keys=True), flush=True)

    for horizon in HORIZONS:
        pair = [row for row in decisions if row["horizon"] == horizon]
        horizon_passes = len(pair) == len(REGIMES) and all(bool(row["case_passes"]) for row in pair)
        for row in pair:
            row["horizon_passes_both_controls"] = horizon_passes
    survives = any(bool(row["horizon_passes_both_controls"]) for row in decisions)
    summary = {
        "topology_counts": {str(atoms): len(enumerate_topologies(atoms)) for atoms in ATOM_BUDGETS},
        "decisions": decisions,
        "physical_synthesis_survives": survives,
        "verdict": "ADVANCE_TO_AQUILA_PROJECTION" if survives else "FALSIFIED_IN_OPTIMISTIC_PHYSICAL_ENVELOPE",
    }

    with (OUT / "physical_surrogate_fits.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (OUT / "physical_surrogate_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )

    figure, axes = plt.subplots(1, 2, figsize=(10.2, 4.2))
    for regime, marker in (("uniform", "o"), ("perturbed", "s")):
        subset = [row for row in rows if row["regime"] == regime and row["atoms"] == 3]
        axes[0].plot(
            [row["horizon"] for row in subset],
            [row["validation_max_error"] for row in subset],
            marker=marker,
            label=regime,
        )
        axes[1].plot(
            [row["horizon"] for row in subset],
            [row["prefix_improvement_factor"] for row in subset],
            marker=marker,
            label=regime,
        )
    axes[0].axhline(0.02, color="black", linestyle="--", alpha=0.5)
    axes[1].axhline(5.0, color="black", linestyle="--", alpha=0.5)
    axes[0].set_ylabel("held-out maximum complex error")
    axes[1].set_ylabel("improvement over 3-atom prefix")
    for axis in axes:
        axis.set_xlabel("horizon T")
        axis.legend()
    figure.suptitle("Optimistic physical-surrogate synthesis gate")
    figure.tight_layout()
    figure.savefig(OUT / "physical_surrogate_gate.png", dpi=180)
    plt.close(figure)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
