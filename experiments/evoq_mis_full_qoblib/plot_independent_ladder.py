"""Create the publication figure for the exact cross-backend MPS audit."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent
ANALYSIS = ROOT / "results" / "independent_ladder" / "analysis.json"
FIGURES = ROOT / "results" / "figures"
ORDERINGS = ("sorted", "spectral")
SETTING_ORDER = ("released", "confirm", "bond128", "cutoff1e-4", "cutoff1e-5")
SETTING_LABELS = (
    "64 / $10^{-3}$",
    "128 / $10^{-4}$",
    "128 / $10^{-12}$",
    "1024 / $10^{-4}$",
    "1024 / $10^{-5}$",
)


def main() -> None:
    payload = json.loads(ANALYSIS.read_text(encoding="utf-8"))
    if not payload.get("complete") or len(payload.get("summaries", [])) != 10:
        raise RuntimeError("A complete ten-cohort independent audit is required")
    rows = {(row["name"], row["ordering"]): row for row in payload["summaries"]}

    plt.rcParams.update(
        {
            "font.size": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.dpi": 180,
        }
    )
    figure, axes = plt.subplots(1, 2, figsize=(9.2, 3.55), sharey=True, constrained_layout=True)
    x = np.arange(len(SETTING_ORDER))
    for ax, ordering, panel in zip(axes, ORDERINGS, ("A", "B")):
        cohort = [rows[(name, ordering)] for name in SETTING_ORDER]
        exact = cohort[0]["exact_matched_bks_effect"]
        aer = [row["aer_matched_bks_effect"] for row in cohort]
        cutn = [row["matched_bks_effect"] for row in cohort]
        ax.axhline(0.0, color="#202020", linewidth=0.9)
        ax.axhline(exact, color="#3b8c58", linestyle="--", linewidth=1.5,
                   label=f"exact ({exact:+.4f})")
        ax.plot(x, aer, marker="s", color="#3267a8", linewidth=1.5,
                markersize=5, label="Aer MPS")
        ax.plot(x, cutn, marker="o", color="#cf5b32", linewidth=1.5,
                markersize=5, label="cuTensorNet MPS")
        for index, row in enumerate(cohort):
            if row["matched_sign_correct"]:
                ax.scatter(index, row["matched_bks_effect"], s=70, facecolors="none",
                           edgecolors="#3b8c58", linewidths=1.1, zorder=5)
        ax.set_xticks(x, SETTING_LABELS, rotation=28, ha="right")
        ax.set_xlabel("Maximum bond / cutoff")
        ax.set_title(f"{panel}  {ordering.capitalize()} qubit ordering")
        ax.grid(axis="y", color="#dddddd", linewidth=0.6)
    axes[0].set_ylabel(r"Matched-random minus LR BKS probability")
    axes[1].legend(frameon=False, fontsize=8, loc="upper right")
    axes[0].text(
        0.02,
        0.96,
        "green rings: correct exact sign",
        transform=axes[0].transAxes,
        va="top",
        fontsize=7.5,
        color="#3b8c58",
    )
    figure.suptitle(
        "The same MPS controls do not define the same schedule ranking across backends",
        fontsize=10.5,
        fontweight="bold",
    )
    FIGURES.mkdir(parents=True, exist_ok=True)
    for suffix in ("png", "pdf"):
        figure.savefig(FIGURES / f"independent_ladder.{suffix}", bbox_inches="tight")
    plt.close(figure)
    print("wrote results/figures/independent_ladder.{png,pdf}")


if __name__ == "__main__":
    main()
