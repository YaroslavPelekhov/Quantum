"""Bounded physical counterexample search for a proposed quantum gear rule."""
import itertools as it
import json
import time
import networkx as nx
import numpy as np
from threadpoolctl import threadpool_limits
from run_c033_gear_bridge import gear_edges
from run_scf_hbar_falsification import standard_saur
from run_scf_two_xx_attack import matrices,optimize
from c020_exact_certificate import DATA


def stable_bound(g,w):
    masks=[(1<<a)|(1<<b) for a,b in g.edges()]
    return max(sum(w[i] for i in range(len(g)) if s>>i&1) for s in range(1<<len(g))
               if all(s&m!=m for m in masks))


def claw_free(g):
    return all(any(g.has_edge(a,b) for a,b in it.combinations(leaves,2))
               for v in g for leaves in it.combinations(g[v],3))


def seeds():
    selected=[];counts={n:0 for n in range(3,7)}
    for h in nx.graph_atlas_g():
        n=len(h)
        if n not in counts or counts[n]>=12 or not nx.is_connected(h):continue
        for a,b in sorted(h.edges()):
            ports=[set(h[a])-{b},set(h[b])-{a}]
            if not all(k and all(h.has_edge(u,v) for u,v in it.combinations(k,2)) for k in ports):continue
            names=['a','c','d1','b1','d2','b2','h1','h2'];mapping={k:n+i for i,k in enumerate(names)}
            g=h.copy();g.remove_nodes_from([a,b]);g.add_nodes_from(mapping.values());g.add_edges_from(gear_edges(mapping))
            for i,k in enumerate(ports,1):g.add_edges_from((mapping[p],v) for p in (f'd{i}',f'b{i}') for v in k)
            nx.set_node_attributes(g,{v:2 if v in (mapping['h1'],mapping['h2']) else 1 for v in g},'weight')
            g=nx.convert_node_labels_to_integers(g,ordering='sorted')
            if any(nx.is_isomorphic(g,old[0],node_match=nx.algorithms.isomorphism.categorical_node_match('weight',1)) for old in selected):continue
            bound=stable_bound(h,[1]*n)+2
            selected.append((g,n,[a,b],nx.to_graph6_bytes(h,header=False).decode().strip(),bound))
            counts[n]+=1
            if counts[n]>=12:break
    return selected,counts


def search(ops,w,rng):
    runs=[optimize(ops,np.array(w),np.ones(len(w)) if j==0 else rng.normal(size=len(w)),32) for j in range(8)]
    return max(runs,key=lambda r:r['value']),sum(r['converged'] for r in runs)


def main():
    start=time.monotonic();rng=np.random.default_rng(20260910);cases,counts=seeds()
    raw=json.loads((DATA/'almost_clique_closure_counterexample.json').read_text());q=len(raw['pauli_words'][0])
    labels=[[sum(1<<(q-1-j) for j,c in enumerate(word) if c in 'XY'),sum(1<<(q-1-j) for j,c in enumerate(word) if c in 'YZ')] for word in raw['pauli_words']]
    control,_=search(matrices(labels,q),raw['weights'],rng)
    report=dict(seed=20260910,selected_counts=counts,selected_cases=len(cases),positive_control=control,
                records=[],status='complete',quantum_transfer_proved=False)
    if control['value']<=3.01:report['status']='positive_control_failed';return report
    for g,n,e,h6,bound in cases:
        if time.monotonic()-start>120:report['status']='time_cap';break
        w=[g.nodes[i]['weight'] for i in g];assert stable_bound(g,w)==bound
        labels,q=standard_saur(g)
        assert all((((x&v).bit_count()+(z&u).bit_count())%2)==int(g.has_edge(i,j))
                   for i,(x,z) in enumerate(labels) for j,(u,v) in enumerate(labels) if i<j)
        best,converged=search(matrices(labels,q),w,rng)
        record=dict(seed_graph6=h6,seed_order=n,seed_edge=e,graph6=nx.to_graph6_bytes(g,header=False).decode().strip(),
                    labels=labels,qubits=q,weights=w,bound=bound,claw_free=claw_free(g),
                    best=best,converged_starts=converged,violation_candidate=best['value']>bound+1e-6)
        report['records'].append(record)
        print(json.dumps({k:v for k,v in record.items() if k in ('seed_order','qubits','bound','claw_free','violation_candidate')}),flush=True)
    report.update(seconds=time.monotonic()-start,completed_cases=len(report['records']),
                  violation_candidates=sum(r['violation_candidate'] for r in report['records']))
    return report


if __name__=='__main__':
    path=DATA/'c034_gear_falsification.json';assert not path.exists()
    with threadpool_limits(limits=1):result=main()
    with path.open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k not in ('records','positive_control')},indent=2))
