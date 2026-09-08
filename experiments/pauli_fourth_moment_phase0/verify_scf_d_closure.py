"""C010 independent exact hull, endpoint and uniform-template checks."""
from collections import Counter
from fractions import Fraction as F
import itertools as it
import json
from pathlib import Path
from verify_scf_generalization import graph_edges, stable, check_scf
from verify_scf_three_row_gate import edges_from_cells
from verify_scf_family_facet_closure import cube_clip, value, verify_polytope
from verify_scf_rectangular_gram_bridge import exact_rank

DATA = Path(__file__).resolve().parents[2]/'results'/'pauli_fourth_moment_phase0'


def d_cells(m):
    return sorted([(r, 0) for r in range(3)]+[(r, c) for r in (0, 2) for c in range(1, m+1)])


def cover_route(cells):
    """Check a constructive induced-map or true-twin quotient witness."""
    cells = sorted(map(tuple, cells))
    outside = [(r, c) for r, c in cells if c]
    universe = [('r', r) for r in range(3)]+[('c', c) for c in sorted({c for r, c in outside})]
    covers = [s for k in range(3) for s in it.combinations(universe, k)
              if all(('r', r) in s or ('c', c) in s for r, c in outside)]
    assert covers, 'noncentral matching obstruction'
    cover = covers[0]
    rows = {v for kind, v in cover if kind == 'r'}
    columns = {v for kind, v in cover if kind == 'c'}
    n, edges = edges_from_cells(cells)
    if not rows or columns:
        # All column-cover cases, including a mixed row/column cover.
        renaming = {c: i+1 for i, c in enumerate(sorted(columns))}
        mapped = [(r, 0 if c == 0 else renaming.get(c, 2)) for r, c in cells]
        target_cells = list(it.product(range(3), range(3)))
        mapping = [target_cells.index(c) for c in mapped]+[9, 10, 11]
        _, target_edges = edges_from_cells(target_cells)
        for i, j in it.combinations(range(n), 2):
            want = mapping[i] == mapping[j] or tuple(sorted((mapping[i], mapping[j]))) in target_edges
            assert ((i, j) in edges) == want
        return 'C009_with_known_splitting' if len(set(mapping)) < n else 'C009_induced'
    # A one-row cover can be extended by another row without adding edges.
    if len(rows) == 1:
        rows.add(0 if 0 not in rows else 1)
    if rows == {0, 1}:
        kind = 'C007_induced'
        swap = False
        target_rows = (0, 1)
    else:
        kind = 'D_induced'
        swap = rows == {1, 2}
        target_rows = (0, 2)
    colmap = {c: i+1 for i, c in enumerate(sorted({c for r, c in outside}))}
    target_cells = sorted([(r, 0) for r in range(3)]+
                          [(r, c) for r in target_rows for c in colmap.values()])
    rowmap = {0: 1, 1: 0, 2: 2} if swap else {r: r for r in range(3)}
    mapping = [target_cells.index((rowmap[r], colmap.get(c, 0))) for r, c in cells]
    k = len(target_cells)
    mapping += [k+1, k, k+2] if swap else [k, k+1, k+2]
    _, target_edges = edges_from_cells(target_cells)
    assert len(set(mapping)) == n
    assert all(((i, j) in edges) == (tuple(sorted((mapping[i], mapping[j]))) in target_edges)
               for i, j in it.combinations(range(n), 2))
    return kind


def description(m, core):
    cells = d_cells(m)
    n = len(cells)+3
    groups = [[cells.index((0, 0))], [cells.index((0, j)) for j in range(1, m+1)],
              [cells.index((1, 0))], [cells.index((2, 0))],
              [cells.index((2, j)) for j in range(1, m+1)], [n-3], [n-2], [n-1]]
    rows = [[0]+[int(i == v) for i in range(n)] for v in range(n)]
    for row in core['facets_b_plus_ax']:
        if not row[0]:
            continue
        out = [row[0]]+[0]*n
        for coeff, group in zip(row[1:], groups):
            for v in group:
                out[v+1] = coeff
        rows.append(out)
    for j in range(1, m+1):
        pair = {cells.index((0, j)), cells.index((2, j))}
        fixed = {cells.index((r, 0)) for r in range(3)} | {n-3, n-2, n-1}
        rows += [[1]+[-int(i in pair | {n-2, n-1}) for i in range(n)],
                 [2]+[-int(i in pair | fixed) for i in range(n)]]
    return sorted(map(list, set(map(tuple, rows))))


