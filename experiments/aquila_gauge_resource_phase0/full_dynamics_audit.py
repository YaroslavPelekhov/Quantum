"""Post-hoc full-dynamics falsification of a weak-drive QTV extrapolation.

This module deliberately contains no optimizer.  The exploratory optimization
that produced ``FROZEN_PULSE`` is over; the pulse is embedded verbatim so every
reported number can be regenerated with NumPy/SciPy alone.  The primary
reference is adaptive DOP853 propagation of the complete three-atom, eight-
dimensional C6 Hamiltonian.  Midpoint propagation is used only for the frozen
128-draw perturbation sweep and is independently spot-checked with DOP853.

Scope: this is a post-hoc adversarial test, not part of the preregistered gauge-
resource validation.  It falsifies an unrestricted extension of the weak-drive
single-response QTV bound to arbitrary full propagators.  It does not falsify
the weak-drive Fourier theorem or a theorem conditioned on nonzero response on
all configuration-space edges.
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
from experiments.aquila_one_mask_phase0.control_core import (
    ControlLimits,
    QuantumModel,
    full_c6_model,
    validate_pulse,
)

RESULTS = ROOT / "results" / "aquila_gauge_resource_phase0"
DEFAULT_COMPACT_OUTPUT = RESULTS / "full_dynamics_audit.json"

C6_RAD_PER_US_UM6 = 5_420_000.0
NOMINAL_POSITIONS_UM = np.asarray(
    [[0.0, 0.0], [9.4730465146837, 0.0], [3.0, 11.0]], dtype=float
)
HARDWARE_QUANTIZED_POSITIONS_UM = np.asarray(
    [[0.0, 0.0], [9.5, 0.0], [3.0, 11.0]], dtype=float
)
STATIC_MASK = np.asarray([0.0, 0.4, 1.0], dtype=float)
ROBUSTNESS_SEED = 241_109

# Clockwise face order: |000> -> |001> -> |011> -> |010> -> |000>.
FACE_SOURCES = np.asarray([0, 1, 3, 2], dtype=int)
CLOCKWISE_TARGETS = np.asarray([1, 3, 2, 0], dtype=int)
COUNTERCLOCKWISE_TARGETS = np.asarray([2, 0, 1, 3], dtype=int)

# Frozen after exploratory multistart optimization.  Phase was fixed to zero,
# so every instantaneous Hamiltonian is real symmetric.  The endpoint, range,
# time-grid, and slew constraints are independently checked below.
FROZEN_PULSE: dict[str, list[float]] = {
    "times_us": [
        0.0,
        0.1,
        0.2,
        0.3,
        0.4,
        0.5,
        0.6,
        0.7,
        0.8,
        0.9,
        1.0,
        1.1,
        1.2,
    ],
    "omega_rad_per_us": [
        0.0,
        13.561246871948242,
        11.104994773864746,
        8.143071174621582,
        3.490602970123291,
        0.5192868709564209,
        2.817172050476074,
        9.636846542358398,
        3.9511234760284424,
        4.266055107116699,
        2.8116137981414795,
        14.024016380310059,
        0.0,
    ],
    "phase_rad": [0.0] * 13,
    "global_detuning_rad_per_us": [
        0.0,
        3.9372317790985107,
        48.30323791503906,
        17.753358840942383,
        12.636280059814453,
        0.48222070932388306,
        -30.90934181213379,
        27.0598087310791,
        0.8030229806900024,
        -18.29681396484375,
        80.4147720336914,
        -11.640413284301758,
        0.0,
    ],
    "local_detuning_rad_per_us": [
        0.0,
        -30.70500373840332,
        -57.10270309448242,
        -32.954010009765625,
        -11.961651802062988,
        -47.258758544921875,
        -30.70797348022461,
        -62.70475769042969,
        -11.82868766784668,
        -25.05221176147461,
        -80.18392944335938,
        -39.39570236206055,
        0.0,
    ],
}

WAVEFORM_RESOLUTIONS = {
    "times_us": 0.001,
    "omega_rad_per_us": 0.0004,
    "phase_rad": 5e-7,
    "global_detuning_rad_per_us": 2e-7,
    "local_detuning_rad_per_us": 2e-7,
}


def copy_pulse(pulse: dict[str, list[float]]) -> dict[str, list[float]]:
    return {key: list(values) for key, values in pulse.items()}


def quantize_pulse(pulse: dict[str, list[float]]) -> dict[str, list[float]]:
    return {
        key: (
            np.round(np.asarray(values, dtype=float) / WAVEFORM_RESOLUTIONS[key])
            * WAVEFORM_RESOLUTIONS[key]
        ).tolist()
        for key, values in pulse.items()
    }


def reverse_waveform(pulse: dict[str, list[float]]) -> dict[str, list[float]]:
    result = copy_pulse(pulse)
    for key in (
        "omega_rad_per_us",
        "phase_rad",
        "global_detuning_rad_per_us",
        "local_detuning_rad_per_us",
    ):
        result[key] = list(reversed(result[key]))
    return result


def scale_pulse(
    pulse: dict[str, list[float]],
    rabi_factor: float,
    global_factor: float,
    local_factor: float,
) -> dict[str, list[float]]:
    result = copy_pulse(pulse)
    result["omega_rad_per_us"] = (
        rabi_factor * np.asarray(result["omega_rad_per_us"])
    ).tolist()
    result["global_detuning_rad_per_us"] = (
        global_factor * np.asarray(result["global_detuning_rad_per_us"])
    ).tolist()
    result["local_detuning_rad_per_us"] = (
        local_factor * np.asarray(result["local_detuning_rad_per_us"])
    ).tolist()
    return result


def exact_unitary(model: QuantumModel, pulse: dict[str, list[float]]) -> np.ndarray:
    """High-accuracy reference for a piecewise-linear waveform."""
    return unitary_ivp(
        model,
        pulse,
        rtol=5e-12,
        atol=5e-14,
        max_step_fraction=0.03125,
    )


def population_cycle_metrics(unitary: np.ndarray) -> dict:
    clockwise = np.abs(unitary[CLOCKWISE_TARGETS, FACE_SOURCES]) ** 2
    counterclockwise = np.abs(unitary[COUNTERCLOCKWISE_TARGETS, FACE_SOURCES]) ** 2
    spectator_leakage = np.sum(np.abs(unitary[4:, FACE_SOURCES]) ** 2, axis=0)
    clockwise_amplitudes = unitary[CLOCKWISE_TARGETS, FACE_SOURCES]
    clockwise_mean = float(np.mean(clockwise))
    counterclockwise_mean = float(np.mean(counterclockwise))
    return {
        "clockwise_mean": clockwise_mean,
        "clockwise_minimum": float(np.min(clockwise)),
        "clockwise_probabilities": clockwise.tolist(),
        "counterclockwise_mean": counterclockwise_mean,
        "orientation_contrast": clockwise_mean - counterclockwise_mean,
        "spectator_leakage_mean": float(np.mean(spectator_leakage)),
        "cycle_wilson_phase_rad": float(np.angle(np.prod(clockwise_amplitudes))),
        "unitarity_error_operator_norm": float(
            np.linalg.norm(unitary.conj().T @ unitary - np.eye(unitary.shape[0]), ord=2)
        ),
    }


def build_model(
    positions_um: np.ndarray = NOMINAL_POSITIONS_UM,
    mask: np.ndarray = STATIC_MASK,
) -> QuantumModel:
    return full_c6_model(np.asarray(positions_um), np.asarray(mask), C6_RAD_PER_US_UM6)


def waveform_validation(pulse: dict[str, list[float]]) -> list[str]:
    return validate_pulse(pulse, replace(ControlLimits(), duration_us=1.2))


def midpoint_convergence(
    model: QuantumModel,
    pulse: dict[str, list[float]],
    reference: np.ndarray,
) -> list[dict]:
    rows = []
    for substeps in (1, 2, 4, 8, 16, 32, 64):
        approximate = unitary_midpoint(model, pulse, substeps)
        rows.append(
            {
                "substeps_per_interval": substeps,
                "operator_norm_error": float(np.linalg.norm(approximate - reference, ord=2)),
                **population_cycle_metrics(approximate),
            }
        )
    return rows


def null_and_reversal_audit(
    nominal_model: QuantumModel,
    pulse: dict[str, list[float]],
    nominal_unitary: np.ndarray,
) -> tuple[list[dict], dict]:
    zero_interaction = replace(
        nominal_model, interaction=np.zeros_like(nominal_model.interaction)
    )
    equal_mask_model = build_model(mask=np.full(3, 0.4))
    zero_interaction_equal_mask = replace(
        equal_mask_model, interaction=np.zeros_like(equal_mask_model.interaction)
    )
    local_off = copy_pulse(pulse)
    local_off["local_detuning_rad_per_us"] = [0.0] * len(pulse["times_us"])
    reversed_pulse = reverse_waveform(pulse)
    reversed_unitary = exact_unitary(nominal_model, reversed_pulse)
    cases = (
        ("nominal", nominal_model, pulse, nominal_unitary),
        ("interaction_off", zero_interaction, pulse, None),
        ("equal_mask", equal_mask_model, pulse, None),
        ("interaction_off_equal_mask", zero_interaction_equal_mask, pulse, None),
        ("local_waveform_off", nominal_model, local_off, None),
        ("time_reversed_waveform", nominal_model, reversed_pulse, reversed_unitary),
    )
    rows = []
    for name, model, case_pulse, cached_unitary in cases:
        unitary = cached_unitary if cached_unitary is not None else exact_unitary(model, case_pulse)
        rows.append({"case": name, **population_cycle_metrics(unitary)})
    reversal = {
        "reverse_equals_transpose_operator_norm": float(
            np.linalg.norm(reversed_unitary - nominal_unitary.T, ord=2)
        ),
        "reverse": population_cycle_metrics(reversed_unitary),
    }
    return rows, reversal


def robustness_audit(
    pulse: dict[str, list[float]],
    draws: int = 128,
    midpoint_substeps: int = 24,
) -> tuple[dict, list[dict], list[dict]]:
    """Frozen perturbation audit plus adaptive checks of four selected draws."""
    rng = np.random.default_rng(ROBUSTNESS_SEED)
    rows = []
    for draw in range(draws):
        positions = NOMINAL_POSITIONS_UM + rng.normal(0.0, 0.03, NOMINAL_POSITIONS_UM.shape)
        positions -= positions[0]
        mask = np.clip(STATIC_MASK + rng.normal(0.0, 0.01, 3), 0.0, 1.0)
        rabi_factor = float(rng.normal(1.0, 0.01))
        global_factor = float(rng.normal(1.0, 0.01))
        local_factor = float(rng.normal(1.0, 0.01))
        model = build_model(positions, mask)
        perturbed_pulse = scale_pulse(
            pulse,
            rabi_factor=rabi_factor,
            global_factor=global_factor,
            local_factor=local_factor,
        )
        approximate = unitary_midpoint(model, perturbed_pulse, midpoint_substeps)
        rows.append(
            {
                "draw": draw,
                "positions_um": positions.tolist(),
                "mask": mask.tolist(),
                "rabi_factor": rabi_factor,
                "global_factor": global_factor,
                "local_factor": local_factor,
                **population_cycle_metrics(approximate),
            }
        )

    metric_keys = (
        "clockwise_mean",
        "clockwise_minimum",
        "counterclockwise_mean",
        "orientation_contrast",
        "spectator_leakage_mean",
    )
    summary = {}
    for key in metric_keys:
        values = np.asarray([row[key] for row in rows])
        summary[key] = {
            "p05": float(np.quantile(values, 0.05)),
            "median": float(np.median(values)),
            "p95": float(np.quantile(values, 0.95)),
        }

    clockwise_values = np.asarray([row["clockwise_mean"] for row in rows])
    selected_indices = sorted(
        {
            int(np.argmin(clockwise_values)),
            int(np.argmin(np.abs(clockwise_values - np.quantile(clockwise_values, 0.05)))),
            int(np.argmin(np.abs(clockwise_values - np.median(clockwise_values)))),
            int(np.argmax(clockwise_values)),
        }
    )
    spot_checks = []
    for index in selected_indices:
        row = rows[index]
        model = build_model(np.asarray(row["positions_um"]), np.asarray(row["mask"]))
        perturbed_pulse = scale_pulse(
            pulse,
            rabi_factor=row["rabi_factor"],
            global_factor=row["global_factor"],
            local_factor=row["local_factor"],
        )
        exact_metrics = population_cycle_metrics(exact_unitary(model, perturbed_pulse))
        spot_checks.append(
            {
                "draw": row["draw"],
                "midpoint_clockwise_mean": row["clockwise_mean"],
                "adaptive": exact_metrics,
                "absolute_clockwise_mean_error": abs(
                    row["clockwise_mean"] - exact_metrics["clockwise_mean"]
                ),
            }
        )
    return summary, spot_checks, rows


def native_ground_state_metrics(forward: np.ndarray, reverse: np.ndarray) -> dict:
    forward_target = float(abs(forward[1, 0]) ** 2)
    forward_wrong = float(abs(forward[2, 0]) ** 2)
    reverse_target = float(abs(reverse[2, 0]) ** 2)
    reverse_wrong = float(abs(reverse[1, 0]) ** 2)
    return {
        "forward_target_site_0": forward_target,
        "forward_wrong_site_1": forward_wrong,
        "reverse_target_site_1": reverse_target,
        "reverse_wrong_site_0": reverse_wrong,
        "two_schedule_router_contrast": (
            forward_target - forward_wrong + reverse_target - reverse_wrong
        ),
    }


def run_audit(robustness_draws: int = 128) -> dict:
    pulse = copy_pulse(FROZEN_PULSE)
    nominal_model = build_model()
    nominal_unitary = exact_unitary(nominal_model, pulse)
    nulls, reversal = null_and_reversal_audit(nominal_model, pulse, nominal_unitary)

    quantized = quantize_pulse(pulse)
    quantized_nominal = exact_unitary(nominal_model, quantized)
    quantized_geometry_model = build_model(HARDWARE_QUANTIZED_POSITIONS_UM)
    quantized_geometry_forward = exact_unitary(quantized_geometry_model, quantized)
    quantized_geometry_reverse = exact_unitary(
        quantized_geometry_model, reverse_waveform(quantized)
    )

    robustness_summary, robustness_spot_checks, robustness_rows = robustness_audit(
        pulse, draws=robustness_draws
    )
    return {
        "metadata": {
            "audit_type": "post-hoc adversarial falsification",
            "optimizer_included": False,
            "primary_solver": "DOP853",
            "primary_rtol": 5e-12,
            "primary_atol": 5e-14,
            "robustness_seed": ROBUSTNESS_SEED,
            "robustness_draws": robustness_draws,
            "verdict": "KILL_NAIVE_FULL_DYNAMICS_EXTENSION_OF_WEAK_DRIVE_QTV_BOUND",
            "scope": (
                "Does not refute the weak-drive Fourier-response theorem or an "
                "all-edge response-margin bound."
            ),
            "native_measurement_caveat": (
                "The complete four-leg population cycle uses non-native input "
                "configurations; only its forward/reverse ground-state routing "
                "legs are directly counts-measurable as two Aquila schedules."
            ),
        },
        "model": {
            "c6_rad_per_us_um6": C6_RAD_PER_US_UM6,
            "nominal_positions_um": NOMINAL_POSITIONS_UM.tolist(),
            "hardware_quantized_positions_um": HARDWARE_QUANTIZED_POSITIONS_UM.tolist(),
            "static_mask": STATIC_MASK.tolist(),
            "configuration_dimension": nominal_model.dimension,
            "face_cycle": [0, 1, 3, 2, 0],
        },
        "frozen_pulse": pulse,
        "waveform_validation_errors": waveform_validation(pulse),
        "nominal_adaptive": population_cycle_metrics(nominal_unitary),
        "reversal": reversal,
        "null_controls": nulls,
        "midpoint_convergence": midpoint_convergence(nominal_model, pulse, nominal_unitary),
        "quantized_waveform": {
            "pulse": quantized,
            "validation_errors": waveform_validation(quantized),
            "operator_norm_change": float(
                np.linalg.norm(quantized_nominal - nominal_unitary, ord=2)
            ),
            "nominal_geometry": population_cycle_metrics(quantized_nominal),
        },
        "hardware_quantized_geometry_and_waveform": {
            "interaction_diagonal_rad_per_us": np.diag(
                quantized_geometry_model.interaction
            ).tolist(),
            "forward": population_cycle_metrics(quantized_geometry_forward),
            "reverse": population_cycle_metrics(quantized_geometry_reverse),
            "native_ground_state": native_ground_state_metrics(
                quantized_geometry_forward, quantized_geometry_reverse
            ),
        },
        "robustness": {
            "perturbations": {
                "position_sigma_um": 0.03,
                "mask_additive_sigma": 0.01,
                "rabi_fraction_sigma": 0.01,
                "global_detuning_fraction_sigma": 0.01,
                "local_detuning_fraction_sigma": 0.01,
                "midpoint_substeps_per_interval": 24,
            },
            "summary": robustness_summary,
            "adaptive_spot_checks": robustness_spot_checks,
            "draws": robustness_rows,
        },
    }


def compact_payload(full_payload: dict) -> dict:
    compact = dict(full_payload)
    compact["robustness"] = {
        key: value for key, value in full_payload["robustness"].items() if key != "draws"
    }
    return compact


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--compact-output",
        type=Path,
        default=DEFAULT_COMPACT_OUTPUT,
        help="Compact JSON path; excludes the 128 individual perturbation rows.",
    )
    parser.add_argument(
        "--full-output",
        type=Path,
        default=None,
        help="Optional full JSON path including all individual perturbation rows.",
    )
    parser.add_argument("--robustness-draws", type=int, default=128)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = run_audit(robustness_draws=args.robustness_draws)
    write_json(args.compact_output, compact_payload(payload))
    if args.full_output is not None:
        write_json(args.full_output, payload)
    print(
        json.dumps(
            {
                "compact_output": str(args.compact_output),
                "full_output": str(args.full_output) if args.full_output else None,
                "verdict": payload["metadata"]["verdict"],
                "nominal_clockwise_mean": payload["nominal_adaptive"]["clockwise_mean"],
                "nominal_clockwise_minimum": payload["nominal_adaptive"][
                    "clockwise_minimum"
                ],
                "nominal_counterclockwise_mean": payload["nominal_adaptive"][
                    "counterclockwise_mean"
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
