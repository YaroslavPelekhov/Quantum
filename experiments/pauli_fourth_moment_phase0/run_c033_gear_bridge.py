"""Exact construction bridge to classical gear composition, not quantum closure."""
import itertools as it
import argparse
import json
from c020_exact_certificate import DATA
from verify_scf_generalization import graph_edges
from verify_scf_two_xx_weight import verify as verify_source


def edge(a,b):return tuple(sorted((a,b)))


def gear_edges(mapping):
    result=set()
    for h,cycle in [('h1',['a','d1','b1','c','h2']),('h2',['a','d2','b2','c','h1'])]:
        result|={edge(mapping[h],mapping[v]) for v in cycle}
        result|={edge(mapping[cycle[i]],mapping[cycle[(i+1)%5]]) for i in range(5)}
    return result


def inverse(vertices,edges,mapping,new):
    inside=set(mapping.values());outside=vertices-inside
    assert {e for e in edges if set(e)<=inside}==gear_edges(mapping)
    neighbors={v:{u for u in vertices if u!=v and edge(u,v) in edges} for v in vertices}
    assert all(not neighbors[mapping[k]]&outside for k in ('a','c','h1','h2'))
    ports=[]
    for i in (1,2):
        k=neighbors[mapping[f'd{i}']]&outside
        assert k and k==neighbors[mapping[f'b{i}']]&outside
        assert all(edge(a,b) in edges for a,b in it.combinations(k,2));ports.append(k)
    base={e for e in edges if set(e)<=outside}|{edge(*new)}
    for v,k in zip(new,ports):base|={edge(v,u) for u in k}
    rebuilt={e for e in base if not set(e)&set(new)}|gear_edges(mapping)
    for i,k in enumerate(ports,1):rebuilt|={edge(mapping[p],u) for p in (f'd{i}',f'b{i}') for u in k}
    assert rebuilt==edges
    return outside|set(new),base,[sorted(k) for k in ports]


def stable_opt(vertices,edges,weights):
    labels=sorted(vertices);index={v:i for i,v in enumerate(labels)}
    encoded=[(1<<index[a])|(1<<index[b]) for a,b in edges]
    valid=[s for s in range(1<<len(labels)) if all(s&e!=e for e in encoded)]
    return max(sum(weights[v] for i,v in enumerate(labels) if s>>i&1) for s in valid),len(valid)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',default='c033_gear_bridge.json');args=parser.parse_args()
    source=json.loads((DATA/'scf_two_xx_weight_c014.json').read_text());verify_source(source)
    _,original=graph_edges(source['graph6']);deleted={8,9,19,20};vertices=set(range(24))-deleted
    g20={e for e in original if not set(e)&deleted}
    left=dict(a=5,c=2,d1=0,b1=1,d2=4,b2=3,h1=6,h2=7);right={k:v+11 for k,v in left.items()}
    v14,g14,kleft=inverse(vertices,g20,left,(24,25))
    v8,g8,kright=inverse(v14,g14,right,(26,27))
    v9=v8|{28};g9=(g8-{(26,27)})|{(26,28),(27,28)}
    # Source row has proper-geared weights on left and uniform g-lifted weights on right.
    weights=dict(enumerate(source['records'][0]['weights']))
    assert all(weights[left[k]]==(2 if k in ('h1','h2') else 1) for k in left)
    assert all(weights[v]==1 for v in right.values())
    valid20=[s for s in source['stable_masks'] if not any(s>>i&1 for i in deleted)]
    bound20=max(sum(weights[i] for i in vertices if s>>i&1) for s in valid20)
    bound14,count14=stable_opt(v14,g14,{v:1 for v in v14})
    bound9,count9=stable_opt(v9,g9,{v:1 for v in v9})
    assert (bound20,bound14,bound9)==(6,4,3)
    current=vertices.copy();lifting=[]
    for v in sorted(deleted):
        blocked={u for u in current if edge(u,v) in original}
        eligible=current-blocked
        best=max(sum(weights[i] for i in eligible if s>>i&1) for s in source['stable_masks']
                 if all(not (s>>i&1) for i in set(range(24))-eligible))
        lifting.append(dict(vertex=v,restricted_stable_bound=best,maximal_classical_coefficient=6-best))
        current.add(v)
    result=dict(deleted_C014_vertices=sorted(deleted),left_gear=left,right_gear=right,
                left_ports=kleft,right_ports=kright,core20_edges=sorted(g20),
                inverse14_edges=sorted(g14),base8_edges=sorted(g8),subdivided9_edges=sorted(g9),
                stable_bounds=[bound20,bound14,bound9],stable_counts=[len(valid20),count14,count9],
                exact_forward_reconstructions=2,classical_rhs_steps=[3,4,6],sequential_lifting=lifting,
                quantum_composition_proved=False,quantum_vertex_lifting_proved=False,novelty_confirmed=False)
    with (DATA/args.output).open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2)
    print(json.dumps({k:v for k,v in result.items() if not k.endswith('_edges')},indent=2))
