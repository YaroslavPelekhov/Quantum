"""Reuse a modular factorization for exact rational dual correction."""
from fractions import Fraction
import hashlib
import json
import math
import time
import numpy as np
from scipy.linalg import qr
from threadpoolctl import threadpool_limits
from c020_exact_certificate import DATA,SOURCE,objective,pt_integer
from c021_exact_dual import verify
from verify_c019_saved import hadamard
from run_c030_modular_recovery import reconstruct


def factor(matrix,p):
    a=matrix.copy()%p;steps=[];n=len(a)
    for k in range(n):
        choices=np.flatnonzero(a[k:,k]);assert len(choices),'singular prime'
        j=k+int(choices[0]);a[[k,j]]=a[[j,k]]
        inv=pow(int(a[k,k]),-1,p);a[k,k:]=a[k,k:]*inv%p
        factors=a[k+1:,k].copy();steps.append((j,inv,factors))
        a[k+1:,k:]=(a[k+1:,k:]-factors[:,None]*a[k,k:])%p
    return a,steps


def solve_factored(upper,steps,rhs,p):
    b=rhs.copy()%p;n=len(b)
    for k,(j,inv,factors) in enumerate(steps):
        b[k],b[j]=b[j],b[k];b[k]=b[k]*inv%p
        b[k+1:]=(b[k+1:]-factors*b[k])%p
    x=np.zeros(n,dtype=np.int64)
    for k in range(n-1,-1,-1):x[k]=(b[k]-upper[k,k+1:]@x[k+1:])%p
    return x


def run():
    start=time.monotonic();source=json.loads(SOURCE.read_text());c=np.array(objective(source),dtype=np.int64)
    orbits=json.loads((DATA/'c018_ppt_symmetry.json').read_text())
    with np.load(DATA/'c021_bosonic_ppt.npz',allow_pickle=False) as data:u=-data['C014_dual']
    signs=np.array([(-1)**((i%128)&(i//128)).bit_count() for i in range(16384)])
    score=c+hadamard(signs*hadamard(u))/16384
    rows=[g[0] for g in orbits['affine_orbits'] if signs[g[0]]==1 and abs(score[g[0]]-6)<1e-8]
    groups=[g for g in orbits['linear_orbits'] if float(np.mean(u[g]))>1e-8]
    assert len(rows)*len(groups)<=10_000_000
    labels=np.full(16384,len(groups),dtype=int);index=np.arange(16384)
    for j,g in enumerate(groups):labels[g]=j
    mat=np.array([np.bincount(labels,weights=signs[index^v],minlength=len(groups)+1)[:-1] for v in rows],dtype=np.int64)
    rhs=128*(6-c[rows]);scale=2**20
    rounded=np.array([round(float(np.mean(u[g]))*scale) for g in groups],dtype=np.int64)
    with threadpool_limits(limits=1):
        r,piv=qr(mat.T.astype(float),mode='r',pivoting=True)
        diag=np.abs(np.diag(r));rank=int(sum(diag>max(diag)*1e-10));selected=piv[:rank]
        _,columns=qr(mat[selected].astype(float),mode='r',pivoting=True)
    pivots=columns[:rank];square=mat[selected][:,pivots];original=rhs[selected]*scale-mat[selected]@rounded
    prime=65521;upper,steps=factor(square,prime);residual=original.copy();acc=[0]*rank;modulus=1
    report=dict(rows=len(rows),variables=len(groups),discovery_rank=rank,attempts=[],
                status='lift_cap',exact_six_proved=False)
    for lift in range(1,129):
        if time.monotonic()-start>120:report['status']='time_cap';break
        digit=solve_factored(upper,steps,residual,prime)
        delta=residual-square@digit
        assert np.all(delta%prime==0)
        residual=delta//prime
        acc=[a+modulus*int(d) for a,d in zip(acc,digit)];modulus*=prime
        if lift%8:continue
        vals=[reconstruct(a,modulus) for a in acc]
        attempt=dict(lift=lift,modulus_bits=modulus.bit_length(),all_reconstructed=all(v is not None for v in vals))
        report['attempts'].append(attempt)
        print(json.dumps(attempt),flush=True)
        if not all(v is not None for v in vals):continue
        den=math.lcm(*(v.denominator for v in vals));nums=[v.numerator*(den//v.denominator) for v in vals]
        exact=all(sum(int(a)*v for a,v in zip(row,nums))==int(b)*den for row,b in zip(square,original))
        attempt['exact_square_substitution']=exact
        if not exact:continue
        orbitnums=[int(v)*den for v in rounded]
        for j,v in zip(pivots,nums):orbitnums[int(j)]+=v
        full=[0]*16384
        for g,v in zip(groups,orbitnums):
            for j in g:full[j]=v
        common=scale*den;t=pt_integer(full)
        bound=Fraction(max(int(c[i])*128*common+t[i] for i in range(16384) if signs[i]==1),128*common)
        report.update(status='exact_correction_checked',exact_upper=str(bound),decimal_upper=float(bound),
                      minimum_numerator=min(full),denominator_bits=common.bit_length())
        candidate=dict(source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                       dual_numerators=full,dual_denominator=common,exact_upper=str(bound),symmetric_support_required=True)
        with (DATA/'c031_candidate.json').open('x',encoding='utf-8') as stream:json.dump(candidate,stream)
        if min(full)>=0 and bound==6:
            verify(candidate);report.update(status='exact_six_verified',exact_six_proved=True)
        break
    else:lift=128
    if report['status'] in ('lift_cap','time_cap'):
        checkpoint=dict(lift=lift if report['status']=='lift_cap' else lift-1,prime=prime,modulus=modulus,
                        accumulator=acc,residual=residual.tolist(),pivots=pivots.tolist(),selected_rows=selected.tolist())
        with (DATA/'c031_checkpoint.json').open('x',encoding='utf-8') as stream:json.dump(checkpoint,stream)
    report['seconds']=time.monotonic()-start
    return report


if __name__=='__main__':
    path=DATA/'c031_dixon.json';assert not path.exists()
    result=run()
    with path.open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2)
    print(json.dumps(result,indent=2))
