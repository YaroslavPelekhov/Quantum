"""Bounded constraint generation on C018's exact orbit partitions."""
import argparse
import json
from pathlib import Path
import time
import numpy as np
from scipy.optimize import linprog
from threadpoolctl import threadpool_limits
from run_c018_ppt_symmetry import parity,sp,D,N,Q
from run_c017_ppt import transform


def run():
    start=time.monotonic();data=Path('results/pauli_fourth_moment_phase0')
    orbit=json.loads((data/'c018_ppt_symmetry.json').read_text())
    source=json.loads((data/'scf_two_xx_weight_c014.json').read_text())
    ag,lg=orbit['affine_orbits'],orbit['linear_orbits'];sizes=np.array(list(map(len,ag)))
    labels=[x|(z<<Q) for x,z in source['standard_SAUR_labels']];w=source['records'][0]['weights']
    obj=np.array([sum(weight*(-1)**(parity(p)+sp(v,p)) for weight,p in zip(w,labels)) for v in range(N)])
    costs=obj[[g[0] for g in ag]];ids=np.empty(N,dtype=int)
    for j,g in enumerate(ag):ids[g]=j
    tau=np.array([(-1)**parity(v) for v in range(N)],dtype=np.int64)
    index=np.arange(N);reps=np.array([g[0] for g in lg]);constraints=[];used=set();history=[];states={}
    bounds=[(0,min(1,float(s/D))) for s in sizes]
    status='iteration_cap'
    for iteration in range(20):
        remaining=60-(time.monotonic()-start)
        if remaining<=0:status='overall_time_cap';break
        a=np.array(constraints)/(D*sizes[None,:]) if constraints else None
        result=linprog(-costs,A_ub=-a if a is not None else None,b_ub=np.zeros(len(constraints)) if constraints else None,
                       A_eq=np.ones((1,len(ag))),b_eq=[1],bounds=bounds,method='highs-ds',
                       options={'time_limit':remaining,'threads':1})
        if result.x is None:
            status='solver_no_primal';history.append(dict(iteration=iteration,status=int(result.status)));break
        lam=result.x[ids]/sizes[ids];mu=transform(lam,Q)
        row=dict(iteration=iteration,solver_status=int(result.status),constraints=len(used),
                 value=float(obj@lam),min_lambda=float(min(lam)),min_pt=float(min(mu)),trace=float(sum(lam)))
        history.append(row);states[f'lambda_{iteration}']=lam
        print(json.dumps(row),flush=True)
        if min(mu)>=-1e-9 and min(lam)>=-1e-9:
            status='numerical_ppt_candidate';break
        selected=[int(j) for j in np.argsort(mu[reps]) if mu[reps[j]]<-1e-9 and int(j) not in used][:32]
        if not selected:status='no_new_cut';break
        for j in selected:
            # Each sum is an exact integer; bincount only sums +/-1 in float64.
            sums=np.bincount(ids,weights=tau[index^reps[j]],minlength=len(ag))
            assert np.all(sums==np.rint(sums))
            constraints.append(sums.astype(np.int64));used.add(j)
    report=dict(status=status,history=history,seconds=time.monotonic()-start,quantum_target_proved=False)
    states['objective']=obj
    return report,states


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    assert not args.output.exists() and not args.output.with_suffix('.npz').exists()
    with threadpool_limits(limits=1):report,states=run()
    with args.output.open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2)
    with args.output.with_suffix('.npz').open('xb') as stream:np.savez_compressed(stream,**states)
    print(json.dumps(dict(status=report['status'],seconds=report['seconds'])))
