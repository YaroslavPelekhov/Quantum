"""Independent C008 integer structure and Fraction hull acceptance."""
from collections import Counter
import itertools as it
import json
from pathlib import Path
import time
from verify_scf_generalization import graph_edges, stable, check_scf
from verify_scf_family_facet_closure import verify_polytope, componentwise_scf

DATA = Path(__file__).resolve().parents[2]/'results'/'pauli_fourth_moment_phase0'


def edges_from_cells(cells, three_rows=False):
    cells = list(map(tuple, cells))
    assert cells == sorted(set(cells)) and all(0 <= r < 3 and c >= 0 for r, c in cells)
    k = len(cells)
    root_edges = [{r, 3+c} for r, c in cells]
    edges = {(i, j) for i, j in it.combinations(range(k), 2) if root_edges[i] & root_edges[j]}
    for h in range(3):
        for i, (r, c) in enumerate(cells):
            adjacent = (r != h) if (three_rows or h < 2) else (c != 0)
            if adjacent:
                edges.add((i, k+h))
    edges |= set(it.combinations(range(k, k+3), 2))
    return k+3, edges


def simplicial_clique(n, edges, nodes):
    chosen = set(nodes)
    def clique(values):
        return all(tuple(sorted(p)) in edges for p in it.combinations(values, 2))
    return bool(chosen) and chosen <= set(range(n)) and clique(chosen) and all(
        clique({u for u in range(n) if u not in chosen and tuple(sorted((v, u))) in edges})
        for v in chosen)


def claws_by_four_sets(n, edges):
    result = []
    for vertices in it.combinations(range(n), 4):
        local = [e for e in it.combinations(vertices, 2) if e in edges]
        degrees = {v: sum(v in e for e in local) for v in vertices}
        if sorted(degrees.values()) == [1, 1, 1, 3]:
            hub = next(v for v, d in degrees.items() if d == 3)
            result.append([hub]+[v for v in vertices if v != hub])
    return result


def verify_row(row):
    mask = row['cell_mask']
    assert type(mask) is int and 0 <= mask < 4096
    cells = [(r, c) for r in range(3) for c in range(4) if mask >> (4*r+c) & 1]
    n, edges = graph_edges(row['graph6'])
    assert (n, edges) == edges_from_cells(cells)
    outside = [cell for cell in cells if cell[1] != 0]
    maximum = max(k for k in range(4) if any(
        len({r for r, c in group}) == k == len({c for r, c in group})
        for group in it.combinations(outside, k)))
    pairs = list(map(tuple, row['matching']))
    assert len(pairs) == len(set(pairs)) == maximum and set(pairs) <= set(outside)
    assert len({r for r, c in pairs}) == len({c for r, c in pairs}) == maximum
    universe = [0, 1, 2, 4, 5, 6]
    covers = [list(s) for k in range(7) for s in it.combinations(universe, k)
              if all(r in s or 3+c in s for r, c in outside)]
    assert row['minimum_cover'] == covers[0] and len(covers[0]) == maximum
    claws = claws_by_four_sets(n, edges)
    if row['claw'] is None: assert not claws
    else: assert row['claw'] in claws
    assert (not claws) == (maximum <= 2)
    clique = row['simplicial_clique']
    if clique is None:
        assert not any(simplicial_clique(n, edges, subset) for k in range(1, n+1)
                       for subset in it.combinations(range(n), k))
    else:
        assert clique == sorted(set(clique)) and simplicial_clique(n, edges, clique)
    assert row['SCF'] == (not claws and clique is not None)
    central = [i for i, (r, c) in enumerate(cells) if c == 0]
    if central: assert simplicial_clique(n, edges, central)
    return maximum


def verify_census(report):
    start = time.monotonic()
    assert report['grid_rows'] == 3 and report['grid_columns'] == 4 and report['mask_order'] == 'row_major'
    assert [r['cell_mask'] for r in report['records']] == list(range(4096))
    histogram = Counter()
    for row in report['records']:
        assert time.monotonic()-start < 300, 'registered independent limit'
        histogram[str(verify_row(row))] += 1
    counts = {'graphs': 4096, 'claw_free': sum(r['claw'] is None for r in report['records']),
              'SCF': sum(r['SCF'] for r in report['records']), 'matching_histogram': dict(sorted(histogram.items()))}
    assert counts == report['counts'] and report['S_survives_finite_audit']
    assert not report['new_quantum_theorem'] and not report['A_star_confirmed']
    return counts


