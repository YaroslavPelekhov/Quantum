from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


PAPER_DIR = Path(__file__).resolve().parent
EXPERIMENT_DIR = PAPER_DIR.parent
FIGURE_DIR = PAPER_DIR / "figures"
TABLE_DIR = PAPER_DIR / "generated"


def load(relative: str):
    return json.loads((EXPERIMENT_DIR / relative).read_text(encoding="utf-8"))


def audit_row(label: str, audit: dict) -> dict:
    return {
        "suite": label,
        "normalized_mean": audit["first"]["mean"],
        "unnormalized_mean": audit["second"]["mean"],
        "difference": audit["difference"]["mean"],
        "ci_low": audit["difference"]["bootstrap_95_percent_ci"][0],
        "ci_high": audit["difference"]["bootstrap_95_percent_ci"][1],
        "paired_t_p": audit["paired_t_test_two_sided"]["p_value"],
        "wins": audit["first_wins"],
        "losses": audit["second_wins"],
    }


def save_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)

    multi = load("results_multitask_normalized/results.json")
    scale = load("results_scaleup_20_24/results.json")
    confirm = load("results_confirmatory/results.json")
    random_subset = load("results_random_subsets/results.json")
    hardware = load("results_hardware_audit/results.json")
    classical = load("results_classical_sanity/results.json")
    metriq = load("results_metriq_lrqaoa/result.json")

    effects = [
        audit_row("Frozen 17-qubit", multi["comparisons"]["normalization_effect"]["frozen_test_aggregate_score"]),
        audit_row("Scale-up 20--24", scale["audits"]["aggregate"]["normalization_effect"]["score"]),
        audit_row("Confirmatory 20--24", confirm["audits"]["primary_normalization"]["score"]),
        audit_row("Random subsets 20--24", random_subset["audits"]["primary_normalization"]["score"]),
    ]
    save_csv(TABLE_DIR / "normalization_effects.csv", effects)

    y = np.arange(len(effects))
    means = np.array([row["difference"] for row in effects])
    lower = means - np.array([row["ci_low"] for row in effects])
    upper = np.array([row["ci_high"] for row in effects]) - means
    fig, ax = plt.subplots(figsize=(7.4, 3.6))
    ax.errorbar(means, y, xerr=np.vstack([lower, upper]), fmt="o", color="#2459A6", ecolor="#2459A6", capsize=4, lw=1.8)
    ax.axvline(0, color="#333333", lw=1, ls="--")
    ax.set_yticks(y, [row["suite"] for row in effects])
    ax.invert_yaxis()
    ax.set_xlabel("Paired score difference (normalized $-$ unnormalized)")
    ax.set_title("Normalization effect across frozen test suites")
    ax.grid(axis="x", alpha=0.2)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "normalization_forest.png", dpi=240)
    plt.close(fig)

    suite_sources = [
        ("Frozen 17", multi["comparisons"], "frozen_test_aggregate_score"),
        ("Scale 20--24", scale["audits"]["aggregate"], "score"),
        ("Confirmatory", confirm["audits"], "score"),
        ("Random subsets", random_subset["audits"], "score"),
    ]
    suite_rows = []
    for label, root, key in suite_sources:
        if label == "Frozen 17":
            norm = root["normalization_effect"][key]["first"]["mean"]
            unnorm = root["normalization_effect"][key]["second"]["mean"]
            random = root["evolution_effect"][key]["second"]["mean"]
        elif label == "Scale 20--24":
            norm = root["normalization_effect"][key]["first"]["mean"]
            unnorm = root["normalization_effect"][key]["second"]["mean"]
            random = root["evolution_effect"][key]["second"]["mean"]
        else:
            norm = root["primary_normalization"][key]["first"]["mean"]
            unnorm = root["primary_normalization"][key]["second"]["mean"]
            random = root["secondary_evolution"][key]["second"]["mean"]
        suite_rows.append({"suite": label, "normalized_de": norm, "unnormalized_de": unnorm, "normalized_random": random})
    save_csv(TABLE_DIR / "suite_method_means.csv", suite_rows)

    labels = [row["suite"] for row in suite_rows]
    x = np.arange(len(labels))
    width = 0.24
    fig, ax = plt.subplots(figsize=(8.0, 4.2))
    for index, (key, pretty, color) in enumerate((
        ("normalized_de", "Normalized DE", "#2459A6"),
        ("unnormalized_de", "Unnormalized DE", "#D05A45"),
        ("normalized_random", "Normalized random", "#6B8E23"),
    )):
        ax.bar(x + (index - 1) * width, [row[key] for row in suite_rows], width, label=pretty, color=color)
    ax.set_xticks(x, labels)
    ax.set_ylabel("Mean exact raw composite score")
    ax.set_title("Zero-shot transfer across evaluation suites")
    ax.grid(axis="y", alpha=0.2)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "suite_method_means.png", dpi=240)
    plt.close(fig)

    hardware_rows = []
    topologies = ["unconstrained_basis", "line", "grid_5x5", "hexagonal_lattice_30"]
    for graph, topology_values in hardware["analytical_error_proxy"].items():
        for topology in topologies:
            item = topology_values[topology]
            hardware_rows.append({
                "graph": graph,
                "topology": topology,
                "one_qubit_operations": item["one_qubit_operations"],
                "two_qubit_operations": item["two_qubit_operations"],
                "no_error_survival_proxy": item["independent_no_error_survival_proxy"],
            })
    save_csv(TABLE_DIR / "hardware_resources.csv", hardware_rows)

    graph_names = list(hardware["analytical_error_proxy"])
    x = np.arange(len(graph_names))
    width = 0.2
    fig, ax = plt.subplots(figsize=(8.0, 4.2))
    for index, topology in enumerate(topologies):
        values = [hardware["analytical_error_proxy"][graph][topology]["two_qubit_operations"] for graph in graph_names]
        ax.bar(x + (index - 1.5) * width, values, width, label=topology.replace("_", " "))
    ax.set_xticks(x, [name.replace("_first", "\n") for name in graph_names])
    ax.set_yscale("log")
    ax.set_ylabel("Two-qubit operations (log scale)")
    ax.set_title("Routing overhead for depth-two MIS QAOA")
    ax.grid(axis="y", alpha=0.2, which="both")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "routing_overhead.png", dpi=240)
    plt.close(fig)

    fig, ax1 = plt.subplots(figsize=(6.8, 4.0))
    layers = [row["layers"] for row in metriq["results"]]
    ratios = [row["approx_ratio"] for row in metriq["results"]]
    opt = [row["optimal_probability"] for row in metriq["results"]]
    ax1.plot(layers, ratios, "o-", color="#2459A6", label="Approximation ratio")
    ax1.axhline(0.5, color="#777777", ls="--", label="Uniform baseline")
    ax1.set_xlabel("QAOA depth")
    ax1.set_ylabel("Approximation ratio")
    ax2 = ax1.twinx()
    ax2.plot(layers, opt, "s-", color="#D05A45", label="Optimum probability")
    ax2.set_ylabel("Optimum probability")
    lines = ax1.get_lines() + ax2.get_lines()
    ax1.legend(lines, [line.get_label() for line in lines], frameon=False, loc="center right")
    ax1.set_title("Metriq-Gym LR-QAOA local cross-check")
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "metriq_crosscheck.png", dpi=240)
    plt.close(fig)

    graph_rows = []
    for suite, report in (
        ("scaleup", scale),
        ("confirmatory", confirm),
        ("random_subsets", random_subset),
    ):
        for row in report["graphs"]:
            graph_rows.append({"suite": suite, **row["graph"]})
    save_csv(TABLE_DIR / "graph_inventory.csv", graph_rows)

    summary = {
        "normalization_effects": effects,
        "suite_method_means": suite_rows,
        "classical_summary": classical["summary"],
        "confirmatory_metric_sensitivity": confirm["audits"]["primary_normalization"],
        "random_subset_metric_sensitivity": random_subset["audits"]["primary_normalization"],
        "hardware_limits": hardware["limitations"],
    }
    (TABLE_DIR / "paper_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({"figures": 4, "tables": 4, "output": str(PAPER_DIR)}, indent=2))


if __name__ == "__main__":
    main()
