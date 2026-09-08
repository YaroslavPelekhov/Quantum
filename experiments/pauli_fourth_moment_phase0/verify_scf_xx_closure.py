"""C012 independent exact closed-XX hull and induced proof route."""
from collections import Counter
from fractions import Fraction as F
import itertools as it
import json
from verify_scf_xx_gate import DATA,published_edges
from verify_scf_generalization import graph_edges,check_scf
from verify_scf_three_row_gate import simplicial_clique
from verify_scf_family_facet_closure import verify_polytope,cube_clip,value,componentwise_scf


def verify(report,negative=True):
    assert not report['quantum_all_weight_theorem']
    assert not report['unrestricted_SCF_theorem'] and not report['A_star_confirmed']
    row=report['target']
    n,edges=graph_edges(row['graph6'])
    source=published_edges()|{(7,14),(14,15),(8,15)}
    assert n==15 and edges=={(i-1,j-1) for i,j in source}
    check_scf(n,edges)
    assert simplicial_clique(n,edges,[13,14])
    assert simplicial_clique(n,edges,row['simplicial_clique'])
    hull=verify_polytope(row,max_dimension=15,indexed_edges=True)
    assert max(s.bit_count() for s in row['stable_masks'])==row['alpha']==4
    xxedges={(i-1,j-1) for i,j in published_edges()}
    assert len(row['routes'])==len(row['facets_b_plus_ax'])
    for idx,(f,r) in enumerate(zip(row['facets_b_plus_ax'],row['routes'])):
        support=[i for i,c in enumerate(f[1:]) if c<0]
        assert r['support']==support and r['facet_index']==idx
        alpha=max(sum(bool(s>>i&1) for i in support) for s in row['stable_masks'])
        assert r['support_alpha']==alpha
        if not support:
            assert r['route']=='nonnegativity'
            continue
        assert all(c<=0 for c in f[1:])
        componentwise_scf(n,edges,support)
        if r['route']=='SCF_rank':assert len({f[i+1] for i in support})==1
        elif r['route']=='SCF_alpha_two':assert alpha<=2
        elif r['route']=='SCF_order9':assert len(support)<=9
        elif r['route']=='C011_induced':
            mapping={int(k):v for k,v in r['C011_mapping'].items()}
            assert len(mapping)==len(set(mapping.values()))==len(support)
            assert set(mapping)<=set(range(13)) and set(mapping.values())==set(support)
            assert all(((i,j) in xxedges)==(tuple(sorted((mapping[i],mapping[j]))) in edges)
                       for i,j in it.combinations(sorted(mapping),2))
        else:raise AssertionError('uncovered')
    if negative:
        idx=next(r['facet_index'] for r in row['routes'] if r['route']=='C011_induced')
        actual,_=cube_clip(15,[f for j,f in enumerate(row['facets_b_plus_ax']) if j!=idx],max_dimension=15,indexed_edges=True)
        true={tuple(F(s>>i&1) for i in range(15)) for s in row['stable_masks']}
        assert true<=actual and actual-true
        assert all(value(row['facets_b_plus_ax'][idx],p)<0 for p in actual-true)
    return dict(status='C012_exact_fixed_closed_XX_all_weight_routes_verified',
                STAB_vertices=hull['vertices'],facets=hull['facets'],
                routes=dict(Counter(r['route'] for r in row['routes'])),
                general_strip_composition_proved=False,unrestricted_SCF_theorem=False,A_star_confirmed=False)


if __name__=='__main__':
    if not __debug__:raise RuntimeError('Assertions required')
    print(json.dumps(verify(json.loads((DATA/'scf_xx_closure_c012.json').read_text()))))
