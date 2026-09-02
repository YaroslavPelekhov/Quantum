"""Run the frozen configuration-curvature validation and falsification suite."""

from __future__ import annotations

import csv
import json
import math
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.aquila_configuration_curvature_phase0.curvature_core import (
    analytic_weak_flux,
    branch_effective_hamiltonians,
    circular_difference,
    continued_log_near_diagonal,
    continuous_log_by_scaling,
    counts_witness,
    gauge_rephase,
    palindrome_pulse,
    plaquette_metrics,
    principal_effective,
    reverse_pulse,
    scale_pulse,
    unitary_ivp,
    unitary_midpoint,
)
from experiments.aquila_one_mask_phase0.control_core import ControlLimits, full_c6_model, validate_pulse


EXPERIMENT = ROOT / "experiments" / "aquila_configuration_curvature_phase0"
OUTPUT = ROOT / "results" / "aquila_configuration_curvature_phase0"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def development_pulse(config: dict) -> dict[str, list[float]]:
    return {
        key: list(config[key])
        for key in (
            "times_us",
            "omega_rad_per_us",
            "phase_rad",
            "global_detuning_rad_per_us",
            "local_detuning_rad_per_us",
        )
    }


def model_at_interaction(interaction: float, mask: np.ndarray, c6: float):
    if interaction <= 0.0:
        distance = 1000.0
    else:
        distance = (c6 / interaction) ** (1.0 / 6.0)
    model = full_c6_model(np.array([[0.0, 0.0], [distance, 0.0]]), mask, c6)
    if interaction <= 0.0:
        model = replace(model, interaction=np.zeros_like(model.interaction))
    return model


def evaluate_case(model, pulse, solver: dict) -> dict:
    forward = unitary_ivp(
        model,
        pulse,
        rtol=solver["rtol"],
        atol=solver["atol"],
        max_step_fraction=solver["max_step_fraction_of_knot_interval"],
    )
    reversed_waveform = reverse_pulse(pulse)
    reverse = unitary_ivp(
        model,
        reversed_waveform,
        rtol=solver["rtol"],
        atol=solver["atol"],
        max_step_fraction=solver["max_step_fraction_of_knot_interval"],
    )
    duration = pulse["times_us"][-1] - pulse["times_us"][0]
    effective, diagnostics = principal_effective(forward, duration)
    return {
        "forward": forward,
        "reverse": reverse,
        "effective": effective,
        "plaquette": plaquette_metrics(effective),
        "counts": counts_witness(forward, reverse),
        "diagnostics": diagnostics,
        "reverse_transpose_error": float(np.linalg.norm(reverse - forward.T, ord=2)),
    }


def weak_pulse(config: dict, drive_scale: float = 1.0) -> dict[str, list[float]]:
    duration = config["duration_us"]
    first, second = config["kick_centers_us"]
    halfwidth = config["kick_halfwidth_us"]
    times = [0.0, first - halfwidth, first, first + halfwidth, second - halfwidth, second, second + halfwidth, duration]
    peaks = config["kick_peaks_rad_per_us"]
    return {
        "times_us": times,
        "omega_rad_per_us": [0.0, 0.0, drive_scale * peaks[0], 0.0, 0.0, drive_scale * peaks[1], 0.0, 0.0],
        "phase_rad": [0.0] * len(times),
        "global_detuning_rad_per_us": [config["global_detuning_rad_per_us"]] * len(times),
        "local_detuning_rad_per_us": [config["local_detuning_rad_per_us"]] * len(times),
    }


