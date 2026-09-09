"""Discover rational clique / induced odd-cycle LP certificates for C035."""
import itertools as it
import json
from fractions import Fraction as F
import networkx as nx
import numpy as np
from scipy.optimize import linprog
from c020_exact_certificate import DATA


def constraints(g, cycles):
    rows=[dict(vertices=sorted(c),bound=1,kind='clique') for c in nx.find_cliques(g)]
    if cycles:
        for k in range(5,len(g)+1,2):
            for v in it.combinations(g,k):
                h=g.subgraph(v)
                if all(h.degree(u)==2 for u in h) and nx.is_connected(h):
                    rows.append(dict(vertices=list(v),bound=k//2,kind='odd_cycle'))
    return rows


def solve(g,w,cycles):
    rows=constraints(g,cycles)
    A=np.array([[int(i in r['vertices']) for i in g] for r in rows])
    b=np.array([r['bound'] for r in rows])
    p=linprog(-np.array(w),A_ub=A,b_ub=b,bounds=(0,None),method='highs')
    assert p.success
    x=[F(float(t)).limit_denominator(1000000) for t in p.x]
    y=[F(float(-t)).limit_denominator(1000000) for t in p.ineqlin.marginals]
    assert all(t>=0 for t in x+y)
    assert all(sum(x[i] for i in r['vertices'])<=r['bound'] for r in rows)
    assert all(sum(y[j] for j,r in enumerate(rows) if i in r['vertices'])>=w[i] for i in g)
    lower=sum(a*b for a,b in zip(x,w))
    upper=sum(a*r['bound'] for a,r in zip(y,rows))
    assert lower==upper
    return dict(value=str(upper),primal=list(map(str,x)),
                dual=[dict(**r,coefficient=str(t)) for r,t in zip(rows,y) if t],
                constraint_count=len(rows))


if __name__=='__main__':
    path=DATA/'c036_known_bound_audit.json';assert not path.exists()
    source=json.loads((DATA/'c035_weighted_gear.json').read_text())
    output=[]
    for r in source['records']:
        g=nx.from_graph6_bytes(r['graph6'].encode())
        proofs={name:solve(g,r['weights'],cycles) for name,cycles in [('clique',False),('clique_odd_cycle',True)]}
        output.append(dict(case=r['case'],variant=r['variant'],graph6=r['graph6'],weights=r['weights'],
                           target=r['bound'],**proofs))
    report=dict(records=output,quantum_transfer_proved=False,
                clique_explained=sum(F(r['clique']['value'])==r['target'] for r in output),
                clique_odd_cycle_explained=sum(F(r['clique_odd_cycle']['value'])==r['target'] for r in output))
    with path.open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2)
    print(json.dumps({k:v for k,v in report.items() if k!='records'},indent=2))
