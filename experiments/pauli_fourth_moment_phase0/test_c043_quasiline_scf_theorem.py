"""Mutation tests for the independent C043 verifier."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_c043_quasiline_scf_theorem import RESULT, verify


class C043TheoremTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(RESULT.read_text(encoding="utf-8"))

    def test_frozen_record(self) -> None:
        self.assertEqual(verify(copy.deepcopy(self.payload))["status"], "C043_verified")

    def test_rejects_false_circulant_boundary(self) -> None:
        payload = copy.deepcopy(self.payload)
        row = next(row for row in payload["circulant_obstruction_audit"]["records"] if row["p"] >= 3)
        row["SCF"] = True
        with self.assertRaises(AssertionError):
            verify(payload)

    def test_rejects_erased_nonlocal_countercontrol(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["exact_small_circulant_audit"]["nonlocal_cliques"] = 0
        with self.assertRaises(AssertionError):
            verify(payload)

    def test_rejects_destroyed_nonrank_control(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["positive_controls"]["records"][0]["facet"]["rhs"] += 1
        with self.assertRaises(AssertionError):
            verify(payload)

    def test_rejects_conjecture_downgrade(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["conjecture_proved"] = False
        with self.assertRaises(AssertionError):
            verify(payload)

    def test_rejects_source_hash_corruption(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["source_sha256"] = "0" * 64
        with self.assertRaises(AssertionError):
            verify(payload)


if __name__ == "__main__":
    unittest.main()
