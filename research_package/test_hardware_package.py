import hashlib
import json
import unittest
from pathlib import Path

from qiskit import qpy


HERE = Path(__file__).resolve().parent
HARDWARE = HERE / 'hardware'


class HardwarePackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((HARDWARE / 'manifest.json').read_text(encoding='utf-8'))

    def test_submission_is_impossible_from_preparation_script(self):
        script = (HERE / 'prepare_hardware.py').read_text(encoding='utf-8')
        self.assertFalse(self.manifest['submission_enabled'])
        self.assertEqual(self.manifest['status'], 'prepared_not_submitted')
        self.assertIsNone(self.manifest['backend'])
        self.assertIsNone(self.manifest['approved_max_cost'])
        self.assertNotIn('AwsDevice', script)
        self.assertNotIn('create_quantum_task', script)

    def test_all_six_measured_circuits_are_hashed(self):
        self.assertEqual(len(self.manifest['circuits']), 6)
        for row in self.manifest['circuits']:
            path = HARDWARE / row['file']
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), row['sha256'])
            with path.open('rb') as stream:
                circuit, = qpy.load(stream)
            self.assertEqual(circuit.num_qubits, row['qubits'])
            self.assertEqual(circuit.num_clbits, row['qubits'])
            self.assertEqual(circuit.count_ops().get('measure'), row['qubits'])
            self.assertTrue((HARDWARE / path.with_suffix('.qasm').name).exists())

    def test_plan_is_balanced_and_exactly_60000_shots(self):
        tasks = self.manifest['planned_tasks']
        self.assertEqual(len(tasks), 24)
        self.assertEqual(sum(row['shots'] for row in tasks), 60000)
        self.assertEqual(self.manifest['shots_total'], 60000)
        counts = {}
        for row in tasks:
            key = (row['block'], row['case'], row['method'])
            counts[key] = counts.get(key, 0) + 1
        self.assertEqual(len(counts), 24)
        self.assertEqual(set(counts.values()), {1})

    def test_scorers_and_exact_preflight_are_present(self):
        self.assertTrue(self.manifest['local_exact_preflight_passed'])
        for row in self.manifest['circuits']:
            self.assertGreaterEqual(row['exact_bks'], 0)
            self.assertLessEqual(row['exact_bks'], 1)
            self.assertIn('weights', row['scorer'])
            self.assertEqual(len(row['scorer']['weights']), row['qubits'])


if __name__ == '__main__':
    unittest.main()
