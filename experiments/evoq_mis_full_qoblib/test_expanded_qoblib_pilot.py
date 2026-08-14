import unittest

import run_expanded_qoblib_pilot as pilot


class ExpandedPilotTests(unittest.TestCase):
    def test_frozen_design_size(self):
        self.assertEqual(len(pilot.NEW_CASES), 3)
        self.assertEqual(len(pilot.METHODS), 3)
        self.assertEqual(len(pilot.ORDERINGS), 2)
        self.assertEqual(len(pilot.SETTINGS), 2)
        self.assertEqual(len(pilot.SEEDS), 3)
        self.assertEqual(3 * 3 * 2, 18)
        self.assertEqual(3 * 3 * 2 * 2 * 3, 108)

    def test_screen_binding(self):
        cases, bks = pilot.configuration()
        self.assertEqual(set(cases), set(pilot.NEW_CASES))
        self.assertTrue(all(cases[name] > 0 for name in cases))
        self.assertTrue(all(bks[name] > 0 for name in bks))

    def test_sign(self):
        self.assertEqual(pilot.sign(0.1), 1)
        self.assertEqual(pilot.sign(-0.1), -1)
        self.assertEqual(pilot.sign(0.0), 0)


if __name__ == "__main__":
    unittest.main()
