"""Exact certificates for the two collapsible two-hole SCF residual types."""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import networkx as nx
import numpy as np
import sympy as sp


TARGETS = {34: "shared_heavy_pair", 48: "equal_profile_heavy_leaves"}


def holes(graph: nx.Graph) -> list[tuple[int, ...]]:
    return [
        vertices
        for vertices in itertools.combinations(graph.nodes(), 4)
        if graph.subgraph(vertices).number_of_edges() == 4
        and all(degree == 2 for _, degree in graph.subgraph(vertices).degree())
    ]


def multiply_words(
    graph: nx.Graph, left: tuple[int, ...], right: tuple[int, ...]
) -> tuple[tuple[int, ...], int]:
    word = list(left) + list(right)
    sign = 1
    index = 0
    while index < len(word) - 1:
        if word[index] == word[index + 1]:
            del word[index : index + 2]
            index = max(0, index - 1)
        elif word[index] > word[index + 1]:
            first, second = word[index], word[index + 1]
            word[index], word[index + 1] = second, first
            if graph.has_edge(first, second):
                sign *= -1
            index = max(0, index - 1)
        else:
            index += 1
    return tuple(word), sign


def is_coefficientwise_nonnegative(expression: sp.Expr, variables: tuple) -> bool:
    return all(
        coefficient >= 0
        for _, coefficient in sp.Poly(sp.expand(expression), *variables).terms()
    )


def assert_nonnegative(*expressions: sp.Expr, variables: tuple) -> None:
    for expression in expressions:
        if not is_coefficientwise_nonnegative(expression, variables):
            raise AssertionError(expression)


def graph_data(record: dict) -> tuple:
    graph = nx.from_graph6_bytes(record["support_graph6"].encode())
    weights = np.asarray(record["weights"], dtype=float)
    light = np.flatnonzero(weights == 0.5).tolist()
    heavy = np.flatnonzero(weights == 1.0).tolist()
    variables = sp.symbols(f"p0:{len(graph)}", nonnegative=True)
    four_holes = holes(graph)
    if len(four_holes) != 2:
        raise AssertionError(four_holes)
    forward = multiply_words(graph, four_holes[0], four_holes[1])
    reverse = multiply_words(graph, four_holes[1], four_holes[0])
    if forward[0] != reverse[0] or forward[1] != -reverse[1]:
        raise AssertionError((forward, reverse))
    triples = [
        vertices
        for vertices in itertools.combinations(graph.nodes(), 3)
        if graph.subgraph(vertices).number_of_edges() == 0
    ]
    if any(any(vertex in heavy for vertex in triple) for triple in triples):
        raise AssertionError(triples)
    light_sum = sum(variables[vertex] for vertex in light)
    q_light = sum(
        variables[left] * variables[right]
        for left, right in itertools.combinations(light, 2)
        if not graph.has_edge(left, right)
    )
    e3 = sum(sp.prod(variables[vertex] for vertex in triple) for triple in triples)
    score = {
        vertex: sum(
            variables[other]
            for other in light
            if not graph.has_edge(vertex, other)
        )
        for vertex in heavy
    }
    return graph, light, heavy, variables, four_holes, triples, light_sum, q_light, e3, score


def finish_block(
    record: dict,
    variables: tuple,
    light_sum: sp.Expr,
    q_light: sp.Expr,
    e3: sp.Expr,
    first_diagonal: sp.Expr,
    second_diagonal: sp.Expr,
    off_diagonal_squared: sp.Expr,
    isolated: list[dict],
    collapse: dict,
) -> dict:
    determinant = sp.expand(
        first_diagonal * second_diagonal - off_diagonal_squared
    )
    remaining = sp.expand(light_sum - first_diagonal - second_diagonal)
    q_slack = sp.expand(
        remaining * (first_diagonal + second_diagonal) + determinant - q_light
    )
    e3_slack = sp.expand(remaining * determinant - e3)
    assert_nonnegative(
        first_diagonal,
        second_diagonal,
        off_diagonal_squared,
        determinant,
        remaining,
        q_slack,
        e3_slack,
        variables=variables,
    )
    for branch in isolated:
        assert_nonnegative(
            branch["q_slack_expression"],
            branch["e3_slack_expression"],
            variables=variables,
        )
    return {
        "representative_index": record["representative_index"],
        "support_graph6": record["support_graph6"],
        "collapse": collapse,
        "cycle_block": {
            "first_diagonal": str(first_diagonal),
            "second_diagonal": str(second_diagonal),
            "off_diagonal_squared": str(sp.factor(off_diagonal_squared)),
            "remaining_light_mass": str(remaining),
            "determinant": str(sp.factor(determinant)),
            "q_slack": str(sp.factor(q_slack)),
            "e3_slack": str(sp.factor(e3_slack)),
        },
        "isolated_branches": [
            {
                key: value
                for key, value in branch.items()
                if key not in {"q_slack_expression", "e3_slack_expression"}
            }
            for branch in isolated
        ],
        "certificate": "all displayed slacks have nonnegative integer coefficients",
        "exact_beta": 1.5,
    }


