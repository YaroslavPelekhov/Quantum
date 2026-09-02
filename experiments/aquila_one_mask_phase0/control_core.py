"""Exact small-system models and structural checks for Aquila one-mask Phase 0."""

from __future__ import annotations

from dataclasses import dataclass
from math import floor, sqrt
from typing import Iterable

import networkx as nx
import numpy as np
from scipy.integrate import solve_ivp

from experiments.quantum_safe_kernelization_phase0.qdk_core import independent_masks


@dataclass(frozen=True)
class ControlLimits:
    duration_us: float = 4.0
    rabi_max: float = 15.8
    rabi_slew_max: float = 250.0
    global_detuning_abs_max: float = 125.0
    global_detuning_slew_max: float = 2500.0
    local_detuning_abs_max: float = 125.0
    local_detuning_slew_max: float = 1256.0
    time_resolution_us: float = 0.001
    time_delta_min_us: float = 0.05


@dataclass(frozen=True)
class QuantumModel:
    name: str
    masks: tuple[int, ...]
    x_sum: np.ndarray
    y_sum: np.ndarray
    number: np.ndarray
    mask_number: np.ndarray
    interaction: np.ndarray

    @property
    def dimension(self) -> int:
        return len(self.masks)

    def hamiltonian(self, omega: float, phase: float, delta_g: float, delta_l: float) -> np.ndarray:
        return (
            self.interaction
            + 0.5 * omega * (np.cos(phase) * self.x_sum - np.sin(phase) * self.y_sum)
            - delta_g * self.number
            - delta_l * self.mask_number
        )


def _operators_for_masks(n: int, masks: Iterable[int], spatial_mask: np.ndarray) -> tuple[np.ndarray, ...]:
    states = tuple(int(mask) for mask in masks)
    index = {mask: i for i, mask in enumerate(states)}
    d = len(states)
    x_sum = np.zeros((d, d), dtype=complex)
    y_sum = np.zeros((d, d), dtype=complex)
    counts = np.zeros(d, dtype=float)
    weighted = np.zeros(d, dtype=float)
    for column, state in enumerate(states):
        counts[column] = state.bit_count()
        weighted[column] = sum(spatial_mask[bit] for bit in range(n) if state & (1 << bit))
        for bit in range(n):
            target = state ^ (1 << bit)
            row = index.get(target)
            if row is None:
                continue
            x_sum[row, column] += 1.0
            y_sum[row, column] += 1j if not (state & (1 << bit)) else -1j
    return x_sum, y_sum, np.diag(counts), np.diag(weighted)


def interaction_diagonal(
    masks: Iterable[int], coordinates_um: np.ndarray, c6_rad_per_us_um6: float
) -> np.ndarray:
    states = tuple(int(mask) for mask in masks)
    n = len(coordinates_um)
    values = np.zeros(len(states), dtype=float)
    for row, state in enumerate(states):
        for first in range(n):
            if not (state & (1 << first)):
                continue
            for second in range(first + 1, n):
                if state & (1 << second):
                    distance = float(np.linalg.norm(coordinates_um[first] - coordinates_um[second]))
                    values[row] += c6_rad_per_us_um6 / distance**6
    return np.diag(values)


def full_c6_model(
    coordinates_um: np.ndarray, spatial_mask: np.ndarray, c6_rad_per_us_um6: float = 5_420_000.0
) -> QuantumModel:
    n = len(coordinates_um)
    masks = tuple(range(1 << n))
    x_sum, y_sum, number, mask_number = _operators_for_masks(n, masks, spatial_mask)
    interaction = interaction_diagonal(masks, coordinates_um, c6_rad_per_us_um6)
    return QuantumModel("full_c6", masks, x_sum, y_sum, number, mask_number, interaction)


def hard_blockade_model(
    graph: nx.Graph,
    coordinates_um: np.ndarray,
    spatial_mask: np.ndarray,
    c6_rad_per_us_um6: float = 5_420_000.0,
) -> QuantumModel:
    n = graph.number_of_nodes()
    masks = independent_masks(graph)
    x_sum, y_sum, number, mask_number = _operators_for_masks(n, masks, spatial_mask)
    interaction = interaction_diagonal(masks, coordinates_um, c6_rad_per_us_um6)
    return QuantumModel("hard_blockade", masks, x_sum, y_sum, number, mask_number, interaction)


def state_index(model: QuantumModel, bitmask: int) -> int:
    return model.masks.index(bitmask)


def reflection_matrix(model: QuantumModel, n: int) -> np.ndarray:
    matrix = np.zeros((model.dimension, model.dimension), dtype=complex)
    index = {mask: i for i, mask in enumerate(model.masks)}
    for column, state in enumerate(model.masks):
        reflected = 0
        for bit in range(n):
            if state & (1 << bit):
                reflected |= 1 << (n - 1 - bit)
        matrix[index[reflected], column] = 1.0
    return matrix


def reflection_commutator_norm(model: QuantumModel) -> float:
    n = max(model.masks, default=0).bit_length()
    reflection = reflection_matrix(model, n)
    generators = (model.interaction, model.x_sum, model.y_sum, model.number)
    return max(float(np.linalg.norm(reflection @ item - item @ reflection, ord=2)) for item in generators)


