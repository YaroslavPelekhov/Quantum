from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from feasible_mixer import FeasibleMixerSimulator
from qaoa_mis import (
    counts_metrics,
    differential_evolution_fixed_budget,
    enumerate_exact_space,
    multinomial_counts,
    random_search_fixed_budget,
)
from run_multitask_normalized import build_suites, paired_audit, summarize


OUTPUT_DIR = Path(__file__).resolve().parent / "results_feasible_mixer"


def aggregate(metrics: dict[str, dict[str, float]]) -> float:
    scores = np.asarray([value["score"] for value in metrics.values()], dtype=float)
    return float(0.7 * scores.mean() + 0.3 * scores.min())


def evaluate(simulators: list[FeasibleMixerSimulator], params: np.ndarray) -> dict:
    tasks = {sim.graph.name: sim.metrics(params) for sim in simulators}
    return {"aggregate_score": aggregate(tasks), "tasks": tasks}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--budget", type=int, default=300)
    parser.add_argument("--repeats", type=int, default=12)
    parser.add_argument("--seed", type=int, default=20260803)
    parser.add_argument("--shots", type=int, default=4096)
    parser.add_argument("--shot-trials", type=int, default=8)
    args = parser.parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    train, validation, frozen_test, _ = build_suites()
    train_simulators = [FeasibleMixerSimulator(graph, enumerate_exact_space(graph)) for graph in train]
    validation_simulators = [FeasibleMixerSimulator(graph, enumerate_exact_space(graph)) for graph in validation]
    test_simulators = [FeasibleMixerSimulator(graph, enumerate_exact_space(graph)) for graph in frozen_test]
    bounds = [(0.0, 3.999999)] + [(0.0, math.pi)] * 3 + [(0.0, 2.0 * math.pi)] * 2
    cache = {}
    replicates = []

    def cached(params):
        key = tuple(float(x) for x in params)
        if key not in cache:
            cache[key] = evaluate(train_simulators, np.asarray(params))
        return cache[key]

    started = time.perf_counter()
    for replicate in range(args.repeats):
        seed = args.seed + 10007 * replicate
        row = {"replicate": replicate}
        for method in ("feasible_de", "feasible_random"):
            def objective(params):
                return cached(params)["aggregate_score"]

            if method == "feasible_de":
                params, score, _ = differential_evolution_fixed_budget(
                    objective, bounds, args.budget, seed, population_size=18
                )
            else:
                params, score, _ = random_search_fixed_budget(objective, bounds, args.budget, seed + 1)
            row[method] = {
                "params": params.tolist(),
                "order_policy": int(np.floor(params[0])),
                "train_aggregate_score": float(score),
                "train_tasks": cached(params)["tasks"],
                "validation": evaluate(validation_simulators, params),
                "frozen_test": evaluate(test_simulators, params),
            }
        replicates.append(row)
    search_seconds = time.perf_counter() - started

    comparisons = {}
    for offset, (field, getter) in enumerate({
        "train": lambda row, method: row[method]["train_aggregate_score"],
        "validation": lambda row, method: row[method]["validation"]["aggregate_score"],
        "frozen_test": lambda row, method: row[method]["frozen_test"]["aggregate_score"],
    }.items()):
        comparisons[field] = paired_audit(
            [getter(row, "feasible_de") for row in replicates],
            [getter(row, "feasible_random") for row in replicates],
            args.seed + offset,
        )

    champion_row = max(replicates, key=lambda row: row["feasible_de"]["train_aggregate_score"])
    champion = champion_row["feasible_de"]
    params = np.asarray(champion["params"], dtype=float)
    finite_shot = {}
    for simulator in train_simulators[:1] + validation_simulators + test_simulators:
        probs = simulator.probabilities(params)
        trials = []
        for trial in range(args.shot_trials):
            counts = multinomial_counts(probs, args.shots, args.seed + 1000 * trial)
            trials.append(counts_metrics(counts, simulator.graph, simulator.exact))
        finite_shot[simulator.graph.name] = {
            key: summarize([float(row[key]) for row in trials])
            for key in trials[0]
            if key != "best_repaired_mask"
        }

    previous_path = Path(__file__).resolve().parent / "results_multitask_normalized" / "results.json"
    previous = json.loads(previous_path.read_text(encoding="utf-8")) if previous_path.exists() else None
    penalty_comparison = None
    if previous:
        penalty_test = [row["normalized_de"]["frozen_test_aggregate_score"] for row in previous["replicates"]]
        feasible_test = [row["feasible_de"]["frozen_test"]["aggregate_score"] for row in replicates]
        penalty_comparison = paired_audit(feasible_test, penalty_test, args.seed + 100)

    gate_checks = {
        "feasible_probability_is_one": all(
            abs(task["feasible_probability"] - 1.0) < 1e-10
            for row in replicates
            for task in row["feasible_de"]["frozen_test"]["tasks"].values()
        ),
        "de_beats_random_train_mean": comparisons["train"]["difference"]["mean"] > 0,
        "de_beats_random_frozen_test_mean": comparisons["frozen_test"]["difference"]["mean"] > 0,
        "de_wins_random_frozen_test_majority": comparisons["frozen_test"]["first_wins"] > args.repeats / 2,
    }
    report = {
        "experiment": "Feasibility-preserving MIS mixer with evolutionary shared schedules",
        "configuration": vars(args),
        "genome": "[order policy in {natural, degree-ascending, degree-descending, fixed-random}, beta1, beta2, beta3, gamma2, gamma3]",
        "search_seconds": search_seconds,
        "unique_train_genomes": len(cache),
        "replicates": replicates,
        "comparisons": comparisons,
        "penalty_normalized_de_frozen_test_comparison": penalty_comparison,
        "champion": {"replicate": champion_row["replicate"], **champion},
        "finite_shot_champion": finite_shot,
        "promotion_gate": {"checks": gate_checks, "promote_to_circuit_resource_audit": all(gate_checks.values())},
    }
    (OUTPUT_DIR / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    x = np.arange(1, args.repeats + 1)
    for field, getter in (
        ("train", lambda row, method: row[method]["train_aggregate_score"]),
        ("frozen_test", lambda row, method: row[method]["frozen_test"]["aggregate_score"]),
    ):
        de = [getter(row, "feasible_de") for row in replicates]
        random = [getter(row, "feasible_random") for row in replicates]
        plt.figure(figsize=(8.5, 4.8))
        for i in range(args.repeats):
            plt.plot([x[i] - 0.08, x[i] + 0.08], [de[i], random[i]], color="0.75", linewidth=1)
        plt.scatter(x - 0.08, de, label="Feasible-mixer DE")
        plt.scatter(x + 0.08, random, label="Feasible-mixer random")
        plt.xlabel("Paired replicate")
        plt.ylabel("Aggregate raw score")
        plt.title(f"Feasibility-preserving mixer: {field.replace('_', ' ')}")
        plt.xticks(x)
        plt.grid(alpha=0.2)
        plt.legend()
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / f"{field}_paired.png", dpi=180)
        plt.close()

    print(json.dumps({
        "search_seconds": search_seconds,
        "comparisons": comparisons,
        "penalty_comparison": penalty_comparison,
        "promotion_gate": report["promotion_gate"],
        "results": str((OUTPUT_DIR / "results.json").resolve()),
    }, indent=2))


if __name__ == "__main__":
    main()
