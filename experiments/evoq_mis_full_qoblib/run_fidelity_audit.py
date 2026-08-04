"""MPS truncation-sensitivity audit for already frozen QAOA schedules."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from time import perf_counter

import numpy as np
from qiskit_aer import AerSimulator

import run_cycle as rc


def run_config(case, champions, methods, shots, replicates, seed, bond, threshold, output_path):
    backend = AerSimulator(
        method="matrix_product_state",
        matrix_product_state_max_bond_dimension=bond,
        matrix_product_state_truncation_threshold=threshold,
        max_parallel_experiments=1,
    )
    circuits = [rc.bind_case(case, np.asarray(champions[m]["genome"], dtype=float)) for m in methods]
    rows = []
    for replicate in range(replicates):
        job_seed = seed + replicate * 10_007 + bond * 101
        print(
            f"AUDIT bond={bond} threshold={threshold:g} replicate={replicate + 1}/{replicates}",
            flush=True,
        )
        start = perf_counter()
        result = backend.run(circuits, shots=shots, seed_simulator=job_seed).result()
        elapsed = perf_counter() - start
        for index, method in enumerate(methods):
            rows.append(
                {
                    "method": method,
                    "replicate": replicate,
                    "seed": job_seed,
                    "metrics": rc.summarize_counts(case, result.get_counts(index)),
                    "elapsed_batch_seconds": elapsed,
                    "aer_metadata": result.results[index].metadata,
                }
            )
        rc.write_json(
            output_path.with_name(output_path.stem + "_checkpoint.json"),
            {
                "complete": replicate + 1 == replicates,
                "backend": {"bond": bond, "threshold": threshold},
                "shots": shots,
                "replicates_planned": replicates,
                "methods": methods,
                "rows": rows,
            },
        )
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--shots", type=int, default=1000)
    parser.add_argument("--replicates", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20260803)
    parser.add_argument("--bond", type=int, default=128)
    parser.add_argument("--threshold", type=float, default=1e-6)
    parser.add_argument(
        "--methods",
        default="published_lr,evolutionary_search,matched_random_search",
        help="Comma-separated frozen champion names.",
    )
    args = parser.parse_args()

    validation = json.loads((rc.RESULTS / "validation.json").read_text(encoding="utf-8"))
    champions = validation["frozen_champions"]
    methods = [item.strip() for item in args.methods.split(",") if item.strip()]
    case = rc.prepare_case(rc.TEST_NAME)
    threshold_tag = f"{args.threshold:.0e}".replace("+", "").replace("-", "m")
    output_path = rc.RESULTS / f"fidelity_bond{args.bond}_thr{threshold_tag}.json"
    rows = run_config(
        case, champions, methods, args.shots, args.replicates, args.seed, args.bond,
        args.threshold, output_path
    )
    comparisons = []
    for method in (item for item in methods if item != "published_lr"):
        for metric in ("bks_rate", "near_bks_rate", "feasible_rate", "quality_mass", "robust_score"):
            comparisons.append(rc.paired_summary(rows, method, "published_lr", metric, args.seed + 313))
    payload = {
        "stage": "mps_fidelity_audit",
        "provenance": rc.provenance(),
        "case": rc.case_metadata(case),
        "backend": {
            "method": "matrix_product_state",
            "matrix_product_state_max_bond_dimension": args.bond,
            "matrix_product_state_truncation_threshold": args.threshold,
        },
        "shots_per_method_replicate": args.shots,
        "replicates": args.replicates,
        "rows": rows,
        "comparisons": comparisons,
    }
    rc.write_json(output_path, payload)


if __name__ == "__main__":
    main()
