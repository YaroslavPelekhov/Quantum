"""Run the frozen development or held-out DCS-RDT benchmark."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULTS = REPO / "results" / "decision_conditioned_srdt"
sys.path[:0] = [
    str(HERE),
    str(REPO / "experiments" / "rankcert_mps"),
    str(REPO / "experiments" / "contrastive_tensor_simulation"),
]

import rankcert_inputs
from contrastive_core import atomic_json, sha256
from dcsrdt_core import benchmark_pair, bks_effect_diagonal


PROTOCOL = HERE / "PROTOCOL.md"
COHORTS = {
    "development": {
        "cases": ("ibm32", "aves-sparrow-social"),
        "cut": 5,
        "ranks": (1, 2, 4, 8, 16),
        "fixed_rank": 8,
    },
    "transfer": {
        "cases": ("chesapeake", "football"),
        "cut": 3,
        "ranks": (1, 2, 4),
        "fixed_rank": 4,
    },
}
ORDERINGS = ("sorted", "spectral")
NUMERICAL_FLOOR = 1e-15


def specs_by_key() -> dict:
    return {
        (row["case"], row["ordering"], row["method"]): row
        for row in rankcert_inputs.load_specs()
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=tuple(COHORTS))
    args = parser.parse_args()
    config = COHORTS[args.stage]
    output = RESULTS / f"{args.stage}.json"
    indexed = specs_by_key()
    payload = {
        "complete": False,
        "stage": args.stage,
        "protocol_sha256": sha256(PROTOCOL),
        "cases": list(config["cases"]),
        "cut": config["cut"],
        "ranks": list(config["ranks"]),
        "fixed_rank": config["fixed_rank"],
        "rows": [],
    }
    for case in config["cases"]:
        for ordering in ORDERINGS:
            spec_a = indexed[(case, ordering, "published_lr")]
            spec_b = indexed[(case, ordering, "prior_matched_random")]
            state_a = np.asarray(np.load(spec_a["reference_file"], mmap_mode="r", allow_pickle=False))
            state_b = np.asarray(np.load(spec_b["reference_file"], mmap_mode="r", allow_pickle=False))
            effect = bks_effect_diagonal(spec_a["scorer"])
            benchmark = benchmark_pair(
                state_a, state_b, effect, config["cut"], config["ranks"]
            )
            if abs(benchmark["exact_delta"] - spec_b["exact_metrics"]["bks_rate"] + spec_a["exact_metrics"]["bks_rate"]) > 1e-10:
                raise AssertionError("BKS effect does not reproduce frozen exact metrics")
            fixed = next(row for row in benchmark["rows"] if row["rank"] == config["fixed_rank"])
            target = fixed["methods"]["decision_conditioned"]
            exact_at_rank = target["trace_norm_bound"] <= NUMERICAL_FLOOR
            factors = {
                control: fixed["methods"][control]["trace_norm_bound"]
                / max(target["trace_norm_bound"], NUMERICAL_FLOOR)
                for control in ("srdt_basis", "state_averaged_basis")
            }
            row = {
                "case": case,
                "ordering": ordering,
                "qubits": spec_a["qubits"],
                "bks_projector_rank": int(effect.sum()),
                **benchmark,
                "fixed_rank_factors": factors,
                "fixed_rank_factor_is_lower_bound": exact_at_rank,
                "fixed_rank_pass": all(
                    target["trace_norm_bound"] < fixed["methods"][control]["trace_norm_bound"]
                    for control in factors
                ),
            }
            payload["rows"].append(row)
            atomic_json(output, payload)
            print(json.dumps({
                "case": case,
                "ordering": ordering,
                "exact_delta": row["exact_delta"],
                "fixed_rank": config["fixed_rank"],
                "target_bound": target["trace_norm_bound"],
                "factors": factors,
                "pass": row["fixed_rank_pass"],
            }, indent=2), flush=True)
    payload["passed_rows"] = sum(row["fixed_rank_pass"] for row in payload["rows"])
    factors = {
        control: [row["fixed_rank_factors"][control] for row in payload["rows"]]
        for control in ("srdt_basis", "state_averaged_basis")
    }
    payload["geometric_mean_factors"] = {
        control: float(np.exp(np.mean(np.log(values)))) for control, values in factors.items()
    }
    if args.stage == "development":
        payload["success"] = bool(
            payload["passed_rows"] == len(payload["rows"])
            and all(value >= 2.0 for value in payload["geometric_mean_factors"].values())
        )
    else:
        payload["success"] = payload["passed_rows"] == len(payload["rows"])
    payload["complete"] = True
    atomic_json(output, payload)
    print(json.dumps({
        "output": str(output),
        "passed_rows": payload["passed_rows"],
        "geometric_mean_factors": payload["geometric_mean_factors"],
        "success": payload["success"],
    }, indent=2))


if __name__ == "__main__":
    main()
