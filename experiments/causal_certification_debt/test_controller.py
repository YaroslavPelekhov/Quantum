from __future__ import annotations
import hashlib, json, unittest
try:
    from .analyze_controller import REPO, RESULTS, build_summary
except ImportError:
    from analyze_controller import REPO, RESULTS, build_summary

class ControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = build_summary(); cls.r = {x["label"]: x for x in cls.s["runs"]}

    def test_sorted(self):
        x = self.r["ibm32_sorted"]; lr, mr = x["methods"]
        self.assertTrue(x["certified"]); self.assertGreater(x["certificate_margin"], .04)
        self.assertGreater(x["paired_work_saving_fraction"], .54)
        self.assertGreater(lr["bond_counts"]["256"], 400)
        self.assertEqual(mr["bond_counts"]["256"], 0)
        self.assertGreater(lr["bond_transitions"], 1)

    def test_spectral(self):
        x = self.r["ibm32_spectral"]
        self.assertTrue(x["certified"]); self.assertGreater(x["paired_work_saving_fraction"], .70)
        self.assertLess(x["methods"][0]["bond_counts"]["256"], 418)
        self.assertLess(self.s["comparisons"]["spectral_controller_work_vs_manual"], .80)

    def test_new_graph(self):
        x = self.r["chesapeake_sorted"]; self.assertTrue(x["certified"])
        for m in x["methods"]: self.assertEqual(m["bond_counts"], {"128":210,"256":0,"512":0})

    def test_audits(self):
        a = self.s["audit_totals"]
        self.assertEqual(a["score_argmin_violations"], 0)
        self.assertEqual(a["dense_operator_violations"], 0)
        self.assertEqual(a["dense_residual_violations"], 0)
        self.assertLess(a["maximum_debt_reconstruction_error"], 1e-12)

    def test_manifest(self):
        m = json.loads((RESULTS/"CONTROLLER_MANIFEST.json").read_text(encoding="utf-8"))
        for section in ("sources","inputs","artifacts"):
            for rel, expected in m[section].items():
                p = REPO/rel
                self.assertEqual(p.stat().st_size, expected["bytes"])
                self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), expected["sha256"])

if __name__ == "__main__": unittest.main()