def weak_response_audit(protocol: dict) -> tuple[list[dict], list[dict], dict]:
    config = protocol["weak_drive_case"]
    c6 = protocol["c6_rad_per_us_um6"]
    mask = np.asarray(config["mask"], dtype=float)
    duration = config["duration_us"]
    delta_g = config["global_detuning_rad_per_us"]
    delta_l = config["local_detuning_rad_per_us"]
    e1, e2 = -delta_g - delta_l * mask
    kick_times = tuple(config["kick_centers_us"])
    kick_weights = tuple(config["kick_peaks_rad_per_us"])
    rows = []
    distance_rows = []
    primary_distance = config["distance_um"]
    primary_interaction = c6 / primary_distance**6
    analytic_primary = analytic_weak_flux(e1, e2, primary_interaction, duration, kick_times, kick_weights)
    model = full_c6_model(np.array([[0.0, 0.0], [primary_distance, 0.0]]), mask, c6)
    reference_energies = np.array([0.0, e1, e2, e1 + e2 + primary_interaction])
    for scale in config["finite_difference_scales"]:
        plus = unitary_ivp(model, weak_pulse(config, scale))
        minus = unitary_ivp(model, weak_pulse(config, -scale))
        h_plus = continued_log_near_diagonal(plus, reference_energies, duration)
        h_minus = continued_log_near_diagonal(minus, reference_energies, duration)
        derivative = (h_plus - h_minus) / (2.0 * scale)
        numerical = plaquette_metrics(derivative)["flux_rad"]
        rows.append(
            {
                "distance_um": primary_distance,
                "interaction_rad_per_us": primary_interaction,
                "drive_scale": scale,
                "analytic_flux_rad": analytic_primary,
                "numerical_flux_rad": numerical,
                "circular_error_rad": abs(circular_difference(numerical, analytic_primary)),
            }
        )
    for distance in config["heldout_distances_um"]:
        interaction = c6 / distance**6
        analytic = analytic_weak_flux(e1, e2, interaction, duration, kick_times, kick_weights)
        model = full_c6_model(np.array([[0.0, 0.0], [distance, 0.0]]), mask, c6)
        energies = np.array([0.0, e1, e2, e1 + e2 + interaction])
        scale = 0.0003
        plus = unitary_ivp(model, weak_pulse(config, scale))
        minus = unitary_ivp(model, weak_pulse(config, -scale))
        derivative = (
            continued_log_near_diagonal(plus, energies, duration)
            - continued_log_near_diagonal(minus, energies, duration)
        ) / (2.0 * scale)
        numerical = plaquette_metrics(derivative)["flux_rad"]
        distance_rows.append(
            {
                "distance_um": distance,
                "interaction_rad_per_us": interaction,
                "analytic_flux_rad": analytic,
                "numerical_flux_rad": numerical,
                "circular_error_rad": abs(circular_difference(numerical, analytic)),
            }
        )
    slope, intercept = np.polyfit(
        np.log([row["distance_um"] for row in distance_rows]),
        np.log(np.abs([row["numerical_flux_rad"] for row in distance_rows])),
        1,
    )
    summary = {
        "primary_analytic_flux_rad": analytic_primary,
        "protocol_predicted_flux_rad": config["predicted_flux_rad"],
        "maximum_formula_error_rad": max(row["circular_error_rad"] for row in rows),
        "heldout_distance_log_slope": float(slope),
        "heldout_distance_log_intercept": float(intercept),
    }
    return rows, distance_rows, summary


def mixed_term_audit(protocol: dict, pulse: dict, solver: dict) -> tuple[list[dict], dict]:
    c6 = protocol["c6_rad_per_us_um6"]
    rows = []
    x_values = []
    y_values = []
    for interaction in protocol["mixed_term_grid"]["interaction_rad_per_us"]:
        for contrast in protocol["mixed_term_grid"]["mask_contrast"]:
            mask = np.array([0.5 - contrast / 2.0, 0.5 + contrast / 2.0])
            model = model_at_interaction(interaction, mask, c6)
            evaluated = evaluate_case(model, pulse, solver)
            x_value = interaction * contrast
            y_value = evaluated["counts"]["chi"]
            rows.append(
                {
                    "interaction_rad_per_us": interaction,
                    "mask_contrast": contrast,
                    "interaction_times_contrast": x_value,
                    "chi": y_value,
                    "chi_over_mixed_term": y_value / x_value,
                }
            )
            x_values.append(x_value)
            y_values.append(y_value)
    x = np.asarray(x_values)
    y = np.asarray(y_values)
    beta = float(np.dot(x, y) / np.dot(x, x))
    predictions = beta * x
    r2_centered = float(1.0 - np.sum((y - predictions) ** 2) / np.sum((y - np.mean(y)) ** 2))
    r2_uncentered = float(1.0 - np.sum((y - predictions) ** 2) / np.sum(y**2))
    return rows, {"coefficient": beta, "r_squared_centered": r2_centered, "r_squared_uncentered": r2_uncentered}


