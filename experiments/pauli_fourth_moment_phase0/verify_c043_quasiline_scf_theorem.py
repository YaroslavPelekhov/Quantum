"""Independent standard-library verifier for the frozen C043 theorem record."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import itertools
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / "results" / "pauli_fourth_moment_phase0" / "c043_quasiline_scf_falsification.json"
SOURCE = ROOT / "experiments" / "pauli_fourth_moment_phase0" / "run_c043_quasiline_scf_falsification.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode_graph6(code: str) -> list[int]:
    raw = code.encode("ascii")
    assert raw and raw[0] != 126
    order = raw[0] - 63
    bits = []
    for value in raw[1:]:
        value -= 63
        bits.extend((value >> shift) & 1 for shift in range(5, -1, -1))
    adjacency = [0] * order
    cursor = 0
    for right in range(1, order):
        for left in range(right):
            if bits[cursor]:
                adjacency[left] |= 1 << right
                adjacency[right] |= 1 << left
            cursor += 1
    return adjacency


def stable_masks(adjacency: list[int]) -> list[int]:
    output = []

    def visit(available: int, chosen: int) -> None:
        if not available:
            output.append(chosen)
            return
        bit = available & -available
        vertex = bit.bit_length() - 1
        visit(available ^ bit, chosen)
        visit((available ^ bit) & ~adjacency[vertex], chosen | bit)

    visit((1 << len(adjacency)) - 1, 0)
    return output


def exact_rank(rows: list[list[int]]) -> int:
    matrix = [[Fraction(value) for value in row] for row in rows]
    rank = 0
    for column in range(len(matrix[0]) if matrix else 0):
        pivot = next((row for row in range(rank, len(matrix)) if matrix[row][column]), None)
        if pivot is None:
            continue
        matrix[rank], matrix[pivot] = matrix[pivot], matrix[rank]
        scale = matrix[rank][column]
        matrix[rank] = [value / scale for value in matrix[rank]]
        for row in range(len(matrix)):
            if row != rank and matrix[row][column]:
                scale = matrix[row][column]
                matrix[row] = [a - scale * b for a, b in zip(matrix[row], matrix[rank])]
        rank += 1
    return rank


def adjacent(order: int, p: int, left: int, right: int) -> bool:
    distance = abs(left - right)
    return left != right and min(distance, order - distance) < p


def verify_circulant_record(row: dict) -> None:
    order, p = row["order"], row["p"]
    assert order > 2 * p >= 4
    assert row["SCF"] == (p == 2)
    if p == 2:
        assert row["certificate"] == "edge_{0,1}_is_simplicial"
        return
    assert row["certificate"] == "local_witnesses_plus_nonlocal_three_arc_bound"
    checked = 0
    for span in range(p - 1):
        left = (-(p - span - 1)) % order
        right = span + 1
        assert adjacent(order, p, 0, left) and adjacent(order, p, 0, right)
        assert not adjacent(order, p, left, right)
        checked += 1
    for missing in range(1, p - 1):
        left = (-(p - missing)) % order
        assert adjacent(order, p, 0, left) and adjacent(order, p, 0, missing)
        assert not adjacent(order, p, left, missing)
        checked += 1
    assert adjacent(order, p, 1, order - 1) and adjacent(order, p, 1, p)
    assert not adjacent(order, p, order - 1, p)
    checked += 1
    assert row["local_clique_templates_checked"] == checked
    nonlocal_bound = max(0, 3 * p - order)
    assert row["nonlocal_clique_size_upper_bound"] == nonlocal_bound
    if order == 2 * p + 1:
        assert math.gcd(order, p) == 1
        assert row["nonlocal_certificate"] == "odd_antihole_has_no_simplicial_clique"
    else:
        assert nonlocal_bound <= p - 2
        assert 2 * p - 1 - nonlocal_bound > p
        assert row["nonlocal_certificate"] == "size_bound_below_p_minus_1"
    checked += 1
    assert checked == row["proof_templates_checked"]


def verify_positive_control(control: dict) -> None:
    adjacency = decode_graph6(control["graph6"])
    facet = control["facet"]
    family = facet["clique_masks"]
    p = facet["p"]
    remainder = len(family) % p
    high, low = p - remainder, p - remainder - 1
    coefficients = []
    for vertex in range(len(adjacency)):
        coverage = sum(mask >> vertex & 1 for mask in family)
        coefficients.append(high if coverage >= p else low if coverage == p - 1 else 0)
    assert coefficients == facet["coefficients"]
    assert len({value for value in coefficients if value > 0}) == 2
    rhs = high * (len(family) // p)
    assert rhs == facet["rhs"]
    masks = stable_masks(adjacency)
    values = [sum(coefficients[v] for v in range(len(adjacency)) if mask >> v & 1) for mask in masks]
    assert max(values) == rhs
    roots = [mask for mask, value in zip(masks, values) if value == rhs]
    rows = [[1] + [(mask >> v) & 1 for v in range(len(adjacency))] for mask in roots]
    assert len(masks) == facet["stable_sets"]
    assert len(roots) == facet["tight_stable_sets"]
    assert exact_rank(rows) == facet["exact_augmented_rank"] == len(adjacency)


def verify(payload: dict, root: Path = ROOT) -> dict:
    assert payload["experiment"] == "C043_quasiline_SCF_rank_perfect_theorem"
    assert payload["status"] == "theorem_proved_and_controls_passed"
    assert payload["conjecture_proved"] and not payload["conjecture_falsified"]
    assert payload["source_sha256"] == sha256(root / SOURCE.relative_to(ROOT))
    assert payload["analytic_result"]["theorem"] == "Every simplicial claw-free quasi-line graph is rank-perfect."
    assert payload["analytic_result"]["corollary"] == "Every simplicial claw-free quasi-line frustration graph is hbar-perfect."

    heredity = payload["heredity_audit"]
    assert heredity["graphs"] == heredity["deterministic_one_vertex_deletions"] == 4308
    assert heredity["quasi_line_graphs"] == 3758 and heredity["failures"] == 0
    census = json.loads((root / heredity["source"]).read_text(encoding="utf-8"))
    assert census["SCF_graphs"] == 4308 and len(census["SCF_records"]) == 4308

    audit = payload["circulant_obstruction_audit"]
    records = audit["records"]
    expected = [
        (order, p)
        for order in range(5, audit["max_order"] + 1)
        for p in range(2, (order - 1) // 2 + 1)
    ]
    assert [(row["order"], row["p"]) for row in records] == expected
    assert len(records) == audit["cases"]
    for row in records:
        verify_circulant_record(row)
    assert sum(row["SCF"] for row in records) == audit["p_equals_2_SCF_cases"]
    assert sum(not row["SCF"] for row in records) == audit["p_at_least_3_non_SCF_cases"]
    assert audit["mismatches"] == 0

    exact = payload["exact_small_circulant_audit"]
    assert exact["max_order"] == 18
    assert exact["parameter_cases"] == sum((order - 1) // 2 - 1 for order in range(5, 19))
    assert exact["cliques_enumerated"] > 0 and exact["nonlocal_cliques"] > 0
    assert exact["first_nonlocal_clique"] == {"order": 9, "p": 4, "clique": [0, 3, 6]}
    assert exact["max_nonlocal_bound_slack"] >= 0
    assert exact["simplicial_cliques_found"] > 0
    assert exact["boundary_mismatches"] == 0

    controls = payload["positive_controls"]
    assert controls["web_cases"] == controls["nonrank_webs_found"] == 1
    assert controls["SCF_nonrank_webs"] == 0
    verify_positive_control(controls["records"][0])
    assert not payload["punctured_web_attack"]["counterexamples"]
    assert not payload["random_proper_circular_arc_attack"]["counterexamples"]
    return {
        "status": "C043_verified",
        "theorem": payload["analytic_result"]["theorem"],
        "heredity_deletions": heredity["deterministic_one_vertex_deletions"],
        "circulant_cases": len(records),
        "positive_nonrank_controls": controls["nonrank_webs_found"],
        "random_CFI_controls": payload["random_proper_circular_arc_attack"]["graphs_tested"],
    }


def main() -> None:
    payload = json.loads(RESULT.read_text(encoding="utf-8"))
    print(json.dumps(verify(payload), indent=2))


if __name__ == "__main__":
    main()
