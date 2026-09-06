"""C007 acceptance: exact full Fraction clipping and independently bound routes."""
from collections import Counter
import hashlib
import itertools
import json
from math import gcd
from pathlib import Path
from verify_scf_generalization import graph_edges, check_scf
from verify_scf_family_facet_closure import componentwise_scf, verify_polytope
from verify_scf_rectangular_gram_bridge import verify_record

DATA = Path(__file__).resolve().parents[2]/'results'/'pauli_fourth_moment_phase0'


def load_bound(name, expected):
    raw = (DATA/name).read_bytes().replace(b'\r\n', b'\n')
    assert hashlib.sha256(raw).hexdigest() == expected
    return json.loads(raw)


def verify_mir(record, weights):
    n, edges = graph_edges(record['graph6'])
    result = record['classical_MIR_identification']
    assert not result['quantum_rounding_claim']
    cert = result['first_certificate']
    if cert is None:
        assert result['matching_certificates'] == 0
        return {'status': 'no_match_reported_not_a_nonexistence_proof'}
    cliques = cert['cliques']
    assert len({tuple(c) for c in cliques}) == len(cliques)
    for c in cliques:
        assert c == sorted(set(c)) and set(c) <= set(range(n))
        assert all(pair in edges for pair in itertools.combinations(c, 2))
        assert all(any(tuple(sorted((u, v))) not in edges for v in c) for u in set(range(n))-set(c))
    p, q, r = cert['p'], cert['q'], cert['r']
    assert p == len(cliques) and 2 <= q and 2*q < p and r == p % q != 0
    mu = [sum(i in c for c in cliques) for i in range(n)]
    # Independent scalar form: coefficient = d*mu/q - correction for
    # the fractional part, evaluated via integer quotient and remainder.
    coeff = []
    for x in mu:
        whole, remainder = divmod(x, q)
        coeff.append((q-r)*whole+(remainder-r if remainder > r else 0))
    rhs = (q-r)*(p//q)
    divisor = gcd(rhs, *coeff)
    assert mu == cert['multiplicities'] and coeff == cert['raw_coefficients']
    assert rhs == cert['raw_rhs'] and divisor == cert['primitive_divisor']
    assert [rhs//divisor]+[x//divisor for x in coeff] == [3]+weights
    assert result['matching_certificates'] > 0
    return {'status': 'exact_classical_MIR_certificate', 'p': p, 'q': q, 'r': r}


def verify_row(record, known):
    assert record['m'] == known['m'] and record['graph6'] == known['graph6']
    verify_record(known)  # Independent construction, SCF and universal C005 identities.
    n, edges = graph_edges(record['graph6'])
    check_scf(n, edges)
    poly = verify_polytope(record, max_dimension=14)
    routes = record['routes']
    assert [r['facet_index'] for r in routes] == list(range(len(record['facets_b_plus_ax'])))
    for facet, route in zip(record['facets_b_plus_ax'], routes):
        w = [-a for a in facet[1:]]
        support = [i for i, x in enumerate(w) if x > 0]
        mask = sum(1 << i for i in support)
        alpha = max((s & mask).bit_count() for s in record['stable_masks'])
        assert support == route['support'] and alpha == route['support_alpha']
        kind = route['kind']
        if not support:
            assert kind == 'nonnegativity'
            continue
        assert min(w) >= 0
        componentwise_scf(n, edges, support)
        if len(set(w[i] for i in support)) == 1:
            assert kind == 'rank'
        elif alpha <= 2:
            assert kind == 'alpha_two_support'
        elif kind == 'C005_full_support':
            mapping = route['weight_automorphism']
            assert sorted(mapping) == list(range(n)) and facet[0] == 3
            assert {tuple(sorted((mapping[i], mapping[j]))) for i, j in edges} == edges
            assert all(known['weights'][i] == w[mapping[i]] for i in range(n))
        else:
            # A genuine falsification may be accepted as such, never as a
            # quantum counterexample or a positive proof of the conjecture.
            assert kind == 'R_m_counterexample' and alpha == 3
            # Full-support counterexamples with the same weight multiset
            # need an independent orbit exclusion, not a sorted comparison.
            if sorted(w) == sorted(known['weights']) and facet[0] == 3:
                assert not weight_automorphism_exists(n, edges, known['weights'], w)
    return {'m': record['m'], 'vertices': n, 'STAB_vertices': poly['vertices'], 'facets': poly['facets'],
            'routes': dict(Counter(r['kind'] for r in routes)),
            'independent_completeness': True, 'MIR': verify_mir(record, known['weights'])}


def weight_automorphism_exists(n, edges, source_weights, target_weights):
    neighbors = [{j for j in range(n) if tuple(sorted((i, j))) in edges} for i in range(n)]
    candidates = {i: [j for j in range(n) if source_weights[i] == target_weights[j]
                       and len(neighbors[i]) == len(neighbors[j])] for i in range(n)}
    def search(mapping, used):
        if len(mapping) == n: return True
        options = {}
        for i in range(n):
            if i not in mapping:
                options[i] = [j for j in candidates[i] if j not in used
                              and all((u in neighbors[i]) == (v in neighbors[j]) for u, v in mapping.items())]
        i = min(options, key=lambda v: (len(options[v]), -len(neighbors[v]), v))
        return any(search(mapping | {i: j}, used | {j}) for j in options[i])
    return search({}, set())


def verify(report):
    bridge = load_bound('scf_rectangular_gram_bridge.json', report['C005_sha256'])
    old = load_bound('scf_family_facet_closure.json', report['C006_sha256'])['target']
    assert report['audit_m'] == [0, 1, 2, 3] == [r['m'] for r in report['records']]
    result = [verify_row(row, bridge['records'][row['m']]) for row in report['records']]
    assert all(report['records'][1][k] == old[k] for k in ('graph6', 'stable_masks', 'facets_b_plus_ax'))
    survives = all('R_m_counterexample' not in row['routes'] for row in result)
    assert survives == report['R_m_survives_finite_audit']
    assert not report['unbounded_R_m_proved'] and not report['unbounded_all_weight_theorem']
    assert not report['unrestricted_SCF_theorem'] and not report['A_star_confirmed']
    return {'status': 'finite_exact_facet_audit_verified', 'records': result,
            'all_audited_sizes_all_weight_proved': survives,
            'unbounded_R_m_proved': False, 'unrestricted_SCF_theorem': False}


if __name__ == '__main__':
    if not __debug__: raise RuntimeError('Assertions required.')
    print(json.dumps(verify(json.loads((DATA/'scf_uniform_facet_gate.json').read_text()))))
