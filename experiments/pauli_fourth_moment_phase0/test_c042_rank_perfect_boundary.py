import copy
import json
from pathlib import Path
import unittest

from verify_c042_rank_perfect_boundary import RESULT, ROOT, verify


class C042BoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = json.loads(RESULT.read_text(encoding="utf-8"))

    def test_reference_record(self):
        outcome = verify(copy.deepcopy(self.reference), ROOT)
        self.assertEqual(outcome["status"], "C042_verified")

    def test_rejects_promoted_conjecture(self):
        payload = copy.deepcopy(self.reference)
        payload["scope"]["not_proved"].remove("all SCF quasi-line graphs are rank-perfect")
        with self.assertRaises(AssertionError):
            verify(payload, ROOT)

    def test_rejects_altered_boundary_count(self):
        payload = copy.deepcopy(self.reference)
        payload["order9"]["classes"][1]["graphs"] += 1
        with self.assertRaises(AssertionError):
            verify(payload, ROOT)

    def test_rejects_altered_witness_facet(self):
        payload = copy.deepcopy(self.reference)
        payload["strict_witness"]["not_hperfect_facet"]["alpha"] += 1
        with self.assertRaises(AssertionError):
            verify(payload, ROOT)

    def test_rejects_altered_sample_certificate(self):
        payload = copy.deepcopy(self.reference)
        payload["sampled_circular_arc_stress"]["records"][0]["rank_facet_certificates"][0]["roots"] += 1
        with self.assertRaises(AssertionError):
            verify(payload, ROOT)

    def test_rejects_altered_artifact_hash(self):
        payload = copy.deepcopy(self.reference)
        key = next(iter(payload["artifacts"]))
        payload["artifacts"][key] = "0" * 64
        with self.assertRaises(AssertionError):
            verify(payload, ROOT)


if __name__ == "__main__":
    unittest.main()
