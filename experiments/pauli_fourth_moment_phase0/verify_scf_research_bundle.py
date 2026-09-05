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
    print(json.dumps({'location': 'git_index' if args.git_index else 'worktree',
                      'artifact_hashes_checked': len(names), 'covered_types_exactly_once': 128,
                      'exact_census_occurrences': sum(occurrences.values()),
                      'frontier_attacks': len(frontier['attacks']),
                      'generalization_obstructions': 13, 'pair_recipe_counterexamples': 5,
                      'status': 'integrity_checks_passed'}))


if __name__ == '__main__':
    if not __debug__:
        raise RuntimeError('Do not disable assertions for verification.')
    main()
