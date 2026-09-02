"""Plot the registered curvature crossover and resource controls."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "interleaved_drift_boundary_phase0"


def load_rows() -> list[dict[str, str]]:
    with (OUT / "monte_carlo.csv").open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def plot_scaling(rows: list[dict[str, str]]) -> None:
    grouped: dict[tuple[str, float, int], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["estimator"], float(row["curvature"]), int(row["depth"]))].append(row)

    figure, axis = plt.subplots(figsize=(7.2, 4.8))
    curvatures = (0.0, 1e-8, 1e-7, 1e-6)
    for curvature in curvatures:
        values = []
        for (estimator, row_curvature, depth), group in grouped.items():
            if estimator == "amplified_rtr" and row_curvature == curvature:
                values.append(
                    (
                        float(np.median([float(row["physical_depth_budget"]) for row in group])),
                        float(np.median([float(row["rmse"]) for row in group])),
                    )
                )
        values.sort()
        axis.loglog(
            [value[0] for value in values],
            [value[1] for value in values],
            "o-",
            label=f"RTR amplified, kappa={curvature:g}",
        )
    direct = []
    for (estimator, _, depth), group in grouped.items():
        if estimator == "direct_depth1_equal_cost":
            direct.append(
                (
                    float(np.median([float(row["physical_depth_budget"]) for row in group])),
                    float(np.median([float(row["rmse"]) for row in group])),
                )
            )
    direct.sort()
    axis.loglog(
        [value[0] for value in direct],
        [value[1] for value in direct],
        "k--",
        linewidth=2,
        label="depth-1 equal-cost control",
    )
    axis.set_xlabel("fully counted physical depth Q")
    axis.set_ylabel("RMSE in theta")
    axis.set_title("Sequential calibration: coherent-depth gain and curvature breakdown")
    axis.grid(True, which="both", alpha=0.25)
    axis.legend(fontsize=8)
    figure.tight_layout()
    figure.savefig(OUT / "curvature_resource_scaling.png", dpi=180)
    plt.close(figure)


def plot_collapse(rows: list[dict[str, str]]) -> None:
    selected = [
        row
        for row in rows
        if row["estimator"] == "amplified_rtr" and float(row["curvature"]) > 0
    ]
    x = np.asarray([float(row["crossover_xi"]) for row in selected])
    y = np.asarray([float(row["normalized_absolute_deterministic_bias"]) for row in selected])
    order = np.argsort(x)
    figure, axis = plt.subplots(figsize=(6.4, 4.6))
    axis.loglog(x, y, "o", markersize=3.5, alpha=0.45, label="registered rows")
    axis.loglog(x[order], 0.5 * x[order], "k--", linewidth=2, label="exact quadratic prediction: xi/2")
    axis.set_xlabel("xi = kappa tau^2 D^3")
    axis.set_ylabel("D |deterministic theta bias|")
    axis.set_title("Exact curvature crossover collapse")
    axis.grid(True, which="both", alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(OUT / "curvature_collapse.png", dpi=180)
    plt.close(figure)


def main() -> None:
    rows = load_rows()
    plot_scaling(rows)
    plot_collapse(rows)
    print("wrote curvature_resource_scaling.png and curvature_collapse.png")


if __name__ == "__main__":
    main()

