"""Falsify profile-only gluing, even after adding every global rank bound.

This searches abstract vectors, not physical quantum states. Every reported
witness and local stable-set decomposition is verified over rational numbers.
"""
from __future__ import annotations
import argparse
from fractions import Fraction as F
import itertools
import json
from pathlib import Path
import cdd.gmp as cdd
import networkx as nx
import numpy as np
from scipy.optimize import linprog
from run_scf_exact_facet_census import primitive, stable_masks


def facet_rows(graph, nodes, n):
    local = nx.convert_node_labels_to_integers(graph.subgraph(nodes), ordering='sorted')
    masks = stable_masks(local)
    points = [[1]+[(mask >> i) & 1 for i in range(len(nodes))] for mask in masks]
    matrix = cdd.matrix_from_array(points, rep_type=cdd.RepType.GENERATOR)
    facets = cdd.copy_inequalities(cdd.polyhedron_from_matrix(matrix))
    output = []
    for row in facets.array:
        row = primitive(row)
        lifted = [0]*n
        for node, value in zip(nodes, row[1:]):
            lifted[node] = -value
        output.append((lifted, row[0]))
    return output, masks


def decomposition(graph, nodes, point):
    local = nx.convert_node_labels_to_integers(graph.subgraph(nodes), ordering='sorted')
    masks = stable_masks(local)
    columns = [[1]+[(m >> i) & 1 for i in range(len(nodes))] for m in masks]
    matrix = np.asarray(columns, dtype=float).T
    target = [F(1)]+[point[i] for i in nodes]
    result = linprog(np.zeros(len(masks)), A_eq=matrix, b_eq=np.asarray(target, float), bounds=(0, None), method='highs')
    assert result.success
    probabilities = [F(float(x)).limit_denominator(1_000_000) for x in result.x]
    assert all(x >= 0 for x in probabilities)
    assert all(sum(probabilities[j]*columns[j][i] for j in range(len(columns))) == t for i, t in enumerate(target))
    return [{'stable_set': [nodes[i] for i in range(len(nodes)) if mask >> i & 1],
             'probability': str(prob)} for mask, prob in zip(masks, probabilities) if prob]


def pair_range(graph, nodes, point, pair):
    local = nx.convert_node_labels_to_integers(graph.subgraph(nodes), ordering='sorted')
    masks = stable_masks(local)
    columns = [[1]+[(m >> i)&1 for i in range(len(nodes))] for m in masks]
    i,j = [nodes.index(v) for v in pair]
    objective = [int(bool(m >> i & 1 and m >> j & 1)) for m in masks]
    target = [F(1)]+[point[v] for v in nodes]
    output = {}
    for sign,name in [(1,'lower'),(-1,'upper')]:
        result = linprog(np.array(objective)*sign, A_eq=np.array(columns).T,
                         b_eq=np.array(target,float), bounds=(0,None), method='highs')
        assert result.success
        dual = [F(float(x)).limit_denominator(1_000_000) for x in result.eqlin.marginals]
        assert all(sum(a*v for a,v in zip(dual,column)) <= sign*c for column,c in zip(columns,objective))
        bound = sign*sum(a*v for a,v in zip(dual,target))
        assert abs(float(bound)-sign*result.fun) < 1e-8
        output[name] = str(bound)
        output[name+'_dual'] = list(map(str,dual))
    return output


def search(record):
    graph = nx.from_graph6_bytes(record['support_graph6'].encode())
    n = len(graph)
    weights = [F(str(w)) for w in record['weights']]
    masks = stable_masks(graph)
    rank_rows = [([(subset >> i) & 1 for i in range(n)],
                  max((mask & subset).bit_count() for mask in masks))
                 for subset in range(1, 1 << n)]
    checked = 0
    clique_control_max = 0.0
    for size in range(1, n-1):
        for separator in itertools.combinations(range(n), size):
            if not nx.is_bipartite(nx.complement(graph.subgraph(separator))):
                continue
            remainder = graph.subgraph(set(graph)-set(separator))
            components = list(nx.connected_components(remainder))
            if len(components) < 2:
                continue
            left = sorted(set(separator) | components[0])
            right = sorted(set(graph)-components[0])
            left_rows, _ = facet_rows(graph, left, n)
            right_rows, _ = facet_rows(graph, right, n)
            rows = rank_rows+left_rows+right_rows
            result = linprog(-np.asarray(weights, float), A_ub=np.asarray([a for a, _ in rows], float),
                             b_ub=np.asarray([b for _, b in rows], float), bounds=(0, None), method='highs')
            assert result.success
            checked += 1
            value = -result.fun
            if nx.is_empty(nx.complement(graph.subgraph(separator))):
                clique_control_max = max(clique_control_max, value-float(record['weighted_alpha']))
                assert value <= float(record['weighted_alpha'])+1e-8
            if value <= float(record['weighted_alpha'])+1e-8:
                continue
            point = [F(float(x)).limit_denominator(1_000_000) for x in result.x]
            assert all(sum(F(a[i])*point[i] for i in range(n)) <= b for a, b in rows)
            exact_value = sum(x*w for x, w in zip(point, weights))
            exact_alpha = max(sum(weights[i] for i in range(n) if mask >> i & 1) for mask in masks)
            assert exact_value > exact_alpha
            coloring = nx.bipartite.color(nx.complement(graph.subgraph(separator)))
            cliques = [[v for v in separator if coloring[v] == color] for color in (0, 1)]
            return {'representative_index': record['representative_index'], 'graph6': record['support_graph6'],
                    'separator': list(separator), 'separator_clique_cover': cliques,
                    'left_vertices': left, 'right_vertices': right, 'profile': list(map(str, point)),
                    'weights': list(map(str, weights)), 'exact_profile_value': str(exact_value),
                    'exact_stable_bound': str(exact_alpha), 'exact_violation': str(exact_value-exact_alpha),
                    'all_global_rank_inequalities_verified': len(rank_rows),
                    'left_STAB_decomposition': decomposition(graph, left, point),
                    'right_STAB_decomposition': decomposition(graph, right, point),
                    'separator_pair_ranges': [{'pair': list(pair),
                         'left': pair_range(graph,left,point,pair),
                         'right': pair_range(graph,right,point,pair)}
                        for pair in itertools.combinations(separator,2) if not graph.has_edge(*pair)],
                    'separators_checked_before_witness': checked,
                    'is_physical_quantum_counterexample': False,
                    'status': 'exact_obstruction_to_profile_only_two_clique_gluing'}
    return {'representative_index': record['representative_index'], 'separators_checked': checked,
            'status': 'no_witness_in_this_separator_class'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    records = json.loads(args.input.read_text())['residual_atoms']
    output = []
    for record in records:
        row = search(record)
        output.append(row)
        print(json.dumps({k: v for k, v in row.items() if k in ('representative_index', 'status', 'exact_violation')}), flush=True)
    payload = {'experiment': 'rank_augmented_two_clique_separator_gluing_falsification',
               'graphs_tested': len(records), 'exact_obstructions': sum('profile' in r for r in output),
               'quantum_claim_falsified': False, 'records': output}
    args.output.write_text(json.dumps(payload, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
