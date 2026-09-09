"""Post-hoc precision audit, frozen case k=2,r=2,seed=0, descending.

80 decimal digits, support threshold 1e-60; not an exact rank proof.
Uses the same float Gaussian factor converted BEFORE forming its Gram.
"""
import argparse
import json
from pathlib import Path
import time
import mpmath as mp
import numpy as np


def tail(a, s):
    n = 2**s
    return mp.matrix([
        [sum(a[h*n+i,h*n+j] for h in range(a.rows//n)) for j in range(n)] for i in range(n)])


def extend(a, count):
    return mp.matrix([[a[i%a.rows,j%a.cols] if i//a.rows==j//a.cols else 0
                       for j in range(count*a.cols)] for i in range(count*a.rows)])


def root(a, inverse=False):
    vals, vecs = mp.eighe(a)
    assert min(vals) > -mp.mpf('1e-60')
    factors = [v**(-mp.mpf('.5') if inverse else mp.mpf('.5'))
               if v>mp.mpf('1e-60') else 0 for v in vals]
    return vecs*mp.diag(factors)*vecs.H


def run():
    mp.mp.dps = 80
    start = time.monotonic()
    rng = np.random.default_rng(np.random.SeedSequence([2,2,0]))
    x0 = rng.normal(size=(32,2))+1j*rng.normal(size=(32,2))
    x = mp.matrix([[mp.mpc(float(v.real),float(v.imag)) for v in row] for row in x0])
    rho = x*x.H
    rho /= sum(rho[i,i] for i in range(32))
    rows = []
    for iteration,s in enumerate((4,2,4,2),1):
        assert time.monotonic()-start < 60
        f = extend(root(tail(rho,s-1)),2)*root(tail(rho,s),True)
        t = extend(f,32//2**s)
        rho = t*rho*t.H
        rho /= sum(rho[i,i] for i in range(32))
        eig = mp.eighe(tail(rho,3),eigvals_only=True)
        rows.append(dict(iteration=iteration,tail_size=s,
                         earlier_marginal_spectrum=[mp.nstr(v,40) for v in eig]))
    return dict(dps=80,threshold='1e-60',rows=rows,seconds=time.monotonic()-start,
                scope='post-hoc diagnostic, different precision and eigensolver, not exact proof')


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=run()
    with args.output.open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2)
    print(json.dumps(result,indent=2))
