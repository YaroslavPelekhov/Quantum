from __future__ import annotations

import math
import unittest

import numpy as np

from .run_phase0 import (
    SAMPLE_COUNT,
    atom_lower_bound,
    conditional_basis,
    effective_rank,
    onsite_detunings,
    path_graph,
    relative_tail,
    response_hankel,
    response_samples,
)
from .run_physical_surrogate import Topology, enumerate_topologies, surrogate_response
from .run_host_transfer import heldout_hosts, host_density
from .run_process_gram import word_gram


class CausalBoundaryResponseTests(unittest.TestCase):
    def test_path_is_native_unit_disk_and_twin_free(self):
        for k in range(3, 14):
            graph = path_graph(k)
            positions = {node: (0.9 * node, 0.0) for node in graph}
            realised = {
                (first, second)
                for first in graph
                for second in graph
                if first < second and math.dist(positions[first], positions[second]) <= 1.0
            }
            self.assertEqual(realised, set(graph.edges()))
            if k >= 4:
                neighbourhoods = [frozenset(graph.neighbors(node)) for node in graph]
                self.assertEqual(len(neighbourhoods), len(set(neighbourhoods)))

    def test_conditional_dimensions(self):
        expected_unoccupied = {3: 5, 4: 8, 5: 13, 6: 21}
        expected_occupied = {3: 3, 4: 5, 5: 8, 6: 13}
        for k, dimension in expected_unoccupied.items():
            self.assertEqual(len(conditional_basis(k, False)), dimension)
            self.assertEqual(len(conditional_basis(k, True)), expected_occupied[k])

    def test_response_starts_at_one_and_prefix_identity(self):
        for regime in ("uniform", "perturbed"):
            response = np.asarray(response_samples(3, 2.0, regime))
            self.assertEqual(len(response), SAMPLE_COUNT)
            self.assertAlmostEqual(response[0].real, 1.0, places=12)
            self.assertAlmostEqual(response[0].imag, 0.0, places=12)
            self.assertTrue(np.all(np.isfinite(response)))

    def test_hankel_rank_helpers(self):
        samples = np.asarray(
            [np.exp(0.17j * index) + 0.7 * np.exp(0.43j * index) for index in range(SAMPLE_COUNT)],
            dtype=complex,
        )
        singular_values = np.linalg.svd(response_hankel(samples), compute_uv=False)
        self.assertLess(relative_tail(singular_values, 2), 1e-10)
        self.assertEqual(effective_rank(singular_values, 1e-9), 2)
        self.assertEqual(atom_lower_bound(1), 0)
        self.assertEqual(atom_lower_bound(4), 1)
        self.assertEqual(atom_lower_bound(5), 2)
        self.assertEqual(atom_lower_bound(64), 3)
        self.assertEqual(atom_lower_bound(65), 4)

    def test_perturbation_is_small_and_nonuniform(self):
        values = onsite_detunings(13, "perturbed")
        self.assertLessEqual(float(np.max(np.abs(values - 0.37))), 0.03 + 1e-12)
        self.assertGreater(float(np.std(values)), 0.0)

    def test_topology_enumeration_and_path_response(self):
        self.assertEqual([len(enumerate_topologies(atoms)) for atoms in (1, 2, 3)], [1, 4, 16])
        horizon = 2.0
        times = np.linspace(0.0, horizon, SAMPLE_COUNT)
        for atoms in (1, 2, 3):
            topology = Topology(
                atoms=atoms,
                internal_edges=tuple((node, node + 1) for node in range(atoms - 1)),
                port_blocked=(0,),
                canonical_code="test_path",
            )
            parameters = np.concatenate((np.full(atoms, 0.37), np.asarray([0.0])))
            expected = np.asarray(response_samples(atoms, horizon, "uniform"))
            actual = surrogate_response(topology, parameters, times)
            self.assertLess(float(np.max(np.abs(actual - expected))), 1e-10)

    def test_heldout_host_corpus_and_partial_trace(self):
        hosts = heldout_hosts()
        self.assertEqual(len(hosts), 30)
        self.assertEqual(len({host.code for host in hosts}), 30)
        state = np.asarray([1.0, 1.0j]) / np.sqrt(2.0)
        density = host_density((0, 1), state, host_n=1)
        self.assertAlmostEqual(float(np.trace(density).real), 1.0, places=12)
        self.assertLess(float(np.max(np.abs(density - np.conjugate(density).T))), 1e-12)

    def test_one_bin_gram_recovers_registered_response(self):
        from .run_phase0 import conditional_hamiltonian

        masks0, h0 = conditional_hamiltonian(3, "uniform", False)
        masks1, h1 = conditional_hamiltonian(3, "uniform", True)
        gram = word_gram(masks0, h0.toarray(), masks1, h1.toarray(), 1)
        response = np.asarray(response_samples(3, 5.0, "uniform"))
        self.assertLess(abs(gram[0, 1] - response[-1]), 1e-10)
        self.assertLess(float(np.max(np.abs(gram - np.conjugate(gram).T))), 1e-12)


if __name__ == "__main__":
    unittest.main()
