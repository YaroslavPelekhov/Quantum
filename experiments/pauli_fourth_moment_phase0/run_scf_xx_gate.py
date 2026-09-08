"""C011 published XX-strip hulls, not a new graph construction."""
from collections import Counter
import itertools as it
import json
import time
import networkx as nx
from run_scf_family_facet_closure import enumerate_polytope
from run_scf_three_row_gate import first_claw, simplicial
from run_scf_d_family import DATA


def full_graph():
    g = nx.cycle_graph(range(1, 7))
    additions = {7: [1, 2], 8: [4, 5], 9: [6, 1, 2, 3], 10: [3, 4, 5, 6, 9],
                 11: [3, 4, 6, 1, 9, 10], 12: [2, 3, 5, 6, 9, 10], 13: [1, 2, 4, 5, 7, 8]}
    g.add_edges_from((v, u) for v, neighbors in additions.items() for u in neighbors)
    return g


def record(mask):
    start = time.monotonic()
    labels = [i for i in range(1, 14) if not (i >= 11 and mask >> (i-11) & 1)]
    g = nx.convert_node_labels_to_integers(full_graph().subgraph(labels), ordering='sorted')
    assert first_claw(g) is None
    clique = simplicial(g)
    assert clique is not None
    poly = enumerate_polytope(g)
    poly.update(deletion_mask=mask, original_labels=labels, simplicial_clique=clique,
                alpha=max(s.bit_count() for s in poly['stable_masks']))
    routes = []
    for idx, f in enumerate(poly['facets_b_plus_ax']):
        support = [i for i, c in enumerate(f[1:]) if c < 0]
        alpha = max(sum(bool(s >> i & 1) for i in support) for s in poly['stable_masks'])
        mapping = None
        if not support: route = 'nonnegativity'
        elif len({f[i+1] for i in support}) == 1: route = 'SCF_rank'
        elif alpha <= 2: route = 'SCF_alpha_two'
        elif len(support) <= 9: route = 'SCF_order9'
        else:
            target = nx.from_graph6_bytes(b'K{S{aSfF~Fln')
            matcher = nx.algorithms.isomorphism.GraphMatcher(target, g.subgraph(support))
            mapping = next(matcher.subgraph_isomorphisms_iter(), None)
            route = 'C009_induced' if mapping is not None else 'unresolved'
        routes.append(dict(facet_index=idx, support=support, support_alpha=alpha,
                           route=route, C009_mapping=mapping))
    poly['routes'] = routes
    assert time.monotonic()-start < 300
    return poly


def main():
    records = []
    for mask in range(8):
        row = record(mask)
        records.append(row)
        print(mask, len(row['original_labels']), row['alpha'], len(row['facets_b_plus_ax']),
              dict(Counter(r['route'] for r in row['routes'])), flush=True)
        for f, r in zip(row['facets_b_plus_ax'], row['routes']):
            if r['route'] == 'unresolved': print('unresolved', f, flush=True)
    out = dict(experiment='C011_published_XX_strip_gate', date='2026-09-08',
               records=records, quantum_all_weight_theorem=False,
               unrestricted_SCF_theorem=False, A_star_confirmed=False)
    (DATA/'scf_xx_gate_c011.json').write_text(json.dumps(out, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__': main()
