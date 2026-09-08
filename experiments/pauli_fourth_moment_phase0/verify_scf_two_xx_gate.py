"""C013 stdlib graph, stable-set census, valid rows and selected-facet check.

This intentionally does NOT certify completeness of the discovered hull.
"""
from collections import Counter
import itertools as it
import json
from math import gcd
from verify_scf_xx_gate import DATA,published_edges
from verify_scf_generalization import graph_edges,stable
from verify_scf_three_row_gate import simplicial_clique
from verify_scf_rectangular_gram_bridge import exact_rank


def expected_graph():
    labels=[i for i in range(1,14) if i not in (7,8)]
    core={(labels.index(a),labels.index(b)) for a,b in published_edges() if a in labels and b in labels}
    edges=core|{(a+11,b+11) for a,b in core}
    left_A={labels.index(i) for i in (1,2,13)}
    left_B={labels.index(i) for i in (4,5,13)}
    edges|={(a,b+11) for a in left_B for b in left_B}
    edges|={(a,22) for a in left_A}|{(a+11,23) for a in left_A}|{(22,23)}
    return core,edges


def all_stable_masks(core,edges):
    # Exhaustive core products, independent of discovery's recursive DFS.
    local=[s for s in range(1<<11) if stable(s,core)]
    cross=[(a,b) for a,b in edges if a//11!=b//11]
    return sorted(a|(b<<11)|c for a in local for b in local
                  for c in (0,1<<22,1<<23) if stable(a|(b<<11)|c,cross))


def verify(report):
    assert not any(report[k] for k in ('independent_complete_hull','quantum_theorem_proved',
                                       'unrestricted_SCF_theorem','A_star_confirmed'))
    row=report['target']
    n,edges=graph_edges(row['graph6'])
    core,expected=expected_graph()
    assert n==24 and edges==expected
    neighbors=[{j for j in range(n) if tuple(sorted((i,j))) in edges} for i in range(n)]
    assert all(any(tuple(sorted(pair)) in edges for pair in it.combinations(leaves,2))
               for i in range(n) for leaves in it.combinations(neighbors[i],3))
    assert row['simplicial_clique']==[22,23] and simplicial_clique(n,edges,[22,23])
    masks=all_stable_masks(core,edges)
    assert masks==row['stable_masks'] and len(masks)<=10000
    assert max(s.bit_count() for s in masks)==row['alpha']
    facets=row['facets_b_plus_ax']
    assert facets==sorted(facets) and len({tuple(f) for f in facets})==len(facets)<=10000
    assert len(row['routes'])==len(facets)
    roots={}
    for idx,(f,r) in enumerate(zip(facets,row['routes'])):
        assert len(f)==25 and all(type(c) is int for c in f) and gcd(*f)==1
        sparse=[(i,a) for i,a in enumerate(f[1:]) if a]
        slacks=[f[0]+sum(a*(s>>i&1) for i,a in sparse) for s in masks]
        assert min(slacks)==0 and max(slacks)>0
        support=[i for i,a in enumerate(f[1:]) if a<0]
        support_mask=sum(1<<i for i in support)
        alpha=max((s&support_mask).bit_count() for s in masks)
        assert r['facet_index']==idx and r['support']==support and r['support_alpha']==alpha
        if idx==report['chosen_facet_index']:
            roots[idx]=[s for s,slack in zip(masks,slacks) if not slack]
        if not support:
            assert r['route']=='nonnegativity'
            continue
        assert all(a<=0 for a in f[1:])
        if r['route'] in ('SCF_rank','SCF_alpha_two','SCF_order9'):
            groups=[set(w['nodes']) for w in r['component_witnesses']]
            assert set().union(*groups)==set(support) and sum(map(len,groups))==len(support)
            assert not any((min(a,b),max(a,b)) in edges for i,A in enumerate(groups) for B in groups[i+1:]
                           for a in A for b in B)
            for w in r['component_witnesses']:
                nodes=w['nodes']; index={v:i for i,v in enumerate(nodes)}
                assert len(index)==len(nodes) and set(w['clique'])<=set(nodes)
                reached={nodes[0]}
                while True:
                    more=reached|{v for v in nodes if neighbors[v]&reached}
                    if more==reached:break
                    reached=more
                assert reached==set(nodes)
                local={(index[a],index[b]) for a,b in edges if a in index and b in index}
                assert simplicial_clique(len(nodes),local,[index[v] for v in w['clique']])
            if r['route']=='SCF_rank':assert len({f[i+1] for i in support})==1
            elif r['route']=='SCF_alpha_two':assert alpha<=2
            else:assert len(support)<=9
        elif r['route'] in ('C009_induced','C011_induced'):
            known='K{S{aSfF~Fln' if r['route']=='C009_induced' else 'LhEM?rcNLhleuo'
            kn,ke=graph_edges(known)
            mapping={int(k):v for k,v in r['mapping'].items()}
            assert set(mapping)<=set(range(kn)) and set(mapping.values())==set(support)
            assert len(mapping)==len(set(mapping.values()))
            assert all(((a,b) in ke)==(tuple(sorted((mapping[a],mapping[b]))) in edges)
                       for a,b in it.combinations(sorted(mapping),2))
        else:assert r['route']=='unresolved'
    unknown=[r['facet_index'] for r in row['routes'] if r['route']=='unresolved']
    assert len(unknown)==report['uncovered_facets']
    selected=min(unknown,key=lambda i:(-len(row['routes'][i]['support']),facets[i])) if unknown else None
    assert selected==report['chosen_facet_index']
    if selected is not None:
        assert exact_rank([[1]+[s>>i&1 for i in range(n)] for s in roots[selected]],n+1)==n
    return dict(status='C013_frozen_graph_rows_and_selected_facet_verified',
                STAB_vertices=len(masks),facets_discovered=len(facets),alpha=row['alpha'],
                routes=dict(Counter(r['route'] for r in row['routes'])),chosen_facet_index=selected,
                independent_complete_hull=False,quantum_theorem_proved=False,A_star_confirmed=False)


if __name__=='__main__':
    if not __debug__:raise RuntimeError('Assertions required')
    print(json.dumps(verify(json.loads((DATA/'scf_two_xx_gate_c013.json').read_text()))))
