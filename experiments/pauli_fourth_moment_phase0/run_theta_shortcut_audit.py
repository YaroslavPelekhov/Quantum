"""Falsify lifting the Pauli shortcut to the full Lovasz theta body.

For fixed coordinate cap t, maximizing w.x over TH(G) is an SDP.  At a
solution whose largest coordinate is t, the proposed universal lift would
require t*w.x <= alpha(G,w).  A violation shows that Pauli structure beyond
mere theta-body feasibility is essential.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cvxpy as cp
import networkx as nx
import numpy as np


def weighted_alpha(graph: nx.Graph, weights: np.ndarray) -> float:
    complement = nx.complement(graph)
    return max(float(weights[list(clique)].sum()) for clique in nx.find_cliques(complement))


def capped_theta(graph: nx.Graph, weights: np.ndarray, cap: float):
    n = len(graph)
    moment = cp.Variable((n + 1, n + 1), symmetric=True)
    x = cp.diag(moment)[1:]
    constraints = [
        moment >> 0,
        moment[0, 0] == 1,
        moment[0, 1:] == x,
        x >= 0,
        x <= cap,
    ]
    constraints += [moment[i + 1, j + 1] == 0 for i, j in graph.edges()]
    problem = cp.Problem(cp.Maximize(weights @ x), constraints)
    problem.solve(solver="CLARABEL", tol_gap_abs=1e-9, tol_feas=1e-9)
    if problem.status not in (cp.OPTIMAL, cp.OPTIMAL_INACCURATE):
        raise RuntimeError(problem.status)
    moment_value = np.asarray(moment.value)
    return np.asarray(x.value).ravel(), float(problem.value), moment_value


def feasibility_audit(graph: nx.Graph, x: np.ndarray, moment: np.ndarray, cap: float):
    edge_residual = max(
        (abs(float(moment[i + 1, j + 1])) for i, j in graph.edges()),
        default=0.0,
    )
    return {
        "minimum_moment_eigenvalue": float(np.linalg.eigvalsh(moment).min()),
        "moment_00_error": abs(float(moment[0, 0]) - 1.0),
        "link_max_error": float(np.max(np.abs(moment[0, 1:] - x))),
        "edge_max_error": edge_residual,
        "lower_bound_violation": max(0.0, float(-x.min())),
        "cap_violation": max(0.0, float(x.max() - cap)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--graphs", type=int, default=80)
    parser.add_argument("--vertices", type=int, default=10)
    parser.add_argument("--seed", type=int, default=660131)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rng = np.random.default_rng(args.seed)
    caps = np.unique(np.r_[np.linspace(0.04, 0.96, 24), 1.0])
    best = None
    tests = 0
    for graph_index in range(args.graphs):
        probability = float(rng.uniform(0.15, 0.85))
        graph = nx.gnp_random_graph(
            args.vertices, probability, seed=int(rng.integers(2**31))
        )
        for weight_kind, weights in (
            ("uniform", np.ones(args.vertices)),
            ("lognormal", rng.lognormal(0.0, 1.4, args.vertices)),
        ):
            alpha = weighted_alpha(graph, weights)
            for cap in caps:
                x, objective, moment = capped_theta(graph, weights, float(cap))
                actual_max = float(x.max())
                ratio = actual_max * objective / alpha
                tests += 1
                record = {
                    "ratio": ratio,
                    "graph_index": graph_index,
                    "edge_probability": probability,
                    "edges": [list(edge) for edge in graph.edges()],
                    "weights": weights.tolist(),
                    "weight_kind": weight_kind,
                    "alpha": alpha,
                    "cap": float(cap),
                    "actual_max_coordinate": actual_max,
                    "weighted_theta_point": objective,
                    "theta_point": x.tolist(),
                    "feasibility_audit": feasibility_audit(
                        graph, x, moment, float(cap)
                    ),
                }
                if best is None or ratio > best["ratio"]:
                    best = record
                if ratio > 1.0 + 1e-6:
                    break
            if best is not None and best["ratio"] > 1.0 + 1e-6:
                break
        if best is not None and best["ratio"] > 1.0 + 1e-6:
            break
    payload = {
        "claim_tested": "for every x in TH(G), max(x_i)*x is in STAB(G)",
        "status": "counterexample" if best and best["ratio"] > 1.0 + 1e-6 else "no_violation",
        "seed": args.seed,
        "requested_graphs": args.graphs,
        "vertices": args.vertices,
        "sdps_solved": tests,
        "best": best,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
