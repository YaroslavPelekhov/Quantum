"""Run the frozen causal boundary-response rank gate.

The diagnostic is the port-coherence influence of an endpoint-attached path.
The port's two logical states induce two conditional motif Hamiltonians: H0
allows the attachment atom to participate, while H1 blockades it.  A surrogate
that preserves the port channel for arbitrary hosts must reproduce the
resulting conditional Loschmidt amplitude.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from functools import lru_cache
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from scipy.linalg import eigh, hankel, svdvals
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import expm_multiply

from experiments.quantum_safe_kernelization_phase0.qdk_core import independent_masks


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "causal_boundary_response_phase0"

K_VALUES = tuple(range(3, 14))
HORIZONS = (2.0, 5.0, 10.0, 20.0)
REGIMES = ("uniform", "perturbed")
OMEGA = 1.0
MEAN_DELTA = 0.37
PERTURBATION = 0.03
HANKEL_SIZE = 256
SAMPLE_COUNT = 2 * HANKEL_SIZE - 1
EFFECTIVE_TOLERANCES = (0.01, 0.05)
COEFFICIENT_THRESHOLDS = (1e-8, 1e-10, 1e-12)
FREQUENCY_CLUSTER_TOLERANCE = 1e-9
PREFIX_BUDGETS = (1, 2, 3)
RANK_BUDGET_THREE_ATOMS = 4**3
RNG_SEED = 20260831


def path_graph(k: int) -> nx.Graph:
    return nx.path_graph(k)


def frozen_detuning_pattern() -> np.ndarray:
    rng = np.random.default_rng(RNG_SEED)
    pattern = rng.normal(size=max(K_VALUES))
    pattern -= np.mean(pattern)
    pattern /= np.max(np.abs(pattern))
    return pattern


DETUNING_PATTERN = frozen_detuning_pattern()


def onsite_detunings(k: int, regime: str) -> np.ndarray:
    if regime == "uniform":
        return np.full(k, MEAN_DELTA, dtype=float)
    if regime == "perturbed":
        return MEAN_DELTA + PERTURBATION * DETUNING_PATTERN[:k]
    raise ValueError(f"unknown regime: {regime}")


def conditional_basis(k: int, port_occupied: bool) -> tuple[int, ...]:
    masks = independent_masks(path_graph(k))
    if port_occupied:
        masks = tuple(mask for mask in masks if not (mask & 1))
    return masks


def conditional_hamiltonian(k: int, regime: str, port_occupied: bool) -> tuple[tuple[int, ...], csr_matrix]:
    masks = conditional_basis(k, port_occupied)
    index = {mask: i for i, mask in enumerate(masks)}
    detunings = onsite_detunings(k, regime)
    rows: list[int] = []
    cols: list[int] = []
    data: list[complex] = []

    for row, mask in enumerate(masks):
        diagonal = -sum(detunings[bit] for bit in range(k) if mask & (1 << bit))
        rows.append(row)
        cols.append(row)
        data.append(complex(diagonal))
        for bit in range(k):
            flipped = mask ^ (1 << bit)
            col = index.get(flipped)
            if col is not None and row < col:
                rows.extend((row, col))
                cols.extend((col, row))
                data.extend((-0.5 * OMEGA, -0.5 * OMEGA))

    matrix = csr_matrix((data, (rows, cols)), shape=(len(masks), len(masks)), dtype=complex)
    return masks, matrix


@lru_cache(maxsize=None)
def response_samples(k: int, horizon: float, regime: str) -> tuple[complex, ...]:
    return tuple(complex(value) for value in response_on_grid(k, horizon, regime, SAMPLE_COUNT))


def response_on_grid(k: int, horizon: float, regime: str, sample_count: int) -> np.ndarray:
    masks0, h0 = conditional_hamiltonian(k, regime, port_occupied=False)
    masks1, h1 = conditional_hamiltonian(k, regime, port_occupied=True)
    initial0 = np.zeros(len(masks0), dtype=complex)
    initial1 = np.zeros(len(masks1), dtype=complex)
    initial0[masks0.index(0)] = 1.0
    initial1[masks1.index(0)] = 1.0
    times0 = expm_multiply(-1j * h0, initial0, start=0.0, stop=horizon, num=sample_count, endpoint=True)
    times1 = expm_multiply(-1j * h1, initial1, start=0.0, stop=horizon, num=sample_count, endpoint=True)
    index0 = {mask: i for i, mask in enumerate(masks0)}
    embedded1 = np.zeros_like(times0)
    for source, mask in enumerate(masks1):
        embedded1[:, index0[mask]] = times1[:, source]
    response = np.sum(np.conjugate(times0) * embedded1, axis=1)
    return response


def response_hankel(response: np.ndarray) -> np.ndarray:
    if len(response) != SAMPLE_COUNT:
        raise ValueError(f"expected {SAMPLE_COUNT} samples")
    return hankel(response[:HANKEL_SIZE], response[HANKEL_SIZE - 1 :])


def relative_tail(singular_values: np.ndarray, rank: int) -> float:
    norm = float(np.linalg.norm(singular_values))
    if norm == 0.0:
        return 0.0
    return float(np.linalg.norm(singular_values[rank:]) / norm)


def effective_rank(singular_values: np.ndarray, tolerance: float) -> int:
    for rank in range(len(singular_values) + 1):
        if relative_tail(singular_values, rank) <= tolerance:
            return rank
    return len(singular_values)


def atom_lower_bound(rank: int) -> int:
    if rank <= 1:
        return 0
    return int(math.ceil(math.log(rank, 4.0) - 1e-12))


def resolved_spectrum(k: int, regime: str, coefficient_threshold: float) -> dict[str, float | int]:
    masks0, h0 = conditional_hamiltonian(k, regime, port_occupied=False)
    masks1, h1 = conditional_hamiltonian(k, regime, port_occupied=True)
    energies0, vectors0 = eigh(h0.toarray())
    energies1, vectors1 = eigh(h1.toarray())

    embedded1 = np.zeros((len(masks0), len(masks1)), dtype=complex)
    index0 = {mask: i for i, mask in enumerate(masks0)}
    for row1, mask in enumerate(masks1):
        embedded1[index0[mask], :] = vectors1[row1, :]

    empty0 = masks0.index(0)
    empty1 = masks1.index(0)
    amplitudes0 = np.conjugate(vectors0[empty0, :])
    amplitudes1 = vectors1[empty1, :]
    overlaps = np.conjugate(vectors0).T @ embedded1
    coefficients = amplitudes0[:, None] * overlaps * amplitudes1[None, :]
    frequencies = energies0[:, None] - energies1[None, :]

    scale = float(np.max(np.abs(coefficients), initial=0.0))
    active = np.abs(coefficients) >= coefficient_threshold * scale
    active_frequencies = frequencies[active].real
    active_coefficients = coefficients[active]
    order = np.argsort(active_frequencies)
    active_frequencies = active_frequencies[order]
    active_coefficients = active_coefficients[order]

    grouped_coefficients: list[complex] = []
    grouped_frequencies: list[float] = []
    for frequency, coefficient in zip(active_frequencies, active_coefficients, strict=True):
        if grouped_frequencies and abs(float(frequency) - grouped_frequencies[-1]) <= FREQUENCY_CLUSTER_TOLERANCE:
            grouped_coefficients[-1] += complex(coefficient)
        else:
            grouped_frequencies.append(float(frequency))
            grouped_coefficients.append(complex(coefficient))
    resolved = sum(abs(value) >= coefficient_threshold * scale for value in grouped_coefficients)
    coefficient_l1 = float(np.sum(np.abs(active_coefficients)))
    return {
        "k": k,
        "regime": regime,
        "coefficient_threshold": coefficient_threshold,
        "dimension_h0": len(masks0),
        "dimension_h1": len(masks1),
        "candidate_frequency_pairs": len(masks0) * len(masks1),
        "active_frequency_pairs": int(np.count_nonzero(active)),
        "resolved_frequency_rank": int(resolved),
        "atom_lower_bound": atom_lower_bound(int(resolved)),
        "active_coefficient_l1": coefficient_l1,
        "response_at_zero_from_coefficients_real": float(np.sum(coefficients).real),
        "response_at_zero_from_coefficients_imag": float(np.sum(coefficients).imag),
    }


def fit_line(rows: list[dict[str, object]], key: str) -> dict[str, float]:
    x = np.asarray([float(row["k"]) for row in rows])
    y = np.asarray([float(row[key]) for row in rows])
    slope, intercept = np.polyfit(x, y, 1)
    prediction = slope * x + intercept
    residual = float(np.sum((y - prediction) ** 2))
    total = float(np.sum((y - np.mean(y)) ** 2))
    return {
        "slope": float(slope),
        "intercept": float(intercept),
        "r2": 1.0 if total == 0.0 else float(1.0 - residual / total),
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def finite_horizon_rows() -> tuple[list[dict[str, object]], list[dict[str, object]], dict[tuple[int, float, str], np.ndarray]]:
    rank_rows: list[dict[str, object]] = []
    prefix_rows: list[dict[str, object]] = []
    singular_values: dict[tuple[int, float, str], np.ndarray] = {}
    hankel_cache: dict[tuple[int, float, str], np.ndarray] = {}

    for regime in REGIMES:
        for horizon in HORIZONS:
            for k in K_VALUES:
                response = np.asarray(response_samples(k, horizon, regime), dtype=complex)
                matrix = response_hankel(response)
                values = svdvals(matrix)
                singular_values[(k, horizon, regime)] = values
                hankel_cache[(k, horizon, regime)] = matrix
                row: dict[str, object] = {
                    "k": k,
                    "horizon": horizon,
                    "regime": regime,
                    "dimension_h0": len(conditional_basis(k, False)),
                    "dimension_h1": len(conditional_basis(k, True)),
                    "response_zero_error": abs(response[0] - 1.0),
                    "response_min_abs": float(np.min(np.abs(response))),
                    "response_final_abs": float(abs(response[-1])),
                    "rank64_relative_residual": relative_tail(values, RANK_BUDGET_THREE_ATOMS),
                }
                for tolerance in EFFECTIVE_TOLERANCES:
                    rank = effective_rank(values, tolerance)
                    suffix = f"{int(round(100 * tolerance))}pct"
                    row[f"effective_rank_{suffix}"] = rank
                    row[f"atom_lower_bound_{suffix}"] = atom_lower_bound(rank)
                rank_rows.append(row)

                norm_response = float(np.linalg.norm(response))
                norm_matrix = float(np.linalg.norm(matrix))
                for budget in PREFIX_BUDGETS:
                    prefix = np.asarray(response_samples(budget, horizon, regime), dtype=complex)
                    prefix_matrix = response_hankel(prefix)
                    difference = response - prefix
                    matrix_difference = matrix - prefix_matrix
                    prefix_rows.append(
                        {
                            "target_k": k,
                            "horizon": horizon,
                            "regime": regime,
                            "prefix_atoms": budget,
                            "max_time_error": float(np.max(np.abs(difference))),
                            "relative_l2_time_error": float(np.linalg.norm(difference) / norm_response),
                            "relative_hankel_error": float(np.linalg.norm(matrix_difference) / norm_matrix),
                        }
                    )
    return rank_rows, prefix_rows, singular_values


def promotion_summary(
    finite_rows: list[dict[str, object]], prefix_rows: list[dict[str, object]]
) -> tuple[list[dict[str, object]], bool]:
    decisions: list[dict[str, object]] = []
    for horizon in HORIZONS:
        if horizon < 5.0:
            continue
        regime_decisions = []
        for regime in REGIMES:
            finite = next(
                row
                for row in finite_rows
                if row["k"] == max(K_VALUES) and row["horizon"] == horizon and row["regime"] == regime
            )
            prefixes = [
                row
                for row in prefix_rows
                if row["target_k"] == max(K_VALUES)
                and row["horizon"] == horizon
                and row["regime"] == regime
            ]
            best_max_error = min(float(row["max_time_error"]) for row in prefixes)
            best_hankel_error = min(float(row["relative_hankel_error"]) for row in prefixes)
            rank64_residual = float(finite["rank64_relative_residual"])
            ratio = best_hankel_error / max(rank64_residual, 1e-15)
            arbitrary_three_atom_possible = rank64_residual <= 0.01
            prefix_fails = best_max_error >= 0.05
            separation = ratio >= 5.0
            passes = arbitrary_three_atom_possible and prefix_fails and separation
            regime_decisions.append(passes)
            decisions.append(
                {
                    "horizon": horizon,
                    "regime": regime,
                    "rank64_relative_residual": rank64_residual,
                    "best_prefix_max_time_error": best_max_error,
                    "best_prefix_relative_hankel_error": best_hankel_error,
                    "prefix_to_rank64_error_ratio": ratio,
                    "arbitrary_three_atom_not_ruled_out": arbitrary_three_atom_possible,
                    "all_prefixes_fail_5pct": prefix_fails,
                    "fivefold_nonlocal_separation": separation,
                    "regime_passes": passes,
                    "failure_class": (
                        "promotion_window"
                        if passes
                        else "complexity"
                        if not arbitrary_three_atom_possible
                        else "locality"
                        if not prefix_fails
                        else "insufficient_separation"
                    ),
                }
            )
        horizon_passes = all(regime_decisions)
        for row in decisions[-len(REGIMES) :]:
            row["horizon_passes_both_controls"] = horizon_passes
    return decisions, any(bool(row["horizon_passes_both_controls"]) for row in decisions)


def make_figures(
    exact_rows: list[dict[str, object]],
    finite_rows: list[dict[str, object]],
    prefix_rows: list[dict[str, object]],
) -> None:
    plt.figure(figsize=(7.2, 4.6))
    for regime, marker in (("uniform", "o"), ("perturbed", "s")):
        subset = [
            row
            for row in exact_rows
            if row["regime"] == regime and float(row["coefficient_threshold"]) == 1e-10
        ]
        plt.plot(
            [row["k"] for row in subset],
            [row["atom_lower_bound"] for row in subset],
            marker=marker,
            label=regime,
        )
    plt.plot(K_VALUES, K_VALUES, "k--", alpha=0.35, label="no compression r=k")
    plt.xlabel("motif atoms k")
    plt.ylabel("exact atom lower bound ceil(log4 R)")
    plt.title("Resolved boundary-response complexity")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUT / "exact_rank_scaling.png", dpi=180)
    plt.close()

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), sharex=True)
    for regime, marker in (("uniform", "o"), ("perturbed", "s")):
        rank_values = []
        prefix_values = []
        for horizon in HORIZONS:
            finite = next(
                row
                for row in finite_rows
                if row["k"] == max(K_VALUES) and row["horizon"] == horizon and row["regime"] == regime
            )
            prefixes = [
                row
                for row in prefix_rows
                if row["target_k"] == max(K_VALUES)
                and row["horizon"] == horizon
                and row["regime"] == regime
            ]
            rank_values.append(float(finite["rank64_relative_residual"]))
            prefix_values.append(min(float(row["max_time_error"]) for row in prefixes))
        axes[0].plot(HORIZONS, rank_values, marker=marker, label=regime)
        axes[1].plot(HORIZONS, prefix_values, marker=marker, label=regime)
    axes[0].axhline(0.01, color="black", linestyle="--", alpha=0.5)
    axes[1].axhline(0.05, color="black", linestyle="--", alpha=0.5)
    axes[0].set_ylabel("best rank-64 Hankel residual")
    axes[1].set_ylabel("best r<=3 prefix max error")
    for axis in axes:
        axis.set_xlabel("horizon T")
        axis.set_yscale("log")
        axis.legend()
    fig.suptitle("The preregistered locality-complexity window, k=13")
    fig.tight_layout()
    fig.savefig(OUT / "locality_complexity_gate.png", dpi=180)
    plt.close(fig)

    plt.figure(figsize=(7.2, 4.6))
    horizon = 10.0
    regime = "perturbed"
    times = np.linspace(0.0, horizon, SAMPLE_COUNT)
    target = np.asarray(response_samples(max(K_VALUES), horizon, regime))
    plt.plot(times, np.abs(target), linewidth=2.0, label=f"target k={max(K_VALUES)}")
    for budget in PREFIX_BUDGETS:
        prefix = np.asarray(response_samples(budget, horizon, regime))
        plt.plot(times, np.abs(prefix), alpha=0.8, label=f"prefix r={budget}")
    plt.xlabel("time")
    plt.ylabel("|g(t)|")
    plt.title("Conditional port-coherence response")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUT / "response_curves_T10.png", dpi=180)
    plt.close()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    exact_rows: list[dict[str, object]] = []
    for regime in REGIMES:
        for k in K_VALUES:
            for threshold in COEFFICIENT_THRESHOLDS:
                exact_rows.append(resolved_spectrum(k, regime, threshold))

    finite_rows, prefix_rows, _ = finite_horizon_rows()
    decisions, survives = promotion_summary(finite_rows, prefix_rows)

    fits: dict[str, dict[str, float]] = {}
    for regime in REGIMES:
        for threshold in COEFFICIENT_THRESHOLDS:
            subset = [
                row
                for row in exact_rows
                if row["regime"] == regime and float(row["coefficient_threshold"]) == threshold
            ]
            fits[f"{regime}_{threshold:g}"] = fit_line(subset, "atom_lower_bound")

    summary = {
        "experiment": "causal boundary-response kernelization structural gate",
        "frozen_parameters": {
            "k_values": list(K_VALUES),
            "horizons": list(HORIZONS),
            "omega": OMEGA,
            "mean_delta": MEAN_DELTA,
            "perturbation": PERTURBATION,
            "hankel_size": HANKEL_SIZE,
            "sample_count": SAMPLE_COUNT,
            "rng_seed": RNG_SEED,
        },
        "exact_atom_lower_bound_fits": fits,
        "promotion_decisions": decisions,
        "phase0_survives": survives,
        "verdict": (
            "ADVANCE_TO_PHYSICAL_SURROGATE_FITTING"
            if survives
            else "FALSIFIED_NO_LOCALITY_COMPLEXITY_WINDOW"
        ),
    }

    write_csv(OUT / "resolved_spectrum.csv", exact_rows)
    write_csv(OUT / "finite_horizon_rank.csv", finite_rows)
    write_csv(OUT / "prefix_baselines.csv", prefix_rows)
    write_csv(OUT / "promotion_gate.csv", decisions)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    (OUT / "detuning_pattern.json").write_text(
        json.dumps(DETUNING_PATTERN.tolist(), indent=2), encoding="utf-8"
    )
    make_figures(exact_rows, finite_rows, prefix_rows)

    artifact_names = (
        "resolved_spectrum.csv",
        "finite_horizon_rank.csv",
        "prefix_baselines.csv",
        "promotion_gate.csv",
        "summary.json",
        "detuning_pattern.json",
        "exact_rank_scaling.png",
        "locality_complexity_gate.png",
        "response_curves_T10.png",
    )
    manifest = {
        "command": "python -m experiments.causal_boundary_response_phase0.run_phase0",
        "artifacts": {name: sha256(OUT / name) for name in artifact_names},
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
