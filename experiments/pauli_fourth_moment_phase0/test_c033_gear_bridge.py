import json
import unittest
from run_c033_gear_bridge import DATA,inverse,edge


class GearBridge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((DATA/'c033_gear_bridge_with_lifting.json').read_text())
        cls.vertices=set(range(24))-{8,9,19,20}
        cls.edges={tuple(e) for e in cls.report['core20_edges']}
    def test_roundtrip(self):
        _,edges,_=inverse(self.vertices,self.edges,self.report['left_gear'],(24,25))
        self.assertEqual(edges,{tuple(e) for e in self.report['inverse14_edges']})
    def test_forbidden_hub_attachment(self):
        bad=self.edges|{(6,22)}
        with self.assertRaises(AssertionError):inverse(self.vertices,bad,self.report['left_gear'],(24,25))
    def test_mismatched_port(self):
        bad=self.edges-{(0,22)}
        with self.assertRaises(AssertionError):inverse(self.vertices,bad,self.report['left_gear'],(24,25))


if __name__=='__main__':unittest.main()
