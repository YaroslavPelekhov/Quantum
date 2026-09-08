"""Read-only manuscript ledger checks, not a mathematical proof checker."""
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / 'results' / 'pauli_fourth_moment_phase0'
PHASE = ROOT / 'experiments' / 'pauli_fourth_moment_phase0'
sys.path.insert(0, str(PHASE))


def read(name):
    return json.loads((DATA / name).read_text(encoding='utf-8'))


def main():
    if not __debug__:
        raise RuntimeError('Assertions required; do not use -O')
    tex = Path(__file__).with_name('main.tex').read_text(encoding='utf-8')
    manifest = read('manifest.json')
    assert len(manifest['artifacts']) == 64
    for row in manifest['artifacts']:
        raw = (DATA / row['path']).read_bytes()
        if row['path'].endswith('.json'):
            raw = raw.replace(b'\r\n', b'\n')
        assert hashlib.sha256(raw).hexdigest() == row['sha256'], row['path']
        assert len(raw) == row['bytes'], row['path']
    target = read('scf_two_xx_weight_c014.json')
    hulls = [read('scf_three_row_target.json')['target'],
             read('scf_xx_gate_c011.json')['records'][0],
             read('scf_xx_closure_c012.json')['target']]
    for hull, count, facets, alpha in zip(hulls, (46, 85, 203), (36, 33, 44), (3, 4, 4)):
        assert len(hull['stable_masks']) == count
        assert len(hull['facets_b_plus_ax']) == facets
        assert max(s.bit_count() for s in hull['stable_masks']) == alpha
    assert len(target['stable_masks']) == 2167 and target['alpha'] == 6
    assert target['minimal_qubits'] == 7
    row, control = target['records']
    assert row['weights'] == [1 + int(i in (6, 7)) for i in range(24)]
    assert row['stable_bound'] == 6 and len(row['tight_masks']) == 88
    assert row['homogeneous_rank'] == 24 and row['facet_inducing']
    assert control['stable_bound'] == 7 and not control['facet_inducing']
    assert not target['independent_complete_hull']
    attack = read('scf_two_xx_attack_c015.json')
    assert len(attack['runs']) == attack['total_registered_starts'] == 1024
    assert sum(r['converged'] for r in attack['runs']) == 144
    assert sum(not r['converged'] for r in attack['runs']) == 880
    assert attack['status'] == 'no_violation_in_completed_finite_attack'
    baseline = read('scf_two_xx_baseline_c016.json')
    assert Fraction(baseline['objective']) == Fraction(325328979, 50000000)
    assert baseline['degree_histogram'] == {'4': 2, '6': 12, '7': 4, '8': 6}
    for record in (target, attack, baseline):
        for flag in ('quantum_target_proved', 'unrestricted_SCF_theorem', 'A_star_confirmed'):
            assert record[flag] is False, flag
    # Lightweight independent physical evaluation, not a replay of optimization.
    from verify_scf_two_xx_attack import evaluate
    actual, _ = evaluate(target['standard_SAUR_labels'], row['weights'], attack['best']['state'])
    assert abs(actual - 6.000000000000059) < 1e-12
    known = read('almost_clique_closure_counterexample.json')
    assert known['exact_stable_bound'] == 3
    assert len(known['pauli_words']) == 8
    assert known['new_imperfect_graph_claim'] is False
    # Keep headline claims and their limitations present in the actual source.
    for token in ('2167', '1024', '144', '880', '441.989', '325328979',
                  '50000000', '25328979', '6.50657958', '127', '64',
                  'quantum validity remains', 'External proof review',
                  'not independently', 'No assertion of its truth',
                  '4dc9dc7bc26cca5ea3a7f4cfa66cc4f7fc969a83'):
        assert token in tex, token
    labels = re.findall(r'\\label\{([^}]+)\}', tex)
    assert len(labels) == len(set(labels)), Counter(labels)
    assert set(re.findall(r'\\(?:eqref|ref)\{([^}]+)\}', tex)) <= set(labels)
    bib = set(re.findall(r'\\bibitem\{([^}]+)\}', tex))
    assert set(re.findall(r'\\cite(?:\[[^\]]+\])?\{([^}]+)\}', tex)) <= bib
    assert not re.search(r'\b(?:TODO|TBD|PLACEHOLDER)\b', tex)
    print(json.dumps({'status': 'paper_ledger_checks_passed',
                      'artifact_hashes': 64, 'target_stable_sets': 2167,
                      'target_tight_sets': 88, 'physical_best': actual,
                      'quantum_target_proved': False,
                      'scope': 'headline consistency; run exact certificate checkers separately'}))


if __name__ == '__main__':
    main()
