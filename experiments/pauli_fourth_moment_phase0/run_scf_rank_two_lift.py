"""Exact audit of the size-independent rank-to-weight lift when alpha<=2.

The general proof is combinatorial (half-integrality of the antiblocker);
this is an independent finite implementation audit, not proof by sampling.
"""
from __future__ import annotations
import argparse
from fractions import Fraction as F
import itertools
import json
from pathlib import Path
import cdd.gmp as cdd
import networkx as nx


def alpha_at_most_two(graph):
    return all(any(graph.has_edge(i, j) for i, j in itertools.combinations(triple, 2))
               for triple in itertools.combinations(graph, 3))


def audit(graph):
    assert alpha_at_most_two(graph)
    n = len(graph)
    rows = []
    for i in range(n):
        positive = [0]*n
        positive[i] = 1
        rows.extend([[0]+positive, [1]+[-x for x in positive]])
    for i, j in itertools.combinations(range(n), 2):
        if not graph.has_edge(i, j):
            normal = [0]*n
            normal[i] = normal[j] = -1
            rows.append([1]+normal)
    matrix = cdd.matrix_from_array(rows, rep_type=cdd.RepType.INEQUALITY)
    vertices = cdd.copy_generators(cdd.polyhedron_from_matrix(matrix))
    assert not vertices.lin_set
    half_vertices = mixed_vertices = 0
    for row in vertices.array:
        assert row[0] == 1
        weights = row[1:]
        assert set(weights) <= {F(0), F(1, 2), F(1)}
        light = [i for i, w in enumerate(weights) if w == F(1, 2)]
        heavy = [i for i, w in enumerate(weights) if w == 1]
        assert all(graph.has_edge(i, j) for i, j in itertools.combinations(heavy, 2))
        assert all(graph.has_edge(i, j) for i in light for j in heavy)
        half_vertices += bool(light)
        mixed_vertices += bool(light and heavy)
    return {'graph6': nx.to_graph6_bytes(graph, header=False).decode().strip(),
            'vertices': n, 'antiblocker_vertices': len(vertices.array),
            'half_integral_vertices': half_vertices,
            'mixed_join_vertices': mixed_vertices, 'all_exact_checks_passed': True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    records = []
    for graph in nx.graph_atlas_g():
        if len(graph) and alpha_at_most_two(graph):
            records.append({'source': 'all_atlas_alpha_at_most_two', **audit(graph)})
    atlas_count = len(records)
    for row in json.loads(args.input.read_text())['SCF_records']:
        graph = nx.from_graph6_bytes(row['graph6'].encode())
        if alpha_at_most_two(graph):
            records.append({'source': 'connected_order9_SCF', **audit(graph)})
    payload = {'experiment': 'exact_antiblocker_rank_to_weight_lift_audit',
               'general_theorem_scope': 'every graph with alpha=2: sup_w beta(G,w)/alpha(G,w)=beta(G,1)/2',
               'perfection_equivalence': 'for alpha<=2, beta(G,1)=alpha(G) iff hbar-perfect',
               'SCF_corollary': 'all nonnegative weights, arbitrary vertex count, alpha<=2',
               'atlas_graphs': atlas_count, 'order9_SCF_graphs': len(records)-atlas_count,
               'antiblocker_vertices': sum(r['antiblocker_vertices'] for r in records),
               'mixed_join_vertices': sum(r['mixed_join_vertices'] for r in records),
               'all_half_integral_and_join_checks_passed': True, 'records': records}
    args.output.write_text(json.dumps(payload, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in payload.items() if k != 'records'}), flush=True)


if __name__ == '__main__':
    main()
