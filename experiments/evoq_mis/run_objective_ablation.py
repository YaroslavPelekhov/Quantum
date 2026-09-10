from __future__ import annotations

import json
import math
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from qaoa_mis import differential_evolution_fixed_budget, distribution_metrics, enumerate_exact_space, statevector_probabilities
from run_multitask_normalized import build_suites, paired_audit


EXPERIMENT_DIR = Path(__file__).resolve().parent
SOURCE_PATH = EXPERIMENT_DIR / "results_multitask_normalized" / "results.json"
OUTPUT_DIR = EXPERIMENT_DIR / "results_objective_ablation"


def task_metrics(graphs, exact_spaces, params):
    return {
        graph.name: distribution_metrics(
            statevector_probabilities(graph, params, p=2, cost_scale="max_coefficient"), exact
        )
        for graph, exact in zip(graphs, exact_spaces)
    }


def aggregates(tasks):
    scores = np.asarray([row["score"] for row in tasks.values()], dtype=float)
    return {
        "single_full_score": float(scores[0]),
        "mean_score": float(scores.mean()),
        "robust_score": float(0.7 * scores.mean() + 0.3 * scores.min()),
        "minimum_score": float(scores.min()),
    }


def evaluate(graphs, exact_spaces, params):
    tasks = task_metrics(graphs, exact_spaces, params)
    return {"tasks": tasks, **aggregates(tasks)}


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    source = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    train, validation, frozen_test, _ = build_suites()
    train_exact = [enumerate_exact_space(graph) for graph in train]
    validation_exact = [enumerate_exact_space(graph) for graph in validation]
    test_exact = [enumerate_exact_space(graph) for graph in frozen_test]
    bounds = [(1.05, 4.0)] + [(0.0, math.pi)] * 2 + [(0.0, 2.0 * math.pi)] * 2
    cache = {}

    def cached(params):
        key = tuple(float(x) for x in params)
        if key not in cache:
            cache[key] = evaluate(train, train_exact, np.asarray(params))
        return cache[key]

    replicates = []
    started = time.perf_counter()
    for replicate, source_row in enumerate(source["replicates"]):
        seed = int(source["configuration"]["seed"]) + 10007 * replicate
        row = {"replicate": replicate}
        robust_params = np.asarray(source_row["normalized_de"]["params"], dtype=float)
        row["robust_de"] = {
            "params": robust_params.tolist(),
            "train": cached(robust_params),
            "validation": evaluate(validation, validation_exact, robust_params),
            "frozen_test": evaluate(frozen_test, test_exact, robust_params),
        }
        for method, objective_key in (("mean_de", "mean_score"), ("single_de", "single_full_score")):
            def objective(params, objective_key=objective_key):
                return cached(params)[objective_key]

            params, _, _ = differential_evolution_fixed_budget(
                objective, bounds, 300, seed, population_size=15
            )
            row[method] = {
                "params": params.tolist(),
                "train": cached(params),
                "validation": evaluate(validation, validation_exact, params),
                "frozen_test": evaluate(frozen_test, test_exact, params),
            }
        replicates.append(row)
    seconds = time.perf_counter() - started

    comparisons = {}
    for baseline in ("mean_de", "single_de"):
        comparisons[f"robust_vs_{baseline}"] = {}
        for offset, stage in enumerate(("train", "validation", "frozen_test")):
            comparisons[f"robust_vs_{baseline}"][stage] = paired_audit(
                [row["robust_de"][stage]["robust_score"] for row in replicates],
                [row[baseline][stage]["robust_score"] for row in replicates],
                20260803 + offset,
            )

    report = {
        "experiment": "Objective ablation for normalized multi-instance QAOA",
        "methods": {
            "robust_de": "0.7*mean + 0.3*minimum task score (existing frozen schedules)",
            "mean_de": "mean task score",
            "single_de": "full mammalia task only",
        },
        "seconds": seconds,
        "unique_genomes": len(cache),
        "replicates": replicates,
        "comparisons_on_common_robust_metric": comparisons,
    }
    (OUTPUT_DIR / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    stages = ("train", "validation", "frozen_test")
    methods = ("robust_de", "mean_de", "single_de")
    x = np.arange(len(stages))
    width = 0.25
    plt.figure(figsize=(8.8, 5.0))
    for index, method in enumerate(methods):
        values = [[row[method][stage]["robust_score"] for row in replicates] for stage in stages]
        plt.bar(
            x + (index - 1) * width,
            [np.mean(value) for value in values],
            width,
            yerr=[np.std(value, ddof=1) for value in values],
            capsize=4,
            label=method,
        )
    plt.xticks(x, stages)
    plt.ylabel("Common robust aggregate score")
    plt.title("Training-objective ablation")
    plt.grid(axis="y", alpha=0.2)
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "objective_ablation.png", dpi=180)
    plt.close()

    print(json.dumps({"seconds": seconds, "comparisons": comparisons, "results": str((OUTPUT_DIR / "results.json").resolve())}, indent=2))


if __name__ == "__main__":
    main()
