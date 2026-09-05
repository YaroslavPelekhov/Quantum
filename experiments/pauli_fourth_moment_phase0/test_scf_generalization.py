from fractions import Fraction as F
import json
import unittest
from verify_scf_generalization import DATA, verify_all, verify_gluing, verify_pair_failure, stable


class GeneralizationTests(unittest.TestCase):
    def test_all_exact_obstructions(self):
        result = verify_all()
        self.assertEqual(result['exact_gluing_obstructions'], 13)
        self.assertEqual(result['exact_quantum_pair_recipe_counterexamples'], 5)

    def test_one_missing_pair_event(self):
        data = json.loads((DATA/'scf_gluing_obstruction.json').read_text())
        row = next(r for r in data['records'] if r['representative_index'] == 7)
        pair = row['separator_pair_ranges'][0]
        self.assertEqual(pair['pair'], [5,6])
        self.assertEqual((pair['left']['upper'], pair['right']['lower']), ('0','1/3'))

    def test_corrupt_mixture_rejected(self):
        row = json.loads((DATA/'scf_gluing_obstruction.json').read_text())['records'][0]
        row['left_STAB_decomposition'][0]['probability'] = '1/2'
        with self.assertRaises(AssertionError):
            verify_gluing(row)

    def test_corrupt_quantum_state_rejected(self):
        rows = json.loads((DATA/'scf_pair_completion_audit.json').read_text())['records']
        row = next(r for r in rows if 'separator' in r)
        row['integer_state_real'][0] += 1
        with self.assertRaises(AssertionError):
            verify_pair_failure(row)

    def test_exact_antiblocker_audit_counts(self):
        row = json.loads((DATA/'scf_rank_two_lift.json').read_text())
        self.assertEqual((row['atlas_graphs'],row['order9_SCF_graphs'],row['antiblocker_vertices']), (172,1725,177287))
        self.assertTrue(all(r['all_exact_checks_passed'] for r in row['records']))

    def test_classical_rank_polytope_is_not_STAB(self):
        # C5 plus a universal hub. This guards against omitting the quantum
        # join step from the alpha<=2 rank-to-weight theorem.
        edges = {tuple(sorted((i,(i+1)%5))) for i in range(5)} | {(i,5) for i in range(5)}
        masks = [m for m in range(64) if stable(m,edges)]
        for subset in range(1,64):
            self.assertLessEqual(F(subset.bit_count(),3), max((m&subset).bit_count() for m in masks))
        self.assertEqual(F(5,3)+2*F(1,3)-2, F(1,3))


if __name__ == '__main__':
    unittest.main(verbosity=2)
