import unittest
import numpy as np
from scipy.stats import beta
import verify_completed as v


class AuditControls(unittest.TestCase):
    def test_reject_corrupted_norm(self):
        with self.assertRaises(AssertionError):
            v.evolve(np.array([0., 2.]), [])

    def test_reject_nan(self):
        with self.assertRaises(AssertionError):
            v.close(np.nan, 0.)

    def test_wrong_channel_detected(self):
        psi = np.array([0., 1.])
        a = v.evolve(psi, v.kraus_maps(1, 'depolarizing', .2))
        b = v.evolve(psi, v.kraus_maps(1, 'amplitude_damping', .2))
        with self.assertRaises(AssertionError):
            v.close(a, b)

    def test_y_sign(self):
        psi = np.array([1., 1j])/np.sqrt(2.)
        self.assertAlmostEqual(float(np.vdot(psi, v.dense_paulis([(1, 1)], 1)[0]@psi).real), 1.)

    def test_kraus_completeness(self):
        for channel in ('depolarizing', 'amplitude_damping'):
            for p in (0., .03, 1.):
                for group in v.kraus_maps(2, channel, p):
                    v.close(sum(k.conj().T@k for k in group), np.eye(4))

    def test_interval_edges_and_reference(self):
        k = np.array([0, 1, 5, 10]); n = np.full(4, 10)
        lo, hi = v.interval(k, n, .025)
        self.assertEqual(lo[0], 0.)
        self.assertEqual(hi[-1], 1.)
        v.close(lo[1:], beta.ppf(.025, k[1:], n[1:]-k[1:]+1))
        v.close(hi[:-1], beta.ppf(.975, k[:-1]+1, n[:-1]-k[:-1]))

    def test_square_crossing_zero(self):
        self.assertEqual(v.lower(np.array([[5]]), np.array([10]), np.array([2.]))[0], 0.)

    def test_allocation(self):
        n = v.allocate(np.array([0., 1., .5]), np.array([1., 2., 1.]), 10000)
        self.assertEqual(sum(n), 10000)
        self.assertGreaterEqual(min(n), 2)
        self.assertGreater(n[2], n[0])


if __name__ == '__main__':
    unittest.main()
