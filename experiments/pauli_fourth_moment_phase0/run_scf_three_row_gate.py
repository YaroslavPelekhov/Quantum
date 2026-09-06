"""C008: frozen 3x4 structural census and ONE exact 3x3 target hull."""
from collections import Counter
import itertools as it
import json
from pathlib import Path
import time
import networkx as nx
from run_scf_family_facet_closure import enumerate_polytope

DATA = Path(__file__).resolve().parents[2]/'results'/'pauli_fourth_moment_phase0'


def build(cells, selectors='two_rows_one_column'):
    cells = sorted(map(tuple, cells))
    graph = nx.Graph()
    k = len(cells)
    graph.add_nodes_from(range(k+3))
    graph.add_edges_from((i, j) for i, j in it.combinations(range(k), 2)
                         if cells[i][0] == cells[j][0] or cells[i][1] == cells[j][1])
    graph.add_edges_from(it.combinations(range(k, k+3), 2))
    for i, (r, c) in enumerate(cells):
        for h in range(3):
            nonneighbor = r == h if selectors == 'three_rows' else (r == h if h < 2 else c == 0)
            if not nonneighbor:
                graph.add_edge(i, k+h)
    return graph


def first_claw(graph):
    for v in graph:
        for leaves in it.combinations(sorted(graph[v]), 3):
            if not any(graph.has_edge(i, j) for i, j in it.combinations(leaves, 2)):
                return [v]+list(leaves)
    return None


def simplicial(graph):
    for clique in nx.enumerate_all_cliques(graph):
        chosen = set(clique)
        if all(all(graph.has_edge(i, j) for i, j in it.combinations(set(graph[v])-chosen, 2))
               for v in clique):
            return sorted(clique)
    return None


def root_record(cells, columns):
    graph = build(cells)
    root = nx.Graph()
    root.add_nodes_from(range(3+columns))
    root.add_edges_from((r, 3+c) for r, c in cells if c)
    matching = nx.bipartite.maximum_matching(root, top_nodes=range(3))
    pairs = sorted([r, matching[r]-3] for r in range(3) if r in matching)
    universe = [0, 1, 2]+list(range(4, 3+columns))
    cover = next(list(s) for s in it.combinations(universe, len(pairs))
                 if all(r in s or 3+c in s for r, c in cells if c))
    claw, clique = first_claw(graph), simplicial(graph)
    return {'graph6': nx.to_graph6_bytes(graph, header=False).decode().strip(),
            'matching': pairs, 'minimum_cover': cover,
            'claw': claw, 'simplicial_clique': clique,
            'SCF': claw is None and clique is not None}


def classify_target(graph, poly):
    rows = []
    for i, f in enumerate(poly['facets_b_plus_ax']):
        w = [-v for v in f[1:]]
        support = [j for j, v in enumerate(w) if v > 0]
        mask = sum(1 << j for j in support)
        alpha = max((s & mask).bit_count() for s in poly['stable_masks'])
        if not support: route = 'nonnegativity'
        elif len({w[j] for j in support}) == 1: route = 'SCF_rank'
        elif alpha <= 2: route = 'SCF_alpha_two'
        elif len(support) <= 9: route = 'SCF_order9'
        else: route = 'unresolved_by_rank_alpha_two_order9'
        rows.append({'facet_index': i, 'support': support, 'support_alpha': alpha, 'route': route})
    return rows


def main():
    start = time.monotonic()
    grid = list(it.product(range(3), range(4)))
    records = []
    for mask in range(1 << 12):
        assert time.monotonic()-start < 300, 'registered discovery limit'
        cells = [cell for i, cell in enumerate(grid) if mask >> i & 1]
        row = root_record(cells, 4)
        row['cell_mask'] = mask
        records.append(row)
    census = {'experiment': 'C008_three_row_structural_gate', 'date': '2026-09-06',
              'preregistration_commit': '2c4dc25', 'grid_rows': 3, 'grid_columns': 4,
              'mask_order': 'row_major', 'records': records,
              'counts': {'graphs': len(records), 'claw_free': sum(r['claw'] is None for r in records),
                         'SCF': sum(r['SCF'] for r in records),
                         'matching_histogram': dict(sorted(Counter(str(len(r['matching'])) for r in records).items()))},
              'S_survives_finite_audit': all((r['claw'] is None) == (len(r['matching']) <= 2) for r in records),
              'new_quantum_theorem': False, 'A_star_confirmed': False}
    (DATA/'scf_three_row_gate.json').write_text(json.dumps(census, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(census['counts']), flush=True)
    cells = list(it.product(range(3), range(3)))
    graph = build(cells)
    target = enumerate_polytope(graph)
    target.update({'cells': list(map(list, cells)), 'proof_routes': classify_target(graph, target),
                   'disjoint_triples': [[0, 4, 8], [1, 5, 6]],
                   'five_wheel': {'hub': 10, 'rim': [0, 6, 9, 11, 1]},
                   'full_one_two_row_is_facet': [3]+[-1]*9+[-2]*3 in target['facets_b_plus_ax']})
    report = {'experiment': 'C008_full_3_by_3_target', 'date': '2026-09-06',
              'preregistration_commit': '2c4dc25', 'target': target,
              'all_weight_quantum_theorem': False, 'unrestricted_SCF_theorem': False,
              'A_star_confirmed': False}
    (DATA/'scf_three_row_target.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'graph6': target['graph6'], 'stable_vertices': len(target['stable_masks']),
                      'facets': len(target['facets_b_plus_ax']),
                      'routes': dict(Counter(r['route'] for r in target['proof_routes'])),
                      'full_one_two_row_is_facet': target['full_one_two_row_is_facet']}), flush=True)


if __name__ == '__main__':
    if not __debug__: raise RuntimeError('Assertions required.')
    main()
