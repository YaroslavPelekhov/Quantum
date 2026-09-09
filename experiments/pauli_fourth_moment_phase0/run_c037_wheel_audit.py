"""Exact-certificate discovery for the known odd-wheel strengthening."""
import json
from fractions import Fraction as F
import networkx as nx
import numpy as np
from scipy.optimize import linprog
from run_c036_known_bound_audit import constraints
from c020_exact_certificate import DATA


def rows_for(g):
    rows=[]
    for r in constraints(g,True):
        rows.append(dict(**r,weights=[1]*len(r['vertices'])))
        if r['kind']=='odd_cycle':
            rim=r['vertices'];k=r['bound']
            for hub in g:
                if hub not in rim and all(g.has_edge(hub,v) for v in rim):
                    rows.append(dict(vertices=rim+[hub],weights=[1]*len(rim)+[k],bound=k,kind='odd_wheel'))
    return rows


if __name__=='__main__':
    path=DATA/'c037_wheel_audit.json';assert not path.exists()
    source=json.loads((DATA/'c035_weighted_gear.json').read_text())
    output=[]
    for r in source['records']:
        g=nx.from_graph6_bytes(r['graph6'].encode());rows=rows_for(g)
        A=np.array([[dict(zip(t['vertices'],t['weights'])).get(i,0) for i in g] for t in rows])
        b=np.array([t['bound'] for t in rows]);w=r['weights']
        p=linprog(-np.array(w),A_ub=A,b_ub=b,bounds=(0,None),method='highs');assert p.success
        x=[F(float(t)).limit_denominator(1000000) for t in p.x]
        y=[F(float(-t)).limit_denominator(1000000) for t in p.ineqlin.marginals]
        assert all(t>=0 for t in x+y)
        assert all(sum(x[i]*a for i,a in zip(t['vertices'],t['weights']))<=t['bound'] for t in rows)
        assert all(sum(y[j]*int(A[j,i]) for j in range(len(rows)))>=w[i] for i in g)
        lower=sum(a*b for a,b in zip(x,w));upper=sum(a*t['bound'] for a,t in zip(y,rows))
        assert lower==upper
        output.append(dict(case=r['case'],variant=r['variant'],graph6=r['graph6'],weights=w,target=r['bound'],
                           value=str(upper),primal=list(map(str,x)),
                           dual=[dict(**t,coefficient=str(a)) for t,a in zip(rows,y) if a]))
    report=dict(records=output,explained=sum(F(r['value'])==r['target'] for r in output),quantum_transfer_proved=False)
    with path.open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2)
    print(json.dumps({k:v for k,v in report.items() if k!='records'}))
