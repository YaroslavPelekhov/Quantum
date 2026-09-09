"""Independent bitwise state/objective and graph reconstruction audit."""
import json
import itertools as it
from c020_exact_certificate import DATA
from verify_scf_generalization import graph_edges
from run_c033_gear_bridge import gear_edges,edge


def physical(best,labels,w,q):
    state=[complex(a,b) for a,b in best['state']]
    assert len(state)==1<<q and abs(sum(abs(v)**2 for v in state)-1)<1e-9
    values=[]
    for x,z in labels:
        assert 0<=x<1<<q and 0<=z<1<<q
        value=sum(state[j^x].conjugate()*(1j**((x&z).bit_count()))*
                  (-1 if (z&j).bit_count()%2 else 1)*v for j,v in enumerate(state))
        assert abs(value.imag)<1e-9;values.append(value.real)
    objective=sum(weight*v*v for weight,v in zip(w,values))
    assert max(abs(a-b) for a,b in zip(values,best['expectations']))<1e-9
    assert abs(objective-best['value'])<1e-9
    return objective


def verify(report):
    assert report['status']=='complete' and not report['quantum_transfer_proved']
    raw=json.loads((DATA/'almost_clique_closure_counterexample.json').read_text());q=len(raw['pauli_words'][0])
    labs=[[sum(1<<(q-1-j) for j,c in enumerate(word) if c in 'XY'),sum(1<<(q-1-j) for j,c in enumerate(word) if c in 'YZ')] for word in raw['pauli_words']]
    control=physical(report['positive_control'],labs,raw['weights'],q);assert control>3.01
    gaps=[];clawfree=0;converged=0
    for r in report['records']:
        n,es=graph_edges(r['seed_graph6']);a,b=r['seed_edge'];assert edge(a,b) in es
        ports=[{u for u in range(n) if u not in (a,b) and edge(v,u) in es} for v in (a,b)]
        assert all(k and all(edge(u,v) in es for u,v in it.combinations(k,2)) for k in ports)
        names=['a','c','d1','b1','d2','b2','h1','h2'];m={k:n+i for i,k in enumerate(names)}
        expected={e for e in es if not set(e)&{a,b}}|gear_edges(m)
        for i,k in enumerate(ports,1):expected|={edge(m[p],u) for p in (f'd{i}',f'b{i}') for u in k}
        vertices=sorted((set(range(n))-{a,b})|set(m.values()));index={v:i for i,v in enumerate(vertices)}
        expected={edge(index[u],index[v]) for u,v in expected}
        assert graph_edges(r['graph6'])==(len(vertices),expected)
        weights=[2 if v in (m['h1'],m['h2']) else 1 for v in vertices];assert r['weights']==weights
        alpha=max(s.bit_count() for s in range(1<<n) if all(not (s>>u&1 and s>>v&1) for u,v in es))
        assert r['bound']==alpha+2
        labels=r['labels'];assert len(labels)==len(vertices)
        assert all((((x&v).bit_count()+(z&u).bit_count())%2)==int((i,j) in expected)
                   for i,(x,z) in enumerate(labels) for j,(u,v) in enumerate(labels) if i<j)
        value=physical(r['best'],labels,weights,r['qubits']);gaps.append(value-r['bound'])
        assert r['violation_candidate']==(value>r['bound']+1e-6)
        neighbors=[{v for v in range(len(vertices)) if v!=u and edge(u,v) in expected} for u in range(len(vertices))]
        cf=all(any(edge(u,v) in expected for u,v in it.combinations(leaves,2)) for ns in neighbors for leaves in it.combinations(ns,3))
        assert cf==r['claw_free'];clawfree+=cf;converged+=r['converged_starts']
    assert len(gaps)==report['completed_cases']==report['selected_cases']==30
    assert sum(g>1e-6 for g in gaps)==report['violation_candidates']
    return dict(states_checked=len(gaps)+1,positive_control=control,max_gap=max(gaps),
                claw_free_outputs=clawfree,non_claw_free_outputs=len(gaps)-clawfree,
                converged_starts=converged,total_starts=8*len(gaps),quantum_transfer_proved=False)


if __name__=='__main__':
    if not __debug__:raise RuntimeError('Assertions required')
    report=verify(json.loads((DATA/'c034_gear_falsification.json').read_text()))
    with (DATA/'c034_independent_audit.json').open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2)
    print(json.dumps(report,indent=2))
