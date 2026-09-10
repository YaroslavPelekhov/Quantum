import copy
import json
import unittest

from c020_exact_certificate import DATA
from verify_c038_line_graph_hbar import verify


class LineGraphHbarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((DATA / "c038_line_graph_hbar.json").read_text())

    def test_valid(self):
        result = verify(self.report)
        self.assertEqual(result["atlas_nonempty_roots"], len(self.report["records"]))

    def test_corrupt_gap(self):
        report = copy.deepcopy(self.report)
        report["strict_hperfect_separations"][0]["h_relaxation_gap"] = "1/3"
        with self.assertRaises(AssertionError):
            verify(report)

    def test_corrupt_scope(self):
        report = copy.deepcopy(self.report)
        report["unrestricted_SCF_theorem"] = True
        with self.assertRaises(AssertionError):
            verify(report)

    def test_corrupt_hash(self):
        report = copy.deepcopy(self.report)
        report["theorem_note_sha256"] = "0" * 64
        with self.assertRaises(AssertionError):
            verify(report)

    def test_corrupt_direct_majorana_check(self):
        report = copy.deepcopy(self.report)
        report["max_direct_majorana_norm_error"] = 0.1
        with self.assertRaises(AssertionError):
            verify(report)


if __name__ == "__main__":
    unittest.main()
