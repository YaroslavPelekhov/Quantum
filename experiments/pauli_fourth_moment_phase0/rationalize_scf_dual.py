"""Convert a discovery dual to exact rational data, then check it independently.

python-flint is an optional accelerator for SymPy's exact elimination.
The verifier requires neither the numerical solver nor its discovery cache.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from fractions import Fraction
import json
from pathlib import Path
import time
import sympy as sp


def independent_moment_product(left, right, edges):
    """Real part of f_left^* f_right, directly from inversion parity."""
    expectations_left, op_left = left
    expectations_right, op_right = right
    word = list(reversed(op_left)) + list(op_right)
    parity = sum(tuple(sorted((word[i], word[j]))) in edges
                 for i in range(len(word)) for j in range(i+1, len(word))
                 if word[i] > word[j]) % 2
    reduced = tuple(v for v in sorted(set(word)) if word.count(v) % 2)
    # A canonical Pauli word is anti-Hermitian exactly when its internal
    # anticommutation-edge count is odd. Its real expectation then vanishes.
    if sum((i, j) in edges for pos, i in enumerate(reduced) for j in reduced[pos+1:]) % 2:
        return None, 0
    factors = [tuple(w) for w in expectations_left + expectations_right if w]
    if reduced:
        factors.append(reduced)
    return tuple(sorted(factors)), (-1)**parity


def verify(certificate):
    if not __debug__:
        raise RuntimeError('Exact verification requires assertions enabled; do not use python -O.')
    # Bind the algebra to the graph6 string without importing a graph library.
    encoded = [ord(ch)-63 for ch in certificate['support_graph6']]
    n = encoded[0]
    assert 1 <= n <= 62
    bits = [(value >> shift) & 1 for value in encoded[1:] for shift in range(5, -1, -1)]
    pairs = [(i, j) for j in range(1, n) for i in range(j)]
    edges = {pair for pair, bit in zip(pairs, bits) if bit}
    assert edges == {tuple(e) for e in certificate['edges']}
    assert sp.Rational(certificate['exact_upper_bound']) == sp.Rational(3, 2)
    assert len(certificate['weights']) == n
    weights = [sp.Rational(w) for w in certificate['weights']]
    assert all(w >= 0 for w in weights)
    stable_values = [sum(weights[i] for i in range(n) if mask >> i & 1)
                     for mask in range(1 << n)
                     if all(not (mask >> i & 1 and mask >> j & 1) for i, j in edges)]
    assert max(stable_values) == sp.Rational(3, 2)
    B = sp.Matrix(certificate['range_basis'])
    Q = sp.Matrix(certificate['rational_gram'])
    assert Q == Q.T
    # Strictly positive rational LDL pivots certify positive definiteness.
    lower, diagonal = Q.LDLdecomposition(hermitian=False)
    assert all(diagonal[i, i] > 0 for i in range(Q.rows))
    assert lower*diagonal*lower.T == Q
    Z = B*Q*B.T
    basis = certificate['moment_basis']
    assert B.rows == len(basis) and B.cols == Q.rows
    for factors, op in basis:
        for word in factors + [op]:
            assert word == sorted(set(word)) and all(0 <= v < n for v in word)
        for word in factors:
            assert sum((i, j) in edges for k, i in enumerate(word) for j in word[k+1:]) % 2 == 0
    coefficients = defaultdict(lambda: sp.S.Zero)
    for i, left in enumerate(basis):
        for j, right in enumerate(basis):
            key, sign = independent_moment_product(left, right, edges)
            if key is not None and Z[i, j]:
                coefficients[key] += sign*Z[i, j]
    expected = {(): sp.Rational(3, 2)}
    for i, weight in enumerate(certificate['weights']):
        expected[((i,), (i,))] = -sp.Rational(weight)
    for key in coefficients.keys() | expected.keys():
        assert coefficients[key] == expected.get(key, 0), (key, coefficients[key], expected.get(key, 0))
    return {'exact_coefficient_identity': True, 'positive_rational_LDL_pivots': Q.rows,
            'minimum_LDL_pivot_as_decimal': float(min(diagonal[i, i] for i in range(Q.rows))),
            'moment_basis_size': len(basis), 'universal_real_Pauli_algebra': True,
            'graph6_edge_binding': True, 'exact_stable_set_lower_bound': '3/2'}


def rationalize(cache_path, output):
    import networkx as nx
    import numpy as np
    from state_moment_sdp import monomial_basis
    started = time.monotonic()
    cache = np.load(cache_path)
    B = sp.Matrix(cache['B'].tolist())
    d = B.cols
    upper = [tuple(map(int, pair)) for pair in cache['upper']]
    Araw = cache['Aeq'][cache['selected']]
    traw = cache['target'][cache['selected']]
    assert np.max(abs(Araw*4-np.rint(Araw*4))) < 1e-9
    A = sp.Matrix(np.rint(Araw*4).astype(int).tolist())
    target = sp.Matrix(np.rint(traw*4).astype(int).tolist())
    reduced, pivots = A.row_join(target).rref()
    assert len(upper) not in pivots, 'inconsistent affine equations'
    print(f'exact RREF: {len(pivots)} pivots, {time.monotonic()-started:.2f}s', flush=True)
    free = [i for i in range(len(upper)) if i not in pivots]
    values = [sp.S.Zero]*len(upper)
    for index in free:
        i, j = upper[index]
        values[index] = sp.Rational(round(float(cache['Y'][i, j])*1_000_000), 1_000_000)
    for row, index in enumerate(pivots):
        values[index] = reduced[row, -1] - sum(reduced[row, col]*values[col] for col in free)
    assert A*sp.Matrix(values) == target
    Q = sp.zeros(d)
    for (i, j), value in zip(upper, values):
        Q[i, j] = Q[j, i] = value
    graph6 = str(cache['graph6'])
    graph = nx.from_graph6_bytes(graph6.encode())
    basis, words = monomial_basis(graph, 2)
    # Weight data is bound to the audited repository facet record.
    source = json.loads((output.parent/'scf_order9_facet_reduction.json').read_text())
    record = next(r for r in source['residual_atoms'] if r['representative_index'] == int(cache['index']))
    assert record['support_graph6'] == graph6
    certificate = {
        'experiment': 'exact_rational_state_moment_dual',
        'representative_index': int(cache['index']), 'support_graph6': graph6,
        'edges': [list(e) for e in sorted(graph.edges())],
        'weights': [str(sp.Rational(str(w))) for w in record['weights']],
        'exact_upper_bound': '3/2',
        'moment_basis': [[[list(words[f]) for f in factors], list(words[op])] for factors, op in basis],
        'range_basis': [[str(v) for v in row] for row in B.tolist()],
        'rational_gram': [[str(v) for v in row] for row in Q.tolist()],
        'identity': '3/2 - sum_i w_i <P_i>^2 = <f^* (B Q B^T) f>, real part',
        'status': 'awaiting_exact_verification'}
    certificate['verification'] = verify(certificate)
    certificate['status'] = 'exact_rational_certificate_verified'
    output.write_text(json.dumps(certificate, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'index': certificate['representative_index'], 'status': certificate['status'],
                      'seconds': time.monotonic()-started, **certificate['verification']}), flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--cache', type=Path)
    p.add_argument('--output', type=Path)
    p.add_argument('--verify', type=Path)
    args = p.parse_args()
    if args.verify:
        print(json.dumps(verify(json.loads(args.verify.read_text()))))
    else:
        if args.cache is None or args.output is None:
            p.error('provide --cache and --output, or --verify')
        rationalize(args.cache, args.output)


if __name__ == '__main__':
    main()
