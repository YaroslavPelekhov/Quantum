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

from qaoa_mis import (
    counts_metrics,
    differential_evolution_fixed_budget,
    distribution_metrics,
    enumerate_exact_space,
    load_dimacs_graph,
    mask_to_vertices,
    multinomial_counts,
    qaoa_circuit,
    random_search_fixed_budget,
    sample_counts,
    statevector_probabilities,
)


ROOT = Path(__file__).resolve().parents[2]
INSTANCE_DIR = ROOT / "QOBLIB" / "07-independentset" / "instances"
OUTPUT_DIR = Path(__file__).resolve().parent / "results"


def evaluate_exact(graph, exact, params: np.ndarray, p: int) -> dict[str, float]:
    return distribution_metrics(statevector_probabilities(graph, params, p), exact)


def aggregate_trials(trials: list[dict[str, float | int]]) -> dict[str, dict[str, float]]:
    keys = [key for key in trials[0] if key not in {"best_repaired_mask"}]
    result = {}
    for key in keys:
        values = np.asarray([float(trial[key]) for trial in trials], dtype=float)
        result[key] = {"mean": float(values.mean()), "std": float(values.std(ddof=1)) if len(values) > 1 else 0.0}
    return result


def summarize_scores(scores: list[float]) -> dict[str, float]:
    values = np.asarray(scores, dtype=float)
    return {
        "mean": float(values.mean()),
        "std": float(values.std(ddof=1)) if len(values) > 1 else 0.0,
        "median": float(np.median(values)),
        "min": float(values.min()),
        "max": float(values.max()),
    }


def save_history_csv(path: Path, evolution_history, random_history) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["method", "evaluation", "best_score", "best_params"])
        for method, history in (("differential_evolution", evolution_history), ("random_search", random_history)):
            for row in history:
                writer.writerow([method, row["evaluation"], row["best_score"], json.dumps(row["best_params"])])


