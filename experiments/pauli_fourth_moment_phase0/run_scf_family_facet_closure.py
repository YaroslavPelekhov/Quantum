"""C006: full exact G_1 facet enumeration; no beta optimization."""
import hashlib
import itertools
import json
from math import gcd, lcm
from pathlib import Path
import cdd.gmp as cdd
import networkx as nx

DATA = Path(__file__).resolve().parents[2]/'results'/'pauli_fourth_moment_phase0'


def primitive(row):
    denominator = lcm(*(v.denominator for v in row))
    integers = [int(v*denominator) for v in row]
    common = gcd(*integers)
    return [v//common for v in integers]


def enumerate_polytope(graph):
    n = len(graph)
    masks = [m for m in range(1 << n)
             if all(not (m >> i & 1 and m >> j & 1) for i, j in graph.edges())]
    points = [[1]+[(m >> i) & 1 for i in range(n)] for m in masks]
    source = cdd.matrix_from_array(points, rep_type=cdd.RepType.GENERATOR)
    inequalities = cdd.copy_inequalities(cdd.polyhedron_from_matrix(source))
    assert not inequalities.lin_set
    facets = sorted({tuple(primitive(row)) for row in inequalities.array})
    back = cdd.copy_generators(cdd.polyhedron_from_matrix(inequalities))
    assert not back.lin_set
    assert {tuple(row) for row in back.array} == {tuple(row) for row in points}
    return {'graph6': nx.to_graph6_bytes(graph, header=False).decode().strip(),
            'stable_masks': masks, 'facets_b_plus_ax': list(map(list, facets)),
            'exact_cdd_H_V_roundtrip': True}


def is_scf_component(graph):
    for v in graph:
        for leaves in itertools.combinations(graph[v], 3):
            if not any(graph.has_edge(i, j) for i, j in itertools.combinations(leaves, 2)):
                return False
    # A simplicial clique need not be maximal. The two seven-vertex facet
    # supports of G_1 are regression cases where maximal-only search fails.
    for clique in nx.enumerate_all_cliques(graph):
        nodes = set(clique)
        if all(all(graph.has_edge(i, j)
                   for i, j in itertools.combinations(set(graph[v])-nodes, 2)) for v in nodes):
            return True
    return False


def classify(graph, facets, known_weights):
    n = len(graph)
    source = graph.copy()
    nx.set_node_attributes(source, dict(enumerate(known_weights)), 'weight')
    result = []
    for index, row in enumerate(facets):
        weights = [-v for v in row[1:]]
        support = [i for i, v in enumerate(weights) if v > 0]
        record = {'facet_index': index, 'support': support}
        if not support:
            record['route'] = 'nonnegativity'
        else:
            assert min(weights) >= 0
            local = graph.subgraph(support)
            scf = all(is_scf_component(local.subgraph(c)) for c in nx.connected_components(local))
            record['support_componentwise_SCF'] = scf
            if len(set(weights[i] for i in support)) == 1 and scf:
                record['route'] = 'SCF_rank'
            elif len(support) <= 9 and scf:
                record['route'] = 'SCF_order9_all_weights'
            else:
                target = graph.copy()
                nx.set_node_attributes(target, dict(enumerate(weights)), 'weight')
                matcher = nx.algorithms.isomorphism.GraphMatcher(
                    source, target, node_match=nx.algorithms.isomorphism.categorical_node_match('weight', None))
                if row[0] == 3 and matcher.is_isomorphic():
                    record['route'] = 'C005_rectangular_Gram'
                    record['family_to_facet_automorphism'] = [matcher.mapping[i] for i in range(n)]
                else:
                    record['route'] = 'uncovered'
        result.append(record)
    return result


def main():
    raw = (DATA/'scf_rectangular_gram_bridge.json').read_bytes().replace(b'\r\n', b'\n')
    bridge = json.loads(raw)
    family = bridge['records'][1]
    graph = nx.from_graph6_bytes(family['graph6'].encode())
    assert family['m'] == 1 and len(graph) == 10
    target = enumerate_polytope(graph)
    target['proof_routes'] = classify(graph, target['facets_b_plus_ax'], family['weights'])
    # A failed completeness control is retained as classical, not physical,
    # evidence: the other 26 facets admit points violating the removed one.
    full_index = next(r['facet_index'] for r in target['proof_routes']
                      if r['route'] == 'C005_rectangular_Gram')
    incomplete = [r for i, r in enumerate(target['facets_b_plus_ax']) if i != full_index]
    bad_h = cdd.matrix_from_array(incomplete, rep_type=cdd.RepType.INEQUALITY)
    bad_v = cdd.copy_generators(cdd.polyhedron_from_matrix(bad_h))
    assert not bad_v.lin_set and all(row[0] == 1 for row in bad_v.array)
    expected = {tuple((m >> i) & 1 for i in range(len(graph))) for m in target['stable_masks']}
    extras = sorted({tuple(row[1:]) for row in bad_v.array}-expected)
    assert extras
    report = {'experiment': 'C006_complete_G1_facet_closure', 'date': '2026-09-06',
              'preregistration_commit': 'da1f93d',
              'C005_source_sha256': hashlib.sha256(raw).hexdigest(),
              'source_frontier_graph6': bridge['target']['graph6'],
              'arithmetic': 'cdd.gmp exact rational; independent Fraction clipping required',
              'target': target,
              'controls': [enumerate_polytope(nx.path_graph(4)), enumerate_polytope(nx.cycle_graph(5))],
              'missing_facet_control': {'removed_facet_index': full_index,
                                       'extra_vertices': [list(map(str, row)) for row in extras],
                                       'quantum_state_claim': False},
              'all_facets_have_proof_route': all(r['route'] != 'uncovered' for r in target['proof_routes']),
              'family_all_m_all_weights_claim': False, 'unrestricted_SCF_theorem': False,
              'A_star_confirmed': False}
    (DATA/'scf_family_facet_closure.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    from collections import Counter
    print(json.dumps({'graph6': target['graph6'], 'stable_vertices': len(target['stable_masks']),
                      'facets': len(target['facets_b_plus_ax']),
                      'routes': dict(Counter(r['route'] for r in target['proof_routes'])),
                      'independent_verification': 'still_required'}))


if __name__ == '__main__':
    if not __debug__: raise RuntimeError('Assertions required.')
    main()
