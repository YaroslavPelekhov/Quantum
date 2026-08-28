"""Read-only twin-quotient census of the pre-existing frozen QOBLIB cohort."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import networkx as nx


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path[:0] = [
    str(REPO / "experiments" / "evoq_mis_full_qoblib"),
    str(REPO / "experiments" / "dcsrdt_structural_audit"),
    str(REPO / "experiments" / "symmetry_quotient_decision_rank"),
    str(REPO / "experiments" / "contrastive_tensor_simulation"),
]

import run_cycle as rc
from contrastive_core import atomic_json
from quotient_core import twin_classes


def main() -> None:
    selection = json.loads(
        (REPO / "experiments" / "evoq_mis_full_qoblib" / "results"
         / "qoblib_cohort_screen" / "selected_cases.json")
        .read_text(encoding="utf-8")
    )
    rows = []
    for selected in selection["selected_cases"]:
        graph = rc.parse_gph_file(
            rc.QOBLIB / "07-independentset" / "instances"
            / f"{selected['case']}.gph"
        )
        reduced = rc.reduce_graph_for_quantum(
            graph, max_degree=selected["cap"]
        ).reduced_graph
        mapping = {node: index for index, node in enumerate(sorted(reduced.nodes()))}
        reduced = nx.relabel_nodes(reduced, mapping)
        groups = twin_classes(reduced, list(range(len(reduced))))
        quotient_dimension = math.prod(len(group) + 1 for group in groups)
        rows.append({
            "case": selected["case"],
            "family": selected["family"],
            "qubits": len(reduced),
            "nontrivial_twin_class_sizes": [
                len(group) for group in groups if len(group) > 1
            ],
            "quotient_dimension": quotient_dimension,
            "full_dimension": 1 << len(reduced),
            "dimension_compression": (1 << len(reduced)) / quotient_dimension,
        })
    payload = {
        "complete": True,
        "selection_source": (
            "experiments/evoq_mis_full_qoblib/results/"
            "qoblib_cohort_screen/selected_cases.json"
        ),
        "selection_was_preexisting": True,
        "rows": rows,
        "cases_with_nontrivial_twins": sum(
            bool(row["nontrivial_twin_class_sizes"]) for row in rows
        ),
        "cases_with_at_least_2x_compression": sum(
            row["dimension_compression"] >= 2.0 for row in rows
        ),
    }
    atomic_json(
        REPO / "results" / "symmetry_quotient_backend"
        / "qoblib_twin_census.json",
        payload,
    )
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()

