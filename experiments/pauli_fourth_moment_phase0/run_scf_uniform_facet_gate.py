"""C007 frozen R_m falsification and classical MIR prior-art identification."""
from collections import Counter
import hashlib
import itertools
import json
from math import gcd
from pathlib import Path
import networkx as nx
from run_scf_family_facet_closure import enumerate_polytope

DATA = Path(__file__).resolve().parents[2]/'results'/'pauli_fourth_moment_phase0'


def canonical_hash(path):
    return hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def facet_routes(graph, poly, known):
    n = len(graph)
    source = graph.copy()
    nx.set_node_attributes(source, dict(enumerate(known)), 'w')
    result = []
    for index, row in enumerate(poly['facets_b_plus_ax']):
        w = [-a for a in row[1:]]
        support_mask = sum(1 << i for i, x in enumerate(w) if x > 0)
        alpha = max((mask & support_mask).bit_count() for mask in poly['stable_masks'])
        route = {'facet_index': index, 'support_alpha': alpha,
                 'support': [i for i in range(n) if support_mask >> i & 1]}
        if not support_mask:
            route['kind'] = 'nonnegativity'
        elif len({x for x in w if x > 0}) == 1:
            route['kind'] = 'rank'
        elif alpha <= 2:
            route['kind'] = 'alpha_two_support'
        else:
            target = graph.copy()
            nx.set_node_attributes(target, dict(enumerate(w)), 'w')
            matcher = nx.algorithms.isomorphism.GraphMatcher(
                source, target, node_match=nx.algorithms.isomorphism.categorical_node_match('w', None))
            if row[0] == 3 and matcher.is_isomorphic():
                route['kind'] = 'C005_full_support'
                route['weight_automorphism'] = [matcher.mapping[i] for i in range(n)]
            else:
                route['kind'] = 'R_m_counterexample'
        result.append(route)
    return result


def mir_certificate(graph, weights):
    """Exhaust the frozen subsets/q grid; a missing match is not a priority proof."""
    cliques = sorted(sorted(c) for c in nx.find_cliques(graph))
    first = None
    candidates = matches = 0
    for mask in range(1 << len(cliques)):
        selected = [c for i, c in enumerate(cliques) if mask >> i & 1]
        p = len(selected)
        if p < 5:
            continue
        mu = [sum(i in c for c in selected) for i in range(len(graph))]
        for q in range(2, (p+1)//2):
            r = p % q
            if r == 0:
                continue
            candidates += 1
            coeff = [(q-r)*(x//q)+max(0, x % q-r) for x in mu]
            rhs = (q-r)*(p//q)
            common = gcd(rhs, *coeff)
            if [rhs//common]+[c//common for c in coeff] == [3]+weights:
                matches += 1
                if first is None:
                    first = {'cliques': selected, 'p': p, 'q': q, 'r': r,
                             'multiplicities': mu, 'raw_coefficients': coeff,
                             'raw_rhs': rhs, 'primitive_divisor': common}
    return {'maximal_cliques': len(cliques), 'grid_candidates': candidates,
            'matching_certificates': matches, 'first_certificate': first,
            'quantum_rounding_claim': False}


def main():
    bridge = json.loads((DATA/'scf_rectangular_gram_bridge.json').read_text())
    rows = []
    for m in range(4):
        family = bridge['records'][m]
        assert family['m'] == m
        graph = nx.from_graph6_bytes(family['graph6'].encode())
        poly = enumerate_polytope(graph)
        poly.update({'m': m, 'routes': facet_routes(graph, poly, family['weights']),
                     'classical_MIR_identification': mir_certificate(graph, family['weights'])})
        rows.append(poly)
        print(json.dumps({'m': m, 'vertices': len(graph), 'STAB_vertices': len(poly['stable_masks']),
                          'facets': len(poly['facets_b_plus_ax']),
                          'routes': dict(Counter(r['kind'] for r in poly['routes'])),
                          'MIR_matches': poly['classical_MIR_identification']['matching_certificates']}), flush=True)
    control = json.loads((DATA/'scf_family_facet_closure.json').read_text())['target']
    assert all(rows[1][key] == control[key] for key in ('graph6', 'stable_masks', 'facets_b_plus_ax'))
    result = {'experiment': 'C007_uniform_G_m_facet_gate', 'date': '2026-09-06',
              'preregistration_commit': '8a2d0f5',
              'C005_sha256': canonical_hash(DATA/'scf_rectangular_gram_bridge.json'),
              'C006_sha256': canonical_hash(DATA/'scf_family_facet_closure.json'),
              'audit_m': list(range(4)), 'records': rows,
              'R_m_survives_finite_audit': all(r['kind'] != 'R_m_counterexample' for p in rows for r in p['routes']),
              'unbounded_R_m_proved': False, 'unbounded_all_weight_theorem': False,
              'unrestricted_SCF_theorem': False, 'A_star_confirmed': False,
              'acceptance_status': 'independent_exact_verification_required'}
    (DATA/'scf_uniform_facet_gate.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    if not __debug__: raise RuntimeError('Assertions required.')
    main()
