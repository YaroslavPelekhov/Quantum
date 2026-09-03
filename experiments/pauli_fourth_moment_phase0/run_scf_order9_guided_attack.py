"""Attack every order-nine SCF weighted facet type from every sign orthant."""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import networkx as nx
import numpy as np

from run_scf_hbar_falsification import beta_from_coefficients, matrices_for_graph
from run_scf_theta_guided_attack import theta_profile


def all_sign_orthants(profile: np.ndarray):
    root = np.sqrt(np.maximum(profile, 0.0))
    for tail in itertools.product([-1.0, 1.0], repeat=len(root) - 1):
        yield root * np.asarray((1.0,) + tail)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=320)
    args = parser.parse_args()
    source = json.loads(args.input.read_text(encoding="utf-8"))

    records = []
    largest_ratio = 0.0
    sign_classes = 0
    violation = None
    for index, representative in enumerate(source["representatives"]):
        graph = nx.from_graph6_bytes(representative["support_graph6"].encode())
        weights = np.asarray(representative["weights"], dtype=float)
        alpha = float(representative["weighted_alpha"])
        operators = matrices_for_graph(graph)
        upper, profile = theta_profile(graph, weights)
        starts = 1 << (len(graph) - 1)
        beta = beta_from_coefficients(
            operators, weights, all_sign_orthants(profile), args.iterations
        )
        ratio = beta / alpha
        sign_classes += starts
        largest_ratio = max(largest_ratio, ratio)
        record = {
            "representative_index": index,
            "support_graph6": representative["support_graph6"],
            "weights": representative["weights"],
            "occurrences": representative["occurrences"],
            "weighted_alpha": alpha,
            "theta_upper_bound": upper,
            "theta_upper_ratio": upper / alpha,
            "sign_orthants": starts,
            "guided_beta_lower_bound": beta,
            "guided_ratio": ratio,
        }
        records.append(record)
        if ratio > 1.0 + 1e-7:
            violation = record
            break

    result = {
        "experiment": "exhaustive_order9_SCF_facet_type_theta_guided_attack",
        "weighted_support_isomorphism_classes": source[
            "weighted_support_isomorphism_classes"
        ],
        "classes_tested": len(records),
        "sign_orthants_tested": sign_classes,
        "iterations": args.iterations,
        "largest_guided_ratio": largest_ratio,
        "violation": violation,
        "status": "weighted_claim_falsified" if violation else "no_violation_found",
        "records": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "records"}, indent=2))


if __name__ == "__main__":
    main()
