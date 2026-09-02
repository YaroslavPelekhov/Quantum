"""Run the frozen Aquila one-static-mask Phase-0 screen."""

from __future__ import annotations

import csv
import json
import os
from dataclasses import asdict, replace
from pathlib import Path

import networkx as nx
import numpy as np

from experiments.aquila_one_mask_phase0.control_core import (
    ControlLimits,
    addressability_capacity,
    full_c6_model,
    hard_blockade_model,
    max_local_detuning_area,
    phase_gauge_error,
    reflection_commutator_norm,
    unavoidable_operator_error,
    validate_pulse,
)
from experiments.aquila_one_mask_phase0.lie_closure import control_generators, lie_dimension
from experiments.aquila_one_mask_phase0.pulse_opt import (
    dephased_fidelity,
    optimize_pulses,
    pulse_fidelity,
    quantized_pulse,
    scaled_pulse,
)


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = ROOT / "experiments" / "aquila_one_mask_phase0"
OUTPUT = ROOT / "results" / "aquila_one_mask_phase0"
CHECKPOINT = OUTPUT / "optimization_checkpoint.json"


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


def structural_audit(models: dict[str, object]) -> tuple[list[dict], dict]:
    tolerances = (1e-8, 1e-9, 1e-10)
    rows = []
    for model_name in ("hard_blockade_ideal", "hard_blockade_projected_c6", "full_c6"):
        model = models[model_name]
        for mode in ("global_only", "gradient_mask"):
            target_dimension = model.dimension**2 - 1
            for tolerance in tolerances:
                rank = lie_dimension(control_generators(model, mode), tolerance=tolerance)
                rows.append(
                    {
                        "model": model_name,
                        "hilbert_dimension": model.dimension,
                        "spatial_mode": mode,
                        "tolerance": tolerance,
                        "lie_rank": rank,
                        "su_dimension": target_dimension,
                        "is_full_su": rank == target_dimension,
                    }
                )
    phase_error = phase_gauge_error()
    audit = {
        "phase_gauge_operator_error": phase_error,
        "global_reflection_commutator_norm_full_c6": reflection_commutator_norm(models["full_c6"]),
        "gradient_full_rank_tolerance_stable": all(
            row["is_full_su"]
            for row in rows
            if row["spatial_mode"] == "gradient_mask"
            and row["model"] in {"hard_blockade_projected_c6", "full_c6"}
        ),
    }
    return rows, audit


def checkpoint_key(model_name: str, mode: str, target: int) -> str:
    return f"{model_name}:{mode}:target_{target}"


def run_optimization_jobs(protocol: dict, models: dict[str, object], limits: ControlLimits) -> dict:
    checkpoint = load_json(CHECKPOINT) if CHECKPOINT.exists() else {"jobs": {}}
    quick = os.environ.get("AQUILA_QUICK", "0") == "1"
    optimizer = protocol["optimizer"]
    seeds = optimizer["seeds"][:1] if quick else optimizer["seeds"]
    adam_steps = 10 if quick else optimizer["adam_steps"]
    lbfgs_steps = 0 if quick else optimizer["lbfgs_steps"]
    jobs = [
        ("full_c6", "gradient_mask", True),
        ("hard_blockade_projected_c6", "gradient_mask", True),
        ("full_c6", "global_only", False),
        ("full_c6_uniform", "uniform_mask", True),
    ]
    for model_name, mode, local_enabled in jobs:
        for target in (5, 10):
            key = checkpoint_key(model_name, mode, target)
            if key in checkpoint["jobs"] and not quick:
                print(f"resume {key}", flush=True)
                continue
            print(f"optimize {key}", flush=True)
            results = optimize_pulses(
                models[model_name],
                target,
                seeds=seeds,
                limits=limits,
                knot_count=optimizer["knot_count"] if "knot_count" in optimizer else protocol["provisional_hardware_constraints"]["knot_count"],
                adam_steps=adam_steps,
                adam_learning_rate=optimizer["adam_learning_rate"],
                lbfgs_steps=lbfgs_steps,
                substeps=optimizer["propagation_substeps_per_interval"],
                local_enabled=local_enabled,
            )
            checkpoint["jobs"][key] = {
                "model": model_name,
                "mode": mode,
                "target_mask": target,
                "local_enabled": local_enabled,
                "quick": quick,
                "results": [asdict(item) for item in results],
            }
            dump_json(CHECKPOINT, checkpoint)
    if quick:
        raise RuntimeError("AQUILA_QUICK produced a smoke-test checkpoint only; remove it before the frozen run")
    return checkpoint


