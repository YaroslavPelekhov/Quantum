"""Independent pair-first NetworkX verification of the C003 exact screen."""
import argparse
import itertools
import json
import networkx as nx
from run_almost_clique_closure_audit import DATA, EXPECTED, BASE, fetch


def enumerate_independent(code):
    graph = nx.from_graph6_bytes(code.encode())
    n = len(graph)
    output = []
    # An almost-clique separator is its unique nonedge plus a clique in
    # the common neighborhood. This is not the discovery subset algorithm.
    for u,v in itertools.combinations(range(n),2):
        if graph.has_edge(u,v):
            continue
        common = set(graph[u]) & set(graph[v])
        for clique in itertools.chain([[]],nx.enumerate_all_cliques(graph.subgraph(common))):
            boundary = sorted([u,v]+clique)
            remaining = sorted(set(graph)-set(boundary))
            components = sorted(sorted(c) for c in nx.connected_components(graph.subgraph(remaining)))
            if len(components) < 2:
                continue
            for chosen in itertools.product((False,True),repeat=len(components)-1):
                if all(chosen):
                    continue
                left = set(boundary)|set(components[0])
                right = set(boundary)
                for flag,component in zip(chosen,components[1:]):
                    (left if flag else right).update(component)
                output.append({'separator':boundary,'pair':[u,v],'left':sorted(left),'right':sorted(right)})
    return output


def canonical(rows):
    return sorted((tuple(r['separator']),tuple(r['pair']),tuple(r['left']),tuple(r['right'])) for r in rows)


def verify_audit(verify_upstream=False):
    data = json.loads((DATA/'almost_clique_closure_audit.json').read_text())
    assert len(enumerate_independent('Cl')) == 2 and enumerate_independent('C~') == []
    totals = {}
    for order in (8,9):
        source = data['sources'][str(order)]
        assert source['sha256'] == EXPECTED[order] and source['url'] == f'{BASE}/test{order}.txt'
        rows = [r for r in data['records'] if r['order'] == order]
        assert len(rows) == source['rows'] == {8:18,9:1419}[order]
        assert [r['source_row'] for r in rows] == list(range(1,len(rows)+1))
        assert len({r['graph6'] for r in rows}) == len(rows)
        if verify_upstream:
            assert [r['graph6'] for r in rows] == [r[0] for r in fetch(order)]
        for row in rows:
            graph = nx.from_graph6_bytes(row['graph6'].encode())
            assert len(graph) == order and nx.is_connected(graph)
            found = enumerate_independent(row['graph6'])
            assert canonical(found) == canonical(row['decompositions'])
        totals[str(order)] = {'graphs':len(rows),'with_separator':sum(bool(r['decompositions']) for r in rows),
                              'decompositions':sum(len(r['decompositions']) for r in rows)}
    assert data['graphs_screened'] == len(data['records']) == 1437
    assert data['graphs_with_almost_clique_separator'] == sum(r['with_separator'] for r in totals.values()) == 860
    assert data['decompositions_found'] == sum(r['decompositions'] for r in totals.values()) == 5353
    assert data['status'] == 'structural_screen_only_local_and_quantum_certificates_pending'
    # This file remains the screen, not the separate exact witness certificate.
    assert not data['generic_quantum_closure_falsified'] and not data['SCF_conjecture_falsified']
    return {'status':'independent_structural_enumeration_verified','totals':totals,
            'upstream_rows_and_hashes_verified':verify_upstream}


if __name__ == '__main__':
    if not __debug__:
        raise RuntimeError('Assertions required.')
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify-upstream',action='store_true')
    print(json.dumps(verify_audit(parser.parse_args().verify_upstream)))
