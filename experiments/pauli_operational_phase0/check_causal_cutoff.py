"""Registered practical gate; no author implementation imported."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from threadpoolctl import threadpool_limits
from check_causal_multitime import tail


def root(a, cutoff, inverse=False):
    v,u=np.linalg.eigh(a)
    assert min(v)>-1e-9
    w=np.zeros_like(v)
    mask=v>cutoff
    w[mask]=v[mask]**(-.5 if inverse else .5)
    return (u*w)@u.conj().T


def update(rho,s,cutoff):
    f=np.kron(np.eye(2),root(tail(rho,s-1),cutoff))@root(tail(rho,s),cutoff,True)
    t=np.kron(np.eye(32//2**s),f)
    q=t@rho@t.conj().T
    return q/np.trace(q).real


def stats(rho):
    eig=np.linalg.eigvalsh(rho)
    assert min(eig)>-1e-9
    assert abs(np.trace(rho)-1)<1e-9
    assert np.max(abs(rho-rho.conj().T))<1e-9
    pt=rho.reshape(4,8,4,8).transpose(2,1,0,3).reshape(32,32)
    # Independent block transpose of the four-dimensional side.
    blocks=np.block([[rho[j*8:(j+1)*8,i*8:(i+1)*8] for j in range(4)] for i in range(4)])
    assert np.max(abs(pt-blocks))<1e-12
    ptvals=np.linalg.eigvalsh(pt)
    return dict(negativity=float(-sum(ptvals[ptvals<0])),
                purity=float(np.trace(rho@rho).real),rank=int(sum(eig>1e-9)),
                min_eigenvalue=float(min(eig)),
                residual=max(float(np.linalg.norm(tail(rho,s)-np.kron(np.eye(2)/2,tail(rho,s-1))))
                             for s in (2,4)))


def run():
    start=time.monotonic()
    rows=[]
    pairs=[]
    states={}
    for rank,count in ((2,20),(8,5)):
        for seed in range(count):
            rng=np.random.default_rng(np.random.SeedSequence([2,rank,seed]))
            x=rng.normal(size=(32,rank))+1j*rng.normal(size=(32,rank))
            original=x@x.conj().T
            original/=np.trace(original).real
            local=[]
            for cutoff in (1e-8,1e-12,1e-14):
                rho=original.copy()
                for sweep in range(1,201):
                    assert time.monotonic()-start<60,'overall time cap'
                    for s in (4,2):
                        rho=update(rho,s,cutoff)
                    summary=stats(rho)
                    if summary['residual']<=1e-9:
                        break
                key=f'r{rank}_seed{seed}_cut{cutoff:.0e}'
                states[key]=rho
                row=dict(rank_input=rank,seed=seed,cutoff=cutoff,sweeps=sweep,
                         accepted=summary['residual']<=1e-9,state_key=key,**summary)
                rows.append(row)
                local.append(row)
            for left,right in ((0,1),(1,2),(0,2)):
                a,b=local[left],local[right]
                distance=float(sum(abs(np.linalg.eigvalsh(states[a['state_key']]-states[b['state_key']])))/2)
                pairs.append(dict(rank_input=rank,seed=seed,left=a['cutoff'],right=b['cutoff'],
                                  accepted=a['accepted'] and b['accepted'],
                                  negativity_delta=abs(a['negativity']-b['negativity']),
                                  trace_distance=distance))
    primary=[p for p in pairs if p['rank_input']==2 and p['left']==1e-8 and p['right']==1e-14]
    accepted=all(p['accepted'] for p in primary)
    median=float(np.median([p['negativity_delta'] for p in primary]))
    report=dict(rows=rows,pairs=pairs,seconds=time.monotonic()-start,
                primary_all_accepted=accepted,primary_median_negativity_delta=median,
                primary_gate='pass' if accepted and median>=.01 else 'fail' if accepted else 'inconclusive',
                primary_median_trace_distance=float(np.median([p['trace_distance'] for p in primary])),
                primary_max_trace_distance=max(p['trace_distance'] for p in primary))
    return report,states


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    archive=args.output.with_suffix('.npz')
    assert not args.output.exists() and not archive.exists()
    with threadpool_limits(limits=1):
        result,states=run()
    with archive.open('xb') as stream:
        np.savez_compressed(stream,**states)
    result['state_archive_sha256']=hashlib.sha256(archive.read_bytes()).hexdigest()
    with args.output.open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows','pairs')},indent=2))
