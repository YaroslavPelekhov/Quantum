"""Apply the validated second state-moment level to alpha-three SCF facets."""

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
    parser.add_argument("--tolerance", type=float, default=2e-5)
    args = parser.parse_args()
    source = json.loads(args.input.read_text(encoding="utf-8"))
    records = []
    largest_excess = -np.inf
    for index, representative in enumerate(source["representatives"]):
        alpha = float(representative["weighted_alpha"])
        if abs(alpha - 1.5) > 1e-8:
            continue
        graph = nx.from_graph6_bytes(representative["support_graph6"].encode())
        weights = np.asarray(representative["weights"], dtype=float)
        upper, metadata = beta_state_moment_upper(graph, weights, order=2)
        excess = upper - alpha
        largest_excess = max(largest_excess, excess)
        records.append(
            {
                "representative_index": index,
                "support_graph6": representative["support_graph6"],
                "weights": representative["weights"],
                "weighted_alpha": alpha,
                "state_moment_upper_bound": upper,
                "upper_excess": excess,
                **metadata,
            }
        )
    result = {
        "experiment": "order9_SCF_alpha3_second_state_moment_upper_bounds",
        "classes_tested": len(records),
        "tolerance": args.tolerance,
        "largest_upper_excess": largest_excess,
        "classes_closed_at_tolerance": sum(
            record["upper_excess"] <= args.tolerance for record in records
        ),
        "status": "all_closed_at_numerical_tolerance"
        if all(record["upper_excess"] <= args.tolerance for record in records)
        else "unclosed_classes_remain",
        "records": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "records"}, indent=2))


if __name__ == "__main__":
    main()