def evaluate_search(checkpoint: dict, models: dict[str, object]) -> tuple[list[dict], dict[int, dict], dict[int, dict]]:
    rows: list[dict] = []
    candidate_pool: dict[int, list[dict]] = {5: [], 10: []}
    hb_pool: dict[int, list[dict]] = {5: [], 10: []}
    for job in checkpoint["jobs"].values():
        model = models[job["model"]]
        target = int(job["target_mask"])
        for result in job["results"]:
            fidelity = pulse_fidelity(model, result["pulse"], target, substeps=8)
            full_transfer = ""
            if job["model"] == "hard_blockade_projected_c6":
                full_transfer = pulse_fidelity(models["full_c6"], result["pulse"], target, substeps=8)
                hb_pool[target].append(
                    {
                        "pulse": result["pulse"],
                        "hb_fidelity": fidelity,
                        "full_c6_fidelity": full_transfer,
                        "seed": result["seed"],
                    }
                )
                candidate_pool[target].append(
                    {
                        "source": "hard_blockade_transfer",
                        "pulse": result["pulse"],
                        "full_c6_fidelity": full_transfer,
                        "seed": result["seed"],
                    }
                )
            elif job["mode"] == "gradient_mask":
                candidate_pool[target].append(
                    {
                        "source": "direct_full_c6",
                        "pulse": result["pulse"],
                        "full_c6_fidelity": fidelity,
                        "seed": result["seed"],
                    }
                )
            rows.append(
                {
                    "model": job["model"],
                    "mode": job["mode"],
                    "target_mask": target,
                    "seed": result["seed"],
                    "optimization_grid_fidelity": result["fidelity_optimization_grid"],
                    "independent_high_resolution_fidelity": fidelity,
                    "full_c6_transfer_fidelity": full_transfer,
                }
            )
    best_candidates = {target: max(pool, key=lambda item: item["full_c6_fidelity"]) for target, pool in candidate_pool.items()}
    best_hb = {target: max(pool, key=lambda item: item["hb_fidelity"]) for target, pool in hb_pool.items()}
    return rows, best_candidates, best_hb


