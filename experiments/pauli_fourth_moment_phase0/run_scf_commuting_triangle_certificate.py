"""Exact spectral certificate for residual SCF type 26 (graph6 HEhutx~)."""

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
        row for row in source["residual_atoms"] if row["representative_index"] == 26
    )
    graph = nx.from_graph6_bytes(record["support_graph6"].encode())
    if record["support_graph6"] != "HEhutx~":
        raise AssertionError(record["support_graph6"])
    cycles = chordless_four_cycles(graph)
    expected_cycles = [(0, 8, 3, 4), (0, 8, 6, 7), (3, 4, 6, 7)]
    if cycles != expected_cycles:
        raise AssertionError(cycles)
    relations = []
    for left, right in itertools.combinations(range(3), 2):
        product = multiply_words(graph, cycles[left], cycles[right])
        reverse = multiply_words(graph, cycles[right], cycles[left])
        third = 3 - left - right
        if product != reverse or product != (tuple(sorted(cycles[third])), 1):
            raise AssertionError((left, right, product, reverse))
        relations.append({"left": left, "right": right, "product": third, "sign": 1})

    p = sp.symbols("p0:9", nonnegative=True)
    light = [0, 1, 2, 4, 6]
    heavy = [3, 5, 7, 8]
    light_sum = sum(p[index] for index in light)
    q_light = p[0] * p[1] + p[0] * p[2] + p[1] * p[2] + p[1] * p[4] + p[2] * p[6]
    e3 = p[0] * p[1] * p[2]

    # In the all-positive cycle sector the non-isolated heavy vertices
    # {3,7,8} give this real symmetric matrix.  It is PSD by the displayed
    # diagonal-plus-rank-one factorization.
    matrix = sp.Matrix(
        [
            [p[2] + p[4], sp.sqrt(p[4] * p[6]), sp.sqrt(p[0] * p[4])],
            [sp.sqrt(p[4] * p[6]), p[1] + p[6], sp.sqrt(p[0] * p[6])],
            [sp.sqrt(p[0] * p[4]), sp.sqrt(p[0] * p[6]), p[0]],
        ]
    )
    vector = sp.Matrix([sp.sqrt(p[4]), sp.sqrt(p[6]), sp.sqrt(p[0])])
    decomposition = sp.diag(p[2], p[1], 0) + vector * vector.T
    if any(sp.simplify(value) != 0 for value in matrix - decomposition):
        raise AssertionError(matrix - decomposition)
    trace = sp.factor(sp.trace(matrix))
    second = sp.factor(
        sum(matrix.extract(pair, pair).det() for pair in itertools.combinations(range(3), 2))
    )
    determinant = sp.factor(matrix.det())
    if trace != light_sum or second != q_light or determinant != e3:
        raise AssertionError((trace, second, determinant))

    # Heavy vertex 5 is the only scalar branch.  Its non-neighbour mass is
    # y=p0+p4+p6 and the two remaining light aggregates are x=p1,z=p2.
    x, y, z = p[1], p[0] + p[4] + p[6], p[2]
    q_slack = sp.factor(x * y + x * z + y * z - q_light)
    e3_slack = sp.factor(x * y * z - e3)
    if q_slack != p[1] * p[6] + p[2] * p[4]:
        raise AssertionError(q_slack)
    if e3_slack != p[1] * p[2] * (p[4] + p[6]):
        raise AssertionError(e3_slack)

    result = {
        "experiment": "exact_commuting_cycle_triangle_SCF_certificate",
        "representative_index": 26,
        "support_graph6": record["support_graph6"],
        "weights": record["weights"],
        "light_vertices": light,
        "heavy_vertices": heavy,
        "cycles": [list(cycle) for cycle in cycles],
        "cycle_operator_relations": relations,
        "allowed_extremal_sector": [1, 1, 1],
        "heavy_spectral_block": {
            "vertices": [3, 7, 8],
            "factorization": "diag(p2,p1,0)+u*u^T, u=(sqrt(p4),sqrt(p6),sqrt(p0))",
            "trace": str(trace),
            "second_elementary_coefficient": str(second),
            "determinant": str(determinant),
            "identification": "the three nonnegative eigenvalues sum to L and have e2=q_light, e3=p0*p1*p2",
        },
        "isolated_heavy_branch": {
            "heavy_vertex": 5,
            "aggregates": {"x": str(x), "y": str(y), "z": str(z)},
            "q_slack": str(q_slack),
            "e3_slack": str(e3_slack),
        },
        "consequence": "every heavy branch is bounded by the proved three-variable fixed-L envelope",
        "exact_beta": 1.5,
        "proof_status": "exact_symbolic_certificate_passed",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("experiment", "exact_beta", "proof_status")}, indent=2))


if __name__ == "__main__":
    main()
