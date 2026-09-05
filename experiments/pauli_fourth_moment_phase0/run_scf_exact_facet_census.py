"""Recompute the complete order-nine SCF facet census over GMP rationals.

Requires pycddlib >= 3 (the cdd.gmp module, NOT floating-point cdd).
Qhull and its tolerance-based filters are not used. Every V->H enumeration
is also round-tripped H->V and checked against all independent-set vectors.
"""
from __future__ import annotations
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
from math import gcd, lcm
from pathlib import Path
import time
import cdd.gmp as cdd
import networkx as nx


def stable_masks(graph):
    return [m for m in range(1 << len(graph))
            if all(not (m >> i & 1 and m >> j & 1) for i, j in graph.edges())]


def primitive(row):
    denominator = lcm(*(v.denominator for v in row))
    integers = [int(v * denominator) for v in row]
    common = gcd(*integers)
    return tuple(v // common for v in integers)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--facets', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = json.loads(args.input.read_text())
    old = json.loads(args.facets.read_text())
    representatives = []
    for row in old['representatives']:
        graph = nx.from_graph6_bytes(row['support_graph6'].encode())
        weights = [Fraction(str(w)) for w in row['weights']]
        nx.set_node_attributes(graph, dict(enumerate(weights)), 'weight')
        representatives.append((graph, sorted(weights)))
    counts = Counter()
    records = []
    started = time.monotonic()
    total_facets = total_vertices = rank_facets = 0
    for row in source['SCF_records']:
        if row['line_graph']:
            continue
        graph = nx.from_graph6_bytes(row['graph6'].encode())
        n = len(graph)
        masks = stable_masks(graph)
        points = [[1] + [(m >> i) & 1 for i in range(n)] for m in masks]
        matrix = cdd.matrix_from_array(points, rep_type=cdd.RepType.GENERATOR)
        inequalities = cdd.copy_inequalities(cdd.polyhedron_from_matrix(matrix))
        assert not inequalities.lin_set
        facets = sorted(set(primitive(r) for r in inequalities.array))
        # Independently enumerate back from the exact inequalities. No rays,
        # missing vertices, or fractional/spurious vertices may remain.
        back = cdd.copy_generators(cdd.polyhedron_from_matrix(inequalities))
        assert not back.lin_set
        assert {tuple(v) for v in back.array} == {tuple(v) for v in points}
        nonrank = []
        for facet in facets:
            rhs, weights = facet[0], [-x for x in facet[1:]]
            if max(weights) <= 0:
                assert rhs == 0 and sorted(weights) == [-1] + [0]*(n-1)
                continue
            assert min(weights) >= 0
            exact_alpha = max(sum(weights[i] for i in range(n) if m >> i & 1) for m in masks)
            assert exact_alpha == rhs
            positives = {w for w in weights if w}
            if len(positives) == 1:
                rank_facets += 1
                continue
            nodes = [i for i, w in enumerate(weights) if w]
            support = nx.convert_node_labels_to_integers(graph.subgraph(nodes), ordering='sorted')
            normalized = [Fraction(weights[i], max(weights)) for i in nodes]
            nx.set_node_attributes(support, dict(enumerate(normalized)), 'weight')
            matches = [idx for idx, (candidate, values) in enumerate(representatives)
                       if len(candidate) == len(support)
                       and candidate.number_of_edges() == support.number_of_edges()
                       and values == sorted(normalized)
                       and nx.is_isomorphic(support, candidate,
                           node_match=nx.algorithms.isomorphism.categorical_node_match('weight', None))]
            assert len(matches) == 1, (row['graph6'], facet, matches)
            index = matches[0]
            counts[index] += 1
            nonrank.append({'primitive_inequality_b_minus_wx': list(facet),
                            'representative_index': index})
        records.append({'graph6': row['graph6'], 'vertices_of_STAB': len(points),
                        'facets': len(facets), 'exact_roundtrip': True,
                        'facet_sha256': hashlib.sha256(json.dumps(facets).encode()).hexdigest(),
                        'nonrank_facets': nonrank})
        total_facets += len(facets)
        total_vertices += len(points)
        if len(records) % 200 == 0:
            print(f'{len(records)} graphs, {sum(counts.values())} nonrank facets, {time.monotonic()-started:.1f}s', flush=True)
    assert len(records) == source['SCF_non_line_graphs']
    assert set(counts) == set(range(len(representatives)))
    assert all(counts[i] == r['occurrences'] for i, r in enumerate(old['representatives']))
    result = {'experiment': 'GMP_rational_SCF_order9_complete_facet_census',
              'source_sha256': hashlib.sha256(args.input.read_text(encoding='utf-8').encode('utf-8')).hexdigest(),
              'previous_facet_census_sha256': hashlib.sha256(args.facets.read_text(encoding='utf-8').encode('utf-8')).hexdigest(),
              'json_hash_policy': 'UTF-8 text with LF newlines',
              'arithmetic': 'cdd.gmp exact rational double description',
              'graphs': len(records), 'total_STAB_vertices': total_vertices,
              'total_facets': total_facets, 'rank_facets': rank_facets,
              'nonrank_occurrences': sum(counts.values()), 'nonrank_types': len(counts),
              'graphs_with_nonrank_facets': sum(bool(r['nonrank_facets']) for r in records),
              'every_graph_exact_H_V_roundtrip': True,
              'all_previous_class_occurrences_match_exactly': True,
              'seconds': time.monotonic()-started, 'records': records}
    args.output.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'records'}), flush=True)


if __name__ == '__main__':
    main()
