"""Exact controls, branch audits, and observables for configuration curvature."""

from __future__ import annotations

from itertools import product
from math import pi

import numpy as np
from scipy.linalg import expm, logm, polar, schur
from scipy.integrate import solve_ivp
from scipy.optimize import linear_sum_assignment

from experiments.aquila_one_mask_phase0.control_core import QuantumModel


CONTROL_KEYS = (
    "omega_rad_per_us",
    "phase_rad",
    "global_detuning_rad_per_us",
    "local_detuning_rad_per_us",
)


def circular_difference(first: float, second: float) -> float:
    return float(np.angle(np.exp(1j * (first - second))))


def reverse_pulse(pulse: dict[str, list[float]]) -> dict[str, list[float]]:
    result = {key: list(values) for key, values in pulse.items()}
    for key in CONTROL_KEYS:
        result[key] = list(reversed(result[key]))
    return result


def palindrome_pulse(pulse: dict[str, list[float]]) -> dict[str, list[float]]:
    result = {key: list(values) for key, values in pulse.items()}
    for key in CONTROL_KEYS:
        values = np.asarray(result[key], dtype=float)
        if key == "phase_rad":
            # The development pulse has phase zero; keep the safe exact palindrome.
            symmetrized = 0.5 * (values + values[::-1])
        else:
            symmetrized = 0.5 * (values + values[::-1])
        result[key] = symmetrized.tolist()
    return result


def scale_pulse(
    pulse: dict[str, list[float]],
    omega: float = 1.0,
    global_detuning: float = 1.0,
    local_detuning: float = 1.0,
) -> dict[str, list[float]]:
    result = {key: list(values) for key, values in pulse.items()}
    result["omega_rad_per_us"] = (omega * np.asarray(result["omega_rad_per_us"])).tolist()
    result["global_detuning_rad_per_us"] = (
        global_detuning * np.asarray(result["global_detuning_rad_per_us"])
    ).tolist()
    result["local_detuning_rad_per_us"] = (
        local_detuning * np.asarray(result["local_detuning_rad_per_us"])
    ).tolist()
    return result


def _controls_at(pulse_arrays: dict[str, np.ndarray], time: float) -> list[float]:
    times = pulse_arrays["times_us"]
    interval = int(np.searchsorted(times, time, side="right") - 1)
    interval = min(max(interval, 0), len(times) - 2)
    fraction = (time - times[interval]) / (times[interval + 1] - times[interval])
    return [
        float((1.0 - fraction) * pulse_arrays[key][interval] + fraction * pulse_arrays[key][interval + 1])
        for key in CONTROL_KEYS
    ]


def unitary_ivp(
    model: QuantumModel,
    pulse: dict[str, list[float]],
    rtol: float = 2e-11,
    atol: float = 2e-13,
    max_step_fraction: float = 0.125,
    hamiltonian_scale: float = 1.0,
) -> np.ndarray:
    arrays = {key: np.asarray(value, dtype=float) for key, value in pulse.items()}
    times = arrays["times_us"]
    dimension = model.dimension

    def rhs(time: float, flattened: np.ndarray) -> np.ndarray:
        unitary = flattened.reshape(dimension, dimension)
        hamiltonian = hamiltonian_scale * model.hamiltonian(*_controls_at(arrays, time))
        return (-1j * hamiltonian @ unitary).reshape(-1)

    solution = solve_ivp(
        rhs,
        (float(times[0]), float(times[-1])),
        np.eye(dimension, dtype=complex).reshape(-1),
        method="DOP853",
        rtol=rtol,
        atol=atol,
        t_eval=[float(times[-1])],
        max_step=float(np.min(np.diff(times)) * max_step_fraction),
    )
    if not solution.success:
        raise RuntimeError(solution.message)
    return solution.y[:, -1].reshape(dimension, dimension)


