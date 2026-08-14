"""Create paper-ready cross-case replication figures and compact tables."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import beta, fisher_exact


ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "results" / "cross_case_replication" / "analysis.json"
FIGURES = ROOT / "results" / "figures"
TABLE = ROOT / "results" / "cross_case_replication" / "paper_summary.csv"
STATS = ROOT / "results" / "cross_case_replication" / "paper_statistics.json"

CASE_ORDER = [
    "karate",
    "chesapeake",
    "football",
    "ibm32",
    "aves-sparrow-social",
]
CASE_LABELS = {
    "karate": "karate (3q)",
    "chesapeake": "chesapeake (7q)",
    "football": "football (7q)",
    "ibm32": "ibm32 (18q)",
    "aves-sparrow-social": "aves (24q)",
}
SETTING_ORDER = ["released", "confirm", "bond128", "cutoff1e-4", "cutoff1e-5"]
SETTING_LABELS = [
    r"64/$10^{-3}$",
    r"128/$10^{-4}$",
    r"128/$10^{-12}$",
    r"1024/$10^{-4}$",
    r"1024/$10^{-5}$",
]
COLORS = {
    "karate": "#2E86AB",
    "chesapeake": "#3A9D5D",
    "football": "#E3A018",
    "ibm32": "#D95D39",
    "aves-sparrow-social": "#7551A1",
}


def interval(successes: int, total: int, alpha: float = 0.05) -> list[float]:
    lower = 0.0 if successes == 0 else float(beta.ppf(alpha / 2, successes, total - successes + 1))
    upper = 1.0 if successes == total else float(beta.ppf(1 - alpha / 2, successes + 1, total - successes))
    return [lower, upper]


def main() -> None:
    analysis = json.loads(INPUT.read_text(encoding="utf-8"))
    if not analysis.get("complete") or len(analysis.get("summaries", [])) != 100:
        raise RuntimeError("Completed 100-cohort analysis required")
    rows = analysis["summaries"]
    below = [row for row in rows if row["normalized_margin_ratio"] < 1.0]
    above = [row for row in rows if row["normalized_margin_ratio"] >= 1.0]
    table_2x2 = [
        [sum(row["matched_sign_correct"] for row in below), sum(not row["matched_sign_correct"] for row in below)],
        [sum(row["matched_sign_correct"] for row in above), sum(not row["matched_sign_correct"] for row in above)],
    ]
    odds, p_value = fisher_exact(table_2x2, alternative="two-sided")
    stats = {
        "complete": True,
        "cohorts": len(rows),
        "ratio_below_one": {
            "correct": table_2x2[0][0],
            "wrong": table_2x2[0][1],
            "correct_fraction": table_2x2[0][0] / len(below),
            "clopper_pearson_95": interval(table_2x2[0][0], len(below)),
        },
        "ratio_at_least_one": {
            "correct": table_2x2[1][0],
            "wrong": table_2x2[1][1],
            "correct_fraction": table_2x2[1][0] / len(above),
            "clopper_pearson_95": interval(table_2x2[1][0], len(above)),
        },
        "fisher_exact_two_sided": {"odds_ratio": float(odds), "p_value": float(p_value)},
        "maximum_tvd_bound_violation": float(
            max(row["actual_effect_error"] - row["tvd_effect_bound"] for row in rows)
        ),
    }
    STATS.write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")

    case_summary = {row["case"]: row for row in analysis["cases"]}
    with TABLE.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "case",
                "sign_correct",
                "sign_total",
                "tvd_certified",
                "cross_backend_same_sign",
                "cross_backend_total",
                "first_universal_setting",
                "max_tvd_margin_ratio",
            ]
        )
        for case in CASE_ORDER:
            row = case_summary[case]
            writer.writerow(
                [
                    case,
                    row["sign_correct"],
                    row["sign_total"],
                    row["exact_margin_certified"],
                    row["cross_backend_same_sign"],
                    row["cross_backend_total"],
                    row["first_universal_certified_setting"] or "none",
                    f"{row['maximum_normalized_margin_ratio']:.9g}",
                ]
            )

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8.5,
            "axes.titlesize": 9.5,
            "axes.labelsize": 9,
            "legend.fontsize": 7.5,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )
    fig = plt.figure(figsize=(7.25, 5.65), constrained_layout=True)
    grid = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.05])
    ax_bound = fig.add_subplot(grid[0, 0])
    ax_ratio = fig.add_subplot(grid[0, 1])
    ax_heat = fig.add_subplot(grid[1, :])

    for case in CASE_ORDER:
        cohort = [row for row in rows if row["case"] == case]
        x = np.asarray([row["tvd_effect_bound"] for row in cohort])
        y = np.asarray([max(row["actual_effect_error"], 1e-8) for row in cohort])
        ax_bound.scatter(x, y, s=23, alpha=0.82, color=COLORS[case], label=CASE_LABELS[case], edgecolor="white", linewidth=0.35)
    limits = [1e-5, 2.0]
    ax_bound.plot(limits, limits, "--", color="#303030", linewidth=1.0, label="theorem boundary")
    ax_bound.set(xscale="log", yscale="log", xlim=limits, ylim=limits)
    ax_bound.set_xlabel(r"TVD effect bound $d_{LR}+d_{MR}$")
    ax_bound.set_ylabel(r"Observed effect error $|\widetilde\Delta-\Delta|$")
    ax_bound.set_title("a  All 100 event-error bounds hold", loc="left", fontweight="bold")
    ax_bound.grid(True, which="both", linewidth=0.3, alpha=0.25)

    for case in CASE_ORDER:
        cohort = [row for row in rows if row["case"] == case]
        ratio = np.asarray([row["normalized_margin_ratio"] for row in cohort])
        alignment = np.asarray(
            [row["matched_bks_effect"] / row["exact_matched_bks_effect"] for row in cohort]
        )
        correct = np.asarray([row["matched_sign_correct"] for row in cohort], dtype=bool)
        ax_ratio.scatter(
            ratio[correct], alignment[correct], s=25, color=COLORS[case], alpha=0.82,
            edgecolor="white", linewidth=0.35,
        )
        if np.any(~correct):
            ax_ratio.scatter(
                ratio[~correct], alignment[~correct], s=38, marker="x", color=COLORS[case],
                linewidth=1.25,
            )
    ax_ratio.axvline(1.0, linestyle="--", color="#303030", linewidth=1.0)
    ax_ratio.axhline(0.0, color="#555555", linewidth=0.8)
    ax_ratio.set_xscale("log")
    ax_ratio.set_xlim(2e-4, 100)
    ax_ratio.set_ylim(-12, 15)
    ax_ratio.set_xlabel(r"Normalized bound $(d_{LR}+d_{MR})/|\Delta|$")
    ax_ratio.set_ylabel(r"Effect alignment $\widetilde\Delta/\Delta$")
    ax_ratio.set_title("b  Certificate threshold predicts sign", loc="left", fontweight="bold")
    ax_ratio.text(
        0.03, 0.04, "ratio < 1: 77/77 correct\nratio >= 1: 14/23 correct",
        transform=ax_ratio.transAxes, va="bottom", ha="left",
        bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "alpha": 0.9, "edgecolor": "#bbbbbb"},
    )
    ax_ratio.grid(True, which="both", linewidth=0.3, alpha=0.25)

    correct_matrix = np.zeros((len(CASE_ORDER), len(SETTING_ORDER)), dtype=int)
    certified_matrix = np.zeros_like(correct_matrix)
    for i, case in enumerate(CASE_ORDER):
        for j, setting in enumerate(SETTING_ORDER):
            cohort = [row for row in rows if row["case"] == case and row["name"] == setting]
            if len(cohort) != 4:
                raise AssertionError(f"Expected four backend/order cohorts for {case}/{setting}")
            correct_matrix[i, j] = sum(row["matched_sign_correct"] for row in cohort)
            certified_matrix[i, j] = sum(row["exact_margin_tvd_certified"] for row in cohort)
    image = ax_heat.imshow(certified_matrix, cmap="Blues", vmin=0, vmax=4, aspect="auto")
    for i in range(len(CASE_ORDER)):
        for j in range(len(SETTING_ORDER)):
            value = certified_matrix[i, j]
            color = "white" if value >= 3 else "#222222"
            ax_heat.text(j, i, f"{correct_matrix[i,j]}/4 correct\n{value}/4 certified", ha="center", va="center", color=color, fontsize=8)
    ax_heat.set_xticks(range(len(SETTING_ORDER)), SETTING_LABELS)
    ax_heat.set_yticks(range(len(CASE_ORDER)), [CASE_LABELS[case] for case in CASE_ORDER])
    ax_heat.set_xlabel("Frozen MPS setting (bond / cutoff)")
    ax_heat.set_title("c  Per-case replication across backend and ordering", loc="left", fontweight="bold")
    colorbar = fig.colorbar(image, ax=ax_heat, pad=0.015, fraction=0.025)
    colorbar.set_label("Certified cohorts (of 4)")

    handles, labels = ax_bound.get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside upper center", ncol=6, frameon=False)
    FIGURES.mkdir(parents=True, exist_ok=True)
    for suffix in ("pdf", "png"):
        fig.savefig(FIGURES / f"cross_case_replication.{suffix}", dpi=240, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote figure, {TABLE.relative_to(ROOT)}, and {STATS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
