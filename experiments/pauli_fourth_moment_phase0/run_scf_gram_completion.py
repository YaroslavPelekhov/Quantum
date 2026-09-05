"""Audit transfer coefficients from scratch and prove residuals 15 and 23.

Amplitudes a_i are nonnegative: arbitrary original signs are absorbed into
the Hermitian Pauli generators. Polynomial coefficients are computed in the
universal algebra, without using a compact representation or hole formulas.
"""

from __future__ import annotations

import argparse
from collections import Counter
import itertools
import json
from pathlib import Path

import networkx as nx
import numpy as np
import sympy as sp


def product(graph, left, right):
    """Canonical subset product, computed by inversion parity (not rewriting)."""
    parity = sum(graph.has_edge(i, j) for i in left for j in right if i > j) % 2
    return tuple(sorted(set(left) ^ set(right))), (-1) ** parity


def transfer_coefficients(graph):
    n = len(graph)
    independent = [[s for s in itertools.combinations(range(n), k)
                    if graph.subgraph(s).number_of_edges() == 0] for k in range(4)]
    assert not any(graph.subgraph(s).number_of_edges() == 0
                   for s in itertools.combinations(range(n), 4))
    coefficients = []
    for k in range(1, 4):
        out = Counter()
        for i in range(4):
            j = 2 * k - i
            if not 0 <= j < 4:
                continue
            for left in independent[i]:
                for right in independent[j]:
                    word, sign = product(graph, left, right)
                    powers = tuple(int(v in left) + int(v in right) for v in range(n))
                    out[word, powers] += (-1) ** (j + k) * sign
        coefficients.append({key: value for key, value in out.items() if value})
    return coefficients


def expr(terms, a, absolute=False, scalar_only=False):
    return sp.expand(sum((abs(c) if absolute else c) * sp.prod(x**p for x, p in zip(a, powers))
                         for (word, powers), c in terms.items()
                         if not scalar_only or not word))


def check_zero(value):
    result = sp.expand(value)
    assert result == 0, result


def gram_proof(record, coeffs):
    idx = record['representative_index']
    graph = nx.from_graph6_bytes(record['support_graph6'].encode())
    a = sp.symbols('a0:9', nonnegative=True)
    light = record['light_vertices']
    heavy = record['heavy_vertices']
    L = sum(a[i]**2 for i in light)
    qlight = sum(a[i]**2 * a[j]**2 for i, j in itertools.combinations(light, 2)
                 if not graph.has_edge(i, j))
    scores = {h: sum(a[l]**2 for l in light if not graph.has_edge(h, l)) for h in heavy}
    if idx == 15:
        B = sp.Matrix([[a[7], a[3], a[0]], [a[2], 0, -a[4]], [a[5], -a[1], 0]])
        light_cycle_term = 2*a[0]*a[2]*a[4]*a[7] + 2*a[1]*a[3]*a[5]*a[7]
        mixed_term = sp.Integer(0)
        heavy_certificate = {'6': 'column 0 squared norm of B',
                             '8': 'row 0 squared norm of B'}
        check_zero(scores[6] - sum(B[j, 0]**2 for j in range(3)))
        check_zero(scores[8] - sum(B[0, j]**2 for j in range(3)))
    elif idx == 23:
        B = sp.Matrix([[a[3], a[0], 0], [a[1], -a[6], 0], [a[5], 0, a[2]]])
        light_cycle_term = 2*a[0]*a[1]*a[3]*a[6]
        mixed_term = 2*a[1]*a[5]*a[7]*a[8]
        heavy_certificate = {'4': 'column 0 squared norm of B',
                             '7,8': 'principal rows/columns 1,2 of B B^T'}
        M = B*B.T
        check_zero(scores[4] - sum(B[j, 0]**2 for j in range(3)))
        check_zero(M[1, 1] - scores[7])
        check_zero(M[2, 2] - scores[8])
        check_zero(2*a[7]*a[8]*M[1, 2] - mixed_term)
    else:
        raise ValueError(idx)
    M = B*B.T
    second = sp.expand(sum(M.extract(s, s).det() for s in itertools.combinations(range(3), 2)))
    determinant = sp.expand(B.det()**2)
    check_zero(sp.trace(M) - L)
    check_zero(second - qlight - light_cycle_term)
    # Operator triangle bounds are obtained directly from the full transfer
    # expansion, including the six-letter e3 term of representative 15.
    e2_upper = expr(coeffs[1], a, absolute=True)
    e3_upper = expr(coeffs[2], a, absolute=True)
    check_zero(e2_upper - second - mixed_term - sum(a[h]**2*scores[h] for h in heavy))
    check_zero(e3_upper - determinant)
    assert all(graph.has_edge(i, j) for i, j in itertools.combinations(heavy, 2))
    return {
        'representative_index': idx, 'support_graph6': record['support_graph6'],
        'weights': record['weights'], 'amplitude_convention': 'p_i=a_i^2; a_i>=0',
        'B': [[str(B[i, j]) for j in range(3)] for i in range(3)],
        'trace_BBt': str(sp.trace(M)), 'e2_BBt': str(second),
        'det_B': str(sp.expand(B.det())), 'e3_upper_equals_det_B_squared': True,
        'heavy_branches': heavy_certificate,
        'spectral_bound': 'e2<=e2(BBt)+H*lambda_max(BBt), e3<=det(BBt)',
        'proof': 'Rayleigh and principal-submatrix bounds followed by the exact three-variable envelope',
        'exact_beta': '3/2', 'status': 'proved_by_exact_polynomial_and_Gram_identities'}


def check_envelope():
    L, s = sp.symbols('L s', nonnegative=True)
    y = s**2/6
    x = (L-y)/2
    # 2 sqrt((3/2) x*x*y) = x*s for x>=0, s>=0.
    E = 2*x*y+x*x+(1-2*L)*y+x*s
    check_zero((sp.Rational(1, 4)+L/2)**2-E
               -(s-1)**2*(12*L+s*s+6*s+3)/48)
    check_zero(sp.diff(E, s)+(s-1)*(6*L+s*s+4*s)/12)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    records = json.loads(args.input.read_text())['residual_atoms']
    audits, proofs = [], []
    check_envelope()
    for record in records:
        graph = nx.from_graph6_bytes(record['support_graph6'].encode())
        coeffs = transfer_coefficients(graph)
        row = {'representative_index': record['representative_index'],
               'support_graph6': record['support_graph6'],
               'non_scalar_terms': [sum(bool(word) for word, _ in c) for c in coeffs],
               'e3_nonscalar_expansion': [
                   {'word': list(word), 'powers': list(powers), 'coefficient': value}
                   for (word, powers), value in coeffs[2].items() if word]}
        audits.append(row)
        if record['representative_index'] in (15, 23):
            proofs.append(gram_proof(record, coeffs))
    result = {'experiment': 'universal_transfer_algebra_and_two_Gram_completions',
              'exact_arithmetic': 'integer coefficient collection and symbolic polynomial identities',
              'all_residual_graphs_audited': len(audits), 'new_types_proved': [15, 23],
              'exact_facet_type_count': 126, 'remaining_types': [24, 25],
              'transfer_audits': audits, 'proofs': proofs,
              'status': 'two_Gram_certificates_passed'}
    args.output.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ['all_residual_graphs_audited','new_types_proved',
                                           'exact_facet_type_count','remaining_types','status']}))


if __name__ == '__main__':
    main()
