"""Final multi-switch boundary influence-Gram falsification."""

from __future__ import annotations

import csv
import itertools
import json

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from scipy.linalg import eigh

from .run_host_transfer import load_surrogate
from .run_phase0 import MEAN_DELTA, OUT, REGIMES, conditional_hamiltonian, onsite_detunings
from .run_physical_surrogate import Topology, hamiltonian as topology_hamiltonian


TARGET_K = 13
HORIZON = 5.0
WORD_LENGTHS = tuple(range(1, 7))


SPECTRAL_CACHE: dict[int, tuple[np.ndarray, np.ndarray]] = {}


def apply_batch(matrix: np.ndarray, states: np.ndarray, duration: float) -> np.ndarray:
    key = id(matrix)
    if key not in SPECTRAL_CACHE:
        SPECTRAL_CACHE[key] = eigh(matrix)
    energies, vectors = SPECTRAL_CACHE[key]
    coefficients = states @ np.conjugate(vectors)
    coefficients *= np.exp(-1j * energies * duration)[None, :]
    return coefficients @ vectors.T


def word_gram(
    masks0: tuple[int, ...],
    h0: np.ndarray,
    masks1: tuple[int, ...],
    h1: np.ndarray,
    word_length: int,
    port_phase_rate: float = 0.0,
) -> np.ndarray:
    durations = (HORIZON / word_length,) * word_length
    return word_gram_durations(masks0, h0, masks1, h1, durations, port_phase_rate)


def word_gram_durations(
    masks0: tuple[int, ...],
    h0: np.ndarray,
    masks1: tuple[int, ...],
    h1: np.ndarray,
    durations: tuple[float, ...],
    port_phase_rate: float = 0.0,
) -> np.ndarray:
    index0 = {mask: position for position, mask in enumerate(masks0)}
    allowed = np.asarray([index0[mask] for mask in masks1], dtype=int)
    words = tuple(itertools.product((0, 1), repeat=len(durations)))
    states = np.zeros((len(words), len(masks0)), dtype=complex)
    states[:, index0[0]] = 1.0
    occupied_times = np.zeros(len(words), dtype=float)
    for segment, duration in enumerate(durations):
        zero_rows = np.asarray([index for index, word in enumerate(words) if word[segment] == 0], dtype=int)
        one_rows = np.asarray([index for index, word in enumerate(words) if word[segment] == 1], dtype=int)
        states[zero_rows] = apply_batch(h0, states[zero_rows], duration)
        projected = apply_batch(h1, states[np.ix_(one_rows, allowed)], duration)
        states[one_rows] = 0.0
        states[np.ix_(one_rows, allowed)] = projected
        occupied_times[one_rows] += duration
    states *= np.exp(-1j * port_phase_rate * occupied_times)[:, None]
    return np.conjugate(states) @ states.T


def target_system(regime: str) -> tuple[tuple[int, ...], np.ndarray, tuple[int, ...], np.ndarray]:
    masks0, h0 = conditional_hamiltonian(TARGET_K, regime, False)
    masks1, h1 = conditional_hamiltonian(TARGET_K, regime, True)
    return masks0, h0.toarray(), masks1, h1.toarray()


def prefix_system(regime: str) -> tuple[tuple[int, ...], np.ndarray, tuple[int, ...], np.ndarray]:
    topology = Topology(
        atoms=4,
        internal_edges=((0, 1), (1, 2), (2, 3)),
        port_blocked=(0,),
        canonical_code="path_prefix",
    )
    detunings = onsite_detunings(4, regime)
    masks0, h0 = topology_hamiltonian(topology, detunings, False)
    masks1, h1 = topology_hamiltonian(topology, detunings, True)
    return masks0, h0, masks1, h1


def surrogate_system(regime: str) -> tuple[tuple[int, ...], np.ndarray, tuple[int, ...], np.ndarray, float]:
    internal_edges, port_blocked, fields, port_phase_rate = load_surrogate(regime)
    topology = Topology(4, internal_edges, port_blocked, "frozen_surrogate")
    masks0, h0 = topology_hamiltonian(topology, fields, False)
    masks1, h1 = topology_hamiltonian(topology, fields, True)
    return masks0, h0, masks1, h1, port_phase_rate


