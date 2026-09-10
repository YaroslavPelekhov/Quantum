from __future__ import annotations

import argparse
import csv
import json
import math
import platform
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import qiskit
import qiskit_aer
from scipy.stats import ttest_rel, wilcoxon

from qaoa_mis import (
    counts_metrics,
    differential_evolution_fixed_budget,
    distribution_metrics,
    enumerate_exact_space,
    induced_subgraph,
    load_dimacs_graph,
    mask_to_vertices,
    multinomial_counts,
    random_search_fixed_budget,
    sample_counts,
    statevector_probabilities,
)


ROOT = Path(__file__).resolve().parents[2]
INSTANCE_DIR = ROOT / "QOBLIB" / "07-independentset" / "instances"
OUTPUT_DIR = Path(__file__).resolve().parent / "results_multitask_normalized"
METHODS = {
    "normalized_de": {"scale": "max_coefficient", "search": "de"},
    "unnormalized_de": {"scale": "none", "search": "de"},
    "normalized_random": {"scale": "max_coefficient", "search": "random"},
}


def build_suites():
    mammalia = load_dimacs_graph(INSTANCE_DIR / "mammalia-kangaroo-interactions.gph")
    rng = np.random.default_rng(314159)
    train = [mammalia]
    train_vertices = {mammalia.name: list(range(1, mammalia.n + 1))}
    for size in (11, 13, 15):
        vertices = sorted(int(x) for x in rng.choice(mammalia.n, size=size, replace=False))
        graph = induced_subgraph(mammalia, vertices, f"mammalia_induced_{size}")
        train.append(graph)
        train_vertices[graph.name] = [vertex + 1 for vertex in vertices]
    validation = [load_dimacs_graph(INSTANCE_DIR / "farm.gph")]
    frozen_test = []
    for name in ("karate", "chesapeake", "aves-sparrow-social"):
        source = load_dimacs_graph(INSTANCE_DIR / f"{name}.gph")
        frozen_test.append(induced_subgraph(source, range(17), f"{name}_first17"))
    return train, validation, frozen_test, train_vertices


def describe_graph(graph, exact) -> dict:
    return {
        "name": graph.name,
        "vertices": graph.n,
        "edges": len(graph.edges),
        "exact_optimum": exact.optimum,
        "source": graph.source,
    }


def summarize(values) -> dict[str, float]:
    array = np.asarray(values, dtype=float)
    return {
        "mean": float(array.mean()),
        "std": float(array.std(ddof=1)) if len(array) > 1 else 0.0,
        "median": float(np.median(array)),
        "min": float(array.min()),
        "max": float(array.max()),
    }


def paired_audit(first, second, seed: int) -> dict:
    first = np.asarray(first, dtype=float)
    second = np.asarray(second, dtype=float)
    differences = first - second
    rng = np.random.default_rng(seed)
    bootstrap = np.asarray([
        rng.choice(differences, size=len(differences), replace=True).mean()
        for _ in range(20000)
    ])
    ttest = ttest_rel(first, second)
    try:
        signed_rank = wilcoxon(first, second, alternative="greater")
        wilcoxon_result = {"statistic": float(signed_rank.statistic), "p_value": float(signed_rank.pvalue)}
    except ValueError:
        wilcoxon_result = {"statistic": 0.0, "p_value": 1.0}
    return {
        "first": summarize(first),
        "second": summarize(second),
        "difference": {
            **summarize(differences),
            "bootstrap_95_percent_ci": [float(np.quantile(bootstrap, 0.025)), float(np.quantile(bootstrap, 0.975))],
        },
        "first_wins": int(np.sum(first > second)),
        "second_wins": int(np.sum(second > first)),
        "paired_t_test_two_sided": {"statistic": float(ttest.statistic), "p_value": float(ttest.pvalue)},
        "wilcoxon_one_sided_first_greater": wilcoxon_result,
    }


def aggregate_suite(task_metrics: dict[str, dict[str, float]]) -> float:
    scores = np.asarray([metrics["score"] for metrics in task_metrics.values()], dtype=float)
    return float(0.7 * scores.mean() + 0.3 * scores.min())


def evaluate_suite(graphs, exact_spaces, params, p: int, scale: str) -> dict:
    tasks = {}
    for graph, exact in zip(graphs, exact_spaces):
        probs = statevector_probabilities(graph, params, p, cost_scale=scale)
        tasks[graph.name] = distribution_metrics(probs, exact)
    return {"aggregate_score": aggregate_suite(tasks), "tasks": tasks}


