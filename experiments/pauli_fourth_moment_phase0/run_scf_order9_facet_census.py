"""Catalogue non-rank facets of every non-line SCF graph of order nine."""

from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

import networkx as nx
import numpy as np

from run_scf_facet_attack import nonrank_facet_weights
from run_scf_hbar_falsification import independent_masks, weighted_alpha


def weighted_support(graph: nx.Graph, weights: np.ndarray) -> tuple[nx.Graph, np.ndarray, list[int]]:
    nodes = [index for index, value in enumerate(weights) if value > 1e-7]
    support = nx.convert_node_labels_to_integers(graph.subgraph(nodes), ordering="sorted")
    values = weights[nodes] / weights[nodes].max()
    values = np.round(values, 7)
    nx.set_node_attributes(support, {i: float(value) for i, value in enumerate(values)}, "weight")
    return support, values, nodes


def weighted_key(graph: nx.Graph, values: np.ndarray) -> tuple:
    return (
        len(graph),
        graph.number_of_edges(),
        tuple(sorted(values)),
        nx.weisfeiler_lehman_graph_hash(graph, node_attr="weight"),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = json.loads(args.input.read_text(encoding="utf-8"))

    representatives = []
    buckets: dict[tuple, list[int]] = {}
    graphs_with_nonrank = 0
    facet_occurrences = 0
    coefficient_patterns = collections.Counter()
    for record in source["SCF_records"]:
        if record["line_graph"]:
            continue
        graph = nx.from_graph6_bytes(record["graph6"].encode())
        masks = independent_masks(graph)
        facets = nonrank_facet_weights(graph, masks)
        if facets:
            graphs_with_nonrank += 1
        for weights in facets:
            facet_occurrences += 1
            support, values, nodes = weighted_support(graph, weights)
            pattern = tuple(float(value) for value in sorted(values))
            coefficient_patterns[str(pattern)] += 1
            key = weighted_key(support, values)
            match = None
            for index in buckets.get(key, []):
                candidate = representatives[index]
                candidate_graph = nx.from_graph6_bytes(candidate["support_graph6"].encode())
                nx.set_node_attributes(
                    candidate_graph,
                    {i: value for i, value in enumerate(candidate["weights"])},
                    "weight",
                )
                if nx.is_isomorphic(
                    support,
                    candidate_graph,
                    node_match=nx.algorithms.isomorphism.categorical_node_match("weight", None),
                ):
                    match = index
                    break
            if match is None:
                match = len(representatives)
                buckets.setdefault(key, []).append(match)
                representatives.append(
                    {
                        "source_graph6": record["graph6"],
                        "source_support_nodes": nodes,
                        "support_graph6": nx.to_graph6_bytes(support, header=False).decode().strip(),
                        "weights": values.tolist(),
                        "weighted_alpha": weighted_alpha(independent_masks(support), values),
                        "occurrences": 1,
                    }
                )
            else:
                representatives[match]["occurrences"] += 1

    result = {
        "experiment": "exhaustive_order9_SCF_nonrank_facet_census",
        "source_sha256": source["source_sha256"],
        "SCF_non_line_graphs": source["SCF_non_line_graphs"],
        "graphs_with_nonrank_facets": graphs_with_nonrank,
        "nonrank_facet_occurrences": facet_occurrences,
        "weighted_support_isomorphism_classes": len(representatives),
        "coefficient_patterns": dict(coefficient_patterns),
        "representatives": representatives,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "representatives"}, indent=2))


if __name__ == "__main__":
    main()
