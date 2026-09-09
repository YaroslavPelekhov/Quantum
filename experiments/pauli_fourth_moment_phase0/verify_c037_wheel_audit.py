"""Exact independent clique/cycle/wheel certificate acceptance."""
import itertools as it
import json
from fractions import Fraction as F
from c020_exact_certificate import DATA
from verify_scf_generalization import graph_edges
from verify_c036_known_bound_audit import connected,valid_row


def verify(report):
    source=json.loads((DATA/'c035_weighted_gear.json').read_text())
    assert len(report['records'])==len(source['records'])==60
    assert not report['quantum_transfer_proved']
    explained=0;frontier=[];wheel_terms=0
    for r,s in zip(report['records'],source['records']):
        for field in ['case','variant','graph6','weights']:assert r[field]==s[field]
        assert r['target']==s['bound']
        n,es=graph_edges(r['graph6']);x=list(map(F,r['primal']))
        assert len(x)==n and all(t>=0 for t in x)
        for mask in range(1,1<<n):
            vertices=[i for i in range(n) if mask>>i&1]
            if all(e in es for e in it.combinations(vertices,2)):
                assert sum(x[i] for i in vertices)<=1
            if len(vertices)>=5 and len(vertices)%2:
                if all(sum(tuple(sorted((a,b))) in es for b in vertices if b!=a)==2 for a in vertices) and connected(vertices,es):
                    bound=len(vertices)//2
                    assert sum(x[i] for i in vertices)<=bound
                    for hub in range(n):
                        if hub not in vertices and all(tuple(sorted((hub,i))) in es for i in vertices):
                            assert sum(x[i] for i in vertices)+bound*x[hub]<=bound
        coverage=[F(0)]*n;upper=F(0)
        for row in r['dual']:
            v=row['vertices'];weights=row['weights'];kind=row['kind']
            if kind=='odd_wheel':
                assert len(v)==len(set(v)) and all(0<=i<n for i in v)
                bound=valid_row(v[:-1],'odd_cycle',n,es)
                assert all(tuple(sorted((v[-1],i))) in es for i in v[:-1])
                assert weights==[1]*(len(v)-1)+[bound]
                wheel_terms+=1
            else:
                bound=valid_row(v,kind,n,es)
                assert weights==[1]*len(v)
            assert row['bound']==bound
            y=F(row['coefficient']);assert y>0
            upper+=y*bound
            for i,w in zip(v,weights):coverage[i]+=y*w
        assert all(a>=b for a,b in zip(coverage,r['weights']))
        assert sum(a*b for a,b in zip(x,r['weights']))==upper==F(r['value'])
        assert upper>=r['target']
        explained+=upper==r['target']
        if upper>r['target']:
            frontier.append(dict(case=r['case'],variant=r['variant'],target=r['target'],
                                 known_bound=str(upper),gap=str(upper-r['target'])))
    assert report['explained']==explained
    return dict(exact_lp_pairs=60,explained=explained,wheel_terms_checked=wheel_terms,
                frontier=frontier,quantum_transfer_proved=False)


if __name__=='__main__':
    result=verify(json.loads((DATA/'c037_wheel_audit.json').read_text()))
    with (DATA/'c037_independent_audit.json').open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2)
    print(json.dumps(result,indent=2))