def plot_history(path: Path, evolution_history, random_history) -> None:
    plt.figure(figsize=(8.5, 4.8))
    plt.plot([x["evaluation"] for x in evolution_history], [x["best_score"] for x in evolution_history], label="Differential evolution", linewidth=2)
    plt.plot([x["evaluation"] for x in random_history], [x["best_score"] for x in random_history], label="Equal-budget random search", linewidth=2)
    plt.xlabel("Exact statevector evaluations")
    plt.ylabel("Best composite score")
    plt.title("Representative paired run on QOBLIB mammalia-kangaroo-interactions")
    plt.grid(alpha=0.25)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--budget", type=int, default=60)
    parser.add_argument("--shots", type=int, default=4096)
    parser.add_argument("--trials", type=int, default=8)
    parser.add_argument("--noise-shots", type=int, default=256)
    parser.add_argument("--noise-trials", type=int, default=4)
    parser.add_argument("--search-repeats", type=int, default=12)
    parser.add_argument("--p", type=int, default=1)
    parser.add_argument("--seed", type=int, default=20260802)
    args = parser.parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    train = load_dimacs_graph(INSTANCE_DIR / "mammalia-kangaroo-interactions.gph")
    held_out = load_dimacs_graph(INSTANCE_DIR / "farm.gph")
    train_exact = enumerate_exact_space(train)
    held_out_exact = enumerate_exact_space(held_out)
    bounds = [(1.05, 4.0)] + [(0.0, math.pi)] * args.p + [(0.0, 2.0 * math.pi)] * args.p

    cache: dict[tuple[float, ...], dict[str, float]] = {}
    def objective(params: np.ndarray) -> float:
        key = tuple(float(x) for x in params)
        if key not in cache:
            cache[key] = evaluate_exact(train, train_exact, params, args.p)
        return cache[key]["score"]

    replicate_rows = []
    evolution_history = None
    random_history = None
    started = time.perf_counter()
    for replicate in range(args.search_repeats):
        replicate_seed = args.seed + replicate * 10007
        de_params, de_score, de_history = differential_evolution_fixed_budget(
            objective, bounds, args.budget, replicate_seed, population_size=10
        )
        rs_params, rs_score, rs_history = random_search_fixed_budget(
            objective, bounds, args.budget, replicate_seed + 1
        )
        if replicate == 0:
            evolution_history = de_history
            random_history = rs_history
        replicate_rows.append({
            "replicate": replicate,
            "evolution_seed": replicate_seed,
            "random_seed": replicate_seed + 1,
            "evolution_score": de_score,
            "random_score": rs_score,
            "evolution_params": de_params.tolist(),
            "random_params": rs_params.tolist(),
        })
    search_seconds = time.perf_counter() - started
    evolution_champion = max(replicate_rows, key=lambda row: row["evolution_score"])
    random_champion = max(replicate_rows, key=lambda row: row["random_score"])
    evolution_params = np.asarray(evolution_champion["evolution_params"], dtype=float)
    random_params = np.asarray(random_champion["random_params"], dtype=float)
    evolution_score = float(evolution_champion["evolution_score"])
    random_score = float(random_champion["random_score"])
    assert evolution_history is not None and random_history is not None

    methods = {
        "differential_evolution": evolution_params,
        "random_search": random_params,
        "fixed_schedule": np.array([2.0] + [math.pi / 4] * args.p + [math.pi / 4] * args.p),
    }
    exact_results = {}
    held_out_results = {}
    sampling_results = {}
    best_solution = None
    circuit_stats = None
    for method, params in methods.items():
        train_probs = statevector_probabilities(train, params, args.p)
        exact_results[method] = distribution_metrics(train_probs, train_exact)
        held_out_results[method] = evaluate_exact(held_out, held_out_exact, params, args.p)
        sampling_results[method] = {}
        for noisy in (False, True):
            label = "depolarizing_noise" if noisy else "noiseless_shots"
            trials = []
            trial_count = args.noise_trials if noisy else args.trials
            shot_count = args.noise_shots if noisy else args.shots
            for trial in range(trial_count):
                seed = args.seed + 1000 * trial + (1 if noisy else 0)
                if noisy:
                    counts, stats = sample_counts(train, params, args.p, shot_count, seed, True)
                else:
                    counts = multinomial_counts(train_probs, shot_count, seed)
                    stats = None
                metrics = counts_metrics(counts, train, train_exact)
                trials.append(metrics)
                if method == "differential_evolution" and not noisy and trial == 0:
                    best_solution = {
                        "mask": int(metrics["best_repaired_mask"]),
                        "vertices_1_based": mask_to_vertices(int(metrics["best_repaired_mask"]), train.n),
                        "size": int(metrics["best_repaired_size"]),
                    }
                if method == "differential_evolution" and noisy and trial == 0:
                    circuit_stats = stats
            sampling_results[method][label] = {"aggregate": aggregate_trials(trials), "trials": trials}

    evolution_scores = [float(row["evolution_score"]) for row in replicate_rows]
    random_scores = [float(row["random_score"]) for row in replicate_rows]
    paired_wins = sum(de > rs for de, rs in zip(evolution_scores, random_scores))
    promotion_checks = {
        "exact_optimal_solution_found": bool(best_solution is not None and best_solution["size"] == train_exact.optimum),
        "raw_train_feasible_probability_at_least_0_5": bool(exact_results["differential_evolution"]["feasible_probability"] >= 0.5),
        "held_out_score_beats_fixed_schedule": bool(held_out_results["differential_evolution"]["score"] > held_out_results["fixed_schedule"]["score"]),
        "replicated_mean_beats_equal_budget_random": bool(np.mean(evolution_scores) > np.mean(random_scores)),
        "strict_majority_of_paired_runs_beat_random": bool(paired_wins > args.search_repeats / 2),
    }
    report = {
        "experiment": "Evolutionary parameter search for depth-p QAOA on QOBLIB MIS",
        "timestamp_local": time.strftime("%Y-%m-%d %H:%M:%S"),
        "configuration": vars(args),
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
        "score_definition": "E[feasible size]/optimum + 0.25*P(optimum) + 0.10*P(feasible); no repair is used during search",
        "noise_model": "Independent depolarizing error: 0.001 after 1-qubit gates and 0.01 after RZZ; generic stress test, not hardware-calibrated",
        "search": {
            "differential_evolution": {"champion_params": evolution_params.tolist(), "champion_score": evolution_score, "summary": summarize_scores(evolution_scores)},
            "random_search": {"champion_params": random_params.tolist(), "champion_score": random_score, "summary": summarize_scores(random_scores)},
            "fixed_schedule": {"params": methods["fixed_schedule"].tolist()},
            "paired_evolution_wins": paired_wins,
            "paired_random_wins": args.search_repeats - paired_wins,
            "replicates": replicate_rows,
            "total_search_seconds": search_seconds,
        },
        "exact_train": exact_results,
        "exact_held_out_transfer": held_out_results,
        "finite_shot_train": sampling_results,
        "best_repaired_solution": best_solution,
        "compiled_circuit": circuit_stats,
        "promotion_gate": {
            "checks": promotion_checks,
            "promote_to_larger_or_hardware_experiment": all(promotion_checks.values()),
            "reason": "All checks must pass; repair-only success cannot compensate for a weak raw quantum distribution.",
        },
    }
    (OUTPUT_DIR / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    save_history_csv(OUTPUT_DIR / "search_history.csv", evolution_history, random_history)
    plot_history(OUTPUT_DIR / "search_convergence.png", evolution_history, random_history)
    if best_solution is not None:
        bits = ["1" if i + 1 in best_solution["vertices_1_based"] else "0" for i in range(train.n)]
        (OUTPUT_DIR / "best_solution.txt").write_text(" ".join(bits) + "\n", encoding="utf-8")

    print(json.dumps({
        "train_optimum": train_exact.optimum,
        "held_out_optimum": held_out_exact.optimum,
        "evolution_score": evolution_score,
        "random_score": random_score,
        "evolution_params": evolution_params.tolist(),
        "best_solution": best_solution,
        "search_seconds": search_seconds,
        "results": str((OUTPUT_DIR / "results.json").resolve()),
    }, indent=2))


if __name__ == "__main__":
    main()
