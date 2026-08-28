import unittest

import numpy as np

from experiments.hardware_model_witness_phase0.witness_core import (
    GATE_NAMES,
    compose,
    count_key,
    declared_identity_p0,
    gate_retentions,
    is_identity_up_to_phase,
    p0_for_sequence,
)


class WitnessCoreTest(unittest.TestCase):
    def test_native_inverse_is_identity(self):
        self.assertTrue(is_identity_up_to_phase(compose(("Xp", "Xm"))))
        self.assertTrue(is_identity_up_to_phase(compose(("Yp", "Ym"))))

    def test_matching_multiset(self):
        first = ("Xp", "Yp", "Ym", "Xm")
        second = ("Yp", "Xp", "Xm", "Ym")
        self.assertEqual(count_key(first), count_key(second))

    def test_declared_prediction_is_order_blind(self):
        retentions = gate_retentions(0.02, 0.01)
        first = ("Xp", "Yp", "Ym", "Xm")
        second = ("Yp", "Xp", "Xm", "Ym")
        self.assertAlmostEqual(
            declared_identity_p0(first, retentions),
            declared_identity_p0(second, retentions),
            places=14,
        )

    def test_noiseless_identity_survival(self):
        for name in GATE_NAMES:
            inverse = {"Xp": "Xm", "Xm": "Xp", "Yp": "Ym", "Ym": "Yp"}[name]
            self.assertAlmostEqual(p0_for_sequence((name, inverse), 0.0, 0.0), 1.0, places=14)

    def test_unitary_composition(self):
        unitary = compose(("Xp", "Xm"))
        phase = np.trace(unitary) / 2.0
        np.testing.assert_allclose(unitary, phase * np.eye(2), atol=1e-12)


if __name__ == "__main__":
    unittest.main()
