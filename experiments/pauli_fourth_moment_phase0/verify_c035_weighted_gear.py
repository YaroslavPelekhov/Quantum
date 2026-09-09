"""Stdlib reconstruction and independent bitwise audit of every saved state."""
import itertools as it
import json
import math
from c020_exact_certificate import DATA
from verify_scf_generalization import graph_edges
from verify_c034_states import physical
from run_c033_gear_bridge import gear_edges, edge, stable_opt


def verify(report):
    assert report['status']=='complete' and not report['quantum_transfer_proved']
    assert report['starts']==16 and report['iteration_limit']==256
    assert len(report['records'])==60
    gaps=[]; residuals=[]; converged=0; classical_failures=0
    nonuniform=0
    assert {(r['case'],r['variant']) for r in report['records']}==set(it.product(range(30),range(2)))
    for r in report['records']:
        n, es=graph_edges(r['seed_graph6']);a,b=r['seed_edge']
        assert edge(a,b) in es and 3<=n<=6
        sw=r['seed_weights'];assert len(sw)==n and sw[a]==sw[b]==1
        assert all(isinstance(x,int) and 1<=x<=3 for x in sw)
        nonuniform+=len(set(sw))>1
        ports=[{u for u in range(n) if u not in (a,b) and edge(v,u) in es} for v in (a,b)]
        assert all(k and all(edge(u,v) in es for u,v in it.combinations(k,2)) for k in ports)
        m={k:n+i for i,k in enumerate(['a','c','d1','b1','d2','b2','h1','h2'])}
        vertices=sorted(set(range(n))-{a,b})+list(range(n,n+8))
        index={v:i for i,v in enumerate(vertices)}
        expected={e for e in es if not set(e)&{a,b}}|gear_edges(m)
        for i,k in enumerate(ports,1):
            expected|={edge(m[p],v) for p in (f'd{i}',f'b{i}') for v in k}
        expected={edge(index[u],index[v]) for u,v in expected}
        assert graph_edges(r['graph6'])==(n+6,expected)
        w=[sw[v] for v in range(n) if v not in (a,b)]+[1]*6+[2]*2
        assert r['weights']==w
        bound=stable_opt(set(range(n)),es,dict(enumerate(sw)))[0]+2
        actual=stable_opt(set(range(n+6)),expected,dict(enumerate(w)))[0]
        assert r['bound']==bound and r['classical_bound']==actual
        if actual!=bound:
            assert r['status']=='classical_transfer_failed' and not r['runs']
            classical_failures+=1;continue
        assert r['status']=='searched' and len(r['runs'])==16
        labs=r['labels'];q=r['qubits'];assert len(labs)==len(w)
        assert all((((x&v).bit_count()+(z&u).bit_count())%2)==int((i,j) in expected)
                   for i,(x,z) in enumerate(labs) for j,(u,v) in enumerate(labs) if i<j)
        for run in r['runs']:
            value=physical(run,labs,w,q);assert math.isfinite(value)
            state=[complex(a,b) for a,b in run['state']]
            action=[0j]*len(state)
            for (x,z),weight,exp in zip(labs,w,run['expectations']):
                for j,v in enumerate(state):
                    action[j^x]+=weight*exp*(1j**((x&z).bit_count()))*(-1 if (z&j).bit_count()%2 else 1)*v
            residual=math.sqrt(sum(abs(t-value*v)**2 for t,v in zip(action,state)))
            assert abs(residual-run['stationarity_residual'])<1e-9
            assert 1<=run['iterations']<=256
            gaps.append(value-bound);residuals.append(residual);converged+=run['converged']
    return dict(records=60,nonuniform_seed_records=nonuniform,states_checked=len(gaps),
                classical_failures=classical_failures,max_gap=max(gaps,default=None),
                violations=sum(g>1e-6 for g in gaps),strict_converged=converged,
                stationary_below_1e_8=sum(r<1e-8 for r in residuals),
                max_stationarity_residual=max(residuals,default=None),
                quantum_transfer_proved=False)


if __name__=='__main__':
    result=verify(json.loads((DATA/'c035_weighted_gear.json').read_text()))
    with (DATA/'c035_independent_audit.json').open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2)
    print(json.dumps(result,indent=2))
