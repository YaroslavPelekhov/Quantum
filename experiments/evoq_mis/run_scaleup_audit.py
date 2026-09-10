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
INPUT_PATH = Path(__file__).resolve().parent / "results_multitask_normalized" / "results.json"
OUTPUT_DIR = Path(__file__).resolve().parent / "results_scaleup_20_24"
METHOD_SCALE = {
    "normalized_de": "max_coefficient",
    "unnormalized_de": "none",
    "normalized_random": "max_coefficient",
}


def build_scale_graphs():
    specs = (("ibm32", 20), ("football", 22), ("johnson8-2-4", 24))
    result = []
    for source_name, size in specs:
        source = load_dimacs_graph(INSTANCE_DIR / f"{source_name}.gph")
        result.append(induced_subgraph(source, range(size), f"{source_name}_first{size}"))
    return result


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    source_report = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    graphs = build_scale_graphs()
    results = []
    started = time.perf_counter()
    for graph in graphs:
        graph_started = time.perf_counter()
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
            method_results = []
            method_started = time.perf_counter()
            for replicate in source_report["replicates"]:
                params = np.asarray(replicate[method]["params"], dtype=float)
                probs = statevector_probabilities(graph, params, p=2, cost_scale=scale)
                method_results.append({
                    "replicate": int(replicate["replicate"]),
                    "params": params.tolist(),
                    **distribution_metrics(probs, exact),
                })
                del probs
                gc.collect()
            row["methods"][method] = method_results
            print(json.dumps({
                "graph": graph.name,
                "method": method,
                "completed": len(method_results),
                "seconds": time.perf_counter() - method_started,
            }), flush=True)
        row["seconds"] = time.perf_counter() - graph_started
        results.append(row)
        (OUTPUT_DIR / "checkpoint.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
        del exact
        gc.collect()

    audits = {"by_graph": {}, "aggregate": {}}
    for graph_row in results:
        name = graph_row["graph"]["name"]
        audits["by_graph"][name] = {}
        for first, second, label in (
            ("normalized_de", "normalized_random", "evolution_effect"),
            ("normalized_de", "unnormalized_de", "normalization_effect"),
        ):
            audits["by_graph"][name][label] = {}
            for offset, metric in enumerate(("score", "approximation_ratio_unconditional", "optimal_probability", "feasible_probability")):
                audits["by_graph"][name][label][metric] = paired_audit(
                    [row[metric] for row in graph_row["methods"][first]],
                    [row[metric] for row in graph_row["methods"][second]],
                    20260803 + offset,
                )

    for first, second, label in (
        ("normalized_de", "normalized_random", "evolution_effect"),
        ("normalized_de", "unnormalized_de", "normalization_effect"),
    ):
        audits["aggregate"][label] = {}
        for offset, metric in enumerate(("score", "approximation_ratio_unconditional", "optimal_probability", "feasible_probability")):
            first_values = []
            second_values = []
            for replicate in range(len(source_report["replicates"])):
                first_values.append(np.mean([graph["methods"][first][replicate][metric] for graph in results]))
                second_values.append(np.mean([graph["methods"][second][replicate][metric] for graph in results]))
            audits["aggregate"][label][metric] = paired_audit(first_values, second_values, 20260903 + offset)

    normalization = audits["aggregate"]["normalization_effect"]["score"]
    evolution = audits["aggregate"]["evolution_effect"]["score"]
    gate_checks = {
        "normalization_mean_positive": normalization["difference"]["mean"] > 0,
        "normalization_bootstrap_ci_positive": normalization["difference"]["bootstrap_95_percent_ci"][0] > 0,
        "normalization_majority_wins": normalization["first_wins"] > len(source_report["replicates"]) / 2,
        "evolution_mean_positive": evolution["difference"]["mean"] > 0,
        "evolution_majority_wins": evolution["first_wins"] > len(source_report["replicates"]) / 2,
    }
    report = {
        "experiment": "Frozen scale-up audit from 11-17-qubit training to 20/22/24-qubit QOBLIB-derived graphs",
        "protocol": "All schedules are copied from the completed 17-qubit experiment; no scale-up graph is used for optimization.",
        "source_results": str(INPUT_PATH.resolve()),
        "seconds": time.perf_counter() - started,
        "graphs": results,
        "audits": audits,
        "promotion_gate": {"checks": gate_checks, "promote_to_hardware_aware_audit": all(gate_checks.values())},
    }
    (OUTPUT_DIR / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    methods = list(METHOD_SCALE)
    labels = ["20", "22", "24"]
    x = np.arange(len(results))
    width = 0.25
    plt.figure(figsize=(8.8, 5.0))
    for index, method in enumerate(methods):
        means = [np.mean([row["score"] for row in graph["methods"][method]]) for graph in results]
        errors = [np.std([row["score"] for row in graph["methods"][method]], ddof=1) for graph in results]
        plt.bar(x + (index - 1) * width, means, width, yerr=errors, capsize=4, label=method.replace("_", " "))
    plt.xticks(x, [f"{graph['graph']['name']}\n({size} qubits)" for graph, size in zip(results, labels)])
    plt.ylabel("Exact raw composite score")
    plt.title("Frozen zero-shot scale transfer")
    plt.grid(axis="y", alpha=0.2)
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "scaleup_scores.png", dpi=180)
    plt.close()

    print(json.dumps({
        "seconds": report["seconds"],
        "graphs": [row["graph"] for row in results],
        "aggregate_normalization": normalization,
        "aggregate_evolution": evolution,
        "promotion_gate": report["promotion_gate"],
        "results": str((OUTPUT_DIR / "results.json").resolve()),
    }, indent=2))


if __name__ == "__main__":
    main()
