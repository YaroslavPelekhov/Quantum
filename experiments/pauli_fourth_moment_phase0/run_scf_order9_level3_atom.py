"""Reproduce the third-level state-moment bound for the last order-nine atom."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import networkx as nx
import numpy as np

from state_moment_sdp import beta_state_moment_upper


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--representative-index", type=int, default=27)
    parser.add_argument("--eps", type=float, default=1e-5)
    parser.add_argument("--max-iters", type=int, default=50000)
    args = parser.parse_args()
    source = json.loads(args.input.read_text(encoding="utf-8"))
    representative = source["representatives"][args.representative_index]
    graph = nx.from_graph6_bytes(representative["support_graph6"].encode())
    weights = np.asarray(representative["weights"], dtype=float)
    upper, metadata = beta_state_moment_upper(
        graph,
        weights,
        order=3,
        solver="SCS",
        solver_options={"eps": args.eps, "max_iters": args.max_iters},
    )
    result = {
        "experiment": "order9_SCF_last_atom_third_state_moment_upper_bound",
        "representative_index": args.representative_index,
        "support_graph6": representative["support_graph6"],
        "weights": representative["weights"],
        "weighted_alpha": representative["weighted_alpha"],
        "state_moment_upper_bound": upper,
        "upper_excess": upper - representative["weighted_alpha"],
        "solver_options": {"eps": args.eps, "max_iters": args.max_iters},
        **metadata,
        "verdict": "relaxation_gap_reduced_but_not_closed",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
