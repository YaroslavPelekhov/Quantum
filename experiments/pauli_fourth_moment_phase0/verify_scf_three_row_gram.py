"""Independent C009 acceptance: word rewriting and Cauchy--Binet minors.

Does not import discovery. Exact polynomial identity checking is separate
from the analytic spectral argument documented in SCF_THREE_ROW_GRAM_C009.md.
"""
import hashlib
import itertools as it
import json
from pathlib import Path
import time
from verify_scf_rectangular_gram_bridge import Algebra, rewrite, verify_envelope
from verify_scf_generalization import graph_edges, stable, check_scf
from verify_scf_three_row_gate import verify_target

DATA = Path(__file__).resolve().parents[2]/'results'/'pauli_fourth_moment_phase0'


def decode(rows):
    result = {(tuple(r['word']), tuple(r['powers'])): r['coefficient'] for r in rows}
    assert len(result) == len(rows) and all(type(c) is int and c for c in result.values())
    return result


def verify(report, hull=True):
    start = time.monotonic()
    assert report['graph6'] == 'K{S{aSfF~Fln'
    assert not report['quantum_bound_proved']  # discovery must not certify its own theorem
    assert not report['unrestricted_SCF_theorem'] and not report['A_star_confirmed']
    n, edges = graph_edges(report['graph6'])
    assert n == 12
    check_scf(n, edges)
    masks = [s for s in range(1 << n) if stable(s, edges)]
    sets = [tuple(i for i in range(n) if s >> i & 1) for s in masks]
    assert max(map(len, sets)) == 3
    assert report['stable_set_counts'] == [sum(len(s) == k for s in sets) for k in range(5)]
    alg = Algebra(n, edges)
    one = alg.constant(1)
    a = [alg.variable(i) for i in range(n)]
    centers = []
    sequences = [(9, 10, j, 3+j) for j in range(3)]+[(0, 6, j, 6+j) for j in (1, 2)]
    assert len(report['central_checks']) == 5
    for seq, stored in zip(sequences, report['central_checks']):
        w, sign = rewrite(seq, (), edges)
        center = {(w, (0,)*n): -sign}
        assert decode(stored['expression']) == center
        assert rewrite(tuple(reversed(w)), (), edges) == (w, 1)
        assert rewrite(w, w, edges) == ((), 1)
        assert all(rewrite(w, (v,), edges) == rewrite((v,), w, edges) for v in range(n))
        assert stored['hermitian'] is True and stored['involution'] is True
        assert stored['noncommuting_generators'] == []
        centers.append(center)
    assert report['mutually_commuting'] is True
    assert all(alg.mul(x, y) == alg.mul(y, x) for x, y in it.combinations(centers, 2))
    signs = [one]*3+centers[:3]+[one]+centers[3:]
    B = [[alg.mul(a[3*r+c], signs[3*r+c]) for c in range(3)] for r in range(3)]
    # Different determinant construction from discovery's det(B B^T).
    minors = [alg.det([[B[r][c] for c in cs] for r in rs])
              for rs in it.combinations(range(3), 2) for cs in it.combinations(range(3), 2)]
    e2light = alg.add(*(alg.sq(v) for v in minors))
    e2heavy = alg.add(*(alg.sq(alg.add(alg.mul(a[9], B[0][c]),
                                      alg.mul(a[10], B[1][c]))) for c in range(3)),
                     *(alg.sq(alg.mul(a[11], B[r][0])) for r in range(3)))
    rhs = [alg.add(*(alg.sq(v) for v in a)), alg.add(e2light, e2heavy), alg.sq(alg.det(B))]
    charges = [alg.add(*({(s, tuple(int(i in s) for i in range(n))): 1}
                         for s in sets if len(s) == k)) for k in range(4)]
    full = [{} for _ in range(7)]
    for i, qi in enumerate(charges):
        for j, qj in enumerate(charges):
            full[i+j] = alg.add(full[i+j], alg.scale(alg.mul(qi, qj), (-1)**j))
    assert full[0] == one and report['constant_ok'] is True
    assert all(not full[d] for d in (1, 3, 5)) and report['odd_zero'] == [True]*3
    assert len(report['transfer_coefficients']) == len(report['candidate_coefficients']) == 3
    for k in range(3):
        coeff = alg.scale(full[2*k+2], (-1)**(k+1))
        assert coeff == rhs[k] == decode(report['transfer_coefficients'][k])
        assert coeff == decode(report['candidate_coefficients'][k])
    assert report['residuals'] == [[], [], []] and report['identity_pass'] == [True]*3
    verify_envelope()
    weights = [1]*9+[2]*3
    assert max(sum(weights[i] for i in s) for s in sets) == 3
    assert (0, 9) in sets  # commuting light/heavy pair attains three
    target = json.loads((DATA/'scf_three_row_target.json').read_text())
    assert target['target']['graph6'] == report['graph6']
    accepted_hull = verify_target(target) if hull else None
    if hull:
        assert accepted_hull['routes'] == {'nonnegativity': 12, 'SCF_rank': 20,
               'SCF_alpha_two': 3, 'unresolved_by_rank_alpha_two_order9': 1}
        assert [3]+[-1]*9+[-2]*3 in target['target']['facets_b_plus_ax']
    assert time.monotonic()-start < 300
    return dict(status='exact_C009_Gram_identities_verified', coefficient_terms=list(map(len, rhs)),
                hull_rechecked=bool(hull), target_all_weight_theorem_supported=bool(hull),
                analytic_argument='SCF_THREE_ROW_GRAM_C009.md',
                unrestricted_SCF_theorem=False, A_star_confirmed=False)


if __name__ == '__main__':
    if not __debug__:
        raise RuntimeError('Assertions required')
    source = DATA/'scf_three_row_gram_c009.json'
    report = json.loads(source.read_text())
    result = verify(report)
    result['source_sha256_LF'] = hashlib.sha256(source.read_bytes().replace(b'\r\n', b'\n')).hexdigest()
    print(json.dumps(result))
