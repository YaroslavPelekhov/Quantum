from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import ttest_rel, wilcoxon

from qaoa_mis import distribution_metrics, enumerate_exact_space, load_dimacs_graph, statevector_probabilities


ROOT = Path(__file__).resolve().parents[2]
RESULT_DIR = Path(__file__).resolve().parent / "results_p2_pareto"
RESULT_PATH = RESULT_DIR / "results.json"
INSTANCE_DIR = ROOT / "QOBLIB" / "07-independentset" / "instances"


def summary(values: np.ndarray) -> dict[str, float]:
    return {
        "mean": float(values.mean()),
        "std": float(values.std(ddof=1)),
        "median": float(np.median(values)),
        "min": float(values.min()),
        "max": float(values.max()),
    }


def paired_audit(de: np.ndarray, random: np.ndarray, seed: int) -> dict:
    difference = de - random
    rng = np.random.default_rng(seed)
    bootstrap = np.empty(20000, dtype=float)
    for i in range(len(bootstrap)):
        bootstrap[i] = rng.choice(difference, size=len(difference), replace=True).mean()
    ttest = ttest_rel(de, random)
    try:
        signed_rank = wilcoxon(de, random, alternative="greater")
        wilcoxon_statistic = float(signed_rank.statistic)
        wilcoxon_p = float(signed_rank.pvalue)
    except ValueError:
        wilcoxon_statistic = 0.0
        wilcoxon_p = 1.0
    return {
        "differential_evolution": summary(de),
        "random_search": summary(random),
        "difference_de_minus_random": {
            **summary(difference),
            "bootstrap_95_percent_ci": [float(np.quantile(bootstrap, 0.025)), float(np.quantile(bootstrap, 0.975))],
        },
        "paired_de_wins": int(np.sum(de > random)),
        "paired_random_wins": int(np.sum(random > de)),
        "paired_t_test_two_sided": {"statistic": float(ttest.statistic), "p_value": float(ttest.pvalue)},
        "wilcoxon_one_sided_de_greater": {"statistic": wilcoxon_statistic, "p_value": wilcoxon_p},
    }


def main() -> None:
    report = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    seed = int(report["configuration"]["seed"])
    p = int(report["configuration"]["p"])
    held_out = load_dimacs_graph(INSTANCE_DIR / "farm.gph")
    exact = enumerate_exact_space(held_out)

    rows = []
    for replicate in report["replicates"]:
        row = {"replicate": int(replicate["replicate"])}
        for method in ("differential_evolution", "random_search"):
            params = np.asarray(replicate[method]["params"], dtype=float)
            probs = statevector_probabilities(held_out, params, p)
            row[method] = distribution_metrics(probs, exact)
        rows.append(row)

    metrics = ("score", "approximation_ratio_unconditional", "optimal_probability", "feasible_probability")
    audits = {}
    for offset, metric in enumerate(metrics):
        de = np.asarray([row["differential_evolution"][metric] for row in rows], dtype=float)
        random = np.asarray([row["random_search"][metric] for row in rows], dtype=float)
        audits[metric] = paired_audit(de, random, seed + offset)

    train_score = np.asarray([row["differential_evolution"]["score"] for row in report["replicates"]], dtype=float)
    train_random_score = np.asarray([row["random_search"]["score"] for row in report["replicates"]], dtype=float)
    train_audit = paired_audit(train_score, train_random_score, seed + 100)
    held_audit = audits["score"]
    promotion_checks = {
        "train_mean_difference_positive": train_audit["difference_de_minus_random"]["mean"] > 0,
        "train_bootstrap_ci_excludes_zero": train_audit["difference_de_minus_random"]["bootstrap_95_percent_ci"][0] > 0,
        "train_wilcoxon_one_sided_p_below_0_05": train_audit["wilcoxon_one_sided_de_greater"]["p_value"] < 0.05,
        "held_out_mean_difference_positive": held_audit["difference_de_minus_random"]["mean"] > 0,
        "held_out_strict_majority_wins": held_audit["paired_de_wins"] > len(rows) / 2,
    }
    audit = {
        "protocol": "Each schedule is selected on the train graph only, then frozen and evaluated exactly on QOBLIB farm.",
        "replicates": rows,
        "train_score_audit": train_audit,
        "held_out_metric_audits": audits,
        "promotion_gate": {
            "checks": promotion_checks,
            "promote": all(promotion_checks.values()),
            "reason": "Exploratory n=12 statistics; promotion still means next simulator stage, not a claim of quantum advantage.",
        },
    }
    (RESULT_DIR / "transfer_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")

    de = np.asarray([row["differential_evolution"]["score"] for row in rows], dtype=float)
    random = np.asarray([row["random_search"]["score"] for row in rows], dtype=float)
    x = np.arange(1, len(rows) + 1)
    plt.figure(figsize=(8.5, 4.8))
    for i in range(len(rows)):
        plt.plot([x[i] - 0.08, x[i] + 0.08], [de[i], random[i]], color="0.75", linewidth=1)
    plt.scatter(x - 0.08, de, label="Differential evolution", s=45)
    plt.scatter(x + 0.08, random, label="Equal-budget random", s=45)
    plt.xlabel("Frozen train-selected replicate")
    plt.ylabel("Exact held-out composite score")
    plt.title("Depth-2 QAOA transfer to QOBLIB farm")
    plt.xticks(x)
    plt.grid(alpha=0.22)
    plt.legend()
    plt.tight_layout()
    plt.savefig(RESULT_DIR / "held_out_paired_scores.png", dpi=180)
    plt.close()

    print(json.dumps({"train_score_audit": train_audit, "held_out_score_audit": held_audit, "promotion_gate": audit["promotion_gate"]}, indent=2))


if __name__ == "__main__":
    main()
