"""Exact modular correction; all heuristic choices face original checks."""
from fractions import Fraction
import hashlib
import json
import math
import time
import numpy as np
from scipy.linalg import qr
from sympy import prevprime
from threadpoolctl import threadpool_limits
from c020_exact_certificate import DATA,SOURCE,objective,pt_integer
from c021_exact_dual import verify


def modular_solve(matrix,rhs,prime):
    a=np.array(matrix,dtype=np.int64)%prime;b=np.array(rhs,dtype=np.int64)%prime;n=len(b)
    for k in range(n):
        choices=np.flatnonzero(a[k:,k])
        if not len(choices):return None
        j=k+int(choices[0])
        if j!=k:a[[k,j]]=a[[j,k]];b[[k,j]]=b[[j,k]]
        inv=pow(int(a[k,k]),-1,prime)
        a[k,k:]=(a[k,k:]*inv)%prime;b[k]=(b[k]*inv)%prime
        factors=a[k+1:,k].copy()
        a[k+1:,k:]=(a[k+1:,k:]-factors[:,None]*a[k,k:])%prime
        b[k+1:]=(b[k+1:]-factors*b[k])%prime
    x=np.zeros(n,dtype=np.int64)
    for k in range(n-1,-1,-1):x[k]=(b[k]-a[k,k+1:]@x[k+1:])%prime
    assert np.all((np.array(matrix,dtype=np.int64)@x-np.array(rhs,dtype=np.int64))%prime==0)
    return [int(v) for v in x]


def reconstruct(a,modulus):
    if not a:return Fraction(0)
    bound=math.isqrt(modulus//2);r0,r1=modulus,a;t0,t1=0,1
    while abs(r1)>bound:
        quotient=r0//r1;r0,r1=r1,r0-quotient*r1;t0,t1=t1,t0-quotient*t1
    if t1<0:r1,t1=-r1,-t1
    if not 0<t1<=bound or math.gcd(r1,t1)!=1 or (r1-a*t1)%modulus:return None
    return Fraction(r1,t1)


def run():
    start=time.monotonic();source=json.loads(SOURCE.read_text());c=np.array(objective(source),dtype=np.int64)
    orbits=json.loads((DATA/'c018_ppt_symmetry.json').read_text())
    with np.load(DATA/'c021_bosonic_ppt.npz',allow_pickle=False) as data:u=-data['C014_dual']
    # Numerical transform used only for discovery, never final acceptance.
    from verify_c019_saved import hadamard
    signs=np.array([(-1)**((i%128)&(i//128)).bit_count() for i in range(16384)])
    score=c+hadamard(signs*hadamard(u))/16384
    rows=[g[0] for g in orbits['affine_orbits'] if signs[g[0]]==1 and abs(score[g[0]]-6)<1e-8]
    groups=[g for g in orbits['linear_orbits'] if float(np.mean(u[g]))>1e-8]
    assert len(rows)*len(groups)<=10_000_000
    labels=np.full(16384,len(groups),dtype=int);idx=np.arange(16384)
    for j,g in enumerate(groups):labels[g]=j
    mat=np.array([np.bincount(labels,weights=signs[idx^v],minlength=len(groups)+1)[:-1] for v in rows],dtype=np.int64)
    rhs=128*(6-c[rows]);scale=2**20
    rounded=np.array([round(float(np.mean(u[g]))*scale) for g in groups],dtype=np.int64)
    with threadpool_limits(limits=1):
        r,p=qr(mat.T.astype(float),mode='r',pivoting=True)
        diag=np.abs(np.diag(r));rank=int(sum(diag>max(diag)*1e-10));selected=p[:rank]
        _,columns=qr(mat[selected].astype(float),mode='r',pivoting=True)
    pivots=columns[:rank];square=mat[selected][:,pivots];residual=rhs[selected]*scale-mat[selected]@rounded
    report=dict(rows=len(rows),variables=len(groups),discovery_rank=rank,rounding_denominator=scale,
                attempts=[],status='no_exact_correction',exact_six_proved=False)
    modulus=1;crt=[0]*rank;prime=65521
    for iteration in range(8):
        if time.monotonic()-start>120:report['status']='time_cap';break
        solution=modular_solve(square,residual,prime)
        attempt=dict(prime=prime,singular=solution is None);report['attempts'].append(attempt)
        if solution is not None:
            inv=pow(modulus%prime,-1,prime)
            crt=[old+modulus*((new-old)*inv%prime) for old,new in zip(crt,solution)];modulus*=prime
            vals=[reconstruct(v,modulus) for v in crt]
            attempt['all_coordinates_reconstructed']=all(v is not None for v in vals)
            if all(v is not None for v in vals):
                den=math.lcm(*(v.denominator for v in vals));nums=[v.numerator*(den//v.denominator) for v in vals]
                if den.bit_length()>512:attempt['denominator_cap']=True
                else:
                    exact=all(sum(int(a)*v for a,v in zip(row,nums))==int(b)*den for row,b in zip(square,residual))
                    attempt['exact_square_substitution']=exact
                    if exact:
                        orbitnums=[int(v)*den for v in rounded]
                        for j,v in zip(pivots,nums):orbitnums[int(j)]+=v
                        full=[0]*16384
                        for g,v in zip(groups,orbitnums):
                            for j in g:full[j]=v
                        common=scale*den;t=pt_integer(full)
                        upper=Fraction(max(int(c[i])*128*common+t[i] for i in range(16384) if signs[i]==1),128*common)
                        report.update(status='exact_correction_checked',minimum_numerator=min(full),
                                      exact_upper=str(upper),decimal_upper=float(upper),denominator_bits=common.bit_length())
                        if min(full)>=0 and upper==6:
                            cert=dict(source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                                      dual_numerators=full,dual_denominator=common,exact_upper='6',symmetric_support_required=True)
                            verify(cert)
                            with (DATA/'c030_exact_six_certificate.json').open('x',encoding='utf-8') as stream:json.dump(cert,stream)
                            report.update(status='exact_six_verified',exact_six_proved=True)
                        break
        prime=int(prevprime(prime))
    report['seconds']=time.monotonic()-start
    return report


if __name__=='__main__':
    output=DATA/'c030_modular_recovery.json';assert not output.exists()
    result=run()
    with output.open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2)
    print(json.dumps(result,indent=2))