def unitary_midpoint(
    model: QuantumModel,
    pulse: dict[str, list[float]],
    substeps_per_interval: int,
    hamiltonian_scale: float = 1.0,
) -> np.ndarray:
    arrays = {key: np.asarray(value, dtype=float) for key, value in pulse.items()}
    unitary = np.eye(model.dimension, dtype=complex)
    for interval, width in enumerate(np.diff(arrays["times_us"])):
        dt = width / substeps_per_interval
        for substep in range(substeps_per_interval):
            fraction = (substep + 0.5) / substeps_per_interval
            controls = [
                float((1.0 - fraction) * arrays[key][interval] + fraction * arrays[key][interval + 1])
                for key in CONTROL_KEYS
            ]
            hamiltonian = hamiltonian_scale * model.hamiltonian(*controls)
            unitary = expm(-1j * dt * hamiltonian) @ unitary
    return unitary


def polar_unitary(unitary: np.ndarray) -> tuple[np.ndarray, float]:
    error = float(np.linalg.norm(unitary.conj().T @ unitary - np.eye(unitary.shape[0]), ord=2))
    projected, _ = polar(unitary)
    return projected, error


def principal_effective(unitary: np.ndarray, duration: float) -> tuple[np.ndarray, dict]:
    projected, unitarity_error = polar_unitary(unitary)
    effective = (1j / duration) * logm(projected)
    effective = 0.5 * (effective + effective.conj().T)
    reconstruction = float(np.linalg.norm(expm(-1j * duration * effective) - projected, ord=2))
    phases = np.angle(np.linalg.eigvals(projected))
    margin = float(np.min(pi - np.abs(phases)))
    return effective, {
        "unitarity_error_before_polar": unitarity_error,
        "reconstruction_error": reconstruction,
        "branch_cut_margin_rad": margin,
    }


def plaquette_metrics(effective: np.ndarray, first_site: int = 0, second_site: int = 1, base: int = 0) -> dict:
    first = base | (1 << first_site)
    both = first | (1 << second_site)
    second = base | (1 << second_site)
    links = np.array(
        [effective[first, base], effective[both, first], effective[second, both], effective[base, second]],
        dtype=complex,
    )
    product_value = np.prod(links)
    magnitudes = np.abs(links)
    flux = float(np.angle(product_value))
    geometric_mean = float(np.prod(magnitudes) ** 0.25)
    diagonals = [abs(effective[both, base]), abs(effective[second, first])]
    leakage = float(max(diagonals) / geometric_mean) if geometric_mean > 0.0 else float("inf")
    return {
        "flux_rad": flux,
        "sin_flux": float(np.sin(flux)),
        "wilson_product_real": float(product_value.real),
        "wilson_product_imag": float(product_value.imag),
        "edge_geometric_mean_rad_per_us": geometric_mean,
        "minimum_edge_rad_per_us": float(np.min(magnitudes)),
        "two_bit_leakage_ratio": leakage,
    }


def counts_witness(forward: np.ndarray, reverse: np.ndarray, first_site: int = 0, second_site: int = 1) -> dict:
    first = 1 << first_site
    second = 1 << second_site
    p_forward = np.abs(forward[:, 0]) ** 2
    p_reverse = np.abs(reverse[:, 0]) ** 2
    first_asymmetry = float(p_forward[first] - p_reverse[first])
    second_asymmetry = float(p_forward[second] - p_reverse[second])
    return {
        "chi": first_asymmetry - second_asymmetry,
        "first_asymmetry": first_asymmetry,
        "second_asymmetry": second_asymmetry,
        "p_forward_first": float(p_forward[first]),
        "p_reverse_first": float(p_reverse[first]),
        "p_forward_second": float(p_forward[second]),
        "p_reverse_second": float(p_reverse[second]),
    }


def branch_effective_hamiltonians(unitary: np.ndarray, duration: float) -> list[dict]:
    projected, _ = polar_unitary(unitary)
    triangular, vectors = schur(projected, output="complex")
    phases = np.angle(np.diag(triangular))
    rows = []
    for shifts in product((-1, 0, 1), repeat=projected.shape[0]):
        quasienergies = (-phases + 2.0 * pi * np.asarray(shifts)) / duration
        effective = vectors @ np.diag(quasienergies) @ vectors.conj().T
        effective = 0.5 * (effective + effective.conj().T)
        metrics = plaquette_metrics(effective)
        rows.append(
            {
                "shifts": list(shifts),
                "common_shift_reduced": shifts[0] == 0,
                **metrics,
                "frobenius_norm": float(np.linalg.norm(effective)),
            }
        )
    return rows


