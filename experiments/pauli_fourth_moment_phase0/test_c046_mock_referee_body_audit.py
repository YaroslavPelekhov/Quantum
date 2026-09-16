import json
import tempfile
import unittest
from pathlib import Path

from verify_c046_mock_referee_body_audit import RECORD, REPORT, TEX, verify


class TestC046Audit(unittest.TestCase):
    def test_frozen_record(self):
        self.assertEqual(verify()["status"], "c046_mock_referee_body_audit_verified")

    def _mutated_record(self, mutate):
        data = json.loads(RECORD.read_text(encoding="utf-8"))
        mutate(data)
        tmp = tempfile.TemporaryDirectory()
        path = Path(tmp.name) / "record.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return tmp, path

    def test_rejects_unresolved_internal_gap(self):
        tmp, path = self._mutated_record(
            lambda d: d.update(headline_internal_gaps_remaining=1)
        )
        with tmp, self.assertRaises(AssertionError):
            verify(record_path=path)

    def test_rejects_external_review_overclaim(self):
        tmp, path = self._mutated_record(lambda d: d.update(external_reviewed=True))
        with tmp, self.assertRaises(AssertionError):
            verify(record_path=path)

    def test_rejects_report_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.md"
            path.write_text(REPORT.read_text(encoding="utf-8") + "\nmutation\n", encoding="utf-8")
            with self.assertRaises(AssertionError):
                verify(report_path=path)

    def test_rejects_missing_body_definition(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "main.tex"
            text = TEX.read_text(encoding="utf-8").replace(
                r"\boxed{\BETA(L(R))=\MATCH(R).}",
                r"\boxed{\beta(L(R),w)=\nu(R,w).}",
            )
            path.write_text(text, encoding="utf-8")
            with self.assertRaises(AssertionError):
                verify(tex_path=path)

    def test_rejects_old_representation_quantifier(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "main.tex"
            text = TEX.read_text(encoding="utf-8").replace(
                r"\max_\rho\sum_i", r"\sup_{\{P_i\},\rho}\sum_i", 1
            )
            path.write_text(text, encoding="utf-8")
            with self.assertRaises(AssertionError):
                verify(tex_path=path)


if __name__ == "__main__":
    unittest.main()
