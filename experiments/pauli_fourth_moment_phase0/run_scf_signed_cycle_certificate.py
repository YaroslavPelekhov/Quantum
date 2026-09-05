"""Exact signed-sector certificate for residual SCF type 44 (HQjVJr\\)."""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import networkx as nx
import sympy as sp

from run_scf_atom_spectral_reduction import chordless_four_cycles, multiply_words


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = json.loads(args.input.read_text(encoding="utf-8"))
    record = next(
        row for row in source["residual_atoms"] if row["representative_index"] == 44
    )
    if record["support_graph6"] != "HQjVJr\\":
        raise AssertionError(record["support_graph6"])
    graph = nx.from_graph6_bytes(record["support_graph6"].encode())
    cycles = chordless_four_cycles(graph)
    expected = [(0, 1, 6, 8), (0, 7, 2, 8), (1, 2, 6, 7)]
    if cycles != expected:
        raise AssertionError(cycles)

    relation_signs = {}
    for left, right in itertools.combinations(range(3), 2):
        product = multiply_words(graph, cycles[left], cycles[right])
        reverse = multiply_words(graph, cycles[right], cycles[left])
        third = 3 - left - right
        target = multiply_words(graph, (), cycles[third])
        if product != reverse or product[0] != target[0]:
            raise AssertionError((left, right, product, reverse))
        relation_signs[f"h{left}*h{right}"] = {
            "cycle": third,
            "sign": product[1] * target[1],
        }
    if [relation_signs[key]["sign"] for key in sorted(relation_signs)] != [-1, -1, -1]:
        raise AssertionError(relation_signs)

    p = sp.symbols("p0:9", nonnegative=True)
    light = [1, 2, 3, 4, 6, 7]
    heavy = [0, 5, 8]
    light_sum = sum(p[index] for index in light)
    q_light = (
        p[1] * p[2]
        + p[1] * p[4]
        + p[2] * p[3]
        + p[3] * p[4]
        + p[3] * p[6]
        + p[4] * p[6]
        + p[6] * p[7]
    )
    e3 = p[3] * p[4] * p[6]
    diagonal_zero = p[1] + p[3] + p[7]
    diagonal_eight = p[2] + p[6]
    remaining = sp.factor(light_sum - diagonal_zero - diagonal_eight)
    if remaining != p[4]:
        raise AssertionError(remaining)

    a = sp.sqrt(p[1] * p[6])
    b = sp.sqrt(p[2] * p[7])
    signed_branches = []
    for sign_product in (1, -1):
        # s2=-s0*s1.  The first two charge terms become the off-diagonal
        # s0*a+s1*b; only its square, determined by t=s0*s1, matters.
        determinant = sp.expand(diagonal_zero * diagonal_eight - a**2 - b**2) - 2 * sign_product * a * b
        adjusted_q = q_light - 2 * sign_product * a * b
        q_slack = sp.factor(
            remaining * (diagonal_zero + diagonal_eight)
            + determinant
            - adjusted_q
        )
        e3_slack = sp.factor(remaining * determinant - e3)
        determinant_certificate = sp.factor(
            determinant
            - (
                (sp.sqrt(p[1] * p[2]) - sign_product * sp.sqrt(p[6] * p[7])) ** 2
                + p[3] * (p[2] + p[6])
            )
        )
        if determinant_certificate != 0:
            raise AssertionError(determinant_certificate)
        if q_slack != p[4] * (p[2] + p[7]):
            raise AssertionError(q_slack)
        expected_e3_slack = p[4] * (
            (sp.sqrt(p[1] * p[2]) - sign_product * sp.sqrt(p[6] * p[7])) ** 2
            + p[2] * p[3]
        )
        if sp.simplify(e3_slack - expected_e3_slack) != 0:
            raise AssertionError((e3_slack, expected_e3_slack))
        signed_branches.append(
            {
                "t=s0*s1": sign_product,
                "s2": -sign_product,
                "determinant_certificate": f"(sqrt(p1*p2){'-' if sign_product == 1 else '+'}sqrt(p6*p7))^2+p3*(p2+p6)",
                "q_slack": str(q_slack),
                "e3_slack": f"p4*((sqrt(p1*p2){'-' if sign_product == 1 else '+'}sqrt(p6*p7))^2+p2*p3)",
            }
        )

    # If heavy vertex 5 is selected, the two mixed holes vanish and the
    # all-light charge can have positive sign.  Use x=p1+p3, y=p2+p4+p7,
    # z=p6 and absorb the remaining radical by a square.
    x, y, z = p[1] + p[3], p[2] + p[4] + p[7], p[6]
    all_light_channel = sp.sqrt(p[1] * p[2] * p[6] * p[7])
    isolated_q_slack = sp.factor(
        x * y + x * z + y * z - q_light - 2 * all_light_channel
    )
    isolated_q_certificate = (
        (sp.sqrt(p[1] * p[7]) - sp.sqrt(p[2] * p[6])) ** 2
        + p[1] * p[6]
        + p[3] * p[7]
    )
    if sp.simplify(isolated_q_slack - isolated_q_certificate) != 0:
        raise AssertionError((isolated_q_slack, isolated_q_certificate))
    isolated_e3_slack = sp.factor(x * y * z - e3)
    if isolated_e3_slack != p[6] * (
        p[1] * p[2]
        + p[1] * p[4]
        + p[1] * p[7]
        + p[2] * p[3]
        + p[3] * p[7]
    ):
        raise AssertionError(isolated_e3_slack)

    result = {
        "experiment": "exact_signed_commuting_cycle_SCF_certificate",
        "representative_index": 44,
        "support_graph6": record["support_graph6"],
        "weights": record["weights"],
        "cycles": [list(cycle) for cycle in cycles],
        "cycle_operator_relations": relation_signs,
        "sector_constraint": "s0*s1*s2=-1",
        "mixed_cycle_block": {
            "heavy_pair": [0, 8],
            "diagonals": [str(diagonal_zero), str(diagonal_eight)],
            "remaining_light_mass": str(remaining),
            "branches": signed_branches,
        },
        "isolated_heavy_branch": {
            "heavy_vertex": 5,
            "aggregates": {"x": str(x), "y": str(y), "z": str(z)},
            "q_slack": "(sqrt(p1*p7)-sqrt(p2*p6))^2+p1*p6+p3*p7",
            "e3_slack": str(isolated_e3_slack),
        },
        "consequence": "every allowed symmetry sector and heavy branch reduces to the proved three-variable fixed-L envelope",
        "exact_beta": 1.5,
        "proof_status": "exact_symbolic_certificate_passed",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("experiment", "exact_beta", "proof_status")}, indent=2))


if __name__ == "__main__":
    main()
