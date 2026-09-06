"""C007 fixed-core lift: exact facets of the joint U,V event polytope."""
import hashlib
import json
from pathlib import Path
import cdd.gmp as cdd
from run_scf_family_facet_closure import primitive

DATA = Path(__file__).resolve().parents[2]/'results'/'pauli_fourth_moment_phase0'


def main():
    raw = (DATA/'scf_uniform_facet_gate.json').read_bytes().replace(b'\r\n', b'\n')
    base = json.loads(raw)['records'][0]
    assert base['m'] == 0
    points = [[(m >> i) & 1 for i in range(8)]+[int(m >> 3 & 1 and m >> 4 & 1)]
              for m in base['stable_masks']]
    source = cdd.matrix_from_array([[1]+p for p in points], rep_type=cdd.RepType.GENERATOR)
    h = cdd.copy_inequalities(cdd.polyhedron_from_matrix(source))
    assert not h.lin_set
    facets = sorted({tuple(primitive(row)) for row in h.array})
    back = cdd.copy_generators(cdd.polyhedron_from_matrix(h))
    assert not back.lin_set
    assert {tuple(r) for r in back.array} == {tuple([1]+p) for p in points}
    result = {'experiment': 'C007_fixed_core_joint_event_lift', 'date': '2026-09-06',
              'preregistration_commit': '68d5ac8',
              'C007_gate_sha256': hashlib.sha256(raw).hexdigest(),
              'graph6': base['graph6'], 'core_names': ['A0', 'B0', 'Z', 'U', 'V', 'H0', 'H1', 'Hc'],
              'joint_event': ['U', 'V'], 'points': points,
              'facets_b_plus_ax': list(map(list, facets)),
              'lower_z_facets': [list(row) for row in facets if row[-1] > 0],
              'exact_cdd_H_V_roundtrip': True,
              'unrestricted_SCF_theorem': False, 'quantum_generic_gluing_claim': False,
              'A_star_confirmed': False}
    (DATA/'scf_core_refinement.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'lifted_vertices': len(points), 'facets': len(facets),
                      'lower_z_facets': result['lower_z_facets']}))


if __name__ == '__main__':
    if not __debug__: raise RuntimeError('Assertions required.')
    main()
