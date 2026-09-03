"""Attack SCF hbar-perfectness in exact non-rank facet directions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import networkx as nx
import numpy as np
from scipy.spatial import ConvexHull

from run_scf_hbar_falsification import (
    beta_lower_bound,
    independent_masks,
    matrices_for_graph,
    weighted_alpha,
)


def stable_points(graph: nx.Graph, masks: list[int]) -> np.ndarray:
    return np.asarray(
        [[(mask >> index) & 1 for index in range(len(graph))] for mask in masks],
        dtype=float,
    )


def nonrank_facet_weights(graph: nx.Graph, masks: list[int]) -> list[np.ndarray]:
    hull = ConvexHull(stable_points(graph, masks))
    unique: dict[tuple[float, ...], np.ndarray] = {}
    for equation in hull.equations:
        normal = equation[:-1]
        if normal.max() <= 1e-8 or normal.min() < -1e-8:
            continue
        normal = np.maximum(normal, 0.0)
        positive = normal[normal > 1e-8]
        if len(positive) == 0 or positive.max() - positive.min() <= 2e-6:
            continue
        normal /= normal.max()
        key = tuple(np.round(normal, 7))
        unique[key] = normal
    return list(unique.values())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=619871)
    parser.add_argument("--starts", type=int, default=256)
    parser.add_argument("--iterations", type=int, default=240)
    args = parser.parse_args()
    rng = np.random.default_rng(args.seed)
    source = json.loads(args.input.read_text(encoding="utf-8"))
    records = []
    violation = None
    tested_facets = 0
    largest_ratio = 0.0
    for source_record in source["records"][1:]:
        graph = nx.from_graph6_bytes(source_record["graph6"].encode())
        masks = independent_masks(graph)
        weights_list = nonrank_facet_weights(graph, masks)
        if not weights_list:
            continue
        operators = matrices_for_graph(graph)
        graph_ratios = []
        for facet_index, weights in enumerate(weights_list):
            alpha = weighted_alpha(masks, weights)
            beta = beta_lower_bound(
                operators, weights, rng, args.starts, args.iterations
            )
            ratio = beta / alpha
            graph_ratios.append(ratio)
            tested_facets += 1
            largest_ratio = max(largest_ratio, ratio)
            if ratio > 1.0 + 1e-7:
                violation = {
                    "graph6": source_record["graph6"],
                    "source": source_record["source"],
                    "facet_index": facet_index,
                    "weights": weights.tolist(),
                    "alpha": alpha,
                    "beta_lower_bound": beta,
                    "ratio": ratio,
                }
                break
        records.append(
            {
                "graph6": source_record["graph6"],
                "source": source_record["source"],
                "vertices": len(graph),
                "edges": graph.number_of_edges(),
                "unique_nonrank_facets": len(weights_list),
                "largest_ratio": max(graph_ratios),
            }
        )
        if violation:
            break
    payload = {
        "experiment": "SCF_exact_nonrank_facet_attack",
        "seed": args.seed,
        "graphs_with_nonrank_facets": len(records),
        "unique_nonrank_facets_tested": tested_facets,
        "starts_per_facet": args.starts,
        "iterations": args.iterations,
        "largest_ratio": largest_ratio,
        "violation": violation,
        "status": "weighted_claim_falsified" if violation else "no_violation_found",
        "records": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in payload.items() if key != "records"}, indent=2))


if __name__ == "__main__":
    main()
