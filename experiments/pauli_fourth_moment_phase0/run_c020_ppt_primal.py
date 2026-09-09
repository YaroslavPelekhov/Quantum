"""Registered full-coordinate PDHG feasibility search for a PPT witness."""
import argparse
import json
from pathlib import Path
import time
import numpy as np
from threadpoolctl import threadpool_limits
from verify_c019_saved import hadamard


def run():
    started=time.monotonic();n=16384
    source=json.loads(Path('results/pauli_fourth_moment_phase0/scf_two_xx_weight_c014.json').read_text())
    tau=np.array([(-1)**((v%128)&(v//128)).bit_count() for v in range(n)])
    c=np.array([sum(w*(-1)**((x&z).bit_count()+((v%128)&z).bit_count()+((v//128)&x).bit_count())
                    for (x,z),w in zip(source['standard_SAUR_labels'],source['records'][0]['weights']))
                for v in range(n)],dtype=float)
    def a(v):return hadamard(tau*hadamard(v))/n
    def simplex(v):
        u=np.sort(v)[::-1];s=(np.cumsum(u)-n)/np.arange(1,n+1)
        j=np.nonzero(u>s)[0][-1]
        return np.maximum(v-s[j],0)
    assert np.max(abs(a(np.ones(n))-1))<1e-12
    x=np.ones(n);bar=x.copy();y=np.zeros(n);average=np.zeros(n)
    history=[];best=dict(value=0.,iteration=0,kind='initial');bestp=x/n
    status='iteration_cap'
    for iteration in range(1,20001):
        if time.monotonic()-started>=60:status='time_cap';break
        y=np.minimum(y+.9*a(bar),0)
        new=simplex(x+.9*c-.9*a(y));bar=2*new-x;x=new
        average+=(x-average)/iteration
        if iteration%100:continue
        for kind,t in [('last',x),('average',average)]:
            minimum=float(min(a(t)));shift=max(0,-minimum)+1e-10
            p=(t+shift)/sum(t+shift);value=float(c@p)
            history.append(dict(iteration=iteration,kind=kind,raw_value=float(c@t/n),
                                minimum_scaled_pt=minimum,repaired_value=value))
            if value>best['value']:
                best=dict(value=value,iteration=iteration,kind=kind);bestp=p.copy()
        if best['value']>6.001:status='candidate';break
    return dict(status=status,best=best,history=history,seconds=time.monotonic()-started,
                quantum_target_proved=False),bestp


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    assert not args.output.exists() and not args.output.with_suffix('.npz').exists()
    with threadpool_limits(limits=1):report,p=run()
    with args.output.open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2)
    with args.output.with_suffix('.npz').open('xb') as stream:np.savez_compressed(stream,probabilities=p)
    print(json.dumps({k:v for k,v in report.items() if k!='history'},indent=2))