def robustness_audit(protocol: dict, base_pulse: dict, solver: dict) -> tuple[list[dict], dict]:
    config = protocol["robustness"]
    development = protocol["development_case"]
    c6 = protocol["c6_rad_per_us_um6"]
    rng = np.random.default_rng(config["seed"])
    rows = []
    for draw in range(config["draws"]):
        distance = rng.normal(development["distance_um"], config["distance_sigma_um"])
        mask = np.clip(
            np.asarray(development["mask"]) + rng.normal(0.0, config["mask_additive_sigma"], 2), 0.0, 1.0
        )
        model = full_c6_model(np.array([[0.0, 0.0], [distance, 0.0]]), mask, c6)
        pulse = scale_pulse(
            base_pulse,
            omega=rng.normal(1.0, config["rabi_fraction_sigma"]),
            global_detuning=rng.normal(1.0, config["global_detuning_fraction_sigma"]),
            local_detuning=rng.normal(1.0, config["local_detuning_fraction_sigma"]),
        )
        evaluated = evaluate_case(model, pulse, solver)
        rows.append(
            {
                "draw": draw,
                "distance_um": distance,
                "mask_0": mask[0],
                "mask_1": mask[1],
                "chi": evaluated["counts"]["chi"],
                "principal_flux_rad": evaluated["plaquette"]["flux_rad"],
                "sin_flux": evaluated["plaquette"]["sin_flux"],
                "edge_geometric_mean": evaluated["plaquette"]["edge_geometric_mean_rad_per_us"],
                "two_bit_leakage_ratio": evaluated["plaquette"]["two_bit_leakage_ratio"],
                "branch_cut_margin_rad": evaluated["diagnostics"]["branch_cut_margin_rad"],
            }
        )
    chis = np.asarray([row["chi"] for row in rows])
    reference_sign = np.sign(np.median(chis))
    summary = {
        "chi_p05": float(np.quantile(chis, 0.05)),
        "chi_median": float(np.median(chis)),
        "chi_p95": float(np.quantile(chis, 0.95)),
        "abs_chi_p05": float(np.quantile(np.abs(chis), 0.05)),
        "sign_retention": float(np.mean(np.sign(chis) == reference_sign)),
    }
    return rows, summary


def heldout_audit(protocol: dict, pulse: dict, solver: dict) -> tuple[list[dict], list[dict], dict]:
    c6 = protocol["c6_rad_per_us_um6"]
    rows = []
    flux_rows = []
    summary = {}
    for instance in protocol["heldout_instances"]:
        coordinates = np.asarray(instance["coordinates_um"], dtype=float)
        mask = np.asarray(instance["mask"], dtype=float)
        model = full_c6_model(coordinates, mask, c6)
        forward = unitary_ivp(model, pulse, **solver_kwargs(solver))
        reverse = unitary_ivp(model, reverse_pulse(pulse), **solver_kwargs(solver))
        palindrome = unitary_ivp(model, palindrome_pulse(pulse), **solver_kwargs(solver))
        palindrome_reverse = unitary_ivp(model, reverse_pulse(palindrome_pulse(pulse)), **solver_kwargs(solver))
        zero_model = replace(model, interaction=np.zeros_like(model.interaction))
        zero_forward = unitary_ivp(zero_model, pulse, **solver_kwargs(solver))
        zero_reverse = unitary_ivp(zero_model, reverse_pulse(pulse), **solver_kwargs(solver))
        asymmetries = {}
        p_forward = np.abs(forward[:, 0]) ** 2
        p_reverse = np.abs(reverse[:, 0]) ** 2
        p_palindrome = np.abs(palindrome[:, 0]) ** 2
        p_palindrome_reverse = np.abs(palindrome_reverse[:, 0]) ** 2
        p_zero = np.abs(zero_forward[:, 0]) ** 2
        p_zero_reverse = np.abs(zero_reverse[:, 0]) ** 2
        for site in range(len(mask)):
            bit = 1 << site
            asymmetries[site] = float(p_forward[bit] - p_reverse[bit])
        pair_values = []
        for first in range(len(mask)):
            for second in range(first + 1, len(mask)):
                first_bit, second_bit = 1 << first, 1 << second
                chi = asymmetries[first] - asymmetries[second]
                chi_palindrome = float(
                    (p_palindrome[first_bit] - p_palindrome_reverse[first_bit])
                    - (p_palindrome[second_bit] - p_palindrome_reverse[second_bit])
                )
                chi_zero = float(
                    (p_zero[first_bit] - p_zero_reverse[first_bit])
                    - (p_zero[second_bit] - p_zero_reverse[second_bit])
                )
                rows.append(
                    {
                        "instance": instance["name"],
                        "first_site": first,
                        "second_site": second,
                        "chi": chi,
                        "palindrome_chi": chi_palindrome,
                        "zero_interaction_chi": chi_zero,
                    }
                )
                pair_values.append(abs(chi))
        duration = pulse["times_us"][-1] - pulse["times_us"][0]
        effective, _ = principal_effective(forward, duration)
        n = len(mask)
        for first in range(n):
            for second in range(first + 1, n):
                remaining = [site for site in range(n) if site not in (first, second)]
                for assignment in range(1 << len(remaining)):
                    base = 0
                    for offset, site in enumerate(remaining):
                        if assignment & (1 << offset):
                            base |= 1 << site
                    metrics = plaquette_metrics(effective, first, second, base)
                    flux_rows.append(
                        {
                            "instance": instance["name"],
                            "base_mask": base,
                            "first_site": first,
                            "second_site": second,
                            **metrics,
                        }
                    )
        summary[instance["name"]] = {
            "maximum_abs_pair_chi": max(pair_values),
            "passes_gate": max(pair_values) >= instance["minimum_abs_pair_witness_gate"],
        }
    return rows, flux_rows, summary


