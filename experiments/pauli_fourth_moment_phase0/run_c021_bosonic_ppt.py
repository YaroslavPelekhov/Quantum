"""Fixed bosonic-support PPT primal/dual numerical diagnostic."""
import argparse
from fractions import Fraction
import json
from pathlib import Path
import time
import numpy as np
from threadpoolctl import threadpool_limits
from verify_c019_saved import hadamard


def solve(name,labels,w,q,bound):
    start=time.monotonic();d=2**q;n=d*d
    sign=np.array([(-1)**((v%d)&(v//d)).bit_count() for v in range(n)])
    even=sign>0;m=int(sum(even))
    c=np.array([sum(weight*(-1)**((x&z).bit_count()+((v%d)&z).bit_count()+((v//d)&x).bit_count())
                    for (x,z),weight in zip(labels,w)) for v in range(n)],dtype=float)
    def a(v):return hadamard(sign*hadamard(v))/n
    def project(v):
        selected=v[even];u=np.sort(selected)[::-1]
        offsets=(np.cumsum(u)-n)/np.arange(1,m+1)
        j=np.nonzero(u>offsets)[0][-1]
        out=np.zeros(n);out[even]=np.maximum(selected-offsets[j],0);return out
    ref=even.astype(float)*n/m;ptref=a(ref)
    assert min(ptref)>0 and abs(min(ptref)-d/(d+1))<1e-12
    x=ref.copy();bar=x.copy();y=np.zeros(n);avg=np.zeros(n)
    best=dict(value=float(c@x/n),iteration=0,kind='reference');bestp=x/n
    upper=float(max(c[even]));besty=y.copy();history=[];status='iteration_cap'
    for iteration in range(1,20001):
        if time.monotonic()-start>=60:status='time_cap';break
        y=np.minimum(y+.9*a(bar),0)
        ay=a(y);new=project(x+.9*c-.9*ay);bar=2*new-x;x=new;avg+=(x-avg)/iteration
        if iteration%100:continue
        candidate_upper=float(max((c-ay)[even]))
        if candidate_upper<upper:upper=candidate_upper;besty=y.copy()
        for kind,t in [('last',x),('average',avg)]:
            pt=a(t);mix=max(0,float(max(-pt/ptref)))+1e-10
            p=(t+mix*ref)/sum(t+mix*ref);value=float(c@p)
            history.append(dict(iteration=iteration,kind=kind,raw_value=float(c@t/n),
                                repaired_value=value,min_scaled_pt=float(min(pt)),dual_candidate=candidate_upper))
            if value>best['value']:best=dict(value=value,iteration=iteration,kind=kind);bestp=p.copy()
        if name=='G8':assert upper>=3.0448-1e-6
        if best['value']>bound+.001:status='primal_candidate';break
    return dict(name=name,q=q,status=status,best=best,dual_upper_candidate=upper,
                history=history,seconds=time.monotonic()-start),bestp,besty


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True,type=Path);args=parser.parse_args()
    assert not args.output.exists() and not args.output.with_suffix('.npz').exists()
    data=Path('results/pauli_fourth_moment_phase0')
    cert=json.loads((data/'c020_exact_ppt_certificate.json').read_text())
    mass=Fraction(sum(v for i,v in enumerate(cert['numerators']) if ((i%128)&(i//128)).bit_count()%2),cert['denominator'])
    assert mass>0
    control=json.loads((data/'almost_clique_closure_counterexample.json').read_text());q=len(control['pauli_words'][0])
    labels=[[sum(1<<(q-1-j) for j,c in enumerate(word) if c in 'XY'),sum(1<<(q-1-j) for j,c in enumerate(word) if c in 'YZ')]
            for word in control['pauli_words']]
    target=json.loads((data/'scf_two_xx_weight_c014.json').read_text());reports=[];arrays={}
    print(json.dumps(dict(C020_antisymmetric_mass=str(mass))),flush=True)
    with threadpool_limits(limits=1):
        for name,lab,w,qubits,bound in [('G8',labels,control['weights'],q,3),('C014',target['standard_SAUR_labels'],target['records'][0]['weights'],7,6)]:
            report,p,y=solve(name,lab,w,qubits,bound);reports.append(report)
            arrays[name+'_probabilities']=p;arrays[name+'_dual']=y
            print(json.dumps({k:v for k,v in report.items() if k!='history'}),flush=True)
    with args.output.open('x',encoding='utf-8') as stream:json.dump(dict(C020_antisymmetric_mass=str(mass),reports=reports),stream,indent=2)
    with args.output.with_suffix('.npz').open('xb') as stream:np.savez_compressed(stream,**arrays)
