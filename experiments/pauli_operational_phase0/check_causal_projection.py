"""Bounded transcription of one-step pseudoinverse causal filtering."""
import json
import time
import numpy as np
from threadpoolctl import threadpool_limits


def marginals(rho):
    t = rho.reshape(2,2,2,2,2,2)
    m = np.trace(t, axis1=0, axis2=3).reshape(4,4)
    r = np.trace(m.reshape(2,2,2,2), axis1=0, axis2=2)
    return m, r


def root(a, inverse=False):
    eig, basis = np.linalg.eigh(a)
    assert min(eig) >= -1e-9
    values = np.zeros_like(eig)
    mask = eig > 1e-12
    values[mask] = 1/np.sqrt(eig[mask]) if inverse else np.sqrt(eig[mask])
    return (basis*values)@basis.conj().T


def step(rho):
    m, r = marginals(rho)
    filt = np.kron(np.eye(4), root(r))@np.kron(np.eye(2),root(m, True))
    updated = filt@rho@filt.conj().T
    return updated/np.trace(updated).real


def residual(rho):
    m,r = marginals(rho)
    return float(np.linalg.norm(m-np.kron(np.eye(2)/2,r)))


def projector(v):
    return np.outer(v,v.conj())/np.vdot(v,v).real


def run():
    started=time.monotonic()
    ghz=projector(np.array([1,0,0,0,0,0,0,1],complex))
    causal=projector(np.array([1,0,0,0,0,0,1,0],complex))
    for positive in (np.eye(8)/8,causal):
        assert residual(positive)<1e-12 and residual(step(positive))<1e-12
    assert np.max(abs(step(ghz)-ghz))<1e-12 and abs(residual(ghz)-.5)<1e-12
    rows=[]
    for seed in range(10):
        rng=np.random.default_rng(seed)
        rho=projector(rng.normal(size=8)+1j*rng.normal(size=8))
        observed={0:residual(rho)}
        for iteration in range(1,301):
            assert time.monotonic()-started<30, 'diagnostic time cap'
            rho=step(rho)
            if iteration in (3,30,300):
                observed[iteration]=residual(rho)
        rows.append(dict(seed=seed,residuals=observed))
    print(json.dumps(dict(ghz_fixed=True,ghz_residual=residual(ghz),
                          positive_controls=2, random_rank_one=rows,
                          seconds=time.monotonic()-started,
                          source_implementation_tested=False),indent=2))


if __name__=='__main__':
    with threadpool_limits(limits=1):
        run()
