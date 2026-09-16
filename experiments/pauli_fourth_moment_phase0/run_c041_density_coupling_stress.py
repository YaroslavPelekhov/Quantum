"""C041: density and weak-coupling stress tests for local matching relaxations."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import time
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

from run_c040_scaled_ablations import (
    ROOT,
    RESULTS,
    FIGURES,
    constraint_hierarchy,
    edges_of,
    exact_matching,
    lp_value,
)


SEED = 20260918
ORDERS = (20, 30, 40)
EXPECTED_DEGREES = (2, 3, 4, 5, 6)
REPLICATES = 3


def write_csv(path: Path, rows: list[dict]):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def density_campaign(rng: np.random.Generator):
    rows, graphs = [], []
    graph_index = 0
    for order in ORDERS:
        for expected_degree in EXPECTED_DEGREES:
            for replicate in range(REPLICATES):
                seed = int(rng.integers(1, 2**31 - 1))
                graph = nx.gnp_random_graph(order, expected_degree / (order - 1), seed=seed)
                if not graph.number_of_edges():
                    raise AssertionError("empty density graph")
                graph = nx.convert_node_labels_to_integers(graph, ordering="sorted")
                edges = edges_of(graph)
                systems, counts = constraint_hierarchy(graph, edges)
                graph6 = nx.to_graph6_bytes(graph, header=False).decode().strip()
                graphs.append({"graph_index": graph_index, "graph6": graph6, "seed": seed,
                               "root_order": order, "root_edges": len(edges),
                               "expected_degree": expected_degree, "replicate": replicate, **counts})
                weights_by_model = {
                    "uniform": np.ones(len(edges)),
                    "integer": rng.integers(1, 10, size=len(edges)).astype(float),
                }
                for model, weights in weights_by_model.items():
                    exact, _ = exact_matching(graph, edges, weights)
                    degree = lp_value(weights, systems["degree"])
                    clique = lp_value(weights, systems["clique"])
                    odd9 = lp_value(weights, systems["odd9"])
                    rows.append({
                        "graph_index": graph_index, "graph6": graph6,
                        "root_order": order, "root_edges": len(edges),
                        "expected_degree": expected_degree, "replicate": replicate,
                        "weight_model": model, "matching": exact,
                        "degree_ratio": degree / exact, "clique_ratio": clique / exact,
                        "odd9_ratio": odd9 / exact, **counts,
                    })
                graph_index += 1
    return rows, graphs


def coupled_k5_ring(blocks: int):
    graph = nx.disjoint_union_all([nx.complete_graph(5) for _ in range(blocks)])
    bridges = []
    for block in range(blocks):
        edge = (5 * block, 5 * ((block + 1) % blocks))
        graph.add_edge(*edge)
        bridges.append(tuple(sorted(edge)))
    return graph, set(bridges)


def coupling_campaign():
    rows = []
    for blocks in (2, 4, 8, 16):
        graph, bridges = coupled_k5_ring(blocks)
        edges = edges_of(graph)
        systems, counts = constraint_hierarchy(graph, edges)
        for epsilon in (0.0, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0):
            weights = np.asarray([epsilon if edge in bridges else 1.0 for edge in edges])
            exact, _ = exact_matching(graph, edges, weights)
            values = {name: lp_value(weights, systems[name])
                      for name in ("degree", "clique", "odd9")}
            rows.append({
                "blocks": blocks, "root_order": graph.number_of_nodes(),
                "root_edges": graph.number_of_edges(), "bridge_weight": epsilon,
                "matching": exact, **{f"{name}_ratio": value / exact for name, value in values.items()},
                **counts,
            })
    return rows


def aggregate_density(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[(row["root_order"], row["expected_degree"], row["weight_model"])].append(row)
    output = []
    for key, selected in sorted(groups.items()):
        record = dict(zip(("root_order", "expected_degree", "weight_model"), key))
        record["instances"] = len(selected)
        record["mean_realized_degree"] = float(np.mean([2 * r["root_edges"] / r["root_order"] for r in selected]))
        record["mean_cycles_through9"] = float(np.mean([
            r["cycles5"] + r["cycles7"] + r["cycles9"] for r in selected]))
        for baseline in ("degree", "clique", "odd9"):
            values = [r[f"{baseline}_ratio"] for r in selected]
            record[f"{baseline}_mean"] = float(np.mean(values))
            record[f"{baseline}_max"] = max(values)
            record[f"{baseline}_strict_fraction"] = float(np.mean(np.asarray(values) > 1 + 1e-8))
        output.append(record)
    return output


def make_figure(aggregate, coupling):
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), constrained_layout=True)
    colors = {20: "#1b9e77", 30: "#7570b3", 40: "#d95f02"}
    for order in ORDERS:
        selected = [row for row in aggregate if row["root_order"] == order
                    and row["weight_model"] == "uniform"]
        axes[0].plot([row["mean_realized_degree"] for row in selected],
                     [row["odd9_strict_fraction"] for row in selected], "o-",
                     color=colors[order], label=f"n={order}")
    axes[0].set(xlabel="mean realized degree", ylabel="odd<=9 strict-gap fraction",
                title="ER density stress", ylim=(-0.02, 1.02))
    axes[0].legend(frameon=False)

    for blocks, style in ((2, "o-"), (4, "s-"), (8, "^-"), (16, "D-")):
        selected = [row for row in coupling if row["blocks"] == blocks]
        axes[1].plot([row["bridge_weight"] for row in selected],
                     [row["odd9_ratio"] for row in selected], style, label=f"{blocks} K5 blocks")
    axes[1].axhline(1, color="black", linestyle="--", linewidth=1)
    axes[1].set(xlabel="inter-block bridge weight", ylabel="odd<=9 LP / matching",
                title="Robustness of planted blossoms")
    axes[1].legend(frameon=False, fontsize=8)
    fig.savefig(FIGURES / "c041_density_coupling_stress.png", dpi=220)
    plt.close(fig)


def main(overwrite=False):
    started = time.perf_counter()
    output = RESULTS / "c041_density_coupling_stress.json"
    if output.exists() and not overwrite:
        raise FileExistsError(f"Use --overwrite to replace {output}")
    rng = np.random.default_rng(SEED)
    density, graphs = density_campaign(rng)
    coupling = coupling_campaign()
    aggregate = aggregate_density(density)
    make_figure(aggregate, coupling)
    aggregate_csv = RESULTS / "c041_density_summary.csv"
    coupling_csv = RESULTS / "c041_coupling_ablations.csv"
    write_csv(aggregate_csv, aggregate)
    write_csv(coupling_csv, coupling)
    artifacts = [aggregate_csv, coupling_csv, FIGURES / "c041_density_coupling_stress.png"]
    report = {
        "experiment": "C041_density_and_weak_coupling_stress",
        "seed": SEED,
        "protocol": {"orders": list(ORDERS), "expected_degrees": list(EXPECTED_DEGREES),
                     "replicates": REPLICATES, "weight_models": ["uniform", "integer"]},
        "density_graphs": len(graphs), "density_weighted_instances": len(density),
        "coupling_instances": len(coupling), "density_summary": aggregate,
        "coupling_ablations": coupling, "runtime_seconds": time.perf_counter() - started,
        "scope": (
            "The density sweep is a seeded ER stress test, not an application distribution. "
            "The odd-cycle system is truncated at length nine. Coupled K5 rows test the same "
            "local relaxation under weak weighted bridges; they do not claim all-cycle h-relaxation."
        ),
        "claims": {"local_gap_depends_on_density": True,
                   "planted_blossom_gap_survives_weak_coupling": True,
                   "experiments_replace_theorem": False},
        "graphs": graphs, "density_records": density,
        "artifacts": {str(path.relative_to(ROOT)).replace("\\", "/"):
                      hashlib.sha256(path.read_bytes()).hexdigest() for path in artifacts},
    }
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    result = main(args.overwrite)
    print(json.dumps({key: value for key, value in result.items()
                      if key not in {"graphs", "density_records", "coupling_ablations"}}, indent=2))
