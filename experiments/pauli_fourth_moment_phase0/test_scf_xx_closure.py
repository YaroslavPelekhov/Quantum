"""C012 exact hull and corruption controls."""
import copy
import json
import unittest
from verify_scf_xx_closure import verify,DATA
from verify_scf_family_facet_closure import cube_clip
from fractions import Fraction as F


class XXClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((DATA/'scf_xx_closure_c012.json').read_text())

    def test_independent_complete_hull_and_missing_facet(self):
        result=verify(self.report)
        self.assertEqual((result['STAB_vertices'],result['facets']),(203,44))

    def test_wrong_graph(self):
        r=copy.deepcopy(self.report)
        r['target']['graph6']='LhEM?rcNLhleuo'
        with self.assertRaises(AssertionError):verify(r)

    def test_overclaim(self):
        r=copy.deepcopy(self.report)
        r['unrestricted_SCF_theorem']=True
        with self.assertRaises(AssertionError):verify(r)

    def test_dimension_guard_still_bounded(self):
        with self.assertRaises(AssertionError):cube_clip(16,[],max_dimension=16)
        with self.assertRaises(AssertionError):cube_clip(15,[])

    def test_cut_order_preserves_exact_rational_intersection(self):
        facets=[[1,-1,-1],[1,-2,-1],[0,1,0],[0,0,1]]
        dense,_=cube_clip(2,facets)
        sparse,_=cube_clip(2,facets,sparse_first=True)
        self.assertEqual(dense,sparse)
        self.assertEqual(sparse,{(F(0),F(0)),(F(0),F(1)),(F(1,2),F(0))})

    def test_edge_index_equals_full_pair_scan(self):
        old=json.loads((DATA/'scf_family_facet_closure.json').read_text())
        missing=copy.deepcopy(old['target'])
        del missing['facets_b_plus_ax'][old['missing_facet_control']['removed_facet_index']]
        for row in old['controls']+[old['target'],missing]:
            n=len(row['facets_b_plus_ax'][0])-1
            for sparse in (False,True):
                expected,trace=cube_clip(n,row['facets_b_plus_ax'],sparse_first=sparse)
                actual,index_trace=cube_clip(n,row['facets_b_plus_ax'],sparse_first=sparse,indexed_edges=True)
                self.assertEqual((actual,index_trace),(expected,trace))


if __name__=='__main__':unittest.main()
