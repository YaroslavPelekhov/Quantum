"""Explore facial reduction of the two remaining state-moment duals.

Numerical discovery output is never itself labelled an exact certificate.
"""
from __future__ import annotations
import argparse
import json
from fractions import Fraction
from pathlib import Path
import cvxpy as cp
import networkx as nx
import numpy as np
import sympy as sp
from scipy.linalg import qr, lstsq
from state_moment_sdp import monomial_basis, multiply_monomials


def recover(record, denominator, cache):
    g = nx.from_graph6_bytes(record['support_graph6'].encode())
    basis, words = monomial_basis(g, 2)
    loc = {w: i for i, w in enumerate(words)}
    edges = {tuple(sorted(e)) for e in g.edges()}
    products = [[multiply_monomials(l, r, words, loc, edges) for r in basis] for l in basis]
    keys = sorted({k for row in products for k, s in row if k is not None})
    kl = {k: i for i, k in enumerate(keys)}
    n, m = len(basis), len(keys)
    y = cp.Variable(m)
    M = cp.bmat([[0 if k is None else s*y[kl[k]] for k, s in row] for row in products])
    c = np.zeros(m)
    for i in g:
        c[kl[(loc[(i,)], loc[(i,)])]] = record['weights'][i]
    con = [M >> 0, y[kl[(loc[()],)]] == 1]
    problem = cp.Problem(cp.Maximize(c@y), con)
    problem.solve(solver='CLARABEL')
    Z = con[0].dual_value
    e, V = np.linalg.eigh(Z)
    K = V[:, e < 1e-4]
    _, _, piv = qr(K.T, pivoting=True)
    normalized = K @ np.linalg.inv(K[piv[:K.shape[1]], :])
    Kr = sp.Matrix([[sp.Rational(Fraction(float(x)).limit_denominator(denominator))
                     for x in row] for row in normalized])
    error = float(np.max(abs(normalized-np.array(Kr, float))))
    B = sp.Matrix.hstack(*Kr.T.nullspace())
    Br = np.array(B, float)
    d = B.cols
    mats = np.zeros((m, d, d))
    for i, row in enumerate(products):
        for j, (k, s) in enumerate(row):
            if k is not None:
                mats[kl[k]] += s*np.outer(Br[i], Br[j])
    t = -c.copy()
    t[kl[(loc[()],)]] += 1.5
    upper = [(i, j) for i in range(d) for j in range(i, d)]
    Aeq = np.stack([mats[:, i, j]*(1 if i == j else 2) for i, j in upper], axis=1)
    _, R, pivrows = qr(Aeq.T, pivoting=True, mode='economic')
    rank = int(np.sum(abs(np.diag(R)) > 1e-9))
    selected = pivrows[:rank]
    estimate = lstsq(Aeq, t, lapack_driver='gelsy')[0]
    residual = float(np.max(abs(Aeq@estimate-t)))
    print(json.dumps({'index': record['representative_index'], 'primal_value': problem.value,
                      'kernel_dimension': K.shape[1], 'rational_kernel_error': error,
                      'range_dimension': d, 'linear_rank': rank, 'linear_residual': residual}), flush=True)
    if residual > 1e-7:
        return {'status': 'rational_kernel_rejected', 'linear_residual': residual}
    Y = cp.Variable((d, d), symmetric=True)
    delta = cp.Variable()
    cons = [Y-delta*np.eye(d) >> 0, cp.trace(Y) <= 100]
    cons += [cp.sum(cp.multiply(mats[j], Y)) == t[j] for j in selected]
    reduced = cp.Problem(cp.Maximize(delta), cons)
    try:
        reduced.solve(solver='CLARABEL')
    except cp.error.SolverError:
        reduced.solve(solver='SCS', eps=1e-7, max_iters=50000)
    print(json.dumps({'index': record['representative_index'], 'reduced_status': reduced.status,
                      'delta': None if delta.value is None else float(delta.value)}), flush=True)
    if Y.value is not None:
        np.savez(cache, B=np.array([[str(x) for x in row] for row in B.tolist()]),
                 Y=Y.value, Aeq=Aeq, target=t, selected=selected,
                 upper=np.array(upper), graph6=record['support_graph6'],
                 index=record['representative_index'])
    return {'status': 'numerical_discovery_only', 'delta': None if delta.value is None else float(delta.value)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--index', type=int, required=True)
    p.add_argument('--denominator', type=int, default=12)
    p.add_argument('--cache', type=Path, required=True)
    args = p.parse_args()
    records = json.loads(args.input.read_text())['residual_atoms']
    rec = next(r for r in records if r['representative_index'] == args.index)
    print(recover(rec, args.denominator, args.cache))


if __name__ == '__main__':
    main()
