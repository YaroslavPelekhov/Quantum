"""Create paper-grade tables, figures, and a concise research-cycle report."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import run_cycle as rc


METHOD_LABELS = {
    "published_lr": "Published LR",
    "evolutionary_search": "Evolutionary",
    "matched_random_search": "Matched random",
}
COLORS = {
    "published_lr": "#4c78a8",
    "evolutionary_search": "#f58518",
    "matched_random_search": "#54a24b",
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def wilson(success: int, total: int, z: float = 1.96):
    p = success / total
    den = 1 + z * z / total
    centre = p + z * z / (2 * total)
    radius = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total))
    return (centre - radius) / den, (centre + radius) / den


def aggregate(rows, method):
    selected = [row for row in rows if row["method"] == method]
    shots = sum(row["metrics"]["total_shots"] for row in selected)
    feasible = sum(row["metrics"]["feasible_shots"] for row in selected)
    bks = sum(row["metrics"]["bks_hits"] for row in selected)
    near = sum(row["metrics"]["near_bks_hits"] for row in selected)
    quality = np.mean([row["metrics"]["quality_mass"] for row in selected])
    bks_rate = bks / shots
    return {
        "method": method,
        "replicates": len(selected),
        "shots": shots,
        "bks_hits": bks,
        "bks_rate": bks_rate,
        "bks_wilson_low": wilson(bks, shots)[0],
        "bks_wilson_high": wilson(bks, shots)[1],
        "near_bks_rate": near / shots,
        "feasible_rate": feasible / shots,
        "quality_mass": float(quality),
        "shots_to_95pct_bks": None
        if bks_rate == 0
        else math.ceil(math.log(0.05) / math.log(1 - bks_rate)),
    }


def audit_row(path: Path, bond: int, threshold: float):
    payload = load(path)
    rows = []
    for method in ("published_lr", "matched_random_search"):
        row = next(item for item in payload["rows"] if item["method"] == method)
        rows.append(
            {
                "bond": bond,
                "threshold": threshold,
                "method": method,
                "shots": row["metrics"]["total_shots"],
                "bks_hits": row["metrics"]["bks_hits"],
                "near_bks_hits": row["metrics"]["near_bks_hits"],
                "feasible_hits": row["metrics"]["feasible_shots"],
                "bks_rate": row["metrics"]["bks_rate"],
                "near_bks_rate": row["metrics"]["near_bks_rate"],
                "feasible_rate": row["metrics"]["feasible_rate"],
                "quality_mass": row["metrics"]["quality_mass"],
                "runtime_seconds": row["aer_metadata"].get("time_taken"),
            }
        )
    return rows


def main():
    results = rc.RESULTS
    figures = results / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    blind = load(results / "blind_test.json")
    methods = ["published_lr", "evolutionary_search", "matched_random_search"]
    summary = [aggregate(blind["rows"], method) for method in methods]

    comparison_csv = results / "blind_method_summary.csv"
    with comparison_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)

    metrics = ["bks_rate", "near_bks_rate", "feasible_rate", "quality_mass"]
    fig, axes = plt.subplots(1, 4, figsize=(13.5, 3.7))
    for ax, metric in zip(axes, metrics):
        values = [row[metric] for row in summary]
        ax.bar(range(3), values, color=[COLORS[m] for m in methods])
        ax.set_xticks(range(3), ["LR", "ES", "RS"])
        ax.set_title(metric.replace("_", " "))
        ax.grid(axis="y", alpha=0.25)
        ax.set_ylim(0, max(values) * 1.2 + 0.001)
    fig.suptitle("Blind es60fst02 benchmark: 15,000 shots per method")
    fig.tight_layout()
    fig.savefig(figures / "blind_method_comparison.png", dpi=220)
    plt.close(fig)

    # Published threshold=1e-3 point uses the higher-power 15-replicate run.
    sensitivity = []
    for method in ("published_lr", "matched_random_search"):
        row = next(item for item in summary if item["method"] == method)
        sensitivity.append(
            {
                "bond": 64,
                "threshold": 1e-3,
                "method": method,
                "shots": row["shots"],
                "bks_hits": row["bks_hits"],
                "near_bks_hits": round(row["near_bks_rate"] * row["shots"]),
                "feasible_hits": round(row["feasible_rate"] * row["shots"]),
                "bks_rate": row["bks_rate"],
                "near_bks_rate": row["near_bks_rate"],
                "feasible_rate": row["feasible_rate"],
                "quality_mass": row["quality_mass"],
                "runtime_seconds": None,
            }
        )
    sensitivity += audit_row(results / "fidelity_bond64_thr3em04.json", 64, 3e-4)
    sensitivity += audit_row(results / "fidelity_bond64_thr1em04.json", 64, 1e-4)
    sensitivity += audit_row(results / "fidelity_bond96_thr1em03.json", 96, 1e-3)
    sensitivity += audit_row(
        results / "fidelity_bond96_thr1e-4_10000shots.json", 96, 1e-4
    )
    for row in sensitivity:
        for metric, hits_key in (
            ("bks_rate", "bks_hits"),
            ("near_bks_rate", "near_bks_hits"),
            ("feasible_rate", "feasible_hits"),
        ):
            low, high = wilson(int(row[hits_key]), int(row["shots"]))
            row[f"{metric}_wilson_low"] = low
            row[f"{metric}_wilson_high"] = high

    sensitivity_csv = results / "mps_sensitivity.csv"
    with sensitivity_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(sensitivity[0]))
        writer.writeheader()
        writer.writerows(sensitivity)

    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.8))
    for ax, metric in zip(axes, ("bks_rate", "near_bks_rate", "feasible_rate")):
        for method in ("published_lr", "matched_random_search"):
            rows = sorted(
                [r for r in sensitivity if r["bond"] == 64 and r["method"] == method],
                key=lambda r: r["threshold"],
            )
            x = [r["threshold"] for r in rows]
            y = [r[metric] for r in rows]
            low = [r[f"{metric}_wilson_low"] for r in rows]
            high = [r[f"{metric}_wilson_high"] for r in rows]
            ax.errorbar(
                x,
                y,
                yerr=[np.asarray(y) - np.asarray(low), np.asarray(high) - np.asarray(y)],
                marker="o",
                linewidth=2,
                capsize=3,
                label=METHOD_LABELS[method],
                color=COLORS[method],
            )
        ax.set_xscale("log")
        ax.invert_xaxis()
        ax.set_xlabel("MPS truncation threshold (tighter →)")
        ax.set_title(metric.replace("_", " "))
        ax.grid(alpha=0.25)
    axes[0].legend(frameon=False)
    fig.suptitle("Schedule ranking is observable-dependent and truncation-sensitive (bond 64)")
    fig.tight_layout()
    fig.savefig(figures / "mps_threshold_sensitivity.png", dpi=220)
    plt.close(fig)

    calibration = load(results / "exact_mps_calibration.json")
    calibration_rows = []
    for row in calibration["rows"]:
        if row["bond"] != 128:
            continue
        calibration_rows.append(
            {
                "case": row["case"],
                "method": row["method"],
                "bond": row["bond"],
                "threshold": row["threshold"],
                "state_fidelity": row["distribution_errors"]["state_fidelity"],
                "total_variation": row["distribution_errors"]["total_variation"],
                "jensen_shannon": row["distribution_errors"]["jensen_shannon"],
                "exact_bks_rate": row["exact_metrics"]["bks_rate"],
                "mps_bks_rate": row["mps_metrics"]["bks_rate"],
                "bks_error": row["metric_errors"]["bks_rate"],
                "feasible_error": row["metric_errors"]["feasible_rate"],
            }
        )
    calibration_csv = results / "exact_mps_calibration.csv"
    with calibration_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(calibration_rows[0]))
        writer.writeheader()
        writer.writerows(calibration_rows)

    fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.7))
    for case, linestyle in (("es60fst01", "-"), ("es60fst03", "--")):
        for method in ("published_lr", "matched_random_search"):
            rows = sorted(
                [
                    r for r in calibration_rows
                    if r["case"] == case and r["method"] == method
                ],
                key=lambda r: r["threshold"],
            )
            label = f"{METHOD_LABELS[method]}, {case}"
            axes[0].plot(
                [r["threshold"] for r in rows],
                [r["total_variation"] for r in rows],
                marker="o", linewidth=2, linestyle=linestyle,
                color=COLORS[method], label=label,
            )
            axes[1].plot(
                [r["threshold"] for r in rows],
                [r["bks_error"] for r in rows],
                marker="o", linewidth=2, linestyle=linestyle,
                color=COLORS[method], label=label,
            )
    axes[0].set_ylabel("total variation")
    axes[1].set_ylabel("MPS - exact BKS probability")
    axes[1].axhline(0, color="black", linewidth=0.8, alpha=0.6)
    for ax in axes:
        ax.set_xscale("log")
        ax.invert_xaxis()
        ax.grid(alpha=0.25)
        ax.set_xlabel("MPS truncation threshold (tighter →)")
    axes[0].legend(frameon=False, fontsize=8)
    fig.suptitle("Exact-state calibration on real QOBLIB kernels (bond 128)")
    fig.tight_layout()
    fig.savefig(figures / "exact_mps_calibration.png", dpi=220)
    plt.close(fig)

    random_summary = next(row for row in summary if row["method"] == "matched_random_search")
    baseline_summary = next(row for row in summary if row["method"] == "published_lr")
    es_summary = next(row for row in summary if row["method"] == "evolutionary_search")
    paired = {
        (row["method"], row["metric"]): row for row in blind["comparisons"]
    }
    bks_cmp = paired[("matched_random_search", "bks_rate")]
    feasible_cmp = paired[("matched_random_search", "feasible_rate")]

    final = {
        "blind_summary": summary,
        "paired_comparisons": blind["comparisons"],
        "sensitivity": sensitivity,
        "exact_mps_calibration": calibration_rows,
        "promotion_gate": {
            "published_setting_bks_gate": (
                bks_cmp["bootstrap_95_ci"][0] > 0
                and feasible_cmp["bootstrap_95_ci"][0] >= 0
            ),
            "simulator_robust_bks_gate": False,
            "reason": "BKS ranking reverses when the MPS truncation threshold is tightened from 1e-3 to 1e-4.",
        },
    }
    rc.write_json(results / "analysis_summary.json", final)

    report = f"""# Full QOBLIB research-cycle report

