from __future__ import annotations

import argparse
import csv
import json
import math
import platform
import sys
import time
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import qiskit
import qiskit_aer

from qaoa_mis import (
    counts_metrics,
    differential_evolution_fixed_budget,
    distribution_metrics,
    enumerate_exact_space,
    load_dimacs_graph,
    mask_to_vertices,
    multinomial_counts,
    random_search_fixed_budget,
    sample_counts,
    statevector_probabilities,
)


ROOT = Path(__file__).resolve().parents[2]
INSTANCE_DIR = ROOT / "QOBLIB" / "07-independentset" / "instances"
OUTPUT_DIR = Path(__file__).resolve().parent / "results_p2_pareto"
OBJECTIVES = (
    "approximation_ratio_unconditional",
    "optimal_probability",
    "feasible_probability",
)


def summarize(values: list[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=float)
    return {
        "mean": float(array.mean()),
        "std": float(array.std(ddof=1)) if len(array) > 1 else 0.0,
        "median": float(np.median(array)),
        "min": float(array.min()),
        "max": float(array.max()),
    }


def pareto_front(records: list[dict]) -> list[dict]:
    unique: dict[tuple[float, ...], dict] = {}
    for record in records:
        key = tuple(record["params"])
        if key not in unique:
            unique[key] = record
    front: list[dict] = []
    for candidate in unique.values():
        point = np.array([candidate[key] for key in OBJECTIVES], dtype=float)
        dominated = False
        survivors = []
        for incumbent in front:
            other = np.array([incumbent[key] for key in OBJECTIVES], dtype=float)
            if np.all(other >= point) and np.any(other > point):
                dominated = True
                break
            if not (np.all(point >= other) and np.any(point > other)):
                survivors.append(incumbent)
        if not dominated:
            survivors.append(candidate)
            front = survivors
    return sorted(front, key=lambda row: row["approximation_ratio_unconditional"], reverse=True)


def aggregate_shot_trials(trials: list[dict]) -> dict[str, dict[str, float]]:
    result = {}
    for key in trials[0]:
        if key == "best_repaired_mask":
            continue
        values = [float(row[key]) for row in trials]
        result[key] = summarize(values)
    return result


def write_records(path: Path, records: list[dict]) -> None:
    fields = ["method", "replicate", "evaluation", "params", "score", *OBJECTIVES,
              "expected_feasible_size_unconditional", "expected_size_given_feasible"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            row = dict(record)
            row["params"] = json.dumps(row["params"])
            writer.writerow(row)


def plot_score_pairs(path: Path, replicate_summary: list[dict]) -> None:
    de = [row["differential_evolution"]["score"] for row in replicate_summary]
    random = [row["random_search"]["score"] for row in replicate_summary]
    x = np.arange(1, len(de) + 1)
    plt.figure(figsize=(8.5, 4.8))
    for i in range(len(de)):
        plt.plot([x[i] - 0.08, x[i] + 0.08], [de[i], random[i]], color="0.75", linewidth=1)
    plt.scatter(x - 0.08, de, label="Differential evolution", s=45)
    plt.scatter(x + 0.08, random, label="Equal-budget random", s=45)
    plt.xlabel("Paired replicate")
    plt.ylabel("Best raw composite score after 300 evaluations")
    plt.title("Depth-2 QAOA: paired search robustness")
    plt.xticks(x)
    plt.grid(alpha=0.22)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def plot_pareto(path: Path, records: list[dict], front: list[dict]) -> None:
    plt.figure(figsize=(8.5, 5.2))
    colors = {"differential_evolution": "#1f77b4", "random_search": "#ff7f0e"}
    for method in colors:
        subset = [row for row in records if row["method"] == method]
        plt.scatter(
            [row["approximation_ratio_unconditional"] for row in subset],
            [row["optimal_probability"] for row in subset],
            c=[row["feasible_probability"] for row in subset],
            cmap="viridis",
            vmin=0,
            vmax=1,
            s=9,
            alpha=0.22,
            marker="o" if method == "differential_evolution" else "x",
            label=method.replace("_", " "),
        )
    plt.scatter(
        [row["approximation_ratio_unconditional"] for row in front],
        [row["optimal_probability"] for row in front],
        facecolors="none",
        edgecolors="black",
        s=70,
        linewidths=1.2,
        label="non-dominated",
    )
    plt.colorbar(label="Raw feasible probability")
    plt.xlabel("Unconditional expected feasible size / optimum")
    plt.ylabel("Exact probability of optimum")
    plt.title("Depth-2 QAOA search landscape and Pareto front")
    plt.grid(alpha=0.2)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--budget", type=int, default=300)
    parser.add_argument("--repeats", type=int, default=12)
    parser.add_argument("--shots", type=int, default=4096)
    parser.add_argument("--shot-trials", type=int, default=8)
    parser.add_argument("--noise-shots", type=int, default=256)
    parser.add_argument("--noise-trials", type=int, default=4)
    parser.add_argument("--seed", type=int, default=20260802)
    args = parser.parse_args()
    p = 2
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    train = load_dimacs_graph(INSTANCE_DIR / "mammalia-kangaroo-interactions.gph")
    held_out = load_dimacs_graph(INSTANCE_DIR / "farm.gph")
    train_exact = enumerate_exact_space(train)
    held_out_exact = enumerate_exact_space(held_out)
    bounds = [(1.05, 4.0)] + [(0.0, math.pi)] * p + [(0.0, 2.0 * math.pi)] * p
    metric_cache: dict[tuple[float, ...], dict[str, float]] = {}
    records: list[dict] = []
    replicate_summary = []

    def metrics_for(params: np.ndarray) -> dict[str, float]:
        key = tuple(float(x) for x in params)
        if key not in metric_cache:
            probs = statevector_probabilities(train, np.asarray(params), p)
            metric_cache[key] = distribution_metrics(probs, train_exact)
        return metric_cache[key]

    started = time.perf_counter()
    for replicate in range(args.repeats):
        replicate_seed = args.seed + 10007 * replicate
        per_method = {}
        for method in ("differential_evolution", "random_search"):
            evaluation = 0

            def objective(params: np.ndarray, method=method, replicate=replicate) -> float:
                nonlocal evaluation
                evaluation += 1
                metrics = metrics_for(params)
                records.append({
                    "method": method,
                    "replicate": replicate,
                    "evaluation": evaluation,
                    "params": [float(x) for x in params],
                    **metrics,
                })
                return metrics["score"]

            if method == "differential_evolution":
                params, score, _ = differential_evolution_fixed_budget(
                    objective, bounds, args.budget, replicate_seed, population_size=15
                )
            else:
                params, score, _ = random_search_fixed_budget(
                    objective, bounds, args.budget, replicate_seed + 1
                )
            method_records = [row for row in records if row["method"] == method and row["replicate"] == replicate]
            per_method[method] = {
                "score": float(score),
                "params": params.tolist(),
                **{f"max_{key}": max(float(row[key]) for row in method_records) for key in OBJECTIVES},
            }
        replicate_summary.append({"replicate": replicate, **per_method})
    search_seconds = time.perf_counter() - started

    front = pareto_front(records)
    de_champion = max((row for row in records if row["method"] == "differential_evolution"), key=lambda row: row["score"])
    random_champion = max((row for row in records if row["method"] == "random_search"), key=lambda row: row["score"])
    optimum_champion = max(records, key=lambda row: row["optimal_probability"])
    expected_champion = max(records, key=lambda row: row["approximation_ratio_unconditional"])

    candidate_rows = {
        "evolution_best_score": de_champion,
        "random_best_score": random_champion,
        "pareto_best_optimum_probability": optimum_champion,
        "pareto_best_expected_feasible_ratio": expected_champion,
    }
    candidates = {}
    best_solution = None
    circuit_stats = None
    for name, row in candidate_rows.items():
        params = np.asarray(row["params"], dtype=float)
        train_probs = statevector_probabilities(train, params, p)
        held_probs = statevector_probabilities(held_out, params, p)
        ideal_trials = []
        noisy_trials = []
        for trial in range(args.shot_trials):
            counts = multinomial_counts(train_probs, args.shots, args.seed + 1000 * trial)
            metrics = counts_metrics(counts, train, train_exact)
            ideal_trials.append(metrics)
            if name == "evolution_best_score" and trial == 0:
                best_solution = {
                    "mask": int(metrics["best_repaired_mask"]),
                    "vertices_1_based": mask_to_vertices(int(metrics["best_repaired_mask"]), train.n),
                    "size": int(metrics["best_repaired_size"]),
                }
        for trial in range(args.noise_trials):
            counts, stats = sample_counts(
                train, params, p, args.noise_shots, args.seed + 20000 + 1000 * trial, True
            )
            noisy_trials.append(counts_metrics(counts, train, train_exact))
            if name == "evolution_best_score" and trial == 0:
                circuit_stats = stats
        candidates[name] = {
            "origin_method": row["method"],
            "params": row["params"],
            "exact_train": distribution_metrics(train_probs, train_exact),
            "exact_held_out": distribution_metrics(held_probs, held_out_exact),
            "ideal_shots": {"aggregate": aggregate_shot_trials(ideal_trials), "trials": ideal_trials},
            "noisy_shots": {"aggregate": aggregate_shot_trials(noisy_trials), "trials": noisy_trials},
        }

    metric_comparison = {}
    for metric in ("score", *OBJECTIVES):
        key = metric if metric == "score" else f"max_{metric}"
        de_values = [float(row["differential_evolution"][key]) for row in replicate_summary]
        random_values = [float(row["random_search"][key]) for row in replicate_summary]
        metric_comparison[metric] = {
            "differential_evolution": summarize(de_values),
            "random_search": summarize(random_values),
            "paired_evolution_wins": sum(de > random for de, random in zip(de_values, random_values)),
            "ties": sum(de == random for de, random in zip(de_values, random_values)),
        }

    score_comparison = metric_comparison["score"]
    promotion_checks = {
        "exact_optimal_solution_found": bool(best_solution and best_solution["size"] == train_exact.optimum),
        "mean_score_beats_equal_budget_random": bool(
            score_comparison["differential_evolution"]["mean"] > score_comparison["random_search"]["mean"]
        ),
        "strict_majority_of_paired_score_runs": bool(score_comparison["paired_evolution_wins"] > args.repeats / 2),
        "held_out_score_beats_random_champion": bool(
            candidates["evolution_best_score"]["exact_held_out"]["score"]
            > candidates["random_best_score"]["exact_held_out"]["score"]
        ),
    }

    report = {
        "experiment": "Depth-2 QAOA: replicated evolutionary search and Pareto audit on QOBLIB MIS",
        "timestamp_local": time.strftime("%Y-%m-%d %H:%M:%S"),
        "configuration": {**vars(args), "p": p, "total_statevector_budget_per_method": args.budget * args.repeats},
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "qiskit": qiskit.__version__,
            "qiskit_aer": qiskit_aer.__version__,
            "numpy": np.__version__,
        },
        "instances": {
            "train": {"name": train.name, "vertices": train.n, "edges": len(train.edges), "exact_optimum": train_exact.optimum, "source": train.source},
            "held_out": {"name": held_out.name, "vertices": held_out.n, "edges": len(held_out.edges), "exact_optimum": held_out_exact.optimum, "source": held_out.source},
        },
        "score_definition": "E[feasible size]/optimum + 0.25*P(optimum) + 0.10*P(feasible); repair excluded",
        "search_seconds": search_seconds,
        "evaluated_records": len(records),
        "unique_genomes": len(metric_cache),
        "replicates": replicate_summary,
        "metric_comparison": metric_comparison,
        "pareto_front_size": len(front),
        "pareto_front": front,
        "candidates": candidates,
        "best_repaired_solution": best_solution,
        "compiled_circuit": circuit_stats,
        "promotion_gate": {
            "checks": promotion_checks,
            "promote": all(promotion_checks.values()),
            "reason": "Promotion requires robust equal-budget superiority and held-out transfer, not a single champion or repair-only success.",
        },
    }
    (OUTPUT_DIR / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_records(OUTPUT_DIR / "all_evaluations.csv", records)
    write_records(OUTPUT_DIR / "pareto_front.csv", front)
    plot_score_pairs(OUTPUT_DIR / "paired_scores.png", replicate_summary)
    plot_pareto(OUTPUT_DIR / "pareto_landscape.png", records, front)
    if best_solution:
        bits = ["1" if i + 1 in best_solution["vertices_1_based"] else "0" for i in range(train.n)]
        (OUTPUT_DIR / "best_solution.txt").write_text(" ".join(bits) + "\n", encoding="utf-8")

    print(json.dumps({
        "search_seconds": search_seconds,
        "evaluations": len(records),
        "unique_genomes": len(metric_cache),
        "pareto_front_size": len(front),
        "score_comparison": score_comparison,
        "promotion_gate": report["promotion_gate"],
        "results": str((OUTPUT_DIR / "results.json").resolve()),
    }, indent=2))


if __name__ == "__main__":
    main()