def verify(core_record, family):
    assert family['audit_m'] == list(range(4)) and len(family['records']) == 4
    assert not family['uniform_all_weight_theorem']  # historical discovery scope
    for obj in (core_record, family):
        assert not obj['unrestricted_SCF_theorem'] and not obj['A_star_confirmed']
    cells = [(0, 0), (0, 1), (1, 0), (2, 0), (2, 2)]
    assert core_record['cells'] == list(map(list, cells))
    core = core_record['core']
    n, edges = graph_edges(core['graph6'])
    assert (n, edges) == edges_from_cells(cells)
    check_scf(n, edges)
    verify_polytope(core)
    masks = [s for s in range(1 << n) if stable(s, edges)]
    points = {tuple([F(s >> i & 1) for i in range(8)]+[F(bool(s >> 1 & 1) and bool(s >> 4 & 1))]) for s in masks}
    assert points == set(map(tuple, core_record['points'])) and len(points) == 21
    facets = core_record['facets_b_plus_ax']
    assert len(facets) == 18 and len(set(map(tuple, facets))) == 18
    for f in facets:
        assert len(f) == 10 and all(type(v) is int for v in f)
        assert all(value(f, p) >= 0 for p in points)
        assert exact_rank([[1]+list(p) for p in points if value(f, p) == 0], 10) == 9
    found, _ = cube_clip(9, facets)
    assert found == points
    lower = sorted([[0]+[0]*8+[1], [1, 0, -1, 0, 0, -1, 0, -1, -1, 1], [2]+[-1]*8+[1]])
    assert core_record['lower_z_facets'] == [f for f in facets if f[-1] > 0] == lower
    # Any expanded independent triple must include B0 and both row groups.
    for f in core['facets_b_plus_ax']:
        if f[0] > 0:
            assert not all(f[i+1] < 0 for i in (1, 2, 4))
    checked = []
    for m, row in enumerate(family['records']):
        assert row['m'] == m and row['cells'] == list(map(list, d_cells(m)))
        nn, ee = graph_edges(row['graph6'])
        assert (nn, ee) == edges_from_cells(d_cells(m))
        check_scf(nn, ee)
        result = verify_polytope(row, max_dimension=14)
        hh = description(m, core)
        vertices, _ = cube_clip(nn, hh, max_dimension=14)
        expected = {tuple(F(s >> i & 1) for i in range(nn)) for s in row['stable_masks']}
        assert vertices == expected
        # All nonnegativity + clique rows imply the cube: every vertex
        # occurs in a rhs-one all-minus-one row, and all coordinates >=0.
        assert all(any(f[0] == 1 and f[v+1] == -1 and set(f[1:]) <= {-1, 0} for f in hh)
                   for v in range(nn))
        for f in hh:
            if not f[0]: continue
            support = [i for i, c in enumerate(f[1:]) if c < 0]
            alpha = max(sum(bool(s >> i & 1) for i in support) for s in row['stable_masks'])
            assert alpha <= 2
            assert max(-sum(f[i+1] for i in range(nn) if s >> i & 1) for s in row['stable_masks']) <= f[0]
        embed = row['C009_induced_embedding']
        if embed is not None:
            mapping = {int(k): v for k, v in embed.items()}
            tn, te = graph_edges('K{S{aSfF~Fln')
            assert set(mapping.values()) == set(range(nn))
            assert all(((i, j) in te) == (tuple(sorted((mapping[i], mapping[j]))) in ee)
                       for i, j in it.combinations(sorted(mapping), 2))
        checked.append(dict(m=m, vertices=nn, stable_vertices=result['vertices'], facets=result['facets']))
    return dict(status='C010_exact_endpoint_and_finite_uniform_templates_verified', records=checked,
                uniform_proof='SCF_THREE_ROW_ALL_WEIGHT_C010.md', unrestricted_SCF_theorem=False,
                A_star_confirmed=False)


if __name__ == '__main__':
    if not __debug__: raise RuntimeError('Assertions required')
    print(json.dumps(verify(json.loads((DATA/'scf_d_core_c010.json').read_text()),
                            json.loads((DATA/'scf_d_family_c010.json').read_text()))))
