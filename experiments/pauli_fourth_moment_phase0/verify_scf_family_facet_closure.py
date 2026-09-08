"""C006 independent polyhedral completeness: Fraction edge clipping.

No cdd, graph library, floating-point arithmetic, symbolic algebra or solver.
The vertex set starts as the complete cube, not the claimed STAB vertices.
Clipping a full-dimensional bounded polytope keeps old feasible vertices
and adds intersections with precisely its crossing edges. Two vertices
share an edge iff their common active constraint normals have rank n-1.
"""
from collections import Counter
from fractions import Fraction as F
import hashlib
import itertools
import json
from math import gcd, comb
from pathlib import Path
import time
from verify_scf_generalization import graph_edges, stable, check_scf
from verify_scf_rectangular_gram_bridge import exact_rank

DATA = Path(__file__).resolve().parents[2]/'results'/'pauli_fourth_moment_phase0'


def value(row, point):
    return row[0]+sum(a*x for a, x in zip(row[1:], point) if a)


def cube_clip(n, facets, seconds_limit=300, max_dimension=10, sparse_first=False,
              indexed_edges=False):
    """Enumerate the whole intersection, without using a candidate vertex set."""
    started = time.monotonic()
    assert 1 <= n <= max_dimension <= 15  # C012 explicitly registers dimension 15.
    constraints = [tuple([0]+[int(j == i) for j in range(n)]) for i in range(n)]
    constraints += [tuple([1]+[-int(j == i) for j in range(n)]) for i in range(n)]
    vertices = {tuple(map(F, point)): sum(1 << (i+n*int(x)) for i, x in enumerate(point))
                for point in itertools.product((0, 1), repeat=n)}
    rank_cache = {}
    trace = []
    # Cut order changes intermediates only, not the exact intersection.
    # C012 explicitly uses sparse cuts first to reduce the initial cube.
    direction = 1 if sparse_first else -1
    for original_index, raw in sorted(enumerate(facets),
                                      key=lambda t: (direction*sum(bool(x) for x in t[1][1:]), t[1])):
        assert time.monotonic()-started <= seconds_limit, 'exact clipping time limit exceeded'
        row = tuple(raw)
        assert len(row) == n+1
        if row in constraints:
            continue
        slacks = {v: value(row, v) for v in vertices}
        positive = [v for v in vertices if slacks[v] > 0]
        negative = [v for v in vertices if slacks[v] < 0]
        assert positive, 'each cut must retain a full-dimensional polytope'
        bit = 1 << len(constraints)
        kept = {v: active | (bit if slacks[v] == 0 else 0)
                for v, active in vertices.items() if slacks[v] >= 0}
        added = set()
        # Exact candidate index, not a geometric approximation: an edge
        # needs >= n-1 common active rows. Enumerate those subsets when
        # cheap; on highly degenerate vertices retain the old full scan.
        postings = [0]*len(constraints)
        if indexed_edges:
            for j, v in enumerate(positive):
                mask = vertices[v]
                while mask:
                    low = mask & -mask
                    postings[low.bit_length()-1] |= 1 << j
                    mask ^= low
        for u in negative:
            assert time.monotonic()-started <= seconds_limit, 'exact clipping time limit exceeded'
            active = vertices[u]
            candidates = positive
            if indexed_edges and comb(active.bit_count(), n-1) <= 128:
                indices = [i for i in range(len(constraints)) if active >> i & 1]
                found = 0
                for subset in itertools.combinations(indices, n-1):
                    matches = (1 << len(positive))-1
                    for i in subset:
                        matches &= postings[i]
                        if not matches:
                            break
                    found |= matches
                candidates = []
                while found:
                    low = found & -found
                    candidates.append(positive[low.bit_length()-1])
                    found ^= low
            for v in candidates:
                common = vertices[u] & vertices[v]
                if common.bit_count() < n-1:
                    continue
                if common not in rank_cache:
                    rank_cache[common] = exact_rank([r[1:] for i, r in enumerate(constraints)
                                                    if common >> i & 1], n)
                rank = rank_cache[common]
                assert rank < n  # Distinct points cannot share n independent equalities.
                if rank != n-1:
                    continue
                t = -slacks[u]/(slacks[v]-slacks[u])
                point = tuple(x+t*(y-x) for x, y in zip(u, v))
                assert 0 < t < 1 and value(row, point) == 0
                # All old inequalities hold along the edge. Recompute all
                # equalities rather than assuming an edge is simple.
                old_slacks = [value(r, point) for r in constraints]
                assert min(old_slacks) >= 0
                active = bit | sum(1 << i for i, s in enumerate(old_slacks) if s == 0)
                if point in kept:
                    assert kept[point] == active
                kept[point] = active
                added.add(point)
        trace.append({'facet_index': original_index, 'vertices_before': len(vertices),
                      'removed': len(negative), 'added': len(added), 'vertices_after': len(kept)})
        constraints.append(row)
        vertices = kept
    assert all(all(value(row, point) >= 0 for row in facets) for point in vertices)
    return set(vertices), trace


def componentwise_scf(n, edges, support):
    remaining = set(support)
    while remaining:
        component = {min(remaining)}
        while True:
            expanded = component | {v for v in remaining
                                     if any(tuple(sorted((u, v))) in edges for u in component)}
            if expanded == component:
                break
            component = expanded
        nodes = sorted(component)
        index = {v: i for i, v in enumerate(nodes)}
        local = {(index[i], index[j]) for i, j in edges if i in component and j in component}
        check_scf(len(nodes), local)
        remaining -= component
    return True


