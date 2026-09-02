"""Constrained pulse optimization and independent high-resolution evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.linalg import expm

from experiments.aquila_one_mask_phase0.control_core import ControlLimits, QuantumModel, state_index


@dataclass
class OptimizationResult:
    seed: int
    fidelity_optimization_grid: float
    pulse: dict[str, list[float]]
    trace: list[float]


def _torch():
    try:
        import torch
    except ImportError as exc:  # pragma: no cover - environment diagnostic
        raise RuntimeError("PyTorch is required for the preregistered differentiable optimizer") from exc
    return torch


def _mapped_controls(raw, limits: ControlLimits, local_enabled: bool):
    torch = _torch()
    batch = raw.shape[0]
    zero = torch.zeros((batch, 1), dtype=raw.dtype, device=raw.device)
    omega_inside = limits.rabi_max * torch.sigmoid(raw[:, :, 0])
    phase_inside = np.pi * torch.tanh(raw[:, :, 1])
    global_inside = limits.global_detuning_abs_max * torch.tanh(raw[:, :, 2])
    if local_enabled:
        local_inside = -limits.local_detuning_abs_max * torch.sigmoid(raw[:, :, 3])
    else:
        local_inside = torch.zeros_like(global_inside)
    return tuple(
        torch.cat((zero, inside, zero), dim=1)
        for inside in (omega_inside, phase_inside, global_inside, local_inside)
    )


def _batch_fidelity(raw, matrices: dict[str, Any], target_index: int, limits: ControlLimits, substeps: int, local_enabled: bool):
    torch = _torch()
    omega, phase, delta_g, delta_l = _mapped_controls(raw, limits, local_enabled)
    batch = raw.shape[0]
    knots = omega.shape[1]
    interval = limits.duration_us / (knots - 1)
    dt = interval / substeps
    samples = []
    for index in range(knots - 1):
        for substep in range(substeps):
            fraction = (substep + 0.5) / substeps
            samples.append((index, fraction))

    def interpolate(values):
        return torch.stack(
            [(1.0 - fraction) * values[:, index] + fraction * values[:, index + 1] for index, fraction in samples],
            dim=1,
        )

    om = interpolate(omega)
    ph = interpolate(phase)
    dg = interpolate(delta_g)
    dl = interpolate(delta_l)
    hamiltonians = (
        matrices["interaction"][None, None, :, :]
        + 0.5
        * om[:, :, None, None]
        * (
            torch.cos(ph)[:, :, None, None] * matrices["x_sum"]
            - torch.sin(ph)[:, :, None, None] * matrices["y_sum"]
        )
        - dg[:, :, None, None] * matrices["number"]
        - dl[:, :, None, None] * matrices["mask_number"]
    )
    unitaries = torch.matrix_exp((-1j * dt) * hamiltonians)
    state = torch.zeros(
        (batch, matrices["dimension"]), dtype=matrices["interaction"].dtype, device=raw.device
    )
    state[:, matrices["zero_index"]] = 1.0 + 0.0j
    for step in range(unitaries.shape[1]):
        state = torch.matmul(unitaries[:, step], state.unsqueeze(-1)).squeeze(-1)
    return torch.abs(state[:, target_index]) ** 2


def _torch_matrices(model: QuantumModel, device, complex_dtype):
    torch = _torch()
    return {
        "interaction": torch.tensor(model.interaction, dtype=complex_dtype, device=device),
        "x_sum": torch.tensor(model.x_sum, dtype=complex_dtype, device=device),
        "y_sum": torch.tensor(model.y_sum, dtype=complex_dtype, device=device),
        "number": torch.tensor(model.number, dtype=complex_dtype, device=device),
        "mask_number": torch.tensor(model.mask_number, dtype=complex_dtype, device=device),
        "dimension": model.dimension,
        "zero_index": state_index(model, 0),
    }


def _pulse_from_row(raw_row: np.ndarray, limits: ControlLimits, local_enabled: bool) -> dict[str, list[float]]:
    torch = _torch()
    tensor = torch.tensor(raw_row[None, :, :], dtype=torch.float64)
    mapped = _mapped_controls(tensor, limits, local_enabled)
    arrays = [item.detach().cpu().numpy()[0] for item in mapped]
    knots = len(arrays[0])
    return {
        "times_us": np.linspace(0.0, limits.duration_us, knots).tolist(),
        "omega_rad_per_us": arrays[0].tolist(),
        "phase_rad": arrays[1].tolist(),
        "global_detuning_rad_per_us": arrays[2].tolist(),
        "local_detuning_rad_per_us": arrays[3].tolist(),
    }


def optimize_pulses(
    model: QuantumModel,
    target_mask: int,
    seeds: list[int],
    limits: ControlLimits,
    knot_count: int = 17,
    adam_steps: int = 1200,
    adam_learning_rate: float = 0.045,
    lbfgs_steps: int = 80,
    substeps: int = 2,
    local_enabled: bool = True,
) -> list[OptimizationResult]:
    """Optimize all preregistered seeds as an independent batched multistart."""
    torch = _torch()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    real_dtype = torch.float32 if device.type == "cuda" else torch.float64
    complex_dtype = torch.complex64 if device.type == "cuda" else torch.complex128
    raw_rows = []
    for seed in seeds:
        generator = torch.Generator().manual_seed(seed)
        row = 0.35 * torch.randn((knot_count - 2, 4), generator=generator, dtype=real_dtype)
        row[:, 0] -= 0.4  # moderate initial Rabi amplitude
        row[:, 3] -= 0.8  # avoid starting every mask pulse near its maximum
        raw_rows.append(row)
    raw = torch.nn.Parameter(torch.stack(raw_rows).to(device))
    matrices = _torch_matrices(model, device, complex_dtype)
    target_index = state_index(model, target_mask)
    optimizer = torch.optim.Adam([raw], lr=adam_learning_rate)
    traces: list[list[float]] = [[] for _ in seeds]
    for step in range(adam_steps):
        optimizer.zero_grad(set_to_none=True)
        fidelities = _batch_fidelity(raw, matrices, target_index, limits, substeps, local_enabled)
        loss = torch.sum(1.0 - fidelities)
        loss.backward()
        torch.nn.utils.clip_grad_norm_([raw], 20.0)
        optimizer.step()
        with torch.no_grad():
            raw.clamp_(-7.0, 7.0)
        if step % 100 == 0 or step == adam_steps - 1:
            values = fidelities.detach().cpu().numpy()
            for trace, value in zip(traces, values):
                trace.append(float(value))

    if lbfgs_steps > 0:
        optimizer_lbfgs = torch.optim.LBFGS(
            [raw], lr=0.5, max_iter=lbfgs_steps, tolerance_grad=1e-10, tolerance_change=1e-12, line_search_fn="strong_wolfe"
        )

        def closure():
            optimizer_lbfgs.zero_grad(set_to_none=True)
            fidelities = _batch_fidelity(raw, matrices, target_index, limits, substeps, local_enabled)
            loss = torch.sum(1.0 - fidelities)
            loss.backward()
            return loss

        optimizer_lbfgs.step(closure)

    with torch.no_grad():
        final_fidelities = _batch_fidelity(raw, matrices, target_index, limits, substeps, local_enabled).cpu().numpy()
        raw_numpy = raw.cpu().numpy()
    results = []
    for seed, fidelity, row, trace in zip(seeds, final_fidelities, raw_numpy, traces):
        trace.append(float(fidelity))
        results.append(
            OptimizationResult(
                seed=seed,
                fidelity_optimization_grid=float(fidelity),
                pulse=_pulse_from_row(row, limits, local_enabled),
                trace=trace,
            )
        )
    return results


def propagate_numpy(model: QuantumModel, pulse: dict[str, list[float]], substeps: int = 8) -> np.ndarray:
    arrays = {
        key: np.asarray(pulse[key], dtype=float)
        for key in (
            "times_us",
            "omega_rad_per_us",
            "phase_rad",
            "global_detuning_rad_per_us",
            "local_detuning_rad_per_us",
        )
    }
    state = np.zeros(model.dimension, dtype=complex)
    state[state_index(model, 0)] = 1.0
    for index, interval in enumerate(np.diff(arrays["times_us"])):
        dt = interval / substeps
        for substep in range(substeps):
            fraction = (substep + 0.5) / substeps
            values = {}
            for key in arrays:
                if key == "times_us":
                    continue
                values[key] = (1.0 - fraction) * arrays[key][index] + fraction * arrays[key][index + 1]
            hamiltonian = model.hamiltonian(
                values["omega_rad_per_us"],
                values["phase_rad"],
                values["global_detuning_rad_per_us"],
                values["local_detuning_rad_per_us"],
            )
            state = expm((-1j * dt) * hamiltonian) @ state
    return state


def pulse_fidelity(model: QuantumModel, pulse: dict[str, list[float]], target_mask: int, substeps: int = 8) -> float:
    state = propagate_numpy(model, pulse, substeps=substeps)
    return float(abs(state[state_index(model, target_mask)]) ** 2)


def quantized_pulse(pulse: dict[str, list[float]]) -> dict[str, list[float]]:
    resolutions = {
        "times_us": 0.001,
        "omega_rad_per_us": 0.0004,
        "phase_rad": 5e-7,
        "global_detuning_rad_per_us": 2e-7,
        "local_detuning_rad_per_us": 2e-7,
    }
    return {
        key: (np.round(np.asarray(values, dtype=float) / resolutions[key]) * resolutions[key]).tolist()
        for key, values in pulse.items()
    }


def scaled_pulse(
    pulse: dict[str, list[float]], rabi_factor: float = 1.0, global_factor: float = 1.0, local_factor: float = 1.0
) -> dict[str, list[float]]:
    result = {key: list(values) for key, values in pulse.items()}
    result["omega_rad_per_us"] = (np.asarray(result["omega_rad_per_us"]) * rabi_factor).tolist()
    result["global_detuning_rad_per_us"] = (
        np.asarray(result["global_detuning_rad_per_us"]) * global_factor
    ).tolist()
    result["local_detuning_rad_per_us"] = (np.asarray(result["local_detuning_rad_per_us"]) * local_factor).tolist()
    return result


def dephased_fidelity(
    model: QuantumModel,
    pulse: dict[str, list[float]],
    target_mask: int,
    gamma_per_us: float,
    substeps: int = 8,
) -> float:
    """Second-order-step unitary evolution plus exact computational-basis dephasing channel."""
    arrays = {key: np.asarray(value, dtype=float) for key, value in pulse.items()}
    rho = np.zeros((model.dimension, model.dimension), dtype=complex)
    zero = state_index(model, 0)
    rho[zero, zero] = 1.0
    hamming = np.zeros_like(rho.real)
    for row, first in enumerate(model.masks):
        for column, second in enumerate(model.masks):
            hamming[row, column] = (first ^ second).bit_count()
    for index, interval in enumerate(np.diff(arrays["times_us"])):
        dt = interval / substeps
        decay = np.exp(-0.5 * gamma_per_us * dt * hamming)
        for substep in range(substeps):
            fraction = (substep + 0.5) / substeps
            controls = [
                (1.0 - fraction) * arrays[key][index] + fraction * arrays[key][index + 1]
                for key in (
                    "omega_rad_per_us",
                    "phase_rad",
                    "global_detuning_rad_per_us",
                    "local_detuning_rad_per_us",
                )
            ]
            unitary = expm((-1j * dt / 2.0) * model.hamiltonian(*controls))
            rho = unitary @ rho @ unitary.conj().T
            rho *= decay
            rho = unitary @ rho @ unitary.conj().T
    return float(np.real(rho[state_index(model, target_mask), state_index(model, target_mask)]))
