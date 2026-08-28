"""Transfer the twin-count structural explanation to the real frozen cohort."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import networkx as nx
import numpy as np


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULTS = REPO / "results" / "symmetry_claim_falsification"
sys.path[:0] = [
    str(HERE),
    str(REPO / "experiments" / "evoq_mis_full_qoblib"),
    str(REPO / "experiments" / "symmetry_quotient_backend"),
    str(REPO / "experiments" / "symmetry_quotient_breadth"),
    str(REPO / "experiments" / "symmetry_quotient_decision_rank"),
    str(REPO / "experiments" / "rankcert_mps"),
    str(REPO / "experiments" / "sparse_mps_dcsrdt"),
    str(REPO / "experiments" / "contrastive_tensor_simulation"),
]

import rankcert_inputs
import run_cycle as rc
from contrastive_core import atomic_json, sha256
from quotient_core import compile_twin_quotient
from run_backend import graph_from_scorer
from run_breadth import basis_data
from sparse_mps_core import enumerate_bks_support
from twin_structural import twin_frontier_profile


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    breadth = json.loads(
        (REPO / "results" / "symmetry_quotient_breadth" / "breadth.json")
        .read_text(encoding="utf-8")
    )
    selection = json.loads(
        (REPO / "experiments" / "evoq_mis_full_qoblib" / "results"
         / "qoblib_cohort_screen" / "selected_cases.json")
        .read_text(encoding="utf-8")
    )
    selected = {row["case"]: row for row in selection["selected_cases"]}
    rows = []
    for archived in breadth["rows"]:
        case = archived["case"]
        spec = selected[case]
        original = rc.parse_gph_file(
            rc.QOBLIB / "07-independentset" / "instances" / f"{case}.gph"
        )
        reduced = rc.reduce_graph_for_quantum(original, max_degree=spec["cap"])
        mapping = {node: index for index, node in enumerate(sorted(reduced.reduced_graph.nodes()))}
        graph = nx.relabel_nodes(reduced.reduced_graph, mapping)
        order = list(range(graph.number_of_nodes()))
        _, events, _ = basis_data(graph)
        architecture = compile_twin_quotient(graph, order, penalty=1.5)
        profile = twin_frontier_profile(events, len(order), architecture.groups)
        cut = archived["cut"]
        bound = profile[cut - 1]["twin_structural_bound"]
        rows.append({
            "case": case,
            "ordering": "reduced-natural",
            "cuts": [cut],
            "ranks": [archived["dense_rank"]],
            "bounds": [bound],
            "violations": int(archived["dense_rank"] > bound),
            "residual_cuts": [cut] if archived["dense_rank"] < bound else [],
        })

    specs = {
        (row["case"], row["ordering"], row["method"]): row
        for row in rankcert_inputs.load_specs()
    }
    structural = json.loads(
        (REPO / "results" / "dcsrdt_structural_audit" / "audit.json")
        .read_text(encoding="utf-8")
    )
    for ordering in ("sorted", "spectral"):
        spec = specs[("aves-sparrow-social", ordering, "published_lr")]
        graph = graph_from_scorer(spec["scorer"])
        architecture = compile_twin_quotient(
            graph, list(range(24)), penalty=1.5, normalized_ising=True
        )
        events = np.asarray(enumerate_bks_support(spec["scorer"]), dtype=np.int64)
        profile = twin_frontier_profile(events, 24, architecture.groups)
        archived = next(
            row for row in structural["rows"]
            if row["case"] == "aves-sparrow-social" and row["ordering"] == ordering
        )
        ranks = [cut["numerical_rank"] for cut in archived["cuts"]]
        bounds = [cut["twin_structural_bound"] for cut in profile]
        rows.append({
            "case": "aves-sparrow-social",
            "ordering": ordering,
            "cuts": list(range(1, 24)),
            "ranks": ranks,
            "bounds": bounds,
            "violations": sum(rank > bound for rank, bound in zip(ranks, bounds)),
            "residual_cuts": [
                cut for cut, rank, bound in zip(range(1, 24), ranks, bounds)
                if rank < bound
            ],
        })

    payload = {
        "complete": True,
        "protocol_sha256": sha256(HERE / "REAL_BOUND_PROTOCOL.md"),
        "selection_was_preexisting": True,
        "rows": rows,
        "tested_rank_rows": sum(len(row["cuts"]) for row in rows),
        "bound_violations": sum(row["violations"] for row in rows),
        "residual_rows": sum(bool(row["residual_cuts"]) for row in rows),
        "all_ranks_equal_bound": all(
            rank == bound for row in rows
            for rank, bound in zip(row["ranks"], row["bounds"])
        ),
    }
    atomic_json(RESULTS / "real_bound.json", payload)
    for row in rows:
        print(json.dumps(row), flush=True)
    print(json.dumps({key: payload[key] for key in (
        "tested_rank_rows", "bound_violations", "residual_rows",
        "all_ranks_equal_bound"
    )}, indent=2))


if __name__ == "__main__":
    main()