## Outcome

The cycle produced a paper-grade result on real QOBLIB instances, but the most
defensible novelty is **benchmark sensitivity**, not a universal superiority
claim for evolutionary search.

At the published Aer/MPS setting (bond 64, truncation threshold 1e-3), the
matched-budget random-search nonlinear ramp achieved {random_summary['bks_hits']}
BKS hits in {random_summary['shots']:,} blind shots ({random_summary['bks_rate']:.4%})
versus {baseline_summary['bks_hits']} ({baseline_summary['bks_rate']:.4%}) for the
published linear ramp. The paired difference was {bks_cmp['mean_difference']:.4%}
with bootstrap 95% CI [{bks_cmp['bootstrap_95_ci'][0]:.4%},
{bks_cmp['bootstrap_95_ci'][1]:.4%}] and exact paired sign-flip
p={bks_cmp['two_sided_paired_sign_flip_p']:.6f}. Estimated shots for 95% chance
of at least one BKS sample fell from {baseline_summary['shots_to_95pct_bks']} to
{random_summary['shots_to_95pct_bks']}.

The nonlinear ramp also increased feasible rate from
{baseline_summary['feasible_rate']:.2%} to {random_summary['feasible_rate']:.2%}
and near-BKS rate from {baseline_summary['near_bks_rate']:.2%} to
{random_summary['near_bks_rate']:.2%}. The evolutionary champion reached
{es_summary['feasible_rate']:.2%} feasibility but did not improve BKS hit rate,
so matched random search beat the evolutionary operator under the same 120
candidate evaluations per replicate.

