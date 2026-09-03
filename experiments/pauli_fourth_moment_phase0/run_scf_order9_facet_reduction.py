"""Split order-nine SCF facet types into proved joins and residual atoms."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import networkx as nx
import numpy as np

from run_scf_hbar_falsification import independent_masks, weighted_alpha


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = json.loads(args.input.read_text(encoding="utf-8"))

    proved_joins = []
    residual_atoms = []
    for index, representative in enumerate(source["representatives"]):
        graph = nx.from_graph6_bytes(representative["support_graph6"].encode())
        weights = np.asarray(representative["weights"], dtype=float)
        heavy = [node for node, weight in enumerate(weights) if abs(weight - 1.0) < 1e-9]
        light = [node for node, weight in enumerate(weights) if abs(weight - 0.5) < 1e-9]
        if len(heavy) + len(light) != len(graph):
            raise AssertionError((index, sorted(set(weights))))

        masks = independent_masks(graph)
        unweighted_alpha = weighted_alpha(masks, np.ones(len(graph)))
        weighted_value = weighted_alpha(masks, weights)
        if abs(weighted_value - representative["weighted_alpha"]) > 1e-9:
            raise AssertionError((index, weighted_value, representative["weighted_alpha"]))

        heavy_is_clique = all(graph.has_edge(left, right) for i, left in enumerate(heavy) for right in heavy[i + 1 :])
        cross_is_complete = all(graph.has_edge(left, right) for left in heavy for right in light)
        light_graph = graph.subgraph(light).copy()
        light_alpha = weighted_alpha(
            independent_masks(nx.convert_node_labels_to_integers(light_graph)),
            np.ones(len(light)),
        )
        record = {
            "representative_index": index,
            "support_graph6": representative["support_graph6"],
            "weights": representative["weights"],
            "weighted_alpha": weighted_value,
            "unweighted_alpha": unweighted_alpha,
            "heavy_vertices": heavy,
            "light_vertices": light,
            "heavy_is_clique": heavy_is_clique,
            "cross_is_complete": cross_is_complete,
            "light_unweighted_alpha": light_alpha,
        }
        if abs(weighted_value - 1.0) < 1e-9:
            if not (heavy_is_clique and cross_is_complete and abs(light_alpha - 2.0) < 1e-9):
                raise AssertionError(record)
            record["proof"] = (
                "G=K join H; beta(K,1)=1 and the SCF rank theorem gives "
                "beta(H,1/2)=alpha(H)/2=1; beta of a join is their maximum"
            )
            proved_joins.append(record)
        else:
            residual_atoms.append(record)

    result = {
        "experiment": "order9_SCF_nonrank_facet_analytic_reduction",
        "weighted_support_classes": len(source["representatives"]),
        "proved_join_classes": len(proved_joins),
        "residual_alpha3_classes": len(residual_atoms),
        "all_proved_classes_have_complete_join_structure": all(
            record["heavy_is_clique"] and record["cross_is_complete"]
            for record in proved_joins
        ),
        "status": "115_classes_proved_13_alpha3_atoms_remain"
        if len(proved_joins) == 115 and len(residual_atoms) == 13
        else "unexpected_classification",
        "proved_joins": proved_joins,
        "residual_atoms": residual_atoms,
    }
    if result["status"] != "115_classes_proved_13_alpha3_atoms_remain":
        raise AssertionError(result["status"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key not in {"proved_joins", "residual_atoms"}}, indent=2))


if __name__ == "__main__":
    main()
