"""C010 frozen exact D_0,...,D_3 polyhedral gate, no quantum optimization."""
from collections import Counter
import itertools as it
import json
from pathlib import Path
import time
import networkx as nx
from run_scf_three_row_gate import build, classify_target
from run_scf_family_facet_closure import enumerate_polytope

DATA = Path(__file__).resolve().parents[2]/'results'/'pauli_fourth_moment_phase0'


def main():
    start = time.monotonic()
    records = []
    for m in range(4):
        cells = sorted([(r, 0) for r in range(3)]+[(r, c) for r in (0, 2) for c in range(1, m+1)])
        g = build(cells)
        row = enumerate_polytope(g)
        row.update(m=m, cells=list(map(list, cells)))
        row['routes'] = classify_target(g, row)
        # Exhaustive known-target embedding diagnostic, not absence-of-prior-art proof.
        known = nx.from_graph6_bytes(b'K{S{aSfF~Fln')
        match = nx.algorithms.isomorphism.GraphMatcher(known, g)
        row['C009_induced_embedding'] = next(match.subgraph_isomorphisms_iter(), None)
        records.append(row)
        print(m, len(g), len(row['stable_masks']), len(row['facets_b_plus_ax']),
              dict(Counter(r['route'] for r in row['routes'])), flush=True)
        for f, route in zip(row['facets_b_plus_ax'], row['routes']):
            if route['route'].startswith('unresolved'):
                print('unresolved', f, flush=True)
        assert time.monotonic()-start < 300
    result = dict(experiment='C010_D_family_frozen_hulls', preregistration_commit='d7408bd',
                  audit_m=list(range(4)), records=records,
                  uniform_all_weight_theorem=False, unrestricted_SCF_theorem=False, A_star_confirmed=False)
    (DATA/'scf_d_family_c010.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