def gf2_rank(n, edges):
    rows = [sum(1 << j for j in range(n) if tuple(sorted((i, j))) in edges) for i in range(n)]
    pivots = {}
    for row in rows:
        while row:
            pivot = row.bit_length()-1
            if pivot in pivots: row ^= pivots[pivot]
            else:
                pivots[pivot] = row
                break
    return len(pivots)


def elementary_reductions(n, edges):
    nodes = set(range(n))
    neighbors = [{j for j in nodes if tuple(sorted((i, j))) in edges} for i in nodes]
    copies = [[i, j] for i, j in it.combinations(range(n), 2) if neighbors[i] == neighbors[j]]
    splits = [[i, j] for i, j in it.combinations(range(n), 2) if neighbors[i] | {i} == neighbors[j] | {j}]
    def disconnected(remaining, complement=False):
        if len(remaining) < 2: return False
        reached = {min(remaining)}
        while True:
            more = {v for v in remaining-reached if any(
                (tuple(sorted((u, v))) in edges) != complement for u in reached)}
            if not more: return reached != remaining
            reached |= more
    separators = []
    for k in range(1, n-1):
        for part in it.combinations(range(n), k):
            if all(e in edges for e in it.combinations(part, 2)) and disconnected(nodes-set(part)):
                separators.append(list(part))
    return {'copy_pairs': copies, 'split_pairs': splits,
            'complete_join_decomposition': disconnected(nodes, complement=True),
            'clique_separators': separators}


def verify_target(report):
    target = report['target']
    cells = list(it.product(range(3), range(3)))
    assert target['cells'] == list(map(list, cells))
    n, edges = graph_edges(target['graph6'])
    assert (n, edges) == edges_from_cells(cells) and n == 12
    check_scf(n, edges)
    hull = verify_polytope(target, max_dimension=14)
    triples = target['disjoint_triples']
    assert len(triples) == 2 and not set(triples[0]) & set(triples[1])
    assert all(len(t) == len(set(t)) == 3 and set(t) <= set(range(n)) and
               stable(sum(1 << v for v in t), edges) for t in triples)
    wheel = target['five_wheel']
    hub, rim = wheel['hub'], wheel['rim']
    assert len(set(rim)) == 5 and hub not in rim and set(rim+[hub]) <= set(range(n))
    cycle = {tuple(sorted((rim[i], rim[(i+1)%5]))) for i in range(5)}
    assert {e for e in edges if set(e) <= set(rim)} == cycle
    assert all(tuple(sorted((hub, v))) in edges for v in rim)
    facets = target['facets_b_plus_ax']
    assert target['full_one_two_row_is_facet'] == ([3]+[-1]*9+[-2]*3 in facets)
    routes = target['proof_routes']
    assert [r['facet_index'] for r in routes] == list(range(len(facets)))
    for f, route in zip(facets, routes):
        support = [i for i, a in enumerate(f[1:]) if a < 0]
        mask = sum(1 << i for i in support)
        alpha = max((s & mask).bit_count() for s in target['stable_masks'])
        assert support == route['support'] and alpha == route['support_alpha']
        if not support: expected = 'nonnegativity'
        else:
            assert all(a <= 0 for a in f[1:])
            componentwise_scf(n, edges, support)
            if len({f[i+1] for i in support}) == 1: expected = 'SCF_rank'
            elif alpha <= 2: expected = 'SCF_alpha_two'
            elif len(support) <= 9: expected = 'SCF_order9'
            else: expected = 'unresolved_by_rank_alpha_two_order9'
        assert route['route'] == expected
    assert not report['all_weight_quantum_theorem'] and not report['unrestricted_SCF_theorem']
    assert not report['A_star_confirmed']
    return {'vertices': n, 'STAB_vertices': hull['vertices'], 'facets': hull['facets'],
            'routes': dict(Counter(r['route'] for r in routes)),
            'GF2_adjacency_rank': gf2_rank(n, edges),
            'elementary_reductions': elementary_reductions(n, edges),
            'outside_C007_hereditary_family': True, 'not_a_line_graph': True,
            'quantum_theorem': False}


if __name__ == '__main__':
    if not __debug__: raise RuntimeError('Assertions required.')
    print(json.dumps({'census': verify_census(json.loads((DATA/'scf_three_row_gate.json').read_text())),
                      'target': verify_target(json.loads((DATA/'scf_three_row_target.json').read_text()))}))