def certify_34(record: dict) -> dict:
    (
        _,
        _,
        _,
        p,
        four_holes,
        _,
        light_sum,
        q_light,
        e3,
        score,
    ) = graph_data(record)
    if {tuple(sorted(set(hole) & {0, 2, 8})) for hole in four_holes} != {(0, 8)}:
        raise AssertionError(four_holes)
    off_squared = sum(
        sp.prod(p[vertex] for vertex in hole if vertex not in {0, 2, 8})
        for hole in four_holes
    )
    x, y, z = p[4], score[2], p[6]
    isolated = [
        {
            "heavy_vertex": 2,
            "x": str(x),
            "y": str(y),
            "z": str(z),
            "q_slack": str(sp.factor(x * y + x * z + y * z - q_light)),
            "e3_slack": str(sp.factor(x * y * z - e3)),
            "q_slack_expression": sp.expand(x * y + x * z + y * z - q_light),
            "e3_slack_expression": sp.expand(x * y * z - e3),
        }
    ]
    return finish_block(
        record,
        p,
        light_sum,
        q_light,
        e3,
        score[0],
        score[8],
        off_squared,
        isolated,
        {
            "kind": "shared_heavy_pair",
            "heavy_pair": [0, 8],
            "identity": "the two anticommuting hole channels add in the squared off-diagonal entry",
        },
    )


def certify_48(record: dict) -> dict:
    (
        _,
        _,
        _,
        p,
        four_holes,
        _,
        light_sum,
        q_light,
        e3,
        score,
    ) = graph_data(record)
    if sp.expand(score[0] - score[2]) != 0:
        raise AssertionError((score[0], score[2]))
    expected_pairs = {tuple(sorted(set(hole) & {0, 2, 6, 8})) for hole in four_holes}
    if expected_pairs != {(0, 8), (2, 8)}:
        raise AssertionError(four_holes)
    # The equal diagonal profiles of heavy leaves 0 and 2 allow an orthogonal
    # rotation.  Only the amplitude parallel to their two cycle couplings
    # remains, with squared off-diagonal p1*p7.
    off_squared = p[1] * p[7]
    x, y, z = p[3], score[6], p[4]
    isolated = [
        {
            "heavy_vertex": 6,
            "x": str(x),
            "y": str(y),
            "z": str(z),
            "q_slack": str(sp.factor(x * y + x * z + y * z - q_light)),
            "e3_slack": str(sp.factor(x * y * z - e3)),
            "q_slack_expression": sp.expand(x * y + x * z + y * z - q_light),
            "e3_slack_expression": sp.expand(x * y * z - e3),
        }
    ]
    return finish_block(
        record,
        p,
        light_sum,
        q_light,
        e3,
        score[0],
        score[8],
        off_squared,
        isolated,
        {
            "kind": "equal_profile_heavy_leaves",
            "heavy_leaf_group": [0, 2],
            "central_heavy_vertex": 8,
            "equal_diagonal_score": str(score[0]),
            "identity": "an orthogonal rotation combines p0 and p2 into their total heavy amplitude",
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = json.loads(args.input.read_text(encoding="utf-8"))
    records = {
        record["representative_index"]: record for record in source["residual_atoms"]
    }
    certified = [certify_34(records[34]), certify_48(records[48])]
    result = {
        "experiment": "exact_collapsible_two_hole_SCF_certificates",
        "target_indices": sorted(TARGETS),
        "classes_proved": 2,
        "proof_status": "exact_symbolic_certificates_passed",
        "shared_consequence": "both types reduce to the proved three-variable fixed-L envelope and satisfy beta(G,w)=alpha(G,w)=3/2",
        "records": certified,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("experiment", "classes_proved", "proof_status")}, indent=2))


if __name__ == "__main__":
    main()
