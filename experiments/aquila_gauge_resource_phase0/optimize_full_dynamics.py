"""Reproduce the exploratory search behind the frozen full-dynamics pulse.

This optimizer is provenance, not part of the independent validator. PyTorch
is an optional dependency required only when this search is rerun; importing
or running ``full_dynamics_audit.py`` does not import PyTorch.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.aquila_configuration_curvature_phase0.curvature_core import (
    unitary_ivp,
    unitary_midpoint,
)
from experiments.aquila_gauge_resource_phase0.full_dynamics_audit import (
    C6_RAD_PER_US_UM6,
    CLOCKWISE_TARGETS,
    COUNTERCLOCKWISE_TARGETS,
    FACE_SOURCES,
    NOMINAL_POSITIONS_UM,
    STATIC_MASK,
    population_cycle_metrics,
)
from experiments.aquila_one_mask_phase0.control_core import (
    ControlLimits,
    full_c6_model,
    validate_pulse,
)


DEFAULT_OUTPUT = (
    ROOT
    / "results"
    / "aquila_gauge_resource_phase0"
    / "full_dynamics_optimizer_search.json"
)
DEFAULT_DURATIONS_US = (0.4, 0.8, 1.2, 2.0)
DEFAULT_BASE_SEED = 99_173


def require_torch():
    try:
        import torch
    except ImportError as exc:  # pragma: no cover - environment diagnostic
        raise RuntimeError(
            "This optional exploratory search requires PyTorch. "
            "The independent full_dynamics_audit.py validator does not."
        ) from exc
    return torch


def make_context(device_name: str) -> dict:
    torch = require_torch()
    if device_name == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(device_name)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")
    real_dtype = torch.float32 if device.type == "cuda" else torch.float64
    complex_dtype = torch.complex64 if device.type == "cuda" else torch.complex128
    torch.manual_seed(DEFAULT_BASE_SEED)

    model = full_c6_model(
        NOMINAL_POSITIONS_UM,
        STATIC_MASK,
        C6_RAD_PER_US_UM6,
    )
    matrices = {
        key: torch.as_tensor(getattr(model, key), dtype=complex_dtype, device=device)
        for key in ("interaction", "x_sum", "y_sum", "number", "mask_number")
    }
    return {
        "torch": torch,
        "device": device,
        "real_dtype": real_dtype,
        "complex_dtype": complex_dtype,
        "model": model,
        "matrices": matrices,
        "sources": torch.as_tensor(FACE_SOURCES, dtype=torch.long, device=device),
        "clockwise_targets": torch.as_tensor(
            CLOCKWISE_TARGETS, dtype=torch.long, device=device
        ),
        "counterclockwise_targets": torch.as_tensor(
            COUNTERCLOCKWISE_TARGETS, dtype=torch.long, device=device
        ),
    }


def mapped_controls(raw, duration_us: float, context: dict):
    """Map unconstrained knots into a box that also enforces every slew bound."""
    torch = context["torch"]
    batch, interior_count, _ = raw.shape
    knot_count = interior_count + 2
    knot_spacing = duration_us / (knot_count - 1)
    zero = torch.zeros((batch, 1), dtype=raw.dtype, device=raw.device)

    # Rabi and local controls are one-sided. Global detuning is two-sided, so
    # its half-range is chosen such that 2*cap/dt <= the slew limit.
    omega_cap = min(15.8, 250.0 * knot_spacing)
    global_cap = min(125.0, 1_250.0 * knot_spacing)
    local_cap = min(125.0, 1_256.0 * knot_spacing)
    omega = torch.cat(
        (zero, omega_cap * torch.sigmoid(raw[:, :, 0]), zero), dim=1
    )
    global_detuning = torch.cat(
        (zero, global_cap * torch.tanh(raw[:, :, 1]), zero), dim=1
    )
    local_detuning = torch.cat(
        (zero, -local_cap * torch.sigmoid(raw[:, :, 2]), zero), dim=1
    )
    return omega, global_detuning, local_detuning


def propagate_optimization_grid(
    raw,
    duration_us: float,
    substeps_per_interval: int,
    context: dict,
):
    torch = context["torch"]
    omega, global_detuning, local_detuning = mapped_controls(raw, duration_us, context)
    batch, knot_count = omega.shape
    interval = duration_us / (knot_count - 1)
    step_width = interval / substeps_per_interval
    dimension = context["model"].dimension
    unitary = (
        torch.eye(dimension, dtype=context["complex_dtype"], device=context["device"])
        .expand(batch, dimension, dimension)
        .clone()
    )
    matrices = context["matrices"]
    for interval_index in range(knot_count - 1):
        for substep in range(substeps_per_interval):
            fraction = (substep + 0.5) / substeps_per_interval
            rabi = (
                (1.0 - fraction) * omega[:, interval_index]
                + fraction * omega[:, interval_index + 1]
            )
            global_value = (
                (1.0 - fraction) * global_detuning[:, interval_index]
                + fraction * global_detuning[:, interval_index + 1]
            )
            local_value = (
                (1.0 - fraction) * local_detuning[:, interval_index]
                + fraction * local_detuning[:, interval_index + 1]
            )
            hamiltonian = (
                matrices["interaction"][None]
                + 0.5 * rabi[:, None, None] * matrices["x_sum"][None]
                - global_value[:, None, None] * matrices["number"][None]
                - local_value[:, None, None] * matrices["mask_number"][None]
            )
            step_unitary = torch.matrix_exp((-1j * step_width) * hamiltonian)
            unitary = step_unitary @ unitary
    return unitary


def torch_cycle_metrics(unitary, context: dict):
    torch = context["torch"]
    clockwise = torch.abs(
        unitary[:, context["clockwise_targets"], context["sources"]]
    ) ** 2
    counterclockwise = torch.abs(
        unitary[:, context["counterclockwise_targets"], context["sources"]]
    ) ** 2
    return clockwise.mean(dim=1), counterclockwise.mean(dim=1), clockwise


def pulse_from_raw(raw_row: np.ndarray, duration_us: float, context: dict) -> dict:
    torch = context["torch"]
    tensor = torch.as_tensor(
        raw_row[None], dtype=context["real_dtype"], device=context["device"]
    )
    omega, global_detuning, local_detuning = mapped_controls(
        tensor, duration_us, context
    )
    knot_count = omega.shape[1]
    return {
        "times_us": np.linspace(0.0, duration_us, knot_count).tolist(),
        "omega_rad_per_us": omega[0].detach().cpu().double().numpy().tolist(),
        "phase_rad": [0.0] * knot_count,
        "global_detuning_rad_per_us": (
            global_detuning[0].detach().cpu().double().numpy().tolist()
        ),
        "local_detuning_rad_per_us": (
            local_detuning[0].detach().cpu().double().numpy().tolist()
        ),
    }


def optimize_duration(
    duration_us: float,
    context: dict,
    base_seed: int,
    seed_count: int,
    adam_steps: int,
    learning_rate: float,
    optimization_substeps: int,
    top_k: int,
    progress_every: int,
) -> list[dict]:
    torch = context["torch"]
    knot_spacing = 0.05 if duration_us < 0.8 else 0.1
    knot_count = int(round(duration_us / knot_spacing)) + 1
    initial_rows = []
    for seed_index in range(seed_count):
        generator = torch.Generator(device="cpu").manual_seed(base_seed + seed_index)
        row = 0.35 * torch.randn(
            (knot_count - 2, 3),
            generator=generator,
            dtype=context["real_dtype"],
        )
        row[:, 0] -= 0.2
        row[:, 2] -= 1.0
        initial_rows.append(row)
    raw = torch.nn.Parameter(torch.stack(initial_rows).to(context["device"]))
    optimizer = torch.optim.Adam([raw], lr=learning_rate)

    for step in range(adam_steps):
        optimizer.zero_grad(set_to_none=True)
        unitary = propagate_optimization_grid(
            raw, duration_us, optimization_substeps, context
        )
        clockwise_mean, counterclockwise_mean, clockwise = torch_cycle_metrics(
            unitary, context
        )
        soft_minimum = -0.08 * torch.logsumexp(-clockwise / 0.08, dim=1)
        objective = (
            clockwise_mean
            + 0.30 * soft_minimum
            - 0.08 * counterclockwise_mean
        )
        (-objective.sum()).backward()
        torch.nn.utils.clip_grad_norm_([raw], 20.0)
        optimizer.step()
        with torch.no_grad():
            raw.clamp_(-8.0, 8.0)
        if progress_every > 0 and (step % progress_every == 0 or step == adam_steps - 1):
            best = int(torch.argmax(clockwise_mean).item())
            print(
                json.dumps(
                    {
                        "duration_us": duration_us,
                        "step": step,
                        "best_clockwise_mean": float(clockwise_mean[best]),
                        "best_clockwise_minimum": float(torch.min(clockwise[best])),
                        "best_counterclockwise_mean": float(counterclockwise_mean[best]),
                    }
                ),
                flush=True,
            )

    with torch.no_grad():
        final_unitaries = propagate_optimization_grid(
            raw, duration_us, optimization_substeps, context
        )
        clockwise_mean, counterclockwise_mean, clockwise = torch_cycle_metrics(
            final_unitaries, context
        )
        search_order = torch.argsort(clockwise_mean, descending=True).cpu().numpy()
        raw_numpy = raw.detach().cpu().double().numpy()
        grid_clockwise_mean = clockwise_mean.cpu().double().numpy()
        grid_counterclockwise_mean = counterclockwise_mean.cpu().double().numpy()
        grid_clockwise = clockwise.cpu().double().numpy()

    candidates = []
    limits = replace(ControlLimits(), duration_us=duration_us)
    for search_rank, seed_index in enumerate(search_order[:top_k]):
        pulse = pulse_from_raw(raw_numpy[seed_index], duration_us, context)
        midpoint = unitary_midpoint(context["model"], pulse, 16)
        adaptive = unitary_ivp(
            context["model"],
            pulse,
            rtol=2e-11,
            atol=2e-13,
            max_step_fraction=0.0625,
        )
        candidates.append(
            {
                "search_rank": search_rank,
                "seed_index": int(seed_index),
                "seed_value": base_seed + int(seed_index),
                "validation_errors": validate_pulse(pulse, limits),
                "optimization_grid": {
                    "clockwise_mean": float(grid_clockwise_mean[seed_index]),
                    "clockwise_minimum": float(np.min(grid_clockwise[seed_index])),
                    "clockwise_probabilities": grid_clockwise[seed_index].tolist(),
                    "counterclockwise_mean": float(
                        grid_counterclockwise_mean[seed_index]
                    ),
                },
                "midpoint16": population_cycle_metrics(midpoint),
                "adaptive": population_cycle_metrics(adaptive),
                "midpoint_adaptive_operator_norm": float(
                    np.linalg.norm(midpoint - adaptive, ord=2)
                ),
                "pulse": pulse,
            }
        )
    adaptive_order = sorted(
        range(len(candidates)),
        key=lambda index: candidates[index]["adaptive"]["clockwise_mean"],
        reverse=True,
    )
    for adaptive_rank, candidate_index in enumerate(adaptive_order):
        candidates[candidate_index]["adaptive_rank"] = adaptive_rank
    return candidates


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--durations-us",
        nargs="+",
        type=float,
        default=list(DEFAULT_DURATIONS_US),
    )
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--base-seed", type=int, default=DEFAULT_BASE_SEED)
    parser.add_argument("--seed-count", type=int, default=8)
    parser.add_argument("--adam-steps", type=int, default=900)
    parser.add_argument("--learning-rate", type=float, default=0.035)
    parser.add_argument("--optimization-substeps", type=int, default=2)
    parser.add_argument("--top-k", type=int, default=4)
    parser.add_argument("--progress-every", type=int, default=300)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    context = make_context(args.device)
    durations = {}
    for duration in args.durations_us:
        durations[str(duration)] = optimize_duration(
            duration_us=duration,
            context=context,
            base_seed=args.base_seed,
            seed_count=args.seed_count,
            adam_steps=args.adam_steps,
            learning_rate=args.learning_rate,
            optimization_substeps=args.optimization_substeps,
            top_k=args.top_k,
            progress_every=args.progress_every,
        )
    payload = {
        "metadata": {
            "audit_type": "post-hoc exploratory optimization provenance",
            "selected_before_independent_audit": True,
            "required_by_independent_validator": False,
            "torch_optional_dependency": True,
            "torch_version": context["torch"].__version__,
            "device": str(context["device"]),
            "real_dtype": str(context["real_dtype"]),
            "complex_dtype": str(context["complex_dtype"]),
            "base_seed": args.base_seed,
            "seed_count_per_duration": args.seed_count,
            "adam_steps": args.adam_steps,
            "learning_rate": args.learning_rate,
            "optimization_substeps_per_interval": args.optimization_substeps,
            "top_validated_candidates_per_duration": args.top_k,
            "durations_us": args.durations_us,
            "adaptive_validation": {
                "method": "DOP853",
                "rtol": 2e-11,
                "atol": 2e-13,
                "max_step_fraction_of_knot_interval": 0.0625,
            },
            "objective": (
                "clockwise_mean + 0.30*soft_min(clockwise probabilities) "
                "- 0.08*counterclockwise_mean"
            ),
            "selection_for_independent_audit": {
                "duration_us": 1.2,
                "seed_index": 1,
                "seed_value": 99_174,
                "rule": (
                    "shortest searched duration whose validated candidate exceeded "
                    "0.98 mean and 0.97 worst-leg clockwise probability"
                ),
            },
        },
        "model": {
            "positions_um": NOMINAL_POSITIONS_UM.tolist(),
            "static_mask": STATIC_MASK.tolist(),
            "c6_rad_per_us_um6": C6_RAD_PER_US_UM6,
            "configuration_dimension": context["model"].dimension,
            "face_cycle": [0, 1, 3, 2, 0],
            "laser_phase_fixed_rad": 0.0,
        },
        "durations": durations,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