def robustness_audit(
    protocol: dict,
    coordinates: np.ndarray,
    mask: np.ndarray,
    candidates: dict[int, dict],
) -> tuple[list[dict], dict]:
    config = protocol["robustness"]
    rng = np.random.default_rng(config["seed"])
    rows = []
    for target, candidate in candidates.items():
        for draw in range(config["draws"]):
            perturbed_coordinates = coordinates + rng.normal(
                0.0, config["coordinate_jitter_sigma_um"], size=coordinates.shape
            )
            perturbed_mask = np.clip(
                mask + rng.normal(0.0, config["mask_additive_sigma"], size=mask.shape), 0.0, 1.0
            )
            model = full_c6_model(perturbed_coordinates, perturbed_mask)
            pulse = scaled_pulse(
                candidate["pulse"],
                rabi_factor=rng.normal(1.0, config["rabi_fraction_sigma"]),
                global_factor=rng.normal(1.0, config["global_detuning_fraction_sigma"]),
                local_factor=rng.normal(1.0, config["local_detuning_fraction_sigma"]),
            )
            rows.append(
                {
                    "target_mask": target,
                    "draw": draw,
                    "fidelity": pulse_fidelity(model, pulse, target, substeps=8),
                }
            )
    summary = {}
    for target in candidates:
        values = np.asarray([row["fidelity"] for row in rows if row["target_mask"] == target])
        summary[str(target)] = {
            "median": float(np.median(values)),
            "fifth_percentile": float(np.quantile(values, 0.05)),
            "minimum": float(np.min(values)),
        }
    return rows, summary


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    protocol = load_json(EXPERIMENT / "protocol.json")
    coordinates = np.asarray(protocol["primary_instance"]["x_um"], dtype=float)
    coordinates = np.column_stack((coordinates, np.asarray(protocol["primary_instance"]["y_um"], dtype=float)))
    mask = np.asarray(protocol["primary_instance"]["mask"], dtype=float)
    uniform_mask = np.ones_like(mask)
    c6 = protocol["hamiltonian"]["c6_rad_per_us_um6"]
    graph = nx.path_graph(4)
    hb_projected = hard_blockade_model(graph, coordinates, mask, c6)
    models = {
        "hard_blockade_projected_c6": hb_projected,
        "hard_blockade_ideal": replace(hb_projected, name="hard_blockade_ideal", interaction=np.zeros_like(hb_projected.interaction)),
        "full_c6": full_c6_model(coordinates, mask, c6),
        "full_c6_uniform": full_c6_model(coordinates, uniform_mask, c6),
    }
    limits = ControlLimits()

    print("structural audit", flush=True)
    lie_rows, structural = structural_audit(models)
    write_csv(OUTPUT / "lie_ranks.csv", lie_rows)
    checkpoint = run_optimization_jobs(protocol, models, limits)
    search_rows, candidates, best_hb = evaluate_search(checkpoint, models)
    write_csv(OUTPUT / "pulse_search.csv", search_rows)

    quantization = {}
    validation = {}
    dephasing_rows = []
    for target, candidate in candidates.items():
        quantized = quantized_pulse(candidate["pulse"])
        quantized_fidelity = pulse_fidelity(models["full_c6"], quantized, target, substeps=16)
        nominal_fidelity = pulse_fidelity(models["full_c6"], candidate["pulse"], target, substeps=16)
        quantization[str(target)] = {
            "nominal_fidelity_substeps16": nominal_fidelity,
            "quantized_fidelity_substeps16": quantized_fidelity,
            "drop": nominal_fidelity - quantized_fidelity,
        }
        validation[str(target)] = validate_pulse(quantized, limits)
        for gamma in protocol["robustness"]["dephasing_rates_per_us"]:
            dephasing_rows.append(
                {
                    "target_mask": target,
                    "gamma_per_us": gamma,
                    "fidelity": dephased_fidelity(models["full_c6"], quantized, target, gamma, substeps=8),
                }
            )
    write_csv(OUTPUT / "dephasing_bracket.csv", dephasing_rows)

    print("robustness audit", flush=True)
    robustness_rows, robustness = robustness_audit(protocol, coordinates, mask, candidates)
    write_csv(OUTPUT / "robustness.csv", robustness_rows)

    area = max_local_detuning_area(
        limits.duration_us, limits.local_detuning_abs_max, limits.local_detuning_slew_max
    )
    action_audit = {
        "ramp_limited_area_rad": area,
        "perfect_two_frequency_unitary_capacity_upper_bound": addressability_capacity(area, 0.0),
        "operator_tolerance_0p1_capacity_upper_bound": addressability_capacity(area, 0.1),
        "unavoidable_operator_error_at_256_sites": unavoidable_operator_error(area, 256),
        "scope": "necessary two-frequency X-versus-I ensemble bound; not a universal arbitrary-geometry bound",
    }

    numerical = {}
    for target in (5, 10):
        hb_drop = best_hb[target]["hb_fidelity"] - best_hb[target]["full_c6_fidelity"]
        numerical[str(target)] = {
            "selected_source": candidates[target]["source"],
            "selected_seed": candidates[target]["seed"],
            "full_c6_fidelity": candidates[target]["full_c6_fidelity"],
            "best_hard_blockade_fidelity": best_hb[target]["hb_fidelity"],
            "hard_blockade_to_full_c6_fidelity": best_hb[target]["full_c6_fidelity"],
            "hard_blockade_transfer_drop": hb_drop,
            "quantization_drop": quantization[str(target)]["drop"],
            "robustness_fifth_percentile": robustness[str(target)]["fifth_percentile"],
        }

    gates = protocol["pass_gates"]
    numerical_pass = (
        all(item["full_c6_fidelity"] >= gates["both_full_c6_target_fidelity_min"] for item in numerical.values())
        and all(item["hard_blockade_transfer_drop"] <= gates["hard_blockade_to_full_c6_drop_max"] for item in numerical.values())
        and all(item["quantization_drop"] <= gates["quantization_drop_max"] for item in numerical.values())
        and all(item["robustness_fifth_percentile"] >= gates["robustness_fifth_percentile_min"] for item in numerical.values())
        and structural["gradient_full_rank_tolerance_stable"]
        and all(not errors for errors in validation.values())
    )
    prior_art_clear = False
    qpu_eligible = numerical_pass and prior_art_clear
    verdict = "CPU_CAPABILITY_PASS_BUT_ASTAR_KILLED" if numerical_pass else "KILL_ONE_MASK_PHASE0"
    summary = {
        "experiment": "aquila_one_static_mask_temporal_reprogramming_phase0",
        "verdict": verdict,
        "numerical_pass": numerical_pass,
        "a_star_novelty": "KILL_BROAD_ONE_MASK_CONTROLLABILITY",
        "prior_art_clearance": prior_art_clear,
        "qpu_eligible": qpu_eligible,
        "qpu_tasks_submitted": 0,
        "structural": structural,
        "action_audit": action_audit,
        "targets": numerical,
        "quantization": quantization,
        "pulse_validation_errors": validation,
        "robustness": robustness,
        "dephasing_bracket": dephasing_rows,
        "next_hypothesis": "interaction-induced gauge-invariant configuration-space curvature from finite C6 tails and one static mask",
    }
    dump_json(OUTPUT / "phase0_summary.json", summary)
    dump_json(
        OUTPUT / "best_pulses.json",
        {
            str(target): {
                "source": candidate["source"],
                "seed": candidate["seed"],
                "full_c6_fidelity_substeps8": candidate["full_c6_fidelity"],
                "pulse": candidate["pulse"],
            }
            for target, candidate in candidates.items()
        },
    )
    report = f"""# Final report: Aquila one-static-mask Phase 0

## Verdict

**{verdict}**

- CPU numerical gates passed: **{numerical_pass}**
- Broad A-star novelty: **KILLED by prior art**
- QPU eligible under the preregistration: **{qpu_eligible}**
- QPU tasks submitted: **0**

The one-mask gradient is a real spatial symmetry-breaking resource, but the
underlying frequency-selective/Vandermonde controllability mechanism is known.
The run is retained as a hardware-feasibility audit and an enabling lemma, not
rebranded as a primary novelty claim.

## Primary target results

| target mask | full-C6 fidelity | HB fidelity | HB to full-C6 | quantization drop | robustness p05 |
|---:|---:|---:|---:|---:|---:|
"""
    for target, item in numerical.items():
        report += (
            f"| `{int(target):04b}` | {item['full_c6_fidelity']:.6f} | "
            f"{item['best_hard_blockade_fidelity']:.6f} | {item['hard_blockade_to_full_c6_fidelity']:.6f} | "
            f"{item['quantization_drop']:.3e} | {item['robustness_fifth_percentile']:.6f} |\n"
        )
    report += f"""

Global-only and uniform-mask dynamics obey an exact per-target fidelity ceiling
of 0.5 by reflection symmetry; this does not depend on optimizer performance.

## Structural falsification

- Rotating-frame phase-gauge error: `{structural['phase_gauge_operator_error']:.3e}`.
- Global-only reflection commutator norm: `{structural['global_reflection_commutator_norm_full_c6']:.3e}`.
- Gradient-mask full Lie rank stable across frozen tolerances:
  `{structural['gradient_full_rank_tolerance_stable']}`.
- Ramp-limited local-detuning action in the provisional 4 us window:
  `{area:.6f} rad`.
- Necessary perfect two-frequency X/I addressability capacity from this action:
  at most `{action_audit['perfect_two_frequency_unitary_capacity_upper_bound']}` labels.
- At 256 packed labels the unavoidable operator-norm error from this necessary
  bound is at least `{action_audit['unavoidable_operator_error_at_256_sites']:.6f}`.

The action result is an ensemble/twin-site bound, not a universal limit for
arbitrary geometries whose interactions already distinguish sites.

## Hardware decision

No hardware job was submitted.  Local detuning is an experimental Braket Direct
capability, its use carries an extra decoherence warning, this environment has
neither a live device snapshot nor confirmed access, and the adversarial
prior-art gate is negative.  The saved pulses are simulation artifacts, not
claimed hardware programs.

## Research continuation

The next hypothesis changes the scientific object: use finite native `C6/r^6`
tails plus a nonlinear, time-asymmetric spectral response to generate a
gauge-invariant Wilson-loop phase on an independent-set configuration
plaquette.  It must vanish for zero interaction, equal masks, palindromic
drives, and large spacing, reverse sign under schedule reversal, and survive a
matrix-log branch audit before it can become a hardware candidate.
"""
    (OUTPUT / "FINAL_REPORT.md").write_text(report, encoding="utf-8")
    print(json.dumps({"verdict": verdict, "numerical_pass": numerical_pass, "qpu_eligible": qpu_eligible}), flush=True)


if __name__ == "__main__":
    main()

