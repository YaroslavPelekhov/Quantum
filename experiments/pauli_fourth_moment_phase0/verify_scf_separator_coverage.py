"""C001 independent exact verifier using integer bitsets, no graph library.

Two-clique covers are enumerated as unions of cliques, independently of the
discovery implementation's bipartite-complement test.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path

from verify_scf_generalization import graph_edges, check_scf

DATA = Path(__file__).resolve().parents[2]/'results'/'pauli_fourth_moment_phase0'


def exhaustive(n,edges):
    all_nodes = (1 << n)-1
    adjacency = [sum(1 << j for j in range(n) if tuple(sorted((i,j))) in edges) for i in range(n)]
    cliques = []
    for mask in range(1 << n):
        if all((mask ^ (1 << i)) & ~adjacency[i] == 0 for i in range(n) if mask >> i & 1):
            cliques.append(mask)
    covered = {a|b for a in cliques for b in cliques}
    best = None
    count = 0
    for boundary in sorted(covered-{0,all_nodes}):
        remaining = all_nodes ^ boundary
        components = []
        while remaining:
            reached = remaining & -remaining
            while True:
                expanded = reached
                for i in range(n):
                    if reached >> i & 1:
                        expanded |= adjacency[i] & remaining
                if expanded == reached:
                    break
                reached = expanded
            components.append(reached)
            remaining &= ~reached
        if len(components) < 2:
            continue
        count += 1
        s = tuple(i for i in range(n) if boundary >> i & 1)
        pairs = sum((i,j) not in edges for i in s for j in s if i < j)
        # Enumerate all oriented splits; retain the canonical first-node side.
        for choice in range(1, (1 << len(components))-1):
            if not choice & 1:
                continue
            left_mask = boundary
            for j,component in enumerate(components):
                if choice >> j & 1:
                    left_mask |= component
            right_mask = (all_nodes ^ left_mask) | boundary
            left = tuple(i for i in range(n) if left_mask >> i & 1)
            right = tuple(i for i in range(n) if right_mask >> i & 1)
            score = (pairs,len(s),max(len(left),len(right)),s,left,right)
            if best is None or score < best:
                best = score
    return count,best


def verify_record(record, require_scf=True):
    n,edges = graph_edges(record['graph6'])
    if require_scf:
        check_scf(n,edges)
    count,best = exhaustive(n,edges)
    assert record['vertices'] == n and record['two_clique_separators'] == count
    assert record['minimum_pair_events'] == (None if best is None else best[0])
    if best is None:
        assert record['best'] is None and record['status'] == 'no_two_clique_separator'
        return
    witness = record['best']
    left,right,s = map(set,[witness['left'],witness['right'],witness['separator']])
    assert left|right == set(range(n)) and left&right == s
    assert left-s and right-s
    assert not any(tuple(sorted((i,j))) in edges for i in left-s for j in right-s)
    cover = witness['clique_cover']
    assert len(cover) <= 2 and set().union(*map(set,cover)) == s
    assert all(all((i,j) in edges for i in part for j in part if i < j) for part in cover)
    pairs = [(i,j) for i in sorted(s) for j in sorted(s) if i < j and (i,j) not in edges]
    assert [tuple(p) for p in witness['pairs']] == pairs
    actual = (len(pairs),len(s),max(len(left),len(right)),tuple(sorted(s)),tuple(sorted(left)),tuple(sorted(right)))
    assert actual == best and record['status'] == 'exact_separator_found'


def verify_all(path=DATA/'scf_separator_coverage.json'):
    data = json.loads(path.read_text())
    for name,digest in data['source_sha256'].items():
        assert hashlib.sha256((DATA/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest() == digest
    first = json.loads((DATA/'scf_order9_facet_reduction.json').read_text())
    second = json.loads((DATA/'scf_order10_frontier.json').read_text())
    expected = {f"order9_residual_{r['representative_index']}":r['support_graph6'] for r in first['residual_atoms']}
    expected.update({f'order10_frontier_{i}':r['graph6'] for i,r in enumerate(second['representatives'])})
    assert len(data['records']) == len(expected) == data['weighted_types'] == 47
    assert {r['label']:r['graph6'] for r in data['records']} == expected
    for row in data['records']:
        verify_record(row)
    unique = {r['graph6']:r for r in data['records']}
    assert data['distinct_graph6'] == len(unique)
    assert data['minimum_pair_histogram_types'] == dict(Counter(str(r['minimum_pair_events']) for r in data['records']))
    assert data['minimum_pair_histogram_graphs'] == dict(Counter(str(r['minimum_pair_events']) for r in unique.values()))
    codes = {'P4':'Ch', 'C4':'Cl', 'K4':'C~'}
    for name,code in codes.items():
        verify_record({'graph6':code,**data['controls'][name]}, require_scf=False)
    assert data['one_pair_route_covers_corpus'] == all(r['minimum_pair_events'] is not None and r['minimum_pair_events'] <= 1 for r in data['records'])
    assert data['all_have_two_clique_separator'] == all(r['best'] is not None for r in data['records'])
    assert not data['quantum_conjecture_falsified'] and not data['quantum_compatibility_proved']
    return {'types_verified':47, 'unique_graphs_verified':len(unique),
            'minimum_pair_histogram_types':data['minimum_pair_histogram_types'],
            'status':'independent_exact_coverage_check_passed'}


if __name__ == '__main__':
    if not __debug__:
        raise RuntimeError('Assertions are required.')
    print(json.dumps(verify_all()))