def plot_paired(path: Path, replicates: list[dict], field: str, title: str, ylabel: str) -> None:
    x = np.arange(1, len(replicates) + 1)
    values = {
        method: np.asarray([row[method][field] for row in replicates], dtype=float)
        for method in METHODS
    }
    offsets = {"normalized_de": -0.16, "unnormalized_de": 0.0, "normalized_random": 0.16}
    labels = {
        "normalized_de": "Normalized multi-task DE",
        "unnormalized_de": "Unnormalized multi-task DE",
        "normalized_random": "Normalized multi-task random",
    }
    plt.figure(figsize=(9.0, 5.0))
    for i in range(len(x)):
        plt.plot(
            [x[i] + offsets[name] for name in METHODS],
            [values[name][i] for name in METHODS],
            color="0.8",
            linewidth=0.9,
        )
    for method in METHODS:
        plt.scatter(x + offsets[method], values[method], s=38, label=labels[method])
    plt.xlabel("Paired replicate")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.xticks(x)
    plt.grid(alpha=0.2)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--budget", type=int, default=300)
    parser.add_argument("--repeats", type=int, default=12)
    parser.add_argument("--seed", type=int, default=20260802)
    parser.add_argument("--shots", type=int, default=4096)
    parser.add_argument("--shot-trials", type=int, default=8)
    parser.add_argument("--noise-shots", type=int, default=256)
    parser.add_argument("--noise-trials", type=int, default=4)
    args = parser.parse_args()
    p = 2
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    train, validation, frozen_test, train_vertices = build_suites()
    train_exact = [enumerate_exact_space(graph) for graph in train]
    validation_exact = [enumerate_exact_space(graph) for graph in validation]
    test_exact = [enumerate_exact_space(graph) for graph in frozen_test]
    bounds = [(1.05, 4.0)] + [(0.0, math.pi)] * p + [(0.0, 2.0 * math.pi)] * p
    cache = {}
    replicates = []

    def cached_train(params, scale):
        key = (scale, *tuple(float(x) for x in params))
        if key not in cache:
            cache[key] = evaluate_suite(train, train_exact, np.asarray(params), p, scale)
        return cache[key]

    started = time.perf_counter()
    for replicate in range(args.repeats):
        seed = args.seed + 10007 * replicate
        row = {"replicate": replicate}
        for method, config in METHODS.items():
            def objective(params, scale=config["scale"]):
                return cached_train(params, scale)["aggregate_score"]

            if config["search"] == "de":
                params, score, _ = differential_evolution_fixed_budget(
                    objective, bounds, args.budget, seed, population_size=15
                )
            else:
                params, score, _ = random_search_fixed_budget(objective, bounds, args.budget, seed + 1)
            train_result = cached_train(params, config["scale"])
            validation_result = evaluate_suite(validation, validation_exact, params, p, config["scale"])
            test_result = evaluate_suite(frozen_test, test_exact, params, p, config["scale"])
            row[method] = {
                "params": params.tolist(),
                "train_aggregate_score": float(score),
                "train_tasks": train_result["tasks"],
                "validation_aggregate_score": validation_result["aggregate_score"],
                "validation_tasks": validation_result["tasks"],
                "frozen_test_aggregate_score": test_result["aggregate_score"],
                "frozen_test_tasks": test_result["tasks"],
            }
        replicates.append(row)
    search_seconds = time.perf_counter() - started

    comparisons = {}
    fields = ("train_aggregate_score", "validation_aggregate_score", "frozen_test_aggregate_score")
    pairs = (
        ("normalized_de", "normalized_random", "evolution_effect"),
        ("normalized_de", "unnormalized_de", "normalization_effect"),
    )
    for first, second, label in pairs:
        comparisons[label] = {}
        for offset, field in enumerate(fields):
            comparisons[label][field] = paired_audit(
                [row[first][field] for row in replicates],
                [row[second][field] for row in replicates],
                args.seed + offset + (100 if label == "normalization_effect" else 0),
            )

    champion_row = max(replicates, key=lambda row: row["normalized_de"]["train_aggregate_score"])
    champion = champion_row["normalized_de"]
    champion_params = np.asarray(champion["params"], dtype=float)
    finite_shot = {}
    best_solution = None
    circuit_stats = None
    for graph, exact in zip(train[:1] + validation + frozen_test, train_exact[:1] + validation_exact + test_exact):
        probs = statevector_probabilities(graph, champion_params, p, cost_scale="max_coefficient")
        ideal_trials = []
        noisy_trials = []
        for trial in range(args.shot_trials):
            counts = multinomial_counts(probs, args.shots, args.seed + 1000 * trial)
            metrics = counts_metrics(counts, graph, exact)
            ideal_trials.append(metrics)
            if graph.name == train[0].name and trial == 0:
                best_solution = {
                    "mask": int(metrics["best_repaired_mask"]),
                    "vertices_1_based": mask_to_vertices(int(metrics["best_repaired_mask"]), graph.n),
                    "size": int(metrics["best_repaired_size"]),
                }
        for trial in range(args.noise_trials):
            counts, stats = sample_counts(
                graph,
                champion_params,
                p,
                args.noise_shots,
                args.seed + 20000 + 1000 * trial,
                True,
                cost_scale="max_coefficient",
            )
            noisy_trials.append(counts_metrics(counts, graph, exact))
            if graph.name == train[0].name and trial == 0:
                circuit_stats = stats
        finite_shot[graph.name] = {
            "ideal": {key: summarize([float(row[key]) for row in ideal_trials]) for key in ideal_trials[0] if key != "best_repaired_mask"},
            "noisy": {key: summarize([float(row[key]) for row in noisy_trials]) for key in noisy_trials[0] if key != "best_repaired_mask"},
        }

    evolution_test = comparisons["evolution_effect"]["frozen_test_aggregate_score"]
    normalization_test = comparisons["normalization_effect"]["frozen_test_aggregate_score"]
    promotion_checks = {
        "normalized_de_beats_random_on_train_mean": comparisons["evolution_effect"]["train_aggregate_score"]["difference"]["mean"] > 0,
        "normalized_de_beats_random_on_frozen_test_mean": evolution_test["difference"]["mean"] > 0,
        "normalized_de_wins_frozen_test_majority_vs_random": evolution_test["first_wins"] > args.repeats / 2,
        "normalization_improves_frozen_test_mean": normalization_test["difference"]["mean"] > 0,
        "normalization_wins_frozen_test_majority": normalization_test["first_wins"] > args.repeats / 2,
    }

    report = {
        "experiment": "Graph-scale-normalized multi-instance depth-2 QAOA",
        "timestamp_local": time.strftime("%Y-%m-%d %H:%M:%S"),
        "configuration": {**vars(args), "p": p, "train_aggregate": "0.7*mean(task scores)+0.3*min(task scores)"},
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "qiskit": qiskit.__version__,
            "qiskit_aer": qiskit_aer.__version__,
            "numpy": np.__version__,
        },
        "protocol": {
            "cost_normalization": "Divide all Ising h and J coefficients by max(max_i |h_i|, |J|) separately for each graph.",
            "train_vertices_1_based": train_vertices,
            "train": [describe_graph(graph, exact) for graph, exact in zip(train, train_exact)],
            "validation": [describe_graph(graph, exact) for graph, exact in zip(validation, validation_exact)],
            "frozen_test": [describe_graph(graph, exact) for graph, exact in zip(frozen_test, test_exact)],
        },
        "methods": METHODS,
        "search_seconds": search_seconds,
        "unique_cached_train_genomes": len(cache),
        "replicates": replicates,
        "comparisons": comparisons,
        "champion": {"replicate": champion_row["replicate"], **champion},
        "finite_shot_champion": finite_shot,
        "best_repaired_train_solution": best_solution,
        "compiled_train_circuit": circuit_stats,
        "promotion_gate": {
            "checks": promotion_checks,
            "promote": all(promotion_checks.values()),
            "reason": "The new QOBLIB-derived test suite was fixed before optimization; all mean and majority checks must pass.",
        },
    }
    (OUTPUT_DIR / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    with (OUTPUT_DIR / "replicate_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["replicate", "method", *fields, "params"])
        for row in replicates:
            for method in METHODS:
                writer.writerow([row["replicate"], method, *(row[method][field] for field in fields), json.dumps(row[method]["params"])])
    plot_paired(OUTPUT_DIR / "train_paired.png", replicates, "train_aggregate_score", "Multi-instance training result", "Aggregate train score")
    plot_paired(OUTPUT_DIR / "validation_paired.png", replicates, "validation_aggregate_score", "Validation transfer to QOBLIB farm", "Exact validation score")
    plot_paired(OUTPUT_DIR / "frozen_test_paired.png", replicates, "frozen_test_aggregate_score", "Frozen QOBLIB-derived test suite", "Aggregate exact test score")
    if best_solution:
        bits = ["1" if i + 1 in best_solution["vertices_1_based"] else "0" for i in range(train[0].n)]
        (OUTPUT_DIR / "best_solution.txt").write_text(" ".join(bits) + "\n", encoding="utf-8")

    print(json.dumps({
        "search_seconds": search_seconds,
        "unique_cached_train_genomes": len(cache),
        "evolution_effect_frozen_test": evolution_test,
        "normalization_effect_frozen_test": normalization_test,
        "promotion_gate": report["promotion_gate"],
        "results": str((OUTPUT_DIR / "results.json").resolve()),
    }, indent=2))


if __name__ == "__main__":
    main()
