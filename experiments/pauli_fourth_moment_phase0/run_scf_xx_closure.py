"""C012 one exact closed-XX hull and known-route screen."""
from collections import Counter
import json
import time
import networkx as nx
from run_scf_xx_gate import full_graph, DATA
from run_scf_three_row_gate import first_claw, simplicial
from run_scf_family_facet_closure import enumerate_polytope


def main():
    start=time.monotonic()
    g=full_graph()
    g.add_edges_from([(7,14),(14,15),(15,8)])
    g=nx.convert_node_labels_to_integers(g,ordering='sorted')
    assert first_claw(g) is None
    row=enumerate_polytope(g)
    row['simplicial_clique']=simplicial(g)
    row['alpha']=max(s.bit_count() for s in row['stable_masks'])
    routes=[]
    known=nx.convert_node_labels_to_integers(full_graph(),ordering='sorted')
    for idx,f in enumerate(row['facets_b_plus_ax']):
        support=[i for i,c in enumerate(f[1:]) if c<0]
        alpha=max(sum(bool(s>>i&1) for i in support) for s in row['stable_masks'])
        mapping=None
        if not support: route='nonnegativity'
        elif len({f[i+1] for i in support})==1: route='SCF_rank'
        elif alpha<=2: route='SCF_alpha_two'
        elif len(support)<=9: route='SCF_order9'
        else:
            matcher=nx.algorithms.isomorphism.GraphMatcher(known,g.subgraph(support))
            mapping=next(matcher.subgraph_isomorphisms_iter(),None)
            route='C011_induced' if mapping is not None else 'unresolved'
        routes.append(dict(facet_index=idx,support=support,support_alpha=alpha,route=route,C011_mapping=mapping))
    row['routes']=routes
    result=dict(experiment='C012_closed_XX_fixed_target',preregistration_commit='ad8602c',
                target=row,quantum_all_weight_theorem=False,unrestricted_SCF_theorem=False,A_star_confirmed=False)
    (DATA/'scf_xx_closure_c012.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(row['graph6'],row['alpha'],len(row['stable_masks']),len(row['facets_b_plus_ax']),Counter(r['route'] for r in routes))
    for f,r in zip(row['facets_b_plus_ax'],routes):
        if r['route']=='unresolved':print('unresolved',f,r)
    assert time.monotonic()-start<300


if __name__=='__main__': main()
