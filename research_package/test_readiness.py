import unittest
import numpy as np
from run_readiness import cp_bounds, bks_indicator, readout_channel


class ReadinessTests(unittest.TestCase):
    def test_cp_extremes_and_symmetry(self):
        k = np.array([0, 1, 5, 9, 10])
        lo, hi = cp_bounds(k, 10, .005)
        self.assertEqual(lo[0], 0)
        self.assertEqual(hi[-1], 1)
        np.testing.assert_allclose(lo, 1-hi[::-1], atol=1e-14)
        self.assertTrue(np.all(lo <= k/10))
        self.assertTrue(np.all(hi >= k/10))

    def test_scorer_little_endian_and_forbidden(self):
        scorer = dict(weights=[1, 2], constant_selected=0, bks=2,
                      impossible=False, forbidden=[[3, 3]])
        np.testing.assert_equal(bks_indicator(scorer), [0, 0, 1, 0])

    def test_readout_exact_product(self):
        p = .1
        out = readout_channel([1, 0, 0, 0], p)
        np.testing.assert_allclose(out, [(1-p)**2, p*(1-p), p*(1-p), p*p])
        self.assertAlmostEqual(out.sum(), 1.)

    def test_noiseless_readout_identity(self):
        probs = np.array([.1, .2, .3, .4])
        np.testing.assert_array_equal(readout_channel(probs, 0), probs)


if __name__ == '__main__':
    unittest.main()