def max_local_detuning_area(duration_us: float, amplitude: float, slew: float) -> float:
    """Maximum integral |Delta_l(t)| dt with zero endpoints, amplitude and slew bounds."""
    ramp = amplitude / slew
    if duration_us >= 2.0 * ramp:
        return amplitude * (duration_us - ramp)
    return slew * duration_us**2 / 4.0


def addressability_capacity(area: float, operator_tolerance: float = 0.0) -> int:
    """Necessary one-mask capacity for X-on-one/I-on-another unitary addressability.

    Duhamel gives ||U_h-U_h'|| <= |h-h'| area/2 after removal of a
    common phase.  The projective operator-norm distance between X and I is
    sqrt(2).  Allowing tolerance eta at both endpoints yields the denominator
    below.  This is a necessary bound, not a constructive guarantee.
    """
    separation = sqrt(2.0) - 2.0 * operator_tolerance
    if separation <= 0.0:
        raise ValueError("operator_tolerance must be smaller than sqrt(2)/2")
    return floor(1.0 + area / (2.0 * separation))


def unavoidable_operator_error(area: float, sites: int) -> float:
    if sites < 2:
        return 0.0
    return max(0.0, 0.5 * (sqrt(2.0) - area / (2.0 * (sites - 1))))


def phase_gauge_error() -> float:
    """Numerically verify that a global drive phase is a rotating-frame gauge."""
    identity = np.eye(2, dtype=complex)
    x = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
    y = np.array([[0.0, -1j], [1j, 0.0]], dtype=complex)
    number = np.diag([0.0, 1.0]).astype(complex)
    duration = 1.37

    def controls(time: float) -> tuple[float, float, float, float]:
        omega = 2.1 + 0.4 * np.cos(1.3 * time)
        phase = 0.7 * np.sin(2.0 * np.pi * time / duration)
        phase_dot = 0.7 * (2.0 * np.pi / duration) * np.cos(2.0 * np.pi * time / duration)
        detuning = -0.3 + 0.2 * np.sin(0.9 * time)
        return float(omega), float(phase), float(phase_dot), float(detuning)

    def integrate(frame: bool) -> np.ndarray:
        def rhs(time: float, flattened: np.ndarray) -> np.ndarray:
            unitary = flattened.reshape(2, 2)
            omega, phase, phase_dot, detuning = controls(time)
            if frame:
                hamiltonian = 0.5 * omega * x - (detuning + phase_dot) * number
            else:
                hamiltonian = 0.5 * omega * (np.cos(phase) * x - np.sin(phase) * y) - detuning * number
            return (-1j * hamiltonian @ unitary).reshape(-1)

        solution = solve_ivp(
            rhs,
            (0.0, duration),
            identity.reshape(-1),
            rtol=2e-11,
            atol=2e-13,
            method="DOP853",
        )
        if not solution.success:
            raise RuntimeError(solution.message)
        return solution.y[:, -1].reshape(2, 2)

    # The chosen phase is zero at both endpoints, so the terminal frame rotation is I.
    return float(np.linalg.norm(integrate(False) - integrate(True), ord=2))


def quantize(value: np.ndarray, resolution: float) -> np.ndarray:
    return np.round(np.asarray(value, dtype=float) / resolution) * resolution


def validate_pulse(pulse: dict[str, list[float]], limits: ControlLimits, tolerance: float = 1e-9) -> list[str]:
    errors: list[str] = []
    times = np.asarray(pulse["times_us"], dtype=float)
    omega = np.asarray(pulse["omega_rad_per_us"], dtype=float)
    phase = np.asarray(pulse["phase_rad"], dtype=float)
    delta_g = np.asarray(pulse["global_detuning_rad_per_us"], dtype=float)
    delta_l = np.asarray(pulse["local_detuning_rad_per_us"], dtype=float)
    if not (len(times) == len(omega) == len(phase) == len(delta_g) == len(delta_l)):
        return ["control arrays have different lengths"]
    if abs(times[0]) > tolerance or abs(times[-1] - limits.duration_us) > tolerance:
        errors.append("wrong time endpoints")
    intervals = np.diff(times)
    if np.any(intervals < limits.time_delta_min_us - tolerance):
        errors.append("timeDeltaMin violation")
    if np.max(np.abs(times / limits.time_resolution_us - np.round(times / limits.time_resolution_us))) > 1e-6:
        errors.append("time resolution violation")
    if np.any(omega < -tolerance) or np.any(omega > limits.rabi_max + tolerance):
        errors.append("Rabi range violation")
    if np.any(np.abs(delta_g) > limits.global_detuning_abs_max + tolerance):
        errors.append("global detuning range violation")
    if np.any(delta_l < -limits.local_detuning_abs_max - tolerance) or np.any(delta_l > tolerance):
        errors.append("local detuning sign/range violation")
    if any(abs(array[0]) > tolerance or abs(array[-1]) > tolerance for array in (omega, delta_g, delta_l)):
        errors.append("nonzero waveform endpoint")
    if np.any(np.abs(np.diff(omega) / intervals) > limits.rabi_slew_max + tolerance):
        errors.append("Rabi slew violation")
    if np.any(np.abs(np.diff(delta_g) / intervals) > limits.global_detuning_slew_max + tolerance):
        errors.append("global detuning slew violation")
    if np.any(np.abs(np.diff(delta_l) / intervals) > limits.local_detuning_slew_max + tolerance):
        errors.append("local detuning slew violation")
    if np.any(np.abs(phase) > 99.0 + tolerance):
        errors.append("phase range violation")
    return errors
