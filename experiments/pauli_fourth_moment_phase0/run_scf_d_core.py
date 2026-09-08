"""C010 adaptive fixed-core joint-event certificate."""
import json
import cdd.gmp as cdd
from run_scf_d_family import DATA
from run_scf_three_row_gate import build
from run_scf_family_facet_closure import enumerate_polytope, primitive


def main():
    cells = [(0, 0), (0, 1), (1, 0), (2, 0), (2, 2)]
    core = enumerate_polytope(build(cells))
    points = [[(s >> i) & 1 for i in range(8)]+[int(bool(s >> 1 & 1) and bool(s >> 4 & 1))]
              for s in core['stable_masks']]
    v = cdd.matrix_from_array([[1]+p for p in points], rep_type=cdd.RepType.GENERATOR)
    h = cdd.copy_inequalities(cdd.polyhedron_from_matrix(v))
    assert not h.lin_set
    facets = sorted({tuple(primitive(row)) for row in h.array})
    result = dict(experiment='C010_D_fixed_core', core=core, cells=list(map(list, cells)),
                  points=points, facets_b_plus_ax=list(map(list, facets)),
                  lower_z_facets=[list(r) for r in facets if r[-1] > 0],
                  unrestricted_SCF_theorem=False, A_star_confirmed=False)
    (DATA/'scf_d_core_c010.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print('core', len(core['stable_masks']), len(core['facets_b_plus_ax']))
    print('lift', len(points), len(facets), 'lower', result['lower_z_facets'])
    print('positive core facets', [r for r in core['facets_b_plus_ax'] if r[0]])


if __name__ == '__main__':
    main()
