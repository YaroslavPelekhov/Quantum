"""Targeted (not exhaustive order-10) extension/falsification of hard atoms.

Enumerate every one-vertex attachment to the nine-vertex residuals, retain
SCF graphs, remove twin/join reductions, and exactly enumerate full-support
nonrank facets. Isomorphism checks, not hashes alone, remove duplicates.
"""
from __future__ import annotations
import argparse
from collections import Counter
from fractions import Fraction
import itertools
import hashlib
import json
from pathlib import Path
import time
import cdd.gmp as cdd
import networkx as nx
import numpy as np
from run_scf_exact_facet_census import primitive, stable_masks
from run_scf_hbar_falsification import is_scf, matrices_for_graph, beta_from_coefficients
from run_scf_theta_guided_attack import theta_profile, published_g9_control


def reducible(graph):
    if not nx.is_connected(nx.complement(graph)):
        return True
    for i, j in itertools.combinations(graph, 2):
        if set(graph[i]) - {j} == set(graph[j]) - {i}:
            return True
    return False


def generate(source):
    buckets, graphs, representatives, facet_buckets = {}, [], [], {}
    proposals = accepted = 0
    started = time.monotonic()
    for base in source['residual_atoms']:
        seed = nx.from_graph6_bytes(base['support_graph6'].encode())
        if len(seed) != 9:
            continue
        for mask in range(1, 1 << 9):
            proposals += 1
            graph = seed.copy()
            graph.add_node(9)
            graph.add_edges_from((i, 9) for i in range(9) if mask >> i & 1)
            if not is_scf(graph):
                continue
            accepted += 1
            if reducible(graph):
                continue
            key = nx.weisfeiler_lehman_graph_hash(graph)
            if any(nx.is_isomorphic(graph, graphs[i]) for i in buckets.get(key, [])):
                continue
            buckets.setdefault(key, []).append(len(graphs))
            graphs.append(graph)
            points = [[1] + [(m >> i) & 1 for i in range(10)] for m in stable_masks(graph)]
            matrix = cdd.matrix_from_array(points, rep_type=cdd.RepType.GENERATOR)
            facets = cdd.copy_inequalities(cdd.polyhedron_from_matrix(matrix))
            for row in sorted(set(primitive(r) for r in facets.array)):
                weights = [-x for x in row[1:]]
                if min(weights) <= 0 or len(set(weights)) == 1:
                    continue
                weighted = graph.copy()
                nx.set_node_attributes(weighted, dict(enumerate(weights)), 'weight')
                wk = (key, tuple(sorted(weights)))
                match = None
                for idx in facet_buckets.get(wk, []):
                    old = representatives[idx]['weighted_graph']
                    if nx.is_isomorphic(weighted, old,
                        node_match=nx.algorithms.isomorphism.categorical_node_match('weight', None)):
                        match = idx
                        break
                if match is None:
                    facet_buckets.setdefault(wk, []).append(len(representatives))
                    representatives.append({'weighted_graph': weighted,
                        'graph6': nx.to_graph6_bytes(graph, header=False).decode().strip(),
                        'base_representative_index': base['representative_index'],
                        'attachment_mask': mask, 'integer_weights': weights,
                        'exact_alpha_integer': row[0]})
        print(f"base {base['representative_index']}: {len(graphs)} irreducible graphs, {len(representatives)} new facet types, {time.monotonic()-started:.1f}s", flush=True)
    for row in representatives:
        del row['weighted_graph']
    return {'proposal_attachments': proposals, 'SCF_accepted_with_multiplicity': accepted,
            'unique_twin_and_join_irreducible_graphs': len(graphs),
            'full_support_nonrank_facet_types': len(representatives),
            'coefficient_patterns': dict(Counter(str(sorted(r['integer_weights'])) for r in representatives)),
            'representatives': representatives}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--attack-cap', type=int, default=12)
    parser.add_argument('--iterations', type=int, default=320)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    source_hash = hashlib.sha256(args.input.read_text(encoding='utf-8').encode('utf-8')).hexdigest()
    if args.resume:
        result = json.loads(args.output.read_text())
        assert result['source_sha256'] == source_hash
    else:
        result = generate(json.loads(args.input.read_text()))
    result['source_sha256'] = source_hash
    result['json_hash_policy'] = 'UTF-8 text with LF newlines'
    result['experiment'] = 'post_order9_targeted_one_vertex_extension_falsification'
    result['scope'] = 'all attachments to the nine-vertex residual seeds; NOT all graphs of order ten'
    result['selection_rule_before_beta_evaluation'] = 'descending number of weight levels, max integer weight, alpha; then graph6'
    result['status'] = 'enumeration_complete_attacks_pending'
    args.output.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    selected = sorted(result['representatives'], key=lambda r: (
        -len(set(r['integer_weights'])), -max(r['integer_weights']), -r['exact_alpha_integer'], r['graph6']))[:args.attack_cap]
    rng = np.random.default_rng(9052026)
    if not args.resume:
        result['published_narrow_basin_positive_control'] = published_g9_control(rng, 256, args.iterations)
    attacks = result.get('attacks', [])
    for row in selected:
        if any(r['graph6'] == row['graph6'] and r['integer_weights'] == row['integer_weights'] for r in attacks):
            continue
        graph = nx.from_graph6_bytes(row['graph6'].encode())
        weights = np.asarray(row['integer_weights'], dtype=float)
        upper, profile = theta_profile(graph, weights)
        operators = matrices_for_graph(graph)
        starts = (np.sqrt(profile)*np.array((1.,)+tail)
                  for tail in itertools.product((-1., 1.), repeat=9))
        beta = beta_from_coefficients(operators, weights, starts, args.iterations)
        attack = {**row, 'first_state_moment_upper': upper, 'sign_orthants': 512,
                  'iterations_per_start': args.iterations, 'beta_lower_bound': beta,
                  'ratio': beta/row['exact_alpha_integer']}
        attacks.append(attack)
        result['attacks'] = attacks
        result['status'] = 'falsified' if attack['ratio'] > 1+1e-7 else 'attacks_in_progress'
        args.output.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
        print(json.dumps({'attack': len(attacks), 'graph6': row['graph6'], 'ratio': attack['ratio']}), flush=True)
        if result['status'] == 'falsified':
            break
    result['status'] = 'falsified' if any(r['ratio'] > 1+1e-7 for r in attacks) else 'no_violation_in_bounded_targeted_frontier'
    result['not_a_proof'] = True
    args.output.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k not in ('representatives', 'attacks')}), flush=True)


if __name__ == '__main__':
    main()
