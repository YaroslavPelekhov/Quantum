import unittest

import numpy as np

import run_independent_ladder_audit as audit


class IndependentLadderAuditTests(unittest.TestCase):
    def test_jsonable_handles_numpy_boolean(self):
        self.assertIs(audit.jsonable(np.bool_(True)), True)

    def test_frozen_design_has_thirty_unique_jobs(self):
        identities = {
            (setting["name"], method, ordering)
            for setting in audit.SETTINGS
            for method in audit.METHOD_NAMES
            for ordering in audit.ORDERINGS
        }
        self.assertEqual(len(audit.SETTINGS), 5)
        self.assertEqual(len(identities), audit.EXPECTED_JOBS)
        self.assertEqual(audit.EXPECTED_JOBS, 30)

    def test_static_accumulator_matches_brute_force(self):
        scorer = {
            "constant_selected": 1,
            "weights": [2, -1, 3, 1],
            "forbidden": [[3, 3], [12, 4]],
            "impossible": False,
            "bks": 5,
        }
        rng = np.random.default_rng(918273)
        state = rng.normal(size=16) + 1j * rng.normal(size=16)
        state /= np.linalg.norm(state)
        metrics, _ = audit.score_state(state, scorer)
        expected = {name: 0.0 for name in audit.METRICS}
        for index, amplitude in enumerate(state):
            probability = float(abs(amplitude) ** 2)
            feasible = all((index & mask) != pattern for mask, pattern in scorer["forbidden"])
            if not feasible:
                continue
            size = scorer["constant_selected"] + sum(
                weight * ((index >> qubit) & 1)
                for qubit, weight in enumerate(scorer["weights"])
            )
            expected["feasible_rate"] += probability
            expected["bks_rate"] += probability * (size >= scorer["bks"])
            expected["near_bks_rate"] += probability * (size >= scorer["bks"] - 1)
            expected["quality_mass"] += probability * min(size / scorer["bks"], 1.0)
        for name in audit.METRICS:
            self.assertAlmostEqual(metrics[name], expected[name], places=14)

    def test_axis_conversion_rule(self):
        qiskit_flat = np.arange(16).reshape(2, 2, 2, 2)
        q0_first = qiskit_flat.transpose(3, 2, 1, 0)
        recovered = q0_first.transpose(3, 2, 1, 0).reshape(-1)
        np.testing.assert_array_equal(recovered, np.arange(16))

    def test_comparison_is_global_phase_invariant(self):
        rng = np.random.default_rng(123)
        reference = rng.normal(size=64) + 1j * rng.normal(size=64)
        reference /= np.linalg.norm(reference)
        approximate = np.asarray(reference * np.exp(0.73j), dtype=np.complex128)
        comparison = audit.compare_states(reference, approximate)
        self.assertAlmostEqual(comparison["state_fidelity"], 1.0, places=14)
        self.assertLess(comparison["total_variation_distance"], 1e-14)


if __name__ == "__main__":
    unittest.main()
