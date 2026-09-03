"""Prove the four one-hole residual SCF facet types by exact reduction.

The proof uses the three-variable envelope already established in
``run_scf_atom_spectral_reduction.py``.  Every checked graph has a clique of
heavy vertices, one induced four-hole alternating between two heavy and two
light vertices, and only light independent triples.  Maximizing over the
heavy simplex is therefore the maximum of one 2-by-2 spectral block and the
remaining scalar branches.  Exact nonnegative-coefficient slacks reduce each
branch to the three-variable envelope.
"""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import networkx as nx
import numpy as np
import sympy as sp


TARGET_INDICES = (5, 7, 9, 33)


def induced_four_holes(graph: nx.Graph) -> list[tuple[int, ...]]:
    holes = []
    for vertices in itertools.combinations(graph.nodes(), 4):
        subgraph = graph.subgraph(vertices)
        if subgraph.number_of_edges() == 4 and all(
            degree == 2 for _, degree in subgraph.degree()
        ):
            holes.append(vertices)
    return holes


def independent_triples(graph: nx.Graph) -> list[tuple[int, ...]]:
    return [
        vertices
        for vertices in itertools.combinations(graph.nodes(), 3)
        if graph.subgraph(vertices).number_of_edges() == 0
    ]


def polynomial_has_nonnegative_coefficients(
    expression: sp.Expr, variables: tuple[sp.Symbol, ...]
) -> bool:
    return all(
        coefficient >= 0
        for _, coefficient in sp.Poly(sp.expand(expression), *variables).terms()
    )


def nonzero_terms(expression: sp.Expr, variables: tuple[sp.Symbol, ...]) -> list[dict]:
    rows = []
    for powers, coefficient in sp.Poly(sp.expand(expression), *variables).terms():
        if coefficient == 0:
            continue
        monomial = "*".join(
            f"p{index}" if power == 1 else f"p{index}^{power}"
            for index, power in enumerate(powers)
            if power
        ) or "1"
        rows.append({"coefficient": str(coefficient), "monomial": monomial})
    return rows


def find_isolated_branch_partition(
    graph: nx.Graph,
    light: list[int],
    heavy_vertex: int,
    q_light: sp.Expr,
    e3: sp.Expr,
    variables: tuple[sp.Symbol, ...],
) -> dict:
    y_vertices = [vertex for vertex in light if not graph.has_edge(heavy_vertex, vertex)]
    remainder = [vertex for vertex in light if vertex not in y_vertices]
    for mask in range(1, 2 ** len(remainder) - 1):
        x_vertices = [
            vertex for index, vertex in enumerate(remainder) if mask & (1 << index)
        ]
        z_vertices = [vertex for vertex in remainder if vertex not in x_vertices]
        if min(x_vertices) > min(z_vertices):
            continue
        x = sum(variables[vertex] for vertex in x_vertices)
        y = sum(variables[vertex] for vertex in y_vertices)
        z = sum(variables[vertex] for vertex in z_vertices)
        q_slack = sp.expand(x * y + x * z + y * z - q_light)
        e3_slack = sp.expand(x * y * z - e3)
        if polynomial_has_nonnegative_coefficients(
            q_slack, variables
        ) and polynomial_has_nonnegative_coefficients(e3_slack, variables):
            return {
                "heavy_vertex": heavy_vertex,
                "x_vertices": x_vertices,
                "y_vertices": y_vertices,
                "z_vertices": z_vertices,
                "q_slack": str(sp.factor(q_slack)),
                "e3_slack": str(sp.factor(e3_slack)),
                "q_slack_terms": nonzero_terms(q_slack, variables),
                "e3_slack_terms": nonzero_terms(e3_slack, variables),
            }
    raise AssertionError((heavy_vertex, y_vertices, remainder))


