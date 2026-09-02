"""Plot frozen and explicitly post-hoc gauge-resource diagnostics."""

from __future__ import annotations

import csv
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "results" / "aquila_gauge_resource_phase0"
RHO = 0.2


def read_rows(name: str) -> list[dict]:
    with (OUTPUT / name).open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def finite(value: str) -> bool:
    return math.isfinite(float(value))


def cohort_rows(rows: list[dict], cohort: str) -> list[dict]:
    return [row for row in rows if row.get("cohort", cohort) == cohort and finite(row["median_objective_lower"])]


def median_width(instances: list[dict], cohort: str, n: int) -> float:
    values = [
        float(row["physical_frequency_width_rad_per_us"])
        for row in instances
        if row["cohort"] == cohort and int(row["n"]) == n
    ]
    return float(np.median(values))


def main() -> None:
    frozen_aggregate = read_rows("scaling_aggregate.csv")
    posthoc_aggregate = read_rows("posthoc_scaling_aggregate.csv")
    frozen_instances = read_rows("milp_instances.csv")
    posthoc_instances = read_rows("posthoc_milp_instances.csv")
    development = cohort_rows(frozen_aggregate, "development")
    posthoc = [row for row in posthoc_aggregate if finite(row["median_objective_lower"])]

    figure, axes = plt.subplots(2, 2, figsize=(11.5, 7.7), constrained_layout=True)

    for rows, label, color in (
        (development, "frozen development", "#31688e"),
        (posthoc, "post-hoc heldout +0.001 um", "#d1495b"),
    ):
        n_values = np.asarray([int(row["n"]) for row in rows])
        lower = np.asarray([float(row["median_objective_lower"]) for row in rows])
        raw = np.asarray([float(row["median_raw_cost"]) for row in rows])
        axes[0, 0].semilogy(n_values, lower, "o-", color=color, linewidth=2, label=label)
        axes[0, 0].semilogy(n_values, raw, ":", color=color, alpha=0.6)
    axes[0, 0].set_xlabel("atoms n")
    axes[0, 0].set_ylabel("normalized spectral cost")
    axes[0, 0].set_title("Certified quotient lower (solid); raw (dotted)")
    axes[0, 0].legend(fontsize=8)

    for rows, instances, cohort, label, color in (
        (development, frozen_instances, "development", "frozen development", "#31688e"),
        (posthoc, posthoc_instances, "posthoc", "post-hoc diagnostic", "#d1495b"),
    ):
        n_values = np.asarray([int(row["n"]) for row in rows])
        bounds = np.asarray(
            [
                (2.0 * RHO / math.pi)
                * float(row["median_objective_lower"])
                / median_width(instances, cohort, int(row["n"]))
                for row in rows
            ]
        )
        axes[0, 1].semilogy(n_values, bounds, "o-", color=color, linewidth=2, label=label)
    axes[0, 1].axhline(4.0, color="black", linestyle="--", linewidth=1, label="4 us reference")
    axes[0, 1].set_xlabel("atoms n")
    axes[0, 1].set_ylabel("certified weak-drive T lower bound (us)")
    axes[0, 1].set_title("Fixed response margin rho=0.2")
    axes[0, 1].legend(fontsize=8)

    for rows, label, color in (
        (development, "frozen development", "#31688e"),
        (posthoc, "post-hoc diagnostic", "#d1495b"),
    ):
        axes[1, 0].plot(
            [int(row["n"]) for row in rows],
            [float(row["median_gauge_to_raw_ratio_upper"]) for row in rows],
            "o-",
            color=color,
            linewidth=2,
            label=label,
        )
    axes[1, 0].set_xlabel("atoms n")
    axes[1, 0].set_ylabel("feasible quotient / raw cost")
    axes[1, 0].set_title("Gauge freedom removes nearest-gap pathology")
    axes[1, 0].legend(fontsize=8)

    frozen_optimal = []
    frozen_total = []
    for n in range(3, 8):
        selected = [row for row in frozen_instances if row["cohort"] == "development" and int(row["n"]) == n]
        frozen_optimal.append(sum(row["success"].lower() == "true" for row in selected))
        frozen_total.append(len(selected))
    posthoc_optimal = [int(row["optimal_instances"]) for row in posthoc_aggregate]
    posthoc_total = [int(row["instances"]) for row in posthoc_aggregate]
    x_dev = np.arange(len(frozen_optimal))
    x_post = np.arange(len(posthoc_optimal)) + len(frozen_optimal) + 0.8
    axes[1, 1].bar(x_dev, frozen_optimal, color="#31688e", label="exact optimum")
    axes[1, 1].bar(
        x_dev,
        np.asarray(frozen_total) - np.asarray(frozen_optimal),
        bottom=frozen_optimal,
        color="#f4a261",
        label="timeout / invalid",
    )
    axes[1, 1].bar(x_post, posthoc_optimal, color="#31688e")
    axes[1, 1].bar(
        x_post,
        np.asarray(posthoc_total) - np.asarray(posthoc_optimal),
        bottom=posthoc_optimal,
        color="#f4a261",
    )
    axes[1, 1].set_xticks(
        np.concatenate((x_dev, x_post)),
        ["D3", "D4", "D5", "D6", "D7", "P5", "P6", "P7", "P8"],
    )
    axes[1, 1].set_ylim(0, 4.4)
    axes[1, 1].set_ylabel("targets (of 4)")
    axes[1, 1].set_title("Exact circular MILP completion")
    axes[1, 1].legend(fontsize=8)

    figure.suptitle(
        "Gauge-quotiented weak-drive cost: finite-size hardness survives; A-star gates fail",
        fontsize=12,
    )
    figure.savefig(OUTPUT / "phase0_diagnostics.png", dpi=180)
    plt.close(figure)


if __name__ == "__main__":
    main()
