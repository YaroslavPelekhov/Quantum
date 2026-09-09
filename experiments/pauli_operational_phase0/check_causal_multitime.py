"""Frozen nested-tail diagnostic, not an author-code reproduction."""
import argparse
import json
from pathlib import Path
import time
import numpy as np
from threadpoolctl import threadpool_limits


def tail(rho, s):
    n = 2**s
    p = len(rho)//n
    return np.trace(rho.reshape(p,n,p,n), axis1=0, axis2=2)


def root(a, inverse=False):
    vals, vecs = np.linalg.eigh(a)
    assert min(vals) >= -1e-9
    factors = np.zeros_like(vals)
    positive = vals > 1e-12
    factors[positive] = vals[positive]**(-.5 if inverse else .5)
    return (vecs*factors)@vecs.conj().T


def update(rho, s):
    f = np.kron(np.eye(2), root(tail(rho,s-1)))@root(tail(rho,s),True)
    t = np.kron(np.eye(len(rho)//2**s), f)
    q = t@rho@t.conj().T
    return q/np.trace(q).real


def inspect(rho, k):
    marginals = [tail(rho,s) for s in range(1,2*k+2)]
    vals = [np.linalg.eigvalsh(m) for m in marginals]
    assert all(min(v) > -1e-9 for v in vals)
    assert abs(np.trace(rho)-1) < 1e-9
    residuals = [float(np.linalg.norm(marginals[s-1]-np.kron(np.eye(2)/2,marginals[s-2])))
                 for s in range(2,2*k+1,2)]
    return dict(ranks=[int(sum(v>1e-9)) for v in vals],
                spectra=[v.tolist() for v in vals], residuals=residuals)


def run():
    started = time.monotonic()
    rows = []
    for k,r in ((2,2),(2,8),(3,8),(3,32)):
        for seed in range(5):
            rng = np.random.default_rng(np.random.SeedSequence([k,r,seed]))
            x = rng.normal(size=(2**(2*k+1),r))+1j*rng.normal(size=(2**(2*k+1),r))
            original = x@x.conj().T
            original /= np.trace(original).real
            expected = [min(2**(2*k+1-s)*r,2**s) for s in range(1,2*k+2)]
            initial = inspect(original,k)
            assert initial['ranks'] == expected
            for direction in ('descending','ascending'):
                rho = original.copy()
                order = list(range(2,2*k+1,2))
                if direction == 'descending':
                    order.reverse()
                steps = []
                for sweep in range(2):
                    for s in order:
                        assert time.monotonic()-started < 60
                        rho = update(rho,s)
                        record = inspect(rho,k)
                        steps.append(dict(sweep=sweep+1,tail_size=s,**record))
                    if r == 2**(2*k-1) and direction == 'descending':
                        assert max(record['residuals']) < 1e-9
                rows.append(dict(k=k,rank=r,seed=seed,direction=direction,
                                 expected_ranks=expected,initial=initial,steps=steps))
    return dict(rows=rows,runs=len(rows),updates=sum(len(row['steps']) for row in rows),
                numerical_rank_mismatches=sum(st['ranks']!=row['expected_ranks']
                                              for row in rows for st in row['steps']),
                seconds=time.monotonic()-started,author_code_tested=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output',required=True,type=Path)
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        result = run()
    with args.output.open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))
