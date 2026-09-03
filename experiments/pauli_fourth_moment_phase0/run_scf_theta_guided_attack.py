"""Use a state-moment SDP profile to seed non-rank SCF facet attacks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cvxpy as cp
import networkx as nx
import numpy as np

from run_published_g9_control import pauli_word
from run_scf_facet_attack import nonrank_facet_weights
from run_scf_hbar_falsification import (
    beta_from_coefficients,
    independent_masks,
    matrices_for_graph,
    weighted_alpha,
)


def theta_profile(graph: nx.Graph, weights: np.ndarray) -> tuple[float, np.ndarray]:
    """Return the first state-moment upper bound and its squared profile."""
    count = len(graph)
    moment = cp.Variable((count + 1, count + 1), symmetric=True)
    constraints = [moment >> 0, moment[0, 0] == 1]
    for index in range(count):
        constraints.append(moment[index + 1, index + 1] == moment[0, index + 1])
    for left, right in graph.edges():
        constraints.append(moment[left + 1, right + 1] == 0)
    problem = cp.Problem(
        cp.Maximize(weights @ cp.diag(moment)[1:]), constraints
    )
    problem.solve(solver="CLARABEL")
    if problem.status not in {cp.OPTIMAL, cp.OPTIMAL_INACCURATE}:
        raise RuntimeError(f"theta relaxation failed: {problem.status}")
    profile = np.maximum(np.diag(moment.value)[1:], 0.0)
    return float(problem.value), profile


def signed_profile_starts(
    profile: np.ndarray, rng: np.random.Generator, starts: int
) -> list[np.ndarray]:
    root = np.sqrt(profile)
    output = [root]
    output.extend(root * rng.choice([-1.0, 1.0], len(root)) for _ in range(starts - 1))
    return output


def graph_from_operators(operators: np.ndarray) -> nx.Graph:
    graph = nx.Graph()
    graph.add_nodes_from(range(len(operators)))
    for left in range(len(operators)):
        for right in range(left + 1, len(operators)):
            if np.linalg.norm(
                operators[left] @ operators[right]
                + operators[right] @ operators[left]
            ) < 1e-8:
                graph.add_edge(left, right)
    return graph


def published_g9_control(rng: np.random.Generator, starts: int, iterations: int) -> dict:
    words = [
        "XIII", "IXII", "IIXI", "ZIII", "IZII", "ZZZI", "YZYX", "YYXX", "YXZZ"
    ]
    operators = np.stack([pauli_word(word) for word in words])
    graph = graph_from_operators(operators)
    weights = np.asarray([1, 1, 1, 1, 1, 1, 1, 2, 2], dtype=float)
    upper, profile = theta_profile(graph, weights)
    beta = beta_from_coefficients(
        operators,
        weights,
        signed_profile_starts(profile, rng, starts),
        iterations,
    )
    result = {
        "theta_upper_bound": upper,
        "weighted_alpha": 3.0,
        "published_beta": 3.044815,
        "guided_beta_lower_bound": beta,
        "absolute_error_to_published": abs(beta - 3.044815),
    }
    if result["absolute_error_to_published"] >= 2e-6:
        raise AssertionError(f"published G9 control failed: {result}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=904219)
    parser.add_argument("--starts", type=int, default=512)
    parser.add_argument("--iterations", type=int, default=320)
    args = parser.parse_args()
    rng = np.random.default_rng(args.seed)
    source = json.loads(args.input.read_text(encoding="utf-8"))
    control = published_g9_control(rng, args.starts, args.iterations)

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
        graph_upper_ratios = []
        for facet_index, weights in enumerate(weights_list):
            alpha = weighted_alpha(masks, weights)
            upper, profile = theta_profile(graph, weights)
            beta = beta_from_coefficients(
                operators,
                weights,
                signed_profile_starts(profile, rng, args.starts),
                args.iterations,
            )
            ratio = beta / alpha
            graph_ratios.append(ratio)
            graph_upper_ratios.append(upper / alpha)
            tested_facets += 1
            largest_ratio = max(largest_ratio, ratio)
            if ratio > 1.0 + 1e-7:
                violation = {
                    "graph6": source_record["graph6"],
                    "source": source_record["source"],
                    "facet_index": facet_index,
                    "weights": weights.tolist(),
                    "alpha": alpha,
                    "theta_upper_bound": upper,
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
                "largest_theta_upper_ratio": max(graph_upper_ratios),
                "largest_guided_ratio": max(graph_ratios),
            }
        )
        if violation:
            break

    payload = {
        "experiment": "SCF_theta_profile_guided_nonrank_facet_attack",
        "seed": args.seed,
        "published_G9_positive_control": control,
        "graphs_with_nonrank_facets": len(records),
        "unique_nonrank_facets_tested": tested_facets,
        "signed_profile_starts_per_facet": args.starts,
        "iterations": args.iterations,
        "largest_guided_ratio": largest_ratio,
        "violation": violation,
        "status": "weighted_claim_falsified" if violation else "no_violation_found",
        "records": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in payload.items() if key != "records"}, indent=2))


if __name__ == "__main__":
    main()
