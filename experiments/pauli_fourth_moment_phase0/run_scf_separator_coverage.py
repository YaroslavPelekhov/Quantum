"""C001: exact finite structural coverage audit; no quantum optimization.

Protocol was committed before this implementation. A separator is accepted
only if its removal disconnects the graph and it is covered by two cliques.
This does not assume any quantum boundary-compatibility lemma.
"""
import argparse
from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path

import networkx as nx

DATA = Path(__file__).resolve().parents[2]/'results'/'pauli_fourth_moment_phase0'
SOURCES = ('scf_order9_facet_reduction.json', 'scf_order10_frontier.json')


def corpus(data_dir=DATA):
    first = json.loads((data_dir/SOURCES[0]).read_text())
    second = json.loads((data_dir/SOURCES[1]).read_text())
    rows = [{'label': f"order9_residual_{r['representative_index']}",
             'graph6': r['support_graph6']} for r in first['residual_atoms']]
    rows += [{'label': f'order10_frontier_{i}', 'graph6': r['graph6']}
             for i,r in enumerate(second['representatives'])]
    assert len(first['residual_atoms']) == 13 and len(second['representatives']) == 34
    return rows


def solve(graph):
    n = len(graph)
    assert set(graph) == set(range(n)) and nx.is_connected(graph)
    best = None
    separator_count = 0
    for mask in range(1, (1 << n)-1):
        boundary = [i for i in range(n) if mask >> i & 1]
        remaining = [i for i in range(n) if not mask >> i & 1]
        components = sorted(sorted(c) for c in nx.connected_components(graph.subgraph(remaining)))
        if len(components) < 2:
            continue
        complement = nx.complement(graph.subgraph(boundary))
        if not nx.is_bipartite(complement):
            continue
        separator_count += 1
        pairs = sorted(tuple(sorted(p)) for p in complement.edges())
        colors = nx.bipartite.color(complement)
        cover = [[i for i in boundary if colors[i] == c] for c in (0,1)]
        # Fix the first component on the left to remove side exchange.
        for choice in range((1 << (len(components)-1))-1):
            left_extra = list(components[0])
            right_extra = []
            for index,component in enumerate(components[1:]):
                (left_extra if choice >> index & 1 else right_extra).extend(component)
            left = sorted(boundary+left_extra)
            right = sorted(boundary+right_extra)
            score = (len(pairs),len(boundary),max(len(left),len(right)),tuple(boundary),tuple(left),tuple(right))
            if best is None or score < best[0]:
                best = (score, {'separator': boundary, 'clique_cover': cover,
                               'pairs': pairs, 'left': left, 'right': right})
    return {'vertices': n, 'two_clique_separators': separator_count,
            'minimum_pair_events': None if best is None else best[0][0],
            'best': None if best is None else best[1],
            'status': 'no_two_clique_separator' if best is None else 'exact_separator_found'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    controls = {name: solve(graph) for name,graph in [
        ('P4',nx.path_graph(4)),('C4',nx.cycle_graph(4)),('K4',nx.complete_graph(4))]}
    assert [controls[k]['minimum_pair_events'] for k in ('P4','C4','K4')] == [0,1,None]
    rows = corpus()
    cache = {}
    for row in rows:
        code = row['graph6']
        if code not in cache:
            cache[code] = solve(nx.from_graph6_bytes(code.encode()))
        row.update(cache[code])
        print(json.dumps({k:row[k] for k in ('label','minimum_pair_events','status')}),flush=True)
    payload = {'experiment': 'C001_two_clique_separator_coverage',
        'date': '2026-09-06', 'preregistration_commit': '5498437',
        'source_sha256': {name: hashlib.sha256((DATA/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest() for name in SOURCES},
        'scope': '13 residual types plus 34 targeted frontier types; not exhaustive SCF',
        'weighted_types': len(rows), 'distinct_graph6': len(cache),
        'minimum_pair_histogram_types': dict(Counter(str(r['minimum_pair_events']) for r in rows)),
        'minimum_pair_histogram_graphs': dict(Counter(str(r['minimum_pair_events']) for r in cache.values())),
        'one_pair_route_covers_corpus': all(r['minimum_pair_events'] is not None and r['minimum_pair_events'] <= 1 for r in rows),
        'all_have_two_clique_separator': all(r['best'] is not None for r in rows),
        'quantum_conjecture_falsified': False, 'quantum_compatibility_proved': False,
        'controls': controls, 'records': rows}
    args.output.write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in payload.items() if k not in ('records','controls')}),flush=True)


if __name__ == '__main__':
    if not __debug__:
        raise RuntimeError('Assertions are required.')
    main()
