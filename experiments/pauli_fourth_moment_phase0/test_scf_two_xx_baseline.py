"""C016 exact matrix and applicability corruption controls."""
import copy
import json
import unittest
from verify_scf_two_xx_baseline import verify,DATA,expected_graph


class TwoXXBaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.report=json.loads((DATA/'scf_two_xx_baseline_c016.json').read_text())
    def rejected(self,change):
        r=copy.deepcopy(self.report);change(r)
        with self.assertRaises(AssertionError):verify(r)
    def test_exact_PSD_and_gap(self):
        r=verify(self.report)
        self.assertEqual(r['positive_pivots'],25)
        self.assertEqual(r['exact_objective'],'325328979/50000000')
    def test_wrong_edge_entry(self):
        i,j=min(expected_graph()[1])
        def change(r):r['moment_numerators'][i+1][j+1]=r['moment_numerators'][j+1][i+1]=1
        self.rejected(change)
    def test_negative_pivot(self):
        def change(r):
            m=r['moment_numerators'];m[1][1]=m[0][1]=m[1][0]=-1
        self.rejected(change)
    def test_wrong_objective(self):self.rejected(lambda r:r.update(objective='7'))
    def test_wrong_degrees(self):self.rejected(lambda r:r['degree_histogram'].update({'5':1}))
    def test_false_physical_claim(self):self.rejected(lambda r:r.update(physical_state_claim=True))


if __name__=='__main__':unittest.main()