def continuous_log_by_scaling(
    model: QuantumModel,
    pulse: dict[str, list[float]],
    steps: int = 1001,
    midpoint_substeps: int = 16,
) -> tuple[np.ndarray, dict]:
    duration = pulse["times_us"][-1] - pulse["times_us"][0]
    previous_vectors = None
    previous_phases = None
    previous_windings = None
    branch_crossings = 0
    final_vectors = None
    final_phases = None
    for index, scale in enumerate(np.linspace(1e-6, 1.0, steps)):
        unitary = unitary_midpoint(model, pulse, midpoint_substeps, hamiltonian_scale=float(scale))
        triangular, vectors = schur(unitary, output="complex")
        phases = np.angle(np.diag(triangular))
        if previous_vectors is not None:
            overlap = np.abs(previous_vectors.conj().T @ vectors) ** 2
            rows, columns = linear_sum_assignment(-overlap)
            permutation = columns[np.argsort(rows)]
            vectors = vectors[:, permutation]
            phases = phases[permutation]
            windings = np.round((previous_phases - phases) / (2.0 * pi)).astype(int)
            branch_crossings += int(np.count_nonzero(windings - previous_windings))
            phases = phases + 2.0 * pi * windings
            previous_windings = windings
        else:
            previous_windings = np.zeros_like(phases, dtype=int)
        previous_vectors = vectors
        previous_phases = phases
        final_vectors = vectors
        final_phases = phases
    effective = final_vectors @ np.diag(-final_phases / duration) @ final_vectors.conj().T
    effective = 0.5 * (effective + effective.conj().T)
    return effective, {"scaling_steps": steps, "detected_phase_wraps": branch_crossings}


def continued_log_near_diagonal(unitary: np.ndarray, reference_energies: np.ndarray, duration: float) -> np.ndarray:
    """Choose eigenphase branches continuously connected to a known diagonal H at zero drive."""
    triangular, vectors = schur(unitary, output="complex")
    phases = np.angle(np.diag(triangular))
    overlap = np.abs(vectors) ** 2
    reference_rows, eigen_columns = linear_sum_assignment(-overlap)
    order = eigen_columns[np.argsort(reference_rows)]
    vectors = vectors[:, order]
    phases = phases[order]
    target_phases = -np.asarray(reference_energies) * duration
    unwrapped = phases + 2.0 * pi * np.round((target_phases - phases) / (2.0 * pi))
    energies = -unwrapped / duration
    effective = vectors @ np.diag(energies) @ vectors.conj().T
    return 0.5 * (effective + effective.conj().T)


def analytic_spectral_phase(omega: float, duration: float, times: tuple[float, float], weights: tuple[float, float]) -> float:
    if abs(omega) < 1e-14:
        denominator = duration
    else:
        denominator = np.expm1(1j * omega * duration) / (1j * omega)
    numerator = weights[0] * np.exp(1j * omega * times[0]) + weights[1] * np.exp(1j * omega * times[1])
    return float(np.angle(numerator / denominator))


def analytic_weak_flux(
    e1: float,
    e2: float,
    interaction: float,
    duration: float,
    kick_times: tuple[float, float],
    kick_weights: tuple[float, float],
) -> float:
    alpha = lambda omega: analytic_spectral_phase(omega, duration, kick_times, kick_weights)
    return float(
        np.angle(
            np.exp(
                1j
                * (
                    alpha(e1)
                    + alpha(e2 + interaction)
                    - alpha(e1 + interaction)
                    - alpha(e2)
                )
            )
        )
    )


def gauge_rephase(effective: np.ndarray, phases: np.ndarray) -> np.ndarray:
    diagonal = np.diag(np.exp(1j * np.asarray(phases)))
    return diagonal.conj().T @ effective @ diagonal