def certify_record(record: dict) -> dict:
    graph = nx.from_graph6_bytes(record["support_graph6"].encode())
    weights = np.asarray(record["weights"], dtype=float)
    light = np.flatnonzero(weights == 0.5).tolist()
    heavy = np.flatnonzero(weights == 1.0).tolist()
    variables = sp.symbols(f"p0:{len(graph)}", nonnegative=True)
    holes = induced_four_holes(graph)
    triples = independent_triples(graph)
    if len(holes) != 1:
        raise AssertionError((record["representative_index"], holes))
    if any(any(vertex in heavy for vertex in triple) for triple in triples):
        raise AssertionError((record["representative_index"], triples))
    if any(
        vertex not in holes[0]
        and all(not graph.has_edge(vertex, hole_vertex) for hole_vertex in holes[0])
        for vertex in graph
    ):
        raise AssertionError("a hole correction could survive in e3")
    if any(not graph.has_edge(left, right) for left, right in itertools.combinations(heavy, 2)):
        raise AssertionError("the heavy support is not a clique")

    hole_heavy = [vertex for vertex in holes[0] if vertex in heavy]
    hole_light = [vertex for vertex in holes[0] if vertex in light]
    if len(hole_heavy) != 2 or len(hole_light) != 2:
        raise AssertionError((hole_heavy, hole_light))

    light_sum = sum(variables[vertex] for vertex in light)
    q_light = sum(
        variables[left] * variables[right]
        for left, right in itertools.combinations(light, 2)
        if not graph.has_edge(left, right)
    )
    e3 = sum(sp.prod(variables[vertex] for vertex in triple) for triple in triples)

    first, second = hole_heavy
    diagonal_first = sum(
        variables[vertex] for vertex in light if not graph.has_edge(first, vertex)
    )
    diagonal_second = sum(
        variables[vertex] for vertex in light if not graph.has_edge(second, vertex)
    )
    determinant = sp.expand(
        diagonal_first * diagonal_second
        - variables[hole_light[0]] * variables[hole_light[1]]
    )
    remaining = sp.expand(light_sum - diagonal_first - diagonal_second)
    q_slack = sp.expand(
        remaining * (diagonal_first + diagonal_second) + determinant - q_light
    )
    e3_slack = sp.expand(remaining * determinant - e3)
    for expression in (diagonal_first, diagonal_second, determinant, remaining, q_slack, e3_slack):
        if not polynomial_has_nonnegative_coefficients(expression, variables):
            raise AssertionError((record["representative_index"], expression))

    isolated = [vertex for vertex in heavy if vertex not in hole_heavy]
    isolated_certificates = [
        find_isolated_branch_partition(
            graph, light, vertex, q_light, e3, variables
        )
        for vertex in isolated
    ]

    return {
        "representative_index": record["representative_index"],
        "support_graph6": record["support_graph6"],
        "weights": record["weights"],
        "light_vertices": light,
        "heavy_vertices": heavy,
        "heavy_is_clique": True,
        "induced_four_hole": list(holes[0]),
        "hole_heavy_vertices": hole_heavy,
        "hole_light_vertices": hole_light,
        "independent_triples": [list(triple) for triple in triples],
        "e2_formula": "q0+2*sqrt(product_{i in C} p_i)",
        "e3_formula": str(e3),
        "cycle_block": {
            "diagonal_first": str(diagonal_first),
            "diagonal_second": str(diagonal_second),
            "off_diagonal_squared": str(
                variables[hole_light[0]] * variables[hole_light[1]]
            ),
            "remaining_light_mass": str(remaining),
            "determinant": str(sp.factor(determinant)),
            "q_slack": str(sp.factor(q_slack)),
            "e3_slack": str(sp.factor(e3_slack)),
            "q_slack_terms": nonzero_terms(q_slack, variables),
            "e3_slack_terms": nonzero_terms(e3_slack, variables),
        },
        "isolated_heavy_branches": isolated_certificates,
        "certificate": "all slacks have nonnegative integer coefficients",
        "consequence": "the proved three-variable envelope gives beta(G,w)<=3/2; a maximum stable set gives equality",
        "exact_beta": 1.5,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = json.loads(args.input.read_text(encoding="utf-8"))
    by_index = {
        record["representative_index"]: record for record in source["residual_atoms"]
    }
    if not all(index in by_index for index in TARGET_INDICES):
        raise AssertionError(sorted(by_index))
    records = [certify_record(by_index[index]) for index in TARGET_INDICES]
    result = {
        "experiment": "exact_one_hole_SCF_residual_facet_certificates",
        "target_indices": list(TARGET_INDICES),
        "classes_proved": len(records),
        "shared_structure": {
            "heavy_support": "clique",
            "four_holes": 1,
            "hole_pattern": "two heavy and two light vertices",
            "independent_triples": "light-only",
            "heavy_simplex_reduction": "one 2x2 spectral block plus scalar branches",
            "envelope": "xy+xz+yz+(1-2L)y+2*sqrt((3/2)xyz), x+y+z=L",
            "fixed_L_maximum": "L(1-2L) for L<=1/6 and (1/4+L/2)^2 for L>=1/6",
        },
        "proof_status": "exact_symbolic_certificates_passed",
        "records": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "experiment": result["experiment"],
                "classes_proved": result["classes_proved"],
                "proof_status": result["proof_status"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
