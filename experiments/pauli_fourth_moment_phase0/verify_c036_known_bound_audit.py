"""Exact LP optimality verifier, no numerical solver or graph library."""
import itertools as it
import json
from fractions import Fraction as F
from c020_exact_certificate import DATA
from verify_scf_generalization import graph_edges


def connected(vertices, es):
    reached={vertices[0]}
    while True:
        new=reached|{v for u in reached for v in vertices if tuple(sorted((u,v))) in es}
        if new==reached:return len(new)==len(vertices)
        reached=new


def valid_row(vertices,kind,n,es):
    assert vertices and len(vertices)==len(set(vertices)) and all(0<=v<n for v in vertices)
    if kind=='clique':
        assert all(tuple(sorted(e)) in es for e in it.combinations(vertices,2))
        return 1
    assert kind=='odd_cycle' and len(vertices)>=5 and len(vertices)%2
    assert all(sum(tuple(sorted((u,v))) in es for v in vertices if v!=u)==2 for u in vertices)
    assert connected(vertices,es)
    return len(vertices)//2


def verify(report):
    source=json.loads((DATA/'c035_weighted_gear.json').read_text())
    assert not report['quantum_transfer_proved']
    assert len(report['records'])==len(source['records'])==60
    counts=dict(clique=0,clique_odd_cycle=0);frontier=[]
    for r,s in zip(report['records'],source['records']):
        for field in ['case','variant','graph6','weights']:assert r[field]==s[field]
        assert r['target']==s['bound']
        n,es=graph_edges(r['graph6']);w=r['weights']
        for name in counts:
            cert=r[name];x=list(map(F,cert['primal']))
            assert len(x)==n and all(t>=0 for t in x)
            # Enumerate every clique, not the discovery code's maximal cliques.
            for mask in range(1,1<<n):
                v=[i for i in range(n) if mask>>i&1]
                clique=all(e in es for e in it.combinations(v,2))
                if clique:assert sum(x[i] for i in v)<=1
                if name=='clique_odd_cycle' and len(v)>=5 and len(v)%2:
                    if all(sum(tuple(sorted((a,b))) in es for b in v if b!=a)==2 for a in v) and connected(v,es):
                        assert sum(x[i] for i in v)<=len(v)//2
            coverage=[F(0)]*n;upper=F(0)
            for row in cert['dual']:
                assert name=='clique_odd_cycle' or row['kind']=='clique'
                bound=valid_row(row['vertices'],row['kind'],n,es)
                assert row['bound']==bound
                y=F(row['coefficient']);assert y>0
                upper+=bound*y
                for i in row['vertices']:coverage[i]+=y
            assert all(a>=b for a,b in zip(coverage,w))
            lower=sum(a*b for a,b in zip(x,w))
            assert lower==upper==F(cert['value']) and lower>=r['target']
            counts[name]+=lower==r['target']
        if F(r['clique_odd_cycle']['value'])>r['target']:
            frontier.append(dict(case=r['case'],variant=r['variant'],target=r['target'],
                                 known_bound=r['clique_odd_cycle']['value'],
                                 gap=str(F(r['clique_odd_cycle']['value'])-r['target'])))
    assert report['clique_explained']==counts['clique']
    assert report['clique_odd_cycle_explained']==counts['clique_odd_cycle']
    return dict(exact_lp_pairs=120,clique_explained=counts['clique'],
                clique_odd_cycle_explained=counts['clique_odd_cycle'],
                frontier=frontier,quantum_transfer_proved=False)


if __name__=='__main__':
    result=verify(json.loads((DATA/'c036_known_bound_audit.json').read_text()))
    with (DATA/'c036_independent_audit.json').open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2)
    print(json.dumps(result,indent=2))
