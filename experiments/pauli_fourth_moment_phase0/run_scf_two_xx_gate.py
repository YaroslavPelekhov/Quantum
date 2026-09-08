"""C013: one preregistered two-XX composition, exact facet discovery only."""
from collections import Counter
import itertools as it
import json
import time
import cdd.gmp as cdd
import networkx as nx
from run_scf_xx_gate import full_graph, DATA
from run_scf_three_row_gate import first_claw, simplicial
from run_scf_family_facet_closure import primitive


def target_graph():
    labels=[i for i in range(1,14) if i not in (7,8)]
    base=full_graph().subgraph(labels)
    g=nx.Graph()
    g.add_nodes_from(range(24))
    for offset in (0,11):
        g.add_edges_from((offset+labels.index(i),offset+labels.index(j)) for i,j in base.edges())
    A=[labels.index(i) for i in (1,2,13)]
    B=[labels.index(i) for i in (4,5,13)]
    g.add_edges_from((i,11+j) for i in B for j in B)
    g.add_edges_from([(22,23)]+[(22,i) for i in A]+[(23,11+i) for i in A])
    return g


def stable_sets(g):
    neighbors=[sum(1<<j for j in g[i]) for i in range(len(g))]
    answer=[]
    def visit(available,chosen):
        if not available:
            answer.append(chosen)
            assert len(answer)<=10000, 'registered stable-set cap'
            return
        low=available & -available
        v=low.bit_length()-1
        visit(available^low,chosen)
        visit(available & ~low & ~neighbors[v],chosen|low)
    visit((1<<len(g))-1,0)
    return sorted(answer)


def main():
    started=time.monotonic()
    g=target_graph()
    assert first_claw(g) is None
    assert simplicial(g) is not None
    masks=stable_sets(g)
    points=[[1]+[s>>i&1 for i in range(24)] for s in masks]
    h=cdd.copy_inequalities(cdd.polyhedron_from_matrix(cdd.matrix_from_array(points,rep_type=cdd.RepType.GENERATOR)))
    assert not h.lin_set and len(h.array)<=10000
    facets=sorted({tuple(primitive(f)) for f in h.array})
    back=cdd.copy_generators(cdd.polyhedron_from_matrix(h))
    assert not back.lin_set and {tuple(r) for r in back.array}=={tuple(r) for r in points}
    known=[('C009_induced',nx.from_graph6_bytes(b'K{S{aSfF~Fln')),
           ('C011_induced',nx.convert_node_labels_to_integers(full_graph(),ordering='sorted'))]
    routes=[]
    for idx,f in enumerate(facets):
        support=[i for i,a in enumerate(f[1:]) if a<0]
        alpha=max((s & sum(1<<i for i in support)).bit_count() for s in masks)
        witnesses=[]
        for nodes in nx.connected_components(g.subgraph(support)):
            witnesses.append(dict(nodes=sorted(nodes),clique=simplicial(g.subgraph(nodes))))
        scf=all(w['clique'] is not None for w in witnesses)
        mapping=None
        if not support: route='nonnegativity'
        elif scf and len({f[i+1] for i in support})==1: route='SCF_rank'
        elif scf and alpha<=2: route='SCF_alpha_two'
        elif scf and len(support)<=9: route='SCF_order9'
        else:
            route='unresolved'
            for name,k in known:
                if len(support)>len(k): continue
                mapping=next(nx.algorithms.isomorphism.GraphMatcher(k,g.subgraph(support)).subgraph_isomorphisms_iter(),None)
                if mapping is not None:
                    route=name
                    break
        routes.append(dict(facet_index=idx,support=support,support_alpha=alpha,
                           route=route,component_witnesses=witnesses,mapping=mapping))
    unknown=[r['facet_index'] for r in routes if r['route']=='unresolved']
    chosen=min(unknown,key=lambda i:(-len(routes[i]['support']),facets[i])) if unknown else None
    result=dict(experiment='C013_two_XX_fixed_gate',preregistration_commit='b140900',
                target=dict(graph6=nx.to_graph6_bytes(g,header=False).decode().strip(),
                            stable_masks=masks,facets_b_plus_ax=list(map(list,facets)),routes=routes,
                            alpha=max(s.bit_count() for s in masks),simplicial_clique=[22,23]),
                cdd_exact_H_V_roundtrip=True,independent_complete_hull=False,
                chosen_facet_index=chosen,uncovered_facets=len(unknown),
                quantum_theorem_proved=False,unrestricted_SCF_theorem=False,A_star_confirmed=False)
    assert time.monotonic()-started<300
    (DATA/'scf_two_xx_gate_c013.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(graph6=result['target']['graph6'],STAB_vertices=len(masks),facets=len(facets),
                          alpha=result['target']['alpha'],routes=dict(Counter(r['route'] for r in routes)),
                          chosen_facet_index=chosen,chosen_facet=facets[chosen] if chosen is not None else None)))


if __name__=='__main__': main()
