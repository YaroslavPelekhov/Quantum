"""Create the compact publication figure for the strict resource-aware cycle."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results" / "resource_aware"
FIGURES = ROOT / "results" / "figures"


def load(name: str) -> dict:
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


def main() -> None:
    reachability = load("reachability.json")
    validation = load("validation_confirm.json")
    blind = load("blind_confirmation.json")
    FIGURES.mkdir(parents=True, exist_ok=True)

    plt.rcParams.update(
        {
            "font.size": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.dpi": 180,
        }
    )
    figure, axes = plt.subplots(1, 3, figsize=(12.2, 3.65), constrained_layout=True)

    # A: certified reachability of the known best solution after reduction.
    ax = axes[0]
    names = ["es60fst01", "es60fst03", "es60fst04", "es60fst02"]
    labels = ["train-1", "train-2", "validation", "blind"]
    markers = ["o", "s", "^", "D"]
    for name, label, marker in zip(names, labels, markers):
        rows = [row for row in reachability["rows"] if row["name"] == name]
        x = [row["max_degree"] for row in rows]
        y = [row["qubits"] for row in rows]
        reachable = np.array([row["bks_reachable"] for row in rows], dtype=bool)
        ax.plot(x, y, color="#7a7a7a", alpha=0.45, linewidth=1)
        ax.scatter(np.array(x)[reachable], np.array(y)[reachable], marker=marker,
                   label=label, s=42)
        ax.scatter(np.array(x)[~reachable], np.array(y)[~reachable], marker="x",
                   color="#c43c39", s=36)
    ax.axvline(4, color="#202020", linestyle="--", linewidth=1, label="minimum cap")
    ax.set(xlabel="Reduction cap", ylabel="Reduced qubits", title="A  Exact reachability gate")
    ax.set_xticks([2, 3, 4, 5, 6])
    ax.legend(frameon=False, fontsize=7, ncol=2, loc="upper left")

    # B: validation quality/runtime frontier under both simulator fidelities.
    ax = axes[1]
    colors = {
        "published_lr_p15__sorted": "#222222",
        "prior_evolutionary_p15__sorted": "#2f6db0",
        "prior_evolutionary_p15__spectral": "#7aa6d8",
        "prior_matched_random_p15__sorted": "#d97927",
        "prior_matched_random_p15__spectral": "#efb06a",
    }
    short = {
        "published_lr_p15__sorted": "LR",
        "prior_evolutionary_p15__sorted": "Evo-S",
        "prior_evolutionary_p15__spectral": "Evo-Sp",
        "prior_matched_random_p15__sorted": "Match-S",
        "prior_matched_random_p15__spectral": "Match-Sp",
    }
    for row in validation["summary"]:
        marker = "o" if row["setting"] == "released" else "s"
        ax.scatter(row["median_elapsed_seconds"], row["bks_rate"], marker=marker,
                   color=colors[row["config_key"]], s=45)
        ax.annotate(short[row["config_key"]],
                    (row["median_elapsed_seconds"], row["bks_rate"]),
                    xytext=(3, 3), textcoords="offset points", fontsize=6.7)
    ax.set_xscale("log")
    ax.set(xlabel="Median seconds/job (log scale)", ylabel="BKS rate",
           title="B  Validation quality-cost frontier")
    ax.text(0.03, 0.04, "circle: released   square: confirm", transform=ax.transAxes,
            fontsize=7, color="#555555")

    # C: blind paired effect and the fidelity reversal.
    ax = axes[2]
    candidate = [row for row in blind["comparisons"]
                 if row["config_key"] == "prior_matched_random_p15__sorted"]
    y_positions = {"released": 1, "confirm": 0}
    for row in candidate:
        stats = row["comparisons"]["bks_rate"]
        y = y_positions[row["setting"]]
        mean = 100 * stats["mean_difference"]
        low, high = (100 * value for value in stats["ci95"])
        ax.errorbar(mean, y, xerr=[[mean - low], [high - mean]], fmt="o", capsize=4,
                    color="#2f6db0" if row["setting"] == "released" else "#c43c39")
        ax.text(high + 0.025, y, f"p={stats['sign_flip_p_two_sided']:.4f}",
                va="center", fontsize=7)
    ax.axvline(0, color="#202020", linestyle="--", linewidth=1)
    ax.set_yticks([0, 1], labels=["confirm", "released"])
    ax.set(xlabel="Paired BKS-rate difference (percentage points)",
           title="C  Blind fidelity reversal")
    ax.set_ylim(-0.6, 1.6)

    figure.suptitle("Strict resource-aware QAOA: certified abstention and simulator-fidelity risk",
                    fontsize=11, fontweight="bold")
    for suffix in ("png", "pdf"):
        figure.savefig(FIGURES / f"resource_aware_cycle.{suffix}", bbox_inches="tight")
    plt.close(figure)
    print("wrote results/figures/resource_aware_cycle.{png,pdf}")


if __name__ == "__main__":
    main()
