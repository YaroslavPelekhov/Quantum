import json
import tempfile
import unittest
from pathlib import Path

from verify_c045_priority_submission_audit import RECORD, REPORT, TEX, verify


class TestC045Audit(unittest.TestCase):
    def test_frozen_record(self):
        self.assertEqual(verify()["status"], "c045_priority_submission_audit_verified")

    def _mutated_record(self, mutate):
        data = json.loads(RECORD.read_text(encoding="utf-8"))
        mutate(data)
        tmp = tempfile.TemporaryDirectory()
        path = Path(tmp.name) / "record.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return tmp, path

    def test_rejects_priority_certification(self):
        tmp, path = self._mutated_record(lambda d: d.update(priority_certified=True))
        with tmp, self.assertRaises(AssertionError):
            verify(record_path=path)

    def test_rejects_collision_flip(self):
        tmp, path = self._mutated_record(lambda d: d.update(exact_collision_found=True))
        with tmp, self.assertRaises(AssertionError):
            verify(record_path=path)

    def test_rejects_report_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.md"
            path.write_text(REPORT.read_text(encoding="utf-8") + "\nmutation\n", encoding="utf-8")
            with self.assertRaises(AssertionError):
                verify(report_path=path)

    def test_rejects_decentralized_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "main.tex"
            text = TEX.read_text(encoding="utf-8").replace(
                "Exact weighted Pauli uncertainty on line graphs", "Two unrelated stories"
            )
            path.write_text(text, encoding="utf-8")
            with self.assertRaises(AssertionError):
                verify(tex_path=path)


if __name__ == "__main__":
    unittest.main()