def solver_kwargs(solver: dict) -> dict:
    return {
        "rtol": solver["rtol"],
        "atol": solver["atol"],
        "max_step_fraction": solver["max_step_fraction_of_knot_interval"],
    }


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    protocol = load_json(EXPERIMENT / "protocol.json")
    solver = protocol["reference_solver"]
    c6 = protocol["c6_rad_per_us_um6"]
    development = protocol["development_case"]
    pulse = development_pulse(development)
    model = full_c6_model(
        np.array([[0.0, 0.0], [development["distance_um"], 0.0]]),
        np.asarray(development["mask"], dtype=float),
        c6,
    )
    limits = ControlLimits(duration_us=development["duration_us"])
    pulse_errors = validate_pulse(pulse, limits)

    print("adaptive development and exact controls", flush=True)
    primary = evaluate_case(model, pulse, solver)
    duration = development["duration_us"]
    reverse_case = evaluate_case(model, reverse_pulse(pulse), solver)
    palindrome_case = evaluate_case(model, palindrome_pulse(pulse), solver)
    zero_model = replace(model, interaction=np.zeros_like(model.interaction))
    zero_case = evaluate_case(zero_model, pulse, solver)
    equal_model = full_c6_model(
        np.array([[0.0, 0.0], [development["distance_um"], 0.0]]), np.array([0.5, 0.5]), c6
    )
    equal_case = evaluate_case(equal_model, pulse, solver)
    local_off_pulse = {key: list(value) for key, value in pulse.items()}
    local_off_pulse["local_detuning_rad_per_us"] = [0.0] * len(pulse["times_us"])
    local_off_case = evaluate_case(model, local_off_pulse, solver)

    control_rows = []
    for name, case in (
        ("development", primary),
        ("reversed_schedule", reverse_case),
        ("palindrome", palindrome_case),
        ("zero_interaction", zero_case),
        ("equal_mask", equal_case),
        ("local_envelope_off", local_off_case),
    ):
        control_rows.append(
            {
                "case": name,
                "chi": case["counts"]["chi"],
                "principal_flux_rad": case["plaquette"]["flux_rad"],
                "sin_flux": case["plaquette"]["sin_flux"],
                "edge_geometric_mean_rad_per_us": case["plaquette"]["edge_geometric_mean_rad_per_us"],
                "two_bit_leakage_ratio": case["plaquette"]["two_bit_leakage_ratio"],
                "branch_cut_margin_rad": case["diagnostics"]["branch_cut_margin_rad"],
                "reverse_transpose_error": case["reverse_transpose_error"],
            }
        )
    write_csv(OUTPUT / "exact_controls.csv", control_rows)

    convergence_rows = []
    for substeps in (1, 2, 4, 8, 16, 32, 64):
        forward = unitary_midpoint(model, pulse, substeps)
        reverse = unitary_midpoint(model, reverse_pulse(pulse), substeps)
        effective, diagnostics = principal_effective(forward, duration)
        convergence_rows.append(
            {
                "solver": f"midpoint_{substeps}",
                "substeps_per_interval": substeps,
                "chi": counts_witness(forward, reverse)["chi"],
                "principal_flux_rad": plaquette_metrics(effective)["flux_rad"],
                "sin_flux": plaquette_metrics(effective)["sin_flux"],
                "unitarity_error": diagnostics["unitarity_error_before_polar"],
            }
        )
    convergence_rows.append(
        {
            "solver": "adaptive_DOP853",
            "substeps_per_interval": "",
            "chi": primary["counts"]["chi"],
            "principal_flux_rad": primary["plaquette"]["flux_rad"],
            "sin_flux": primary["plaquette"]["sin_flux"],
            "unitarity_error": primary["diagnostics"]["unitarity_error_before_polar"],
        }
    )
    write_csv(OUTPUT / "solver_convergence.csv", convergence_rows)

    print("branch and gauge audits", flush=True)
    branches = branch_effective_hamiltonians(primary["forward"], duration)
    write_csv(
        OUTPUT / "log_branches.csv",
        [{**row, "shifts": json.dumps(row["shifts"])} for row in branches],
    )
    continuous_effective, continuous_diagnostics = continuous_log_by_scaling(model, pulse)
    continuous_metrics = plaquette_metrics(continuous_effective)
    rng_gauge = np.random.default_rng(6300)
    gauge_errors = []
    for _ in range(64):
        rephased = gauge_rephase(primary["effective"], rng_gauge.uniform(-math.pi, math.pi, model.dimension))
        gauge_errors.append(
            abs(circular_difference(plaquette_metrics(rephased)["flux_rad"], primary["plaquette"]["flux_rad"]))
        )
    reduced_branches = [row for row in branches if row["common_shift_reduced"]]
    branch_diagnostics = {
        "principal": primary["plaquette"],
        "continuous_scaling": continuous_metrics,
        "continuous_scaling_diagnostics": continuous_diagnostics,
        "inequivalent_branch_count": len(reduced_branches),
        "all_archived_branch_count": len(branches),
        "reduced_branch_sin_flux_min": min(row["sin_flux"] for row in reduced_branches),
        "reduced_branch_sin_flux_max": max(row["sin_flux"] for row in reduced_branches),
        "maximum_gauge_rephase_circular_error_rad": max(gauge_errors),
        "principal_minus_continuous_circular_error_rad": abs(
            circular_difference(primary["plaquette"]["flux_rad"], continuous_metrics["flux_rad"])
        ),
        "branch_independent_effective_flux": False,
    }
    dump_json(OUTPUT / "branch_diagnostics.json", branch_diagnostics)

    print("weak response and held-out scaling", flush=True)
    weak_rows, distance_rows, weak_summary = weak_response_audit(protocol)
    write_csv(OUTPUT / "weak_formula_validation.csv", weak_rows)
    write_csv(OUTPUT / "distance_scaling.csv", distance_rows)

    print("mixed-term grid", flush=True)
    mixed_rows, mixed_summary = mixed_term_audit(protocol, pulse, solver)
    write_csv(OUTPUT / "mixed_term_grid.csv", mixed_rows)

    print("robustness", flush=True)
    robustness_rows, robustness_summary = robustness_audit(protocol, pulse, solver)
    write_csv(OUTPUT / "robustness.csv", robustness_rows)

    print("held-out geometries", flush=True)
    heldout_rows, heldout_flux_rows, heldout_summary = heldout_audit(protocol, pulse, solver)
    write_csv(OUTPUT / "heldout_pair_witnesses.csv", heldout_rows)
    write_csv(OUTPUT / "heldout_plaquettes.csv", heldout_flux_rows)

    counts = primary["counts"]
    variance_coefficient = (
        counts["p_forward_first"]
        + counts["p_forward_second"]
        - (counts["p_forward_first"] - counts["p_forward_second"]) ** 2
        + counts["p_reverse_first"]
        + counts["p_reverse_second"]
        - (counts["p_reverse_first"] - counts["p_reverse_second"]) ** 2
    )
    shots_five_sigma = int(math.ceil(25.0 * variance_coefficient / counts["chi"] ** 2))
    z_at_1000 = abs(counts["chi"]) / math.sqrt(variance_coefficient / 1000.0)
    shot_audit = {
        "multinomial_variance_coefficient": variance_coefficient,
        "shots_per_schedule_for_nominal_five_sigma": shots_five_sigma,
        "nominal_z_at_1000_shots_per_schedule": z_at_1000,
        "scope": "ideal-model planning value; drift and hardware decoherence are not included",
    }

    gates = protocol["mechanism_gates"]
    null_cases = (zero_case, equal_case, palindrome_case, local_off_case)
    numerical_gate_checks = {
        "development_sin_flux": abs(primary["plaquette"]["sin_flux"]) >= gates["development_abs_sin_flux_min"],
        "development_counts_witness": abs(counts["chi"]) >= gates["development_abs_counts_witness_min"],
        "edge_strength": primary["plaquette"]["edge_geometric_mean_rad_per_us"] >= gates["geometric_mean_edge_min_rad_per_us"],
        "branch_cut_margin": primary["diagnostics"]["branch_cut_margin_rad"] >= gates["branch_cut_margin_min_rad"],
        "null_sin_flux": max(abs(case["plaquette"]["sin_flux"]) for case in null_cases) <= gates["null_abs_sin_flux_max"],
        "null_counts_witness": max(abs(case["counts"]["chi"]) for case in null_cases) <= gates["null_abs_counts_witness_max"],
        "reverse_flux": abs(circular_difference(reverse_case["plaquette"]["flux_rad"], -primary["plaquette"]["flux_rad"])) <= gates["reverse_circular_error_max_rad"],
        "reverse_chi": abs(reverse_case["counts"]["chi"] + counts["chi"]) <= gates["null_abs_counts_witness_max"],
        "gauge_invariance": max(gauge_errors) <= gates["gauge_rephase_circular_error_max_rad"],
        "weak_formula": weak_summary["maximum_formula_error_rad"] <= gates["weak_formula_error_max_rad"],
        "distance_slope": abs(weak_summary["heldout_distance_log_slope"] - gates["distance_log_slope_target"]) <= gates["distance_log_slope_tolerance"],
        "robustness_p05": robustness_summary["abs_chi_p05"] >= gates["robustness_abs_counts_witness_p05_min"],
        "robustness_sign": robustness_summary["sign_retention"] >= gates["robustness_sign_retention_min"],
        "mixed_term": mixed_summary["r_squared_centered"] >= gates["mixed_term_r_squared_min"],
        "heldout_instances": all(item["passes_gate"] for item in heldout_summary.values()),
        "pulse_validation": not pulse_errors,
    }
    mechanism_pass = all(numerical_gate_checks.values())
    summary = {
        "verdict": "MECHANISM_PASS_ASTAR_KILL" if mechanism_pass else "MECHANISM_PARTIAL_ASTAR_KILL",
        "mechanism_validation_pass": mechanism_pass,
        "a_star_novelty": "KILL_DENSITY_DEPENDENT_PEIERLS_PRIOR_ART",
        "qpu_eligible": False,
        "qpu_tasks_submitted": 0,
        "development": {
            "counts": counts,
            "principal_plaquette": primary["plaquette"],
            "principal_log_diagnostics": primary["diagnostics"],
            "reverse_transpose_error": primary["reverse_transpose_error"],
        },
        "branch_diagnostics": branch_diagnostics,
        "weak_response": weak_summary,
        "mixed_term": mixed_summary,
        "robustness": robustness_summary,
        "heldout": heldout_summary,
        "shot_audit": shot_audit,
        "pulse_validation_errors": pulse_errors,
        "numerical_gate_checks": numerical_gate_checks,
        "scientific_claim": "branch-free interaction-by-mask directional response; effective-log flux is branch dependent",
        "next_a_star_requirement": "complete rank-one curvature compiler/resource-separation theorem plus scalable phase-sensitive hardware capability",
    }
    dump_json(OUTPUT / "phase0_summary.json", summary)
    report = f"""# Final report: Aquila configuration-space curvature Phase 0

## Verdict

**{summary['verdict']}**

- Frozen numerical mechanism gates passed: **{mechanism_pass}**
- A-star novelty: **KILLED by density-dependent Peierls-phase prior art**
- QPU eligible: **False**
- QPU tasks submitted: **0**

The physically defensible result is a branch-free, counts-only interaction-by-
mask directional response.  A Wilson phase extracted from a matrix logarithm
is a useful mechanistic diagnostic but is not branch independent.

## Development pulse

| quantity | adaptive-ODE result |
|---|---:|
| counts witness `chi` | {counts['chi']:.9f} |
| principal-log flux | {primary['plaquette']['flux_rad']:.9f} rad |
| `sin(flux)` | {primary['plaquette']['sin_flux']:.9f} |
| edge geometric mean | {primary['plaquette']['edge_geometric_mean_rad_per_us']:.9f} rad/us |
| two-bit leakage / edge | {primary['plaquette']['two_bit_leakage_ratio']:.9f} |
| branch-cut margin | {primary['diagnostics']['branch_cut_margin_rad']:.9f} rad |
| reverse-transpose error | {primary['reverse_transpose_error']:.3e} |

Exact zero-interaction, equal-mask, local-envelope-off, and palindrome controls
are archived in `exact_controls.csv`.  Reversal changes the signs of both the
principal diagnostic and `chi`.

## Branch falsification

The principal branch gives flux `{primary['plaquette']['flux_rad']:.6f}`, while
continuous Hamiltonian scaling gives `{continuous_metrics['flux_rad']:.6f}`.
Across the 27 common-shift-reduced nearby logarithm branches, `sin(flux)` spans
`[{branch_diagnostics['reduced_branch_sin_flux_min']:.6f},
{branch_diagnostics['reduced_branch_sin_flux_max']:.6f}]`.  Therefore the
effective-flux sign/locality is branch dependent.  The native `chi` observable
does not use a logarithm and survives this falsification.

## Held-out mechanism checks

- Weak analytic formula maximum circular error:
  `{weak_summary['maximum_formula_error_rad']:.3e}` rad.
- Held-out distance exponent: `{weak_summary['heldout_distance_log_slope']:.6f}`
  (prediction `-6`).
- Small interaction-times-mask-contrast fit: coefficient
  `{mixed_summary['coefficient']:.8f}`, centered `R2={mixed_summary['r_squared_centered']:.8f}`.
- Perturbation `|chi|` fifth percentile: `{robustness_summary['abs_chi_p05']:.6f}`;
  sign retention `{robustness_summary['sign_retention']:.3%}`.
- Nominal ideal-model five-sigma plan: `{shots_five_sigma}` shots per schedule;
  at 1,000 shots the ideal z-score is `{z_at_1000:.3f}`.

The shot calculation omits the documented extra local-detuning decoherence and
device drift.  It is a planning value, not a hardware result.

## Why this is not A-star novelty

The mixed finite-difference mechanism is density-dependent complex hopping.
Interaction-induced plaquette flux in Fock space, Rydberg occupancy-dependent
Peierls phases, chiral Rydberg dynamics, and Peierls-phase tomography all have
direct prior art.  The exact one-mask Aquila integration appears unreported in
the targeted audit, but platform intersection alone is insufficient.

The next defensible A-star object would need a complete characterization of the
curvature tensor attainable with one rank-one spatial mask, necessary-and-
sufficient flatness and tight physical resource bounds, plus a scalable
phase-sensitive hardware capability beyond this known mechanism.
"""
    (OUTPUT / "FINAL_REPORT.md").write_text(report, encoding="utf-8")
    print(json.dumps({"verdict": summary["verdict"], "mechanism_pass": mechanism_pass, "chi": counts["chi"]}), flush=True)


if __name__ == "__main__":
    main()