## Stronger novelty: an MPS-induced rank reversal

Tightening only the MPS truncation threshold changed the BKS conclusion. At
bond 64 / threshold 1e-4 with 10,000 shots per method, published LR reached
1.53% BKS hits while the nonlinear ramp reached 1.09%. At the intermediate
threshold 3e-4, the nonlinear ramp still led 1.61% to 1.16%. Increasing bond
64→96 while keeping threshold 1e-3 preserved the nonlinear advantage (0.70%
versus 0.19%), identifying the truncation threshold—not the bond cap—as the
dominant factor in this experiment.

Crucially, the nonlinear ramp retained higher near-BKS and feasible mass at
every tested setting. Thus optimum-hit ranking is fragile while distributional
quality ranking is robust. Approximate tensor-network benchmark papers should
therefore publish convergence sweeps and avoid selecting algorithms from a
single truncation setting.

## Exact-state calibration

The same protocol was calibrated on the real 12- and 15-qubit ES60FST kernels,
where complete statevectors are available. At threshold 1e-3, total-variation
distance from exact is 0.0518/0.0509 for the published ramp and 0.0742/0.0702
for the nonlinear ramp on es60fst01/03. The MPS BKS bias is positive and larger
for the nonlinear ramp: +0.0342 and +0.0185, versus +0.0158 and +0.0074. At
threshold 1e-6, all four state fidelities exceed 0.99983, total variation falls
below 0.00266, and absolute BKS error falls below 0.00023. At shared thresholds,
bonds 32--128 are numerically identical. Bond 16 differs only for the nonlinear
es60fst01 circuit at threshold 1e-4, where total variation changes by less than
0.0005. Thus the discarded-weight threshold, rather than the bond cap once it
reaches 32, controls these small-kernel errors.

