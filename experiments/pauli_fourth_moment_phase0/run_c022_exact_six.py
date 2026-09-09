"""Bounded dual feasibility recovery at an exact target RHS of six."""
import argparse
import json
from pathlib import Path
import time
import numpy as np
from scipy.optimize import linprog
from threadpoolctl import threadpool_limits
from c020_exact_certificate import objective,SOURCE,DATA


def run():
    start=time.monotonic()
    orbits=json.loads((DATA/'c018_ppt_symmetry.json').read_text())
    with np.load(DATA/'c021_bosonic_ppt.npz',allow_pickle=False) as data:u=-data['C014_dual']
    even=lambda i:((i%128)&(i//128)).bit_count()%2==0
    rows=[g[0] for g in orbits['affine_orbits'] if even(g[0])]
    groups=[g for g in orbits['linear_orbits'] if float(np.mean(u[g]))>1e-8]
    report=dict(rows=len(rows),variables=len(groups),matrix_entries=len(rows)*len(groups))
    if len(rows)*len(groups)>10_000_000:
        report['status']='matrix_size_cap';return report,{}
    labels=np.full(16384,len(groups),dtype=int)
    for j,g in enumerate(groups):labels[g]=j
    tau=np.array([(-1)**((i%128)&(i//128)).bit_count() for i in range(16384)])
    index=np.arange(16384);mat=np.empty((len(rows),len(groups)))
    for j,v in enumerate(rows):
        assert time.monotonic()-start<60,'construction cap'
        mat[j]=np.bincount(labels,weights=tau[index^v],minlength=len(groups)+1)[:-1]
    assert np.all(mat==np.rint(mat))
    c=np.array(objective(json.loads(SOURCE.read_text())))
    rhs=128*(6-c[rows])
    print(json.dumps(report),flush=True)
    result=linprog(np.zeros(len(groups)),A_ub=mat,b_ub=rhs,bounds=(0,None),method='highs-ds',
                   options={'time_limit':60,'threads':1,'primal_feasibility_tolerance':1e-9})
    report.update(status=int(result.status),message=result.message,seconds=time.monotonic()-start)
    arrays={}
    if result.x is not None:
        full=np.zeros(16384)
        for g,value in zip(groups,result.x):full[g]=value
        report.update(nonzero_variables=int(sum(result.x>1e-8)),
                      max_integer_constraint_residual=float(max(mat@result.x-rhs)),
                      minimum_dual=float(min(result.x)))
        arrays={'dual':full,'orbit_dual':result.x}
    return report,arrays


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    assert not args.output.exists() and not args.output.with_suffix('.npz').exists()
    with threadpool_limits(limits=1):report,arrays=run()
    with args.output.open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2)
    with args.output.with_suffix('.npz').open('xb') as stream:np.savez_compressed(stream,**arrays)
    print(json.dumps(report,indent=2))
