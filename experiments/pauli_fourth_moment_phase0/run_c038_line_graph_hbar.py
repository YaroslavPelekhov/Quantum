"""C038: stress the sharp line-graph/matching nuclear-norm theorem."""
from __future__ import annotations

import hashlib
import itertools as it
import json
from functools import cache
from pathlib import Path

import networkx as nx
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "results" / "pauli_fourth_moment_phase0"


def matching_value(graph: nx.Graph, weights: dict[tuple[int, int], int]) -> int:
    """Exact maximum-weight matching by subset recursion (atlas roots only)."""
    vertices = tuple(sorted(graph))

    @cache
    def solve(remaining: tuple[int, ...]) -> int:
        if not remaining:
            return 0
        u = remaining[0]
        tail = remaining[1:]
        best = solve(tail)
        for j, v in enumerate(tail):
            e = tuple(sorted((u, v)))
            if graph.has_edge(*e):
                best = max(best, weights[e] + solve(tail[:j] + tail[j + 1 :]))
        return best

    return solve(vertices)


def polar_witness(a: np.ndarray) -> np.ndarray:
    u, _, vt = np.linalg.svd(a, full_matrices=True)
    q = u @ vt
    return (q - q.T) / 2


def direct_majorana_norm(a: np.ndarray) -> float:
    """Dense Jordan--Wigner check, used only for roots of order at most five."""
    n = a.shape[0]
    qubits = (n + 1) // 2
    identity = np.eye(2, dtype=complex)
    pauli_x = np.array([[0, 1], [1, 0]], dtype=complex)
    pauli_y = np.array([[0, -1j], [1j, 0]], dtype=complex)
    pauli_z = np.array([[1, 0], [0, -1]], dtype=complex)

    def product(factors: list[np.ndarray]) -> np.ndarray:
        value = np.array([[1]], dtype=complex)
        for factor in factors:
            value = np.kron(value, factor)
        return value

    majoranas = []
    for index in range(n):
        site, parity = divmod(index, 2)
        factors = [pauli_z] * site
        factors.append(pauli_x if parity == 0 else pauli_y)
        factors.extend([identity] * (qubits - site - 1))
        majoranas.append(product(factors))
    hamiltonian = np.zeros((2**qubits, 2**qubits), dtype=complex)
    for u in range(n):
        for v in range(u + 1, n):
            if a[u, v]:
                hamiltonian += a[u, v] * (1j * majoranas[u] @ majoranas[v])
    assert np.allclose(hamiltonian, hamiltonian.conj().T, atol=1e-12)
    return float(np.max(np.abs(np.linalg.eigvalsh(hamiltonian))))


def audit_root(graph: nx.Graph, rng: np.random.Generator) -> dict:
    graph = nx.convert_node_labels_to_integers(graph, ordering="sorted")
    edges = [tuple(sorted(e)) for e in sorted(graph.edges())]
    weights = {e: int(rng.integers(1, 8)) for e in edges}
    coefficients = {e: int(rng.integers(-5, 6)) for e in edges}
    if not any(coefficients.values()):
        coefficients[edges[0]] = 1
    n = len(graph)
    a = np.zeros((n, n), dtype=float)
    for (u, v), value in coefficients.items():
        a[u, v] = value
        a[v, u] = -value
    q = polar_witness(a)
    singular = np.linalg.svd(a, compute_uv=False)
    half_nuclear = float(singular.sum() / 2)
    dense_majorana = direct_majorana_norm(a) if n <= 5 else None
    pairing = float(sum(coefficients[e] * q[e] for e in edges))
    degree_max = max(
        sum(q[min(v, u), max(v, u)] ** 2 for u in graph.neighbors(v))
        for v in graph
    )
    odd_max_excess = -1.0
    for size in range(3, n + 1, 2):
        for subset in it.combinations(range(n), size):
            total = sum(q[u, v] ** 2 for u, v in edges if u in subset and v in subset)
            odd_max_excess = max(odd_max_excess, total - (size - 1) / 2)
    matching = matching_value(graph, weights)
    coefficient_norm = sum(coefficients[e] ** 2 / weights[e] for e in edges)
    rhs = matching * coefficient_norm
    assert abs(pairing - half_nuclear) <= 2e-8 * max(1.0, half_nuclear)
    assert degree_max <= 1 + 2e-10
    assert odd_max_excess <= 2e-10
    assert half_nuclear**2 <= rhs + 2e-8 * max(1.0, rhs)
    if dense_majorana is not None:
        assert abs(dense_majorana - half_nuclear) <= 2e-10 * max(1.0, half_nuclear)
    return {
        "graph6": nx.to_graph6_bytes(graph, header=False).decode().strip(),
        "vertices": n,
        "edges": len(edges),
        "matching_value": matching,
        "half_nuclear": half_nuclear,
        "weighted_coefficient_norm": coefficient_norm,
        "ratio_to_bound": half_nuclear**2 / rhs if rhs else 0.0,
        "polar_pairing_error": abs(pairing - half_nuclear),
        "direct_majorana_norm_error": (
            abs(dense_majorana - half_nuclear) if dense_majorana is not None else None
        ),
        "max_degree_excess": degree_max - 1,
        "max_odd_set_excess": odd_max_excess,
    }


def strictness_witness(order: int) -> dict:
    assert order >= 5 and order % 2 == 1
    k = (order - 1) // 2
    edge_count = order * (order - 1) // 2
    return {
        "root": f"K{order}",
        "root_order": order,
        "line_graph_order": edge_count,
        "coordinate": f"1/{order - 1}",
        "star_value": "1",
        "triangle_value": f"3/{order - 1}",
        "matching_bound": k,
        "total_value": f"{order}/2",
        "h_relaxation_gap": "1/2",
        "hbar_perfect_by_C038": True,
    }


def main() -> dict:
    rng = np.random.default_rng(20260910)
    records = []
    for graph in nx.graph_atlas_g():
        if graph.number_of_edges():
            records.append(audit_root(graph, rng))
    theorem_note = Path(__file__).with_name("LINE_GRAPH_HBAR_THEOREM_C038.md")
    report = {
        "experiment": "C038_line_graph_hbar_matrix_audit",
        "seed": 20260910,
        "atlas_nonempty_roots": len(records),
        "max_root_order": max(r["vertices"] for r in records),
        "max_ratio_to_proved_bound": max(r["ratio_to_bound"] for r in records),
        "max_polar_pairing_error": max(r["polar_pairing_error"] for r in records),
        "direct_majorana_norm_cases": sum(
            r["direct_majorana_norm_error"] is not None for r in records
        ),
        "max_direct_majorana_norm_error": max(
            r["direct_majorana_norm_error"]
            for r in records
            if r["direct_majorana_norm_error"] is not None
        ),
        "max_degree_excess": max(r["max_degree_excess"] for r in records),
        "max_odd_set_excess": max(r["max_odd_set_excess"] for r in records),
        "strict_hperfect_separations": [strictness_witness(n) for n in (5, 7, 9)],
        "theorem": "beta(L(R),w)=alpha(L(R),w)=maximum_weight_matching(R,w)",
        "theorem_note_sha256": hashlib.sha256(theorem_note.read_bytes()).hexdigest(),
        "arbitrary_size_theorem": True,
        "unrestricted_SCF_theorem": False,
        "A_star_confirmed": False,
        "records": records,
    }
    return report


if __name__ == "__main__":
    output = DATA / "c038_line_graph_hbar.json"
    if output.exists():
        raise FileExistsError(output)
    result = main()
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({k: v for k, v in result.items() if k != "records"}, indent=2))