## Benchmark protocol

- Real full instances: QOBLIB `es60fst01`/`03` for training, `es60fst04` for
  validation, and blind `es60fst02` (186 vertices, BKS 88) for testing.
- Published graph preprocessing: exact degree-0/1 rules, degree-2 folding,
  recorded high-degree pruning; the test kernel has 55 qubits and 91 edges.
- QAOA depth 15; 1365 RZZ, 825 RZ, and 825 RX gates before measurement.
- Raw samples only: unfold plus feasibility filter; no constraint repair,
  greedy fill, or archived solution.
- Search: three seeds, 120 candidates per method, 256 shots on each of two
  training instances. Deployment: 15 paired jobs × 1000 shots per method.
- QOBLIB and external baseline code are commit-pinned in result provenance.

## Interpretation and promotion gate

The preregistered primary claim that evolutionary search improves BKS transfer
failed. The broader nonlinear-ramp claim passes at the exact published
benchmark setting but fails the simulator-robust BKS promotion gate because of
the threshold-dependent rank reversal. The main-paper-worthy claim is instead:

> On a 55-qubit, depth-15 QOBLIB MIS benchmark, MPS truncation can reverse the
> ranking of transferred QAOA schedules for optimum-hit probability even when
> near-optimal and feasible-mass rankings remain stable.

This aligns with the purpose of QOBLIB as a reproducible comparison framework
([Koch et al., 2026](https://doi.org/10.1038/s43588-026-00991-1)) and addresses
a gap in recent simulator benchmarking, which emphasizes runtime/accuracy
tradeoffs but does not establish schedule-ranking stability for optimization
observables ([Mazumder et al., 2026](https://arxiv.org/abs/2607.09882)). Recent
QAOA transfer work already covers parameter rescaling
([Sureshbabu et al., 2024](https://doi.org/10.22331/q-2024-01-18-1231)) and
penalty-scale resonance ([Grover, 2026](https://arxiv.org/abs/2607.09927)), so
the simulator-stability angle is better differentiated than another penalty or
normalization rule.

## Artifacts

- `results/blind_test.json`: 45 full test rows and paired inference.
- `results/mps_sensitivity.csv`: bond/threshold factorial audit.
- `results/figures/blind_method_comparison.png`: blind method metrics.
- `results/figures/mps_threshold_sensitivity.png`: rank-reversal figure.
- `results/figures/exact_mps_calibration.png`: exact-state convergence figure.
- `PROTOCOL_DEVIATIONS.md`: preserved transpilation audit and correction.
"""
    (rc.HERE / "RESEARCH_CYCLE_REPORT.md").write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
