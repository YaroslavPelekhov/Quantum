"""C011 exact independent published-graph/facet/embedding acceptance."""
from collections import Counter
from fractions import Fraction as F
import itertools as it
import json
from pathlib import Path
from verify_scf_generalization import graph_edges, check_scf, stable
from verify_scf_three_row_gate import simplicial_clique
from verify_scf_family_facet_closure import verify_polytope, cube_clip, value, componentwise_scf
from verify_scf_three_row_gram import verify as verify_c009

DATA = Path(__file__).resolve().parents[2]/'results'/'pauli_fourth_moment_phase0'


def published_edges():
    # One-based edge list, transcribed from the visually inspected source page.
    pairs = [(1,2),(2,3),(3,4),(4,5),(5,6),(1,6),
             (1,7),(2,7),(4,8),(5,8),
             (1,9),(2,9),(3,9),(6,9),
             (3,10),(4,10),(5,10),(6,10),(9,10),
             (1,11),(3,11),(4,11),(6,11),(9,11),(10,11),
             (2,12),(3,12),(5,12),(6,12),(9,12),(10,12),
             (1,13),(2,13),(4,13),(5,13),(7,13),(8,13)]
    assert len(pairs) == len(set(pairs)) == 37
    return set(pairs)


def verify(report, full=True):
    assert not report['quantum_all_weight_theorem']  # discovery's historic scope
    assert not report['unrestricted_SCF_theorem'] and not report['A_star_confirmed']
    assert len(report['records']) == 8
    source_edges = published_edges()
    cn, ce = graph_edges('K{S{aSfF~Fln')
    checked = []
    for mask, row in enumerate(report['records']):
        assert row['deletion_mask'] == mask
        labels = [i for i in range(1,14) if not (i >= 11 and mask >> (i-11) & 1)]
        assert row['original_labels'] == labels
        n, edges = graph_edges(row['graph6'])
        assert n == len(labels)
        assert edges == {(i,j) for i,j in it.combinations(range(n),2)
                         if (labels[i], labels[j]) in source_edges}
        check_scf(n, edges)
        assert simplicial_clique(n, edges, row['simplicial_clique'])
        quad = [labels.index(i) for i in (3,6,7,8)]
        assert stable(sum(1 << v for v in quad), edges)
        assert row['alpha'] == max(s.bit_count() for s in row['stable_masks']) == 4
        result = verify_polytope(row, max_dimension=14)
        assert len(row['routes']) == len(row['facets_b_plus_ax'])
        for idx, (f,r) in enumerate(zip(row['facets_b_plus_ax'],row['routes'])):
            support = [i for i,c in enumerate(f[1:]) if c < 0]
            assert r['facet_index'] == idx and r['support'] == support
            alpha = max(sum(bool(s >> i & 1) for i in support) for s in row['stable_masks'])
            assert r['support_alpha'] == alpha
            if not support:
                assert r['route'] == 'nonnegativity'
                continue
            assert all(c <= 0 for c in f[1:])
            componentwise_scf(n,edges,support)
            if r['route'] == 'SCF_rank': assert len({f[i+1] for i in support}) == 1
            elif r['route'] == 'SCF_alpha_two': assert alpha <= 2
            elif r['route'] == 'SCF_order9': assert len(support) <= 9
            elif r['route'] == 'C009_induced':
                mapping = {int(k):v for k,v in r['C009_mapping'].items()}
                assert len(mapping) == len(set(mapping.values())) == len(support)
                assert set(mapping) <= set(range(cn)) and set(mapping.values()) == set(support)
                assert all(((i,j) in ce) == (tuple(sorted((mapping[i],mapping[j]))) in edges)
                           for i,j in it.combinations(sorted(mapping),2))
            else: raise AssertionError('uncovered facet')
        checked.append(dict(deletion_mask=mask, vertices=n, STAB_vertices=result['vertices'],
                            facets=result['facets'], routes=dict(Counter(r['route'] for r in row['routes']))))
    if full:
        verify_c009(json.loads((DATA/'scf_three_row_gram_c009.json').read_text()))
        base = report['records'][0]
        rows = base['facets_b_plus_ax']
        idx = next(r['facet_index'] for r in base['routes'] if r['route'] == 'C009_induced')
        missing, _ = cube_clip(13,[r for i,r in enumerate(rows) if i != idx],max_dimension=14)
        true = {tuple(F(s >> i & 1) for i in range(13)) for s in base['stable_masks']}
        assert true <= missing and missing-true
        assert all(value(rows[idx],p) < 0 for p in missing-true)
    return dict(status='C011_exact_XX_all_weight_routes_verified',records=checked,
                dependency_C009_rechecked=full, source_graph_is_published=True,
                general_strip_composition_proved=False, unrestricted_SCF_theorem=False,
                A_star_confirmed=False)


if __name__ == '__main__':
    if not __debug__: raise RuntimeError('Assertions required')
    print(json.dumps(verify(json.loads((DATA/'scf_xx_gate_c011.json').read_text()))))
