from __future__ import annotations

import gc
import json
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from qaoa_mis import distribution_metrics, enumerate_exact_space, induced_subgraph, load_dimacs_graph, statevector_probabilities
from run_multitask_normalized import paired_audit


ROOT = Path(__file__).resolve().parents[2]
INSTANCE_DIR = ROOT / "QOBLIB" / "07-independentset" / "instances"
SOURCE_PATH = Path(__file__).resolve().parent / "results_multitask_normalized" / "results.json"
OUTPUT_DIR = Path(__file__).resolve().parent / "results_confirmatory"
METHOD_SCALE = {
    "normalized_de": "max_coefficient",
    "unnormalized_de": "none",
    "normalized_random": "max_coefficient",
}


def frozen_graphs():
    specs = (
        ("insecta-ant-colony1-day38", 20),
        ("sloane_1dc_64", 22),
        ("hamming6-4", 24),
    )
    return [
        induced_subgraph(
            load_dimacs_graph(INSTANCE_DIR / f"{name}.gph"),
            range(size),
            f"{name}_first{size}",
        )
        for name, size in specs
    ]


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    source = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    graphs_output = []
    started = time.perf_counter()
    for graph in frozen_graphs():
        exact = enumerate_exact_space(graph)
        row = {
            "graph": {
                "name": graph.name,
                "vertices": graph.n,
                "edges": len(graph.edges),
                "exact_optimum": exact.optimum,
                "source": graph.source,
            },
            "methods": {},
        }
        for method, scale in METHOD_SCALE.items():
            values = []
            for replicate in source["replicates"]:
                params = np.asarray(replicate[method]["params"], dtype=float)
                probs = statevector_probabilities(graph, params, p=2, cost_scale=scale)
                values.append({"replicate": replicate["replicate"], **distribution_metrics(probs, exact)})
                del probs
                gc.collect()
            row["methods"][method] = values
        graphs_output.append(row)
        (OUTPUT_DIR / "checkpoint.json").write_text(json.dumps(graphs_output, indent=2), encoding="utf-8")
        del exact
        gc.collect()

    audits = {}
    for first, second, label in (
        ("normalized_de", "unnormalized_de", "primary_normalization"),
        ("normalized_de", "normalized_random", "secondary_evolution"),
    ):
        audits[label] = {}
        for offset, metric in enumerate(("score", "approximation_ratio_unconditional", "optimal_probability", "feasible_probability")):
            first_values = [
                np.mean([graph["methods"][first][replicate][metric] for graph in graphs_output])
                for replicate in range(len(source["replicates"]))
            ]
            second_values = [
                np.mean([graph["methods"][second][replicate][metric] for graph in graphs_output])
                for replicate in range(len(source["replicates"]))
            ]
            audits[label][metric] = paired_audit(first_values, second_values, 20261003 + offset)

    primary = audits["primary_normalization"]["score"]
    checks = {
        "primary_mean_positive": primary["difference"]["mean"] > 0,
        "primary_bootstrap_ci_positive": primary["difference"]["bootstrap_95_percent_ci"][0] > 0,
        "primary_paired_t_p_below_0_05": primary["paired_t_test_two_sided"]["p_value"] < 0.05,
        "primary_majority_wins": primary["first_wins"] > len(source["replicates"]) / 2,
    }
    report = {
        "experiment": "Pre-registered confirmatory zero-shot transfer audit",
        "declaration": "Graph suite and all schedules/methods were frozen in NOVELTY_AUDIT.md before evaluation.",
        "primary_endpoint": "Aggregate raw composite score: normalized DE minus identical unnormalized DE.",
        "secondary_endpoint": "Normalized DE minus equal-budget normalized random search.",
        "seconds": time.perf_counter() - started,
        "graphs": graphs_output,
        "audits": audits,
        "confirmatory_gate": {"checks": checks, "passed": all(checks.values())},
    }
    (OUTPUT_DIR / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    labels = [row["graph"]["name"] for row in graphs_output]
    x = np.arange(len(labels))
    width = 0.25
    plt.figure(figsize=(9.2, 5.0))
    for index, method in enumerate(METHOD_SCALE):
        samples = [[item["score"] for item in row["methods"][method]] for row in graphs_output]
        plt.bar(
            x + (index - 1) * width,
            [np.mean(sample) for sample in samples],
            width,
            yerr=[np.std(sample, ddof=1) for sample in samples],
            capsize=4,
            label=method.replace("_", " "),
        )
    plt.xticks(x, labels)
    plt.ylabel("Exact raw composite score")
    plt.title("Pre-registered confirmatory QOBLIB transfer")
    plt.grid(axis="y", alpha=0.2)
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "confirmatory_scores.png", dpi=180)
    plt.close()

    print(json.dumps({
        "seconds": report["seconds"],
        "graphs": [row["graph"] for row in graphs_output],
        "primary": primary,
        "secondary": audits["secondary_evolution"]["score"],
        "gate": report["confirmatory_gate"],
        "results": str((OUTPUT_DIR / "results.json").resolve()),
    }, indent=2))


if __name__ == "__main__":
    main()
