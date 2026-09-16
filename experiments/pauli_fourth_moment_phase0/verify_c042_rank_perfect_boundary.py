"""Independent standard-library verifier for the frozen C042 record."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / "results" / "pauli_fourth_moment_phase0" / "c042_rank_perfect_boundary.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode_graph6(code: str) -> list[int]:
    raw = code.encode("ascii")
    assert raw and raw[0] != 126, "only graph6 orders below 63 are expected"
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


def edges(adjacency: list[int]) -> list[tuple[int, int]]:
    return [(i, j) for i in range(len(adjacency)) for j in range(i + 1, len(adjacency)) if adjacency[i] >> j & 1]


def connected(adjacency: list[int]) -> bool:
    if not adjacency:
        return False
    reached = 1
    frontier = 1
    while frontier:
        vertex = (frontier & -frontier).bit_length() - 1
        frontier &= frontier - 1
        new = adjacency[vertex] & ~reached
        reached |= new
        frontier |= new
    return reached == (1 << len(adjacency)) - 1


def clique(adjacency: list[int], mask: int) -> bool:
    vertices = [i for i in range(len(adjacency)) if mask >> i & 1]
    return all(adjacency[left] >> right & 1 for left, right in itertools.combinations(vertices, 2))


def bipartite_complement_neighborhood(adjacency: list[int], vertex: int) -> bool:
    neighborhood = adjacency[vertex]
    colors = {}
    for start in range(len(adjacency)):
        if not (neighborhood >> start & 1) or start in colors:
            continue
        colors[start] = 0
        queue = [start]
        while queue:
            current = queue.pop()
            for other in range(len(adjacency)):
                if other == current or not (neighborhood >> other & 1):
                    continue
                complement_edge = not (adjacency[current] >> other & 1)
                if not complement_edge:
                    continue
                if other not in colors:
                    colors[other] = 1 - colors[current]
                    queue.append(other)
                elif colors[other] == colors[current]:
                    return False
    return True


def quasi_line(adjacency: list[int]) -> bool:
    return all(bipartite_complement_neighborhood(adjacency, vertex) for vertex in range(len(adjacency)))


def verify_simplicial_clique(adjacency: list[int], vertices: list[int]) -> None:
    selected = sum(1 << vertex for vertex in vertices)
    assert selected and clique(adjacency, selected)
    for vertex in vertices:
        assert clique(adjacency, adjacency[vertex] & ~selected)


def krausz_line_graph(adjacency: list[int]) -> bool:
    graph_edges = edges(adjacency)
    edge_index = {edge: index for index, edge in enumerate(graph_edges)}
    candidates = []
    for mask in range(3, 1 << len(adjacency)):
        if mask.bit_count() < 2 or not clique(adjacency, mask):
            continue
        covered = 0
        for left, right in itertools.combinations([i for i in range(len(adjacency)) if mask >> i & 1], 2):
            covered |= 1 << edge_index[(left, right)]
        candidates.append((mask, covered))
    by_edge = [[] for _ in graph_edges]
    for mask, covered in candidates:
        for index in range(len(graph_edges)):
            if covered >> index & 1:
                by_edge[index].append((mask, covered))
    target = (1 << len(graph_edges)) - 1

    def search(covered: int, memberships: list[int]) -> bool:
        if covered == target:
            return True
        edge = next(index for index in range(len(graph_edges)) if not (covered >> index & 1))
        for mask, addition in by_edge[edge]:
            if addition & covered:
                continue
            vertices = [i for i in range(len(adjacency)) if mask >> i & 1]
            if any(memberships[i] >= 2 for i in vertices):
                continue
            updated = memberships[:]
            for i in vertices:
                updated[i] += 1
            if search(covered | addition, updated):
                return True
        return False

    return search(0, [0] * len(adjacency))


def stable_masks(adjacency: list[int]) -> list[int]:
    return [mask for mask in range(1 << len(adjacency)) if all(not (mask >> i & 1 and mask >> j & 1) for i, j in edges(adjacency))]


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


def verify_rank_facet(adjacency: list[int], masks: list[int], facet: dict) -> None:
    support = facet["support_mask"]
    alpha = max((mask & support).bit_count() for mask in masks)
    assert alpha == facet["alpha"]
    roots = [mask for mask in masks if (mask & support).bit_count() == alpha]
    assert len(roots) == facet["roots"]
    rows = [[1] + [(mask >> index) & 1 for index in range(len(adjacency))] for mask in roots]
    assert exact_rank(rows) == len(adjacency)


def enumerate_rank_facets(adjacency: list[int], masks: list[int]) -> list[dict]:
    output = []
    for support in range(1, 1 << len(adjacency)):
        alpha = max((mask & support).bit_count() for mask in masks)
        roots = [mask for mask in masks if (mask & support).bit_count() == alpha]
        rows = [[1] + [(mask >> index) & 1 for index in range(len(adjacency))] for mask in roots]
        if exact_rank(rows) == len(adjacency):
            output.append({"support_mask": support, "alpha": alpha, "roots": len(roots)})
    return output


def verify(payload: dict, root: Path = ROOT) -> dict:
    assert payload["experiment"] == "C042_rank_perfect_boundary"
    assert payload["scope"]["proved"] == [
        "SCF intersect rank-perfect implies hbar-perfect",
        "SCF semi-line corollary",
        "strict finite separation from line and h-perfect classes",
    ]
    assert "all SCF quasi-line graphs are rank-perfect" in payload["scope"]["not_proved"]
    for item in payload["upstream"].values():
        path = root / item["path"]
        assert sha256(path) == item["sha256"]
    for name, expected in payload["artifacts"].items():
        assert sha256(root / name) == expected

    census = json.loads((root / payload["upstream"]["scf_order9_census"]["path"]).read_text(encoding="utf-8"))
    exact = json.loads((root / payload["upstream"]["exact_facet_census"]["path"]).read_text(encoding="utf-8"))
    exact_by_graph = {row["graph6"]: row for row in exact["records"]}
    classes = {"line": [0, 0], "quasi_line_non_line": [0, 0], "SCF_not_quasi_line": [0, 0]}
    for row in census["SCF_records"]:
        adjacency = decode_graph6(row["graph6"])
        quasi = quasi_line(adjacency)
        label = "line" if row["line_graph"] else ("quasi_line_non_line" if quasi else "SCF_not_quasi_line")
        classes[label][0] += 1
        exact_row = exact_by_graph.get(row["graph6"])
        classes[label][1] += int(exact_row is not None and bool(exact_row["nonrank_facets"]))
    expected_classes = {row["class"]: [row["graphs"], row["graphs_with_nonrank_facets"]] for row in payload["order9"]["classes"]}
    assert classes == expected_classes
    assert classes == {"line": [710, 0], "quasi_line_non_line": [3048, 0], "SCF_not_quasi_line": [550, 550]}

    witness = payload["strict_witness"]
    adjacency = decode_graph6(witness["graph6"])
    assert connected(adjacency) and quasi_line(adjacency)
    assert not krausz_line_graph(adjacency)
    for candidate in witness["simplicial_cliques"]:
        verify_simplicial_clique(adjacency, candidate)
    masks = stable_masks(adjacency)
    assert len(masks) == witness["stable_sets"]
    facets = enumerate_rank_facets(adjacency, masks)
    assert len(facets) == witness["rank_facet_count_excluding_nonnegativity"]
    assert len(facets) + len(adjacency) == witness["exact_facets"]
    special = witness["not_hperfect_facet"]
    verify_rank_facet(adjacency, masks, special)
    support = special["support_mask"]
    assert not clique(adjacency, support)
    support_vertices = [i for i in range(len(adjacency)) if support >> i & 1]
    support_degrees = [sum(1 for j in support_vertices if adjacency[i] >> j & 1) for i in support_vertices]
    assert not (len(support_vertices) >= 5 and len(support_vertices) % 2 == 1 and all(degree == 2 for degree in support_degrees))

    samples = payload["sampled_circular_arc_stress"]
    assert len(samples["records"]) == samples["graphs"] == 60
    for row in samples["records"]:
        adjacency = decode_graph6(row["graph6"])
        assert connected(adjacency) and quasi_line(adjacency) and not krausz_line_graph(adjacency)
        masks = stable_masks(adjacency)
        assert len(masks) == row["stable_sets"] <= 120
        assert max(mask.bit_count() for mask in masks) == row["alpha"] >= 3
        assert row["nonrank_facets"] == 0 and not row["nonrank_candidates"]
        assert len(row["rank_facet_certificates"]) == row["rank_facets"]
        for facet in row["rank_facet_certificates"]:
            verify_rank_facet(adjacency, masks, facet)

    assert payload["web_stress"] == {"orders": [5, 60], "cases": 868, "SCF_cases": 112, "SCF_outside_cycles_or_alpha_le_2": 0}
    return {
        "status": "C042_verified",
        "order9_SCF": census["SCF_graphs"],
        "quasi_line_non_line": classes["quasi_line_non_line"][0],
        "strict_witness": witness["graph6"],
        "sampled_graphs": samples["graphs"],
        "stronger_conjecture_proved": False,
    }


def main() -> None:
    payload = json.loads(RESULT.read_text(encoding="utf-8"))
    print(json.dumps(verify(payload), indent=2))


if __name__ == "__main__":
    main()