def verify_polytope(record, max_dimension=10, sparse_first=False, indexed_edges=False):
    n, edges = graph_edges(record['graph6'])
    masks = [m for m in range(1 << n) if stable(m, edges)]
    assert masks == record['stable_masks']
    points = {tuple(F(m >> i & 1) for i in range(n)) for m in masks}
    facets = record['facets_b_plus_ax']
    assert len({tuple(row) for row in facets}) == len(facets), 'duplicate facet'
    assert facets == sorted(facets)
    for row in facets:
        assert len(row) == n+1 and all(type(x) is int for x in row) and gcd(*row) == 1
        slacks = [value(row, p) for p in points]
        assert min(slacks) == 0 and max(slacks) > 0, 'invalid supporting hyperplane'
        roots = [p for p in points if value(row, p) == 0]
        assert exact_rank([[1]+list(p) for p in roots], n+1) == n, 'not a facet'
    # The listed H-system, not only H intersected with an external cube,
    # implies every cube inequality. Positivity plus a row with w_i=b>0
    # and w_j>=0 implies x_i<=1. This also explicitly proves boundedness.
    for i in range(n):
        lower = [0]+[int(j == i) for j in range(n)]
        assert lower in facets, 'missing nonnegativity'
        assert any(row[0] > 0 and row[i+1] == -row[0]
                   and all(x <= 0 for x in row[1:]) for row in facets), 'unproved cube upper bound'
    actual, trace = cube_clip(n, facets, max_dimension=max_dimension, sparse_first=sparse_first,
                              indexed_edges=indexed_edges)
    extras, missing = actual-points, points-actual
    assert not extras and not missing, ('polyhedral incompleteness',
                                       [list(map(str, p)) for p in sorted(extras)[:3]], len(missing))
    return {'vertices': len(points), 'facets': len(facets), 'clipping_steps': trace,
            'complete_exact_independent_H_V_check': True}


def verify(report):
    raw = (DATA/'scf_rectangular_gram_bridge.json').read_bytes().replace(b'\r\n', b'\n')
    assert hashlib.sha256(raw).hexdigest() == report['C005_source_sha256']
    bridge = json.loads(raw)
    known = bridge['records'][1]
    target = report['target']
    assert target['graph6'] == known['graph6'] and known['m'] == 1
    assert report['source_frontier_graph6'] == bridge['target']['graph6'] == 'ICXmtizr_'
    n, edges = graph_edges(target['graph6'])
    assert n == 10
    check_scf(n, edges)
    result = verify_polytope(target)
    facets = target['facets_b_plus_ax']
    routes = target['proof_routes']
    assert [r['facet_index'] for r in routes] == list(range(len(facets)))
    for row, route in zip(facets, routes):
        weights = [-a for a in row[1:]]
        support = [i for i, w in enumerate(weights) if w > 0]
        assert route['support'] == support
        if not support:
            assert route['route'] == 'nonnegativity'
            assert row[0] == 0 and sorted(weights) == [-1]+[0]*(n-1)
            continue
        assert min(weights) >= 0
        componentwise_scf(n, edges, support)
        assert route['support_componentwise_SCF']
        if route['route'] == 'SCF_rank':
            assert len(set(weights[i] for i in support)) == 1
        elif route['route'] == 'SCF_order9_all_weights':
            assert len(support) <= 9
        elif route['route'] == 'C005_rectangular_Gram':
            mapping = route['family_to_facet_automorphism']
            assert sorted(mapping) == list(range(n)) and row[0] == 3
            assert {tuple(sorted((mapping[i], mapping[j]))) for i, j in edges} == edges
            assert all(known['weights'][i] == weights[mapping[i]] for i in range(n))
        else:
            raise AssertionError(('uncovered quantum facet', row))
    assert report['all_facets_have_proof_route']
    assert not report['family_all_m_all_weights_claim'] and not report['unrestricted_SCF_theorem']
    assert not report['A_star_confirmed']
    assert len(report['controls']) == 2
    # Bind the controls to the declared path P4 and odd cycle C5.
    for record, size, closing in zip(report['controls'], (4, 5), (False, True)):
        cn, ce = graph_edges(record['graph6'])
        expected = {(i, i+1) for i in range(size-1)} | ({(0, size-1)} if closing else set())
        assert cn == size and ce == expected
        verify_polytope(record)
    negative = report['missing_facet_control']
    removed = negative['removed_facet_index']
    assert routes[removed]['route'] == 'C005_rectangular_Gram'
    incomplete = [row for i, row in enumerate(facets) if i != removed]
    actual, _ = cube_clip(n, incomplete)
    expected = {tuple(F(m >> i & 1) for i in range(n)) for m in target['stable_masks']}
    extra = actual-expected
    assert expected <= actual and extra
    assert extra == {tuple(map(F, row)) for row in negative['extra_vertices']}
    assert not negative['quantum_state_claim']
    assert all(value(facets[removed], point) < 0 for point in extra)
    result.update({'status': 'G1_all_weight_closure_exactly_verified_using_C005_and_order9_theorems',
                   'routes': dict(Counter(r['route'] for r in routes)),
                   'target_graph6': target['graph6'], 'frontier_graph6': report['source_frontier_graph6'],
                   'missing_facet_control_extra_vertices': len(extra),
                   'all_m_all_weights_proved': False, 'unrestricted_SCF_theorem': False})
    return result


if __name__ == '__main__':
    if not __debug__: raise RuntimeError('Assertions required.')
    print(json.dumps(verify(json.loads((DATA/'scf_family_facet_closure.json').read_text()))))
