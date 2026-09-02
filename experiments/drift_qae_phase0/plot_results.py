"""Create compact static figures for the drift-QAE falsification artifact."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "drift_qae_phase0"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def median_curves(rows: list[dict[str, str]]) -> dict[tuple[str, str], list[tuple[float, float]]]:
    grouped: dict[tuple[str, str, int], list[tuple[float, float]]] = defaultdict(list)
    for row in rows:
        grouped[(row["model"], row["estimator"], int(row["levels"]))].append(
            (float(row["physical_depth_budget"]), float(row["rmse"]))
        )
    curves: dict[tuple[str, str], list[tuple[float, float]]] = defaultdict(list)
    for (model, estimator, _), values in grouped.items():
        budgets = np.asarray([value[0] for value in values])
        errors = np.asarray([value[1] for value in values])
        curves[(model, estimator)].append((float(np.median(budgets)), float(np.median(errors))))
    for values in curves.values():
        values.sort()
    return curves


def scaling_figure() -> None:
    rows = read_csv(OUT / "strong_estimator_aggregate.csv")
    curves = median_curves(rows)
    labels = {
        "global_mle_oracle": "nuisance oracle",
        "global_mle_anchored": "charged matched anchors",
        "global_mle_nominal_unanchored": "nominal, no anchors",
        "direct_k1_oracle_visibility": "direct k=1 (strong control)",
    }
    styles = {
        "global_mle_oracle": "o-",
        "global_mle_anchored": "s-",
        "global_mle_nominal_unanchored": "^-",
        "direct_k1_oracle_visibility": "k--",
    }
    figure, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), sharey=True)
    for axis, model in zip(axes, ("readout", "gate"), strict=True):
        for (row_model, estimator), values in curves.items():
            if row_model != model:
                continue
            x = np.asarray([value[0] for value in values])
            y = np.asarray([value[1] for value in values])
            axis.loglog(x, y, styles[estimator], linewidth=1.7, markersize=4, label=labels[estimator])
        axis.set_title("Post-circuit visibility" if model == "readout" else "Depth-accumulating visibility")
        axis.set_xlabel("fully counted physical depth Q")
        axis.grid(True, which="both", alpha=0.25)
    axes[0].set_ylabel("RMSE in theta")
    axes[0].legend(fontsize=8)
    figure.suptitle("Strong-estimator control: favorable readout assumptions do not rescue depth noise")
    figure.tight_layout()
    figure.savefig(OUT / "strong_estimator_scaling.png", dpi=180)
    plt.close(figure)


def fisher_figure() -> None:
    rows = read_csv(OUT / "fisher_audit.csv")
    selected = [
        row
        for row in rows
        if abs(float(row["theta"]) - 0.231) < 1e-12 and int(row["path_index"]) == 0
    ]
    figure, axes = plt.subplots(1, 2, figsize=(10.5, 4.2))
    for axis, model in zip(axes, ("readout", "gate"), strict=True):
        model_rows = sorted(
            (row for row in selected if row["model"] == model),
            key=lambda row: int(row["levels"]),
        )
        budgets = np.asarray([float(row["anchored_budget"]) for row in model_rows])
        known = np.asarray([float(row["known_fisher"]) for row in model_rows])
        anchored = np.asarray([float(row["anchored_efficient_fisher"]) for row in model_rows])
        unanchored = np.asarray([max(float(row["unanchored_efficient_fisher"]), 1e-16) for row in model_rows])
        axis.loglog(budgets, known, "o-", label="known nuisance")
        axis.loglog(budgets, anchored, "s-", label="matched anchors")
        axis.loglog(budgets, unanchored, "x--", label="per-round nuisance, no anchors")
        axis.set_title("Post-circuit" if model == "readout" else "Depth-accumulating")
        axis.set_xlabel("anchored physical depth Q")
        axis.grid(True, which="both", alpha=0.25)
    axes[0].set_ylabel("local efficient Fisher information")
    axes[0].legend(fontsize=8)
    figure.suptitle("Identifiability and depth attenuation are separate mechanisms")
    figure.tight_layout()
    figure.savefig(OUT / "fisher_information_audit.png", dpi=180)
    plt.close(figure)


def main() -> None:
    scaling_figure()
    fisher_figure()
    print("wrote strong_estimator_scaling.png and fisher_information_audit.png")


if __name__ == "__main__":
    main()

