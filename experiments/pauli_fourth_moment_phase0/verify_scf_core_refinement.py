"""C007 fixed core and refinement certificate, standard library only."""
from collections import deque
from fractions import Fraction as F
import hashlib
import itertools
import json
from math import gcd
from pathlib import Path
from verify_scf_generalization import graph_edges, stable
from verify_scf_rectangular_gram_bridge import exact_rank
from verify_scf_family_facet_closure import cube_clip, value

DATA = Path(__file__).resolve().parents[2]/'results'/'pauli_fourth_moment_phase0'


def lifted_description(m, base_facets):
    """Uniform explicit H-system, not a fit to independently found facets."""
    assert isinstance(m, int) and m >= 0
    n = 2*m+8
    groups = [[0], [1], [2*m+2], [2*j for j in range(1, m+1)]+[2*m+3],
              [2*j+1 for j in range(1, m+1)]+[2*m+4], [n-3], [n-2], [n-1]]
    output = set()
    for row in base_facets:
        if row == [0]+[int(i == 3) for i in range(8)] or row == [0]+[int(i == 4) for i in range(8)]:
            continue
        lifted = [row[0]]+[0]*n
        for coeff, group in zip(row[1:], groups):
            for v in group:
                lifted[v+1] = coeff
        output.add(tuple(lifted))
    for v in groups[3]+groups[4]:
        output.add(tuple([0]+[int(i == v) for i in range(n)]))
    for j in range(1, m+1):
        pair = {2*j, 2*j+1}
        output.add(tuple([1]+[-int(i in pair | {n-1}) for i in range(n)]))
        core = {0, 1, 2*m+2, n-3, n-2, n-1}
        output.add(tuple([2]+[-int(i in pair | core) for i in range(n)]))
    return list(map(list, sorted(output)))


def refine_transport(a, b, z):
    """Exact boundary controls: refine aggregate flags, forbidding equal labels.

Last entry of a/b is a PRIVATE label U/V (their pair is allowed). Earlier
entries are matched labels Aj/Bj. A final absent label is added internally.
The returned table excludes the absent/absent cell already fixed by T.
"""
    a, b, z = list(map(F, a)), list(map(F, b)), F(z)
    assert len(a) == len(b) and len(a) >= 1 and min(a+b) >= 0
    A, B = sum(a), sum(b)
    assert 0 <= z <= min(A, B) and A+B-z <= 1
    T = A+B-z
    rows, cols = a+[T-A], b+[T-B]
    k = len(rows)
    forbidden = {(i, i) for i in range(k-2)} | {(k-1, k-1)}
    feasible = all(rows[i]+cols[j] <= T for i, j in forbidden)
    source, sink = 2*k, 2*k+1
    capacity = {}
    for i, x in enumerate(rows): capacity[source, i] = x
    for j, x in enumerate(cols): capacity[k+j, sink] = x
    for i in range(k):
        for j in range(k):
            if (i, j) not in forbidden: capacity[i, k+j] = T
    residual = dict(capacity)
    for u, v in list(capacity): residual[v, u] = F(0)
    flow = F(0)
    while True:
        parent = {source: None}
        queue = deque([source])
        while queue and sink not in parent:
            u = queue.popleft()
            for v in range(sink+1):
                if v not in parent and residual.get((u, v), 0) > 0:
                    parent[v] = u
                    queue.append(v)
        if sink not in parent: break
        v, path = sink, []
        while parent[v] is not None:
            u = parent[v]
            path.append((u, v))
            v = u
        amount = min(residual[u, v] for u, v in path)
        for u, v in path:
            residual[u, v] -= amount
            residual[v, u] += amount
        flow += amount
    assert (flow == T) == feasible  # Hall's reduced singleton conditions.
    if not feasible: return None
    table = [[capacity.get((i, k+j), 0)-residual.get((i, k+j), 0)
              for j in range(k)] for i in range(k)]
    assert all(sum(table[i]) == rows[i] for i in range(k))
    assert all(sum(table[i][j] for i in range(k)) == cols[j] for j in range(k))
    assert all(table[i][j] == 0 for i, j in forbidden)
    assert all(x >= 0 for row in table for x in row)
    assert sum(table[i][j] for i in range(k-1) for j in range(k-1)) == z
    return table


def verify(report):
    raw = (DATA/'scf_uniform_facet_gate.json').read_bytes().replace(b'\r\n', b'\n')
    assert hashlib.sha256(raw).hexdigest() == report['C007_gate_sha256']
    gate = json.loads(raw)
    base = gate['records'][0]
    assert report['graph6'] == base['graph6'] and base['m'] == 0
    assert report['core_names'] == ['A0', 'B0', 'Z', 'U', 'V', 'H0', 'H1', 'Hc']
    assert report['joint_event'] == ['U', 'V']
    n, edges = graph_edges(report['graph6'])
    assert n == 8
    masks = [m for m in range(1 << n) if stable(m, edges)]
    expected = {tuple([F(m >> i & 1) for i in range(n)]+[F(bool(m >> 3 & 1) and bool(m >> 4 & 1))]) for m in masks}
    assert len(expected) == len(report['points']) == 22
    assert expected == set(map(tuple, report['points']))
    assert exact_rank([[1]+list(p) for p in expected], 10) == 10
    facets = report['facets_b_plus_ax']
    assert facets == sorted(facets) and len({tuple(r) for r in facets}) == len(facets)
    for row in facets:
        assert len(row) == 10 and all(type(x) is int for x in row) and gcd(*row) == 1
        assert all(value(row, p) >= 0 for p in expected)
        roots = [p for p in expected if value(row, p) == 0]
        assert exact_rank([[1]+list(p) for p in roots], 10) == 9
    # We require completeness INSIDE the cube. The lifted joint event is
    # a probability, and the endpoint proof independently stays in [0,1].
    actual, _ = cube_clip(9, facets)
    assert actual == expected, 'incomplete lifted core polytope'
    lower = [row for row in facets if row[-1] > 0]
    specified = sorted([[0]+[0]*8+[1],
                        [1, 0, 0, 0, -1, -1, 0, 0, -1, 1],
                        [2]+[-1]*8+[1]])
    assert lower == report['lower_z_facets'] == specified
    # Uniform quantum premise: a supported independent triple in the
    # expanded graph exists iff the base support contains Z,U,V. Only the
    # C005 facet has all three; every other positive facet has alpha<=2.
    full = [3]+[-1]*5+[-2]*3
    for facet in base['facets_b_plus_ax']:
        if facet[0] > 0:
            has_triple = all(facet[i+1] < 0 for i in (2, 3, 4))
            assert has_triple == (facet == full)
    for row in gate['records']:
        assert lifted_description(row['m'], base['facets_b_plus_ax']) == row['facets_b_plus_ax']
    assert not report['unrestricted_SCF_theorem'] and not report['quantum_generic_gluing_claim']
    assert not report['A_star_confirmed']
    return {'status': 'exact_core_endpoint_and_uniform_description_templates_verified',
            'core_vertices': 22, 'lifted_dimension': 9, 'lifted_facets': len(facets),
            'exact_lower_z_facets': len(lower), 'finite_template_matches': 4,
            'unrestricted_SCF_theorem': False}


if __name__ == '__main__':
    if not __debug__: raise RuntimeError('Assertions required.')
    print(json.dumps(verify(json.loads((DATA/'scf_core_refinement.json').read_text()))))
