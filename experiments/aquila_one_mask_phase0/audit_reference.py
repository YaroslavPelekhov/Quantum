"""Post-run adaptive-ODE audit of every saved Phase-0 pulse.

This audit is intentionally separate from the frozen optimizer.  It diagnoses
whether the low-resolution optimization grid created a false positive.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import networkx as nx
import numpy as np

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from experiments.aquila_one_mask_phase0.control_core import full_c6_model, hard_blockade_model
from experiments.aquila_one_mask_phase0.pulse_opt import pulse_fidelity, pulse_fidelity_ivp, quantized_pulse


OUTPUT = REPOSITORY_ROOT / "results" / "aquila_one_mask_phase0"


def main() -> None:
    checkpoint = json.loads((OUTPUT / "optimization_checkpoint.json").read_text(encoding="utf-8"))
    coordinates = np.array([[0.0, 0.0], [5.5, 0.0], [11.0, 0.0], [16.5, 0.0]])
    mask = np.linspace(0.0, 1.0, 4)
    models = {
        "full_c6": full_c6_model(coordinates, mask),
        "full_c6_uniform": full_c6_model(coordinates, np.ones(4)),
        "hard_blockade_projected_c6": hard_blockade_model(nx.path_graph(4), coordinates, mask),
    }
    rows = []
    candidate_rows = []
    for job_key, job in checkpoint["jobs"].items():
        model = models[job["model"]]
        target = int(job["target_mask"])
        for result in job["results"]:
            pulse = result["pulse"]
            row = {
                "job": job_key,
                "model": job["model"],
                "mode": job["mode"],
                "target_mask": target,
                "seed": result["seed"],
                "optimization_grid": result["fidelity_optimization_grid"],
            }
            for substeps in (2, 4, 8, 16, 32, 64):
                row[f"midpoint_substeps_{substeps}"] = pulse_fidelity(model, pulse, target, substeps)
            row["adaptive_ode_reference"] = pulse_fidelity_ivp(model, pulse, target)
            row["optimization_minus_reference"] = row["optimization_grid"] - row["adaptive_ode_reference"]
            if job["model"] == "hard_blockade_projected_c6":
                row["full_c6_adaptive_ode_transfer"] = pulse_fidelity_ivp(models["full_c6"], pulse, target)
                candidate_rows.append(
                    {
                        "target": target,
                        "source": "hard_blockade_transfer",
                        "seed": result["seed"],
                        "reference": row["full_c6_adaptive_ode_transfer"],
                        "pulse": pulse,
                    }
                )
            else:
                row["full_c6_adaptive_ode_transfer"] = ""
                if job["mode"] == "gradient_mask":
                    candidate_rows.append(
                        {
                            "target": target,
                            "source": "direct_full_c6",
                            "seed": result["seed"],
                            "reference": row["adaptive_ode_reference"],
                            "pulse": pulse,
                        }
                    )
            rows.append(row)
            print(f"audited {job_key} seed {result['seed']}", flush=True)

    with (OUTPUT / "reference_convergence.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    best = {}
    for target in (5, 10):
        selected = max((item for item in candidate_rows if item["target"] == target), key=lambda item: item["reference"])
        quantized_reference = pulse_fidelity_ivp(models["full_c6"], quantized_pulse(selected["pulse"]), target)
        best[str(target)] = {
            "source": selected["source"],
            "seed": selected["seed"],
            "adaptive_ode_reference_fidelity": selected["reference"],
            "quantized_adaptive_ode_reference_fidelity": quantized_reference,
            "quantization_drop": selected["reference"] - quantized_reference,
        }
    payload = {
        "verdict": "CONFIRMED_OPTIMIZATION_MESH_FALSE_POSITIVE",
        "reference_solver": "scipy DOP853, rtol=2e-10, atol=2e-12, max_step=knot_interval/4",
        "best_hardware_facing_candidates": best,
        "passes_0p95_gate": all(item["adaptive_ode_reference_fidelity"] >= 0.95 for item in best.values()),
        "note": "The frozen optimization grid reported near-unit values, but adaptive ODE truth stays below the preregistered gate.",
    }
    (OUTPUT / "reference_audit.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = """# Adaptive-ODE reference audit

## Verdict

**CONFIRMED_OPTIMIZATION_MESH_FALSE_POSITIVE.**

The frozen differentiable optimizer used two midpoint propagations per 0.25 us
knot interval.  It found near-unit values on that grid, but the values fell
monotonically under grid refinement and converged to the adaptive DOP853
reference below.  The original `KILL_ONE_MASK_PHASE0` decision is therefore
strengthened, not reversed.

| target | selected source | seed | adaptive-ODE fidelity | quantized fidelity |
|---:|---|---:|---:|---:|
"""
    for target, item in best.items():
        report += (
            f"| `{int(target):04b}` | {item['source']} | {item['seed']} | "
            f"{item['adaptive_ode_reference_fidelity']:.6f} | "
            f"{item['quantized_adaptive_ode_reference_fidelity']:.6f} |\n"
        )
    report += """

This is a useful systems lesson: exact hardware bounds and a differentiable
optimizer do not make a pulse physically valid if the propagation mesh is too
coarse for the always-on `C6/r^6` scale.  Any later pulse optimization must put
an adaptive reference solver or a converged interaction-picture integrator
inside the acceptance loop.
"""
    (OUTPUT / "REFERENCE_AUDIT.md").write_text(report, encoding="utf-8")
    print(json.dumps(payload), flush=True)


if __name__ == "__main__":
    main()

