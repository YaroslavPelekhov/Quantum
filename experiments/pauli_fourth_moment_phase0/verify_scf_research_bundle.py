"""Verify artifact hashes and proof coverage, on disk or in the Git index.

Only Python's standard library is needed. This integrity/ledger check is not
a replacement for the exact mathematical certificate verifiers.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--git-index', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    prefix = 'results/pauli_fourth_moment_phase0/'

    def read(name):
        if args.git_index:
            raw = subprocess.check_output(['git', 'show', ':'+prefix+name], cwd=root)
        else:
            raw = (root/prefix/name).read_bytes()
        return raw.replace(b'\r\n', b'\n') if name.endswith('.json') else raw

    manifest = json.loads(read('manifest.json'))
    assert manifest['hash_policy'] == 'JSON: UTF-8 with LF newlines; binary artifacts: raw bytes'
    names = [r['path'] for r in manifest['artifacts']]
    assert len(names) == len(set(names))
    for row in manifest['artifacts']:
        raw = read(row['path'])
        assert len(raw) == row['bytes'], (row['path'], 'length')
        assert hashlib.sha256(raw).hexdigest() == row['sha256'], (row['path'], 'hash')
    source = json.loads(read('scf_order9_facet_reduction.json'))
    indices = [r['representative_index'] for r in source['proved_joins']]
    groups = [[27], [5, 7, 9, 33], [34, 48], [26], [44], [15, 23], [24, 25]]
    indices.extend(i for group in groups for i in group)
    assert sorted(indices) == list(range(128))
    for index in (24, 25):
        cert = json.loads(read(f'scf_exact_dual{index}.json'))
        row = next(r for r in source['residual_atoms'] if r['representative_index'] == index)
        assert cert['support_graph6'] == row['support_graph6']
        from fractions import Fraction
        assert list(map(Fraction, cert['weights'])) == [Fraction(str(w)) for w in row['weights']]
    census = json.loads(read('scf_exact_facet_census.json'))
    assert census['source_sha256'] == hashlib.sha256(read('scf_order9_census.json')).hexdigest()
    assert census['previous_facet_census_sha256'] == hashlib.sha256(read('scf_order9_facet_census.json')).hexdigest()
    occurrences = Counter(f['representative_index'] for r in census['records'] for f in r['nonrank_facets'])
    old = json.loads(read('scf_order9_facet_census.json'))
    assert all(occurrences[i] == r['occurrences'] for i, r in enumerate(old['representatives']))
    frontier = json.loads(read('scf_order10_frontier.json'))
    assert frontier['source_sha256'] == hashlib.sha256(read('scf_order9_facet_reduction.json')).hexdigest()
    assert len(frontier['attacks']) == 34
    assert frontier['status'] == 'no_violation_in_bounded_targeted_frontier'
    assert all(r['ratio'] <= 1+1e-7 for r in frontier['attacks'])
    gluing = json.loads(read('scf_gluing_obstruction.json'))
    pair = json.loads(read('scf_pair_completion_audit.json'))
    rank_two = json.loads(read('scf_rank_two_lift.json'))
    assert gluing['exact_obstructions'] == 13 and not gluing['quantum_claim_falsified']
    assert pair['separator_failures'] == 5 and not pair['quantum_hbar_claim_falsified']
    assert rank_two['antiblocker_vertices'] == 177287
    coverage = json.loads(read('scf_separator_coverage.json'))
    coordinates = json.loads(read('scf_coordinate_compatibility.json'))
    assert coverage['weighted_types'] == 47 and coverage['distinct_graph6'] == 46
    assert coordinates['exact_obstructions'] == 8 and not coordinates['quantum_conjecture_falsified']
    closure = json.loads(read('almost_clique_closure_counterexample.json'))
    closure_screen = json.loads(read('almost_clique_closure_audit.json'))
    assert closure['generic_quantum_closure_falsified'] and not closure['SCF_conjecture_falsified']
    assert closure['exact_gap'] == '556/15625'
    assert closure_screen['graphs_screened'] == 1437 and closure_screen['decompositions_found'] == 5353
    cross = json.loads(read('scf_cross_claw_gate.json'))
    assert cross['central_side_histogram'] == {'1': 36} and not cross['quantum_compatibility_proved']
    assert cross['exhaustive_template']['counts']['graphs'] == 16384
    bridge = json.loads(read('scf_rectangular_gram_bridge.json'))
    assert bridge['target']['graph6'] == 'ICXmtizr_' and bridge['finite_audit_m'] == list(range(6))
    assert not bridge['all_weights_claim'] and not bridge['unrestricted_SCF_theorem']
    family_facets = json.loads(read('scf_family_facet_closure.json'))
    assert family_facets['C005_source_sha256'] == hashlib.sha256(read('scf_rectangular_gram_bridge.json')).hexdigest()
    assert family_facets['target']['graph6'] == 'IrqaaulLw'
    assert len(family_facets['target']['stable_masks']) == 34
    assert len(family_facets['target']['facets_b_plus_ax']) == 27
    assert family_facets['all_facets_have_proof_route'] and not family_facets['family_all_m_all_weights_claim']
    gate = json.loads(read('scf_uniform_facet_gate.json'))
    assert gate['C005_sha256'] == hashlib.sha256(read('scf_rectangular_gram_bridge.json')).hexdigest()
    assert gate['C006_sha256'] == hashlib.sha256(read('scf_family_facet_closure.json')).hexdigest()
    assert gate['audit_m'] == [0, 1, 2, 3] == [r['m'] for r in gate['records']]
    assert [len(r['stable_masks']) for r in gate['records']] == [22, 34, 50, 70]
    assert [len(r['facets_b_plus_ax']) for r in gate['records']] == [23, 27, 31, 35]
    assert gate['R_m_survives_finite_audit'] and not gate['unbounded_R_m_proved']
    # Historical discovery flags describe the finite stage. The subsequent
    # uniform proof is written in SCF_UNBOUNDED_ALL_WEIGHT_FAMILY.md.
    core = json.loads(read('scf_core_refinement.json'))
    assert core['C007_gate_sha256'] == hashlib.sha256(read('scf_uniform_facet_gate.json')).hexdigest()
    assert core['graph6'] == gate['records'][0]['graph6']
    assert len(core['points']) == 22 and len(core['facets_b_plus_ax']) == 24
    assert len(core['lower_z_facets']) == 3 and not core['unrestricted_SCF_theorem']
    assert not core['A_star_confirmed']
    three_row = json.loads(read('scf_three_row_gate.json'))
    three_target = json.loads(read('scf_three_row_target.json'))
    assert [r['cell_mask'] for r in three_row['records']] == list(range(4096))
    assert three_row['counts']['SCF'] == three_row['counts']['claw_free'] == 2120
    assert three_row['S_survives_finite_audit'] and not three_row['new_quantum_theorem']
    t = three_target['target']
    assert t['graph6'] == 'K{S{aSfF~Fln' and len(t['stable_masks']) == 46
    assert len(t['facets_b_plus_ax']) == 36 and t['full_one_two_row_is_facet']
    assert Counter(r['route'] for r in t['proof_routes']) == {
        'nonnegativity': 12, 'SCF_rank': 20, 'SCF_alpha_two': 3,
        'unresolved_by_rank_alpha_two_order9': 1}
    assert not three_target['all_weight_quantum_theorem'] and not three_target['A_star_confirmed']
    gram = json.loads(read('scf_three_row_gram_c009.json'))
    assert gram['graph6'] == t['graph6']
    assert gram['identity_pass'] == [True]*3 and gram['residuals'] == [[], [], []]
    assert gram['odd_zero'] == [True]*3 and gram['mutually_commuting']
    assert [len(c) for c in gram['transfer_coefficients']] == [12, 39, 21]
    assert not gram['quantum_bound_proved'] and not gram['unrestricted_SCF_theorem']
    assert not gram['A_star_confirmed']
    d_family = json.loads(read('scf_d_family_c010.json'))
    d_core = json.loads(read('scf_d_core_c010.json'))
    assert d_family['audit_m'] == [0, 1, 2, 3]
    assert [len(r['facets_b_plus_ax']) for r in d_family['records']] == [11, 17, 23, 27]
    assert len(d_core['points']) == 21 and len(d_core['facets_b_plus_ax']) == 18
    assert len(d_core['lower_z_facets']) == 3
    assert not d_core['unrestricted_SCF_theorem'] and not d_core['A_star_confirmed']
    xx = json.loads(read('scf_xx_gate_c011.json'))
    assert [r['deletion_mask'] for r in xx['records']] == list(range(8))
    assert xx['records'][0]['graph6'] == 'LhEM?rcNLhleuo'
    assert [len(r['facets_b_plus_ax']) for r in xx['records']] == [33,30,30,29,26,23,23,22]
    assert all(r['alpha'] == 4 for r in xx['records'])
    assert not xx['unrestricted_SCF_theorem'] and not xx['A_star_confirmed']
    print(json.dumps({'location': 'git_index' if args.git_index else 'worktree',
                      'artifact_hashes_checked': len(names), 'covered_types_exactly_once': 128,
                      'exact_census_occurrences': sum(occurrences.values()),
                      'frontier_attacks': len(frontier['attacks']),
                      'generalization_obstructions': 13, 'pair_recipe_counterexamples': 5,
                      'separator_types': 47, 'coordinatewise_obstructions': 8,
                      'generic_closure_exact_counterexamples': 1,
                      'cross_claw_template_graphs': 16384,
                      'rectangular_Gram_family_audit_sizes': 6,
                      'all_weight_G1_facets': 27,
                      'C007_finite_facets': 116,
                      'C007_lifted_core_facets': 24,
                      'C008_structural_patterns': 4096,
                      'C008_target_facets': 36,
                      'C008_target_open_quantum_facets': 1,
                      'C009_subsequently_closed_target_facets': 1,
                      'C010_lifted_core_facets': 18,
                      'C011_published_XX_facets': 33,
                      'status': 'integrity_checks_passed'}))


if __name__ == '__main__':
    if not __debug__:
        raise RuntimeError('Do not disable assertions for verification.')
    main()
