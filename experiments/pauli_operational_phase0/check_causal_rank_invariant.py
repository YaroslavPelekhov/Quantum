"""Bounded post-derivation diagnostic; see CAUSAL_RANK_INVARIANT.md."""
import argparse
import json
from pathlib import Path
import time
import numpy as np
from threadpoolctl import threadpool_limits


def marginals(rho, d):
    m = np.trace(rho.reshape((d,)*6), axis1=0, axis2=3).reshape(d*d, d*d)
    return m, np.trace(m.reshape((d,)*4), axis1=0, axis2=2)


def root(a, inverse=False):
    vals, vecs = np.linalg.eigh(a)
    assert min(vals) > -1e-10
    factors = np.zeros_like(vals)
    mask = vals > 1e-10
    factors[mask] = vals[mask]**(-.5 if inverse else .5)
    return (vecs*factors)@vecs.conj().T


def step(rho, d):
    m, r = marginals(rho, d)
    t = np.kron(np.eye(d), np.kron(np.eye(d), root(r))@root(m, True))
    result = t@rho@t.conj().T
    return result/np.trace(result).real


def describe(rho, d):
    m, r = marginals(rho, d)
    # Separate index-slice contractions, not calls to marginals().
    other_m = sum(rho[a*d*d:(a+1)*d*d, a*d*d:(a+1)*d*d] for a in range(d))
    other_r = sum(other_m[b*d:(b+1)*d, b*d:(b+1)*d] for b in range(d))
    assert np.max(abs(m-other_m)) < 1e-12
    assert np.max(abs(r-other_r)) < 1e-12
    spectra = [np.linalg.eigvalsh(a) for a in (rho, m, r)]
    assert all(min(s) > -1e-10 for s in spectra)
    assert abs(np.trace(rho)-1) < 1e-10
    return dict(ranks=[int(sum(s > 1e-10)) for s in spectra],
                spectra=[s.tolist() for s in spectra],
                residual=float(np.linalg.norm(m-np.kron(np.eye(d)/d, r))))


def run():
    start = time.monotonic()
    rows = []
    for d in (2, 3, 4):
        for rank in range(1, d+1):
            for seed in range(10):
                assert time.monotonic()-start < 60
                rng = np.random.default_rng(np.random.SeedSequence([d, rank, seed]))
                x = rng.normal(size=(d**3, rank))+1j*rng.normal(size=(d**3, rank))
                rho = x@x.conj().T
                rho /= np.trace(rho).real
                before = describe(rho, d)
                after = describe(step(rho, d), d)
                expected = [rank, min(d*rank, d*d), d]
                assert before['ranks'] == after['ranks'] == expected
                if rank == d:
                    assert after['residual'] < 1e-9
                else:
                    assert after['residual'] > 1e-9
                rows.append(dict(d=d, rank=rank, seed=seed, before=before, after=after))
    v = np.zeros(8, complex)
    v[0] = v[6] = 1/np.sqrt(2)
    control = np.outer(v, v.conj())
    assert describe(control, 2)['residual'] < 1e-12
    assert np.max(abs(step(control, 2)-control)) < 1e-12
    return dict(rows=rows, inputs=len(rows), positive_controls=1,
                cutoff=1e-10, seconds=time.monotonic()-start,
                scope='numerical one-step checks, not proof or author implementation')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        result = run()
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}, indent=2))