def main() -> None:
    rows: list[dict[str, object]] = []
    split_rows: list[dict[str, object]] = []
    matrix_artifacts: dict[str, np.ndarray] = {}
    for regime in REGIMES:
        SPECTRAL_CACHE.clear()
        target = target_system(regime)
        prefix = prefix_system(regime)
        surrogate_parts = surrogate_system(regime)
        surrogate = surrogate_parts[:4]
        phase_rate = surrogate_parts[4]
        for word_length in WORD_LENGTHS:
            target_gram = word_gram(*target, word_length)
            prefix_gram = word_gram(*prefix, word_length)
            surrogate_gram = word_gram(*surrogate, word_length, port_phase_rate=phase_rate)
            prefix_difference = prefix_gram - target_gram
            surrogate_difference = surrogate_gram - target_gram
            prefix_max = float(np.max(np.abs(prefix_difference)))
            surrogate_max = float(np.max(np.abs(surrogate_difference)))
            target_norm = float(np.linalg.norm(target_gram))
            prefix_relative = float(np.linalg.norm(prefix_difference) / target_norm)
            surrogate_relative = float(np.linalg.norm(surrogate_difference) / target_norm)
            row = {
                "regime": regime,
                "word_length": word_length,
                "history_count": 2**word_length,
                "surrogate_max_gram_error": surrogate_max,
                "prefix_max_gram_error": prefix_max,
                "max_error_improvement": prefix_max / max(surrogate_max, 1e-15),
                "surrogate_relative_frobenius_error": surrogate_relative,
                "prefix_relative_frobenius_error": prefix_relative,
                "frobenius_improvement": prefix_relative / max(surrogate_relative, 1e-15),
            }
            row["case_passes"] = word_length == 1 or (
                surrogate_max <= 0.02 and float(row["max_error_improvement"]) >= 5.0
            )
            rows.append(row)
            matrix_artifacts[f"{regime}_K{word_length}_target"] = target_gram
            matrix_artifacts[f"{regime}_K{word_length}_surrogate"] = surrogate_gram
            matrix_artifacts[f"{regime}_K{word_length}_prefix"] = prefix_gram

        for tau in np.linspace(0.05, 4.95, 99):
            durations = (float(tau), float(HORIZON - tau))
            target_gram = word_gram_durations(*target, durations)
            prefix_gram = word_gram_durations(*prefix, durations)
            surrogate_gram = word_gram_durations(*surrogate, durations, port_phase_rate=phase_rate)
            prefix_difference = prefix_gram - target_gram
            surrogate_difference = surrogate_gram - target_gram
            prefix_max = float(np.max(np.abs(prefix_difference)))
            surrogate_max = float(np.max(np.abs(surrogate_difference)))
            target_norm = float(np.linalg.norm(target_gram))
            prefix_relative = float(np.linalg.norm(prefix_difference) / target_norm)
            surrogate_relative = float(np.linalg.norm(surrogate_difference) / target_norm)
            split_rows.append(
                {
                    "regime": regime,
                    "tau": float(tau),
                    "surrogate_max_gram_error": surrogate_max,
                    "prefix_max_gram_error": prefix_max,
                    "max_error_improvement": prefix_max / max(surrogate_max, 1e-15),
                    "surrogate_relative_frobenius_error": surrogate_relative,
                    "prefix_relative_frobenius_error": prefix_relative,
                    "frobenius_improvement": prefix_relative / max(surrogate_relative, 1e-15),
                    "case_passes": (
                        surrogate_max <= 0.02 and prefix_max / max(surrogate_max, 1e-15) >= 5.0
                    ),
                }
            )

    decisions = []
    for regime in REGIMES:
        subset = [row for row in rows if row["regime"] == regime and int(row["word_length"]) >= 2]
        split_subset = [row for row in split_rows if row["regime"] == regime]
        worst_split = max(split_subset, key=lambda row: float(row["surrogate_max_gram_error"]))
        decisions.append(
            {
                "regime": regime,
                "all_multiswitch_cases_pass": all(bool(row["case_passes"]) for row in subset),
                "all_two_bin_splits_pass": all(bool(row["case_passes"]) for row in split_subset),
                "worst_surrogate_max_gram_error": max(float(row["surrogate_max_gram_error"]) for row in subset),
                "minimum_max_error_improvement": min(float(row["max_error_improvement"]) for row in subset),
                "worst_split_tau": worst_split["tau"],
                "worst_split_max_gram_error": worst_split["surrogate_max_gram_error"],
                "worst_split_improvement": worst_split["max_error_improvement"],
            }
        )
    survives = all(
        bool(row["all_multiswitch_cases_pass"]) and bool(row["all_two_bin_splits_pass"])
        for row in decisions
    )
    summary = {
        "decisions": decisions,
        "process_gram_survives": survives,
        "verdict": "ADVANCE_TO_HARDWARE" if survives else "FALSIFIED_BY_CONTROLLED_BOUNDARY_HISTORIES",
    }
    with (OUT / "process_gram.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with (OUT / "process_split_scan.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(split_rows[0]))
        writer.writeheader()
        writer.writerows(split_rows)
    np.savez_compressed(OUT / "process_gram_matrices.npz", **matrix_artifacts)
    (OUT / "process_gram_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )

    figure, axes = plt.subplots(1, 2, figsize=(10.2, 4.2), sharex=True)
    for regime, marker in (("uniform", "o"), ("perturbed", "s")):
        subset = [row for row in rows if row["regime"] == regime]
        axes[0].plot(
            [row["word_length"] for row in subset],
            [row["surrogate_max_gram_error"] for row in subset],
            marker=marker,
            label=regime,
        )
        axes[1].plot(
            [row["word_length"] for row in subset],
            [row["max_error_improvement"] for row in subset],
            marker=marker,
            label=regime,
        )
    axes[0].axhline(0.02, color="black", linestyle="--", alpha=0.5)
    axes[1].axhline(5.0, color="black", linestyle="--", alpha=0.5)
    axes[0].set_ylabel("maximum Gram-entry error")
    axes[1].set_ylabel("improvement over inherited prefix")
    axes[1].set_yscale("log")
    for axis in axes:
        axis.set_xlabel("binary-history length K")
        axis.legend()
    figure.suptitle("Controlled boundary-process falsification")
    figure.tight_layout()
    figure.savefig(OUT / "process_gram_gate.png", dpi=180)
    plt.close(figure)
    print(json.dumps({"summary": summary, "rows": rows}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
