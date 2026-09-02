"""Unit tests for the pure-NumPy CMRT synthetic QAOA backend."""

from __future__ import annotations

import numpy as np

from experiments.cmrt_phase0.synthetic_qaoa import (
    event_probability,
    hardware_surrogate_distribution,
    maximum_independent_set_indices,
    qaoa_mis_statevector,
    truncate_state_tt_svd,
)


def _problem() -> tuple[int, list[tuple[int, int]], list[float], list[float]]:
    return 5, [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)], [0.37, 0.81], [0.22, 0.49]


def test_qaoa_statevector_is_normalized() -> None:
    n_qubits, edges, gammas, betas = _problem()
    exact = qaoa_mis_statevector(n_qubits, edges, gammas, betas)
    approximate = qaoa_mis_statevector(
        n_qubits,
        edges,
        gammas,
        betas,
        qubit_order=[2, 4, 1, 3, 0],
        max_bond=2,
    )
    assert np.isclose(np.linalg.norm(exact), 1.0, atol=1e-12)
    assert np.isclose(np.linalg.norm(approximate), 1.0, atol=1e-12)


def test_default_truncation_occurs_after_both_sublayers() -> None:
    n_qubits, edges, gammas, betas = _problem()
    _, diagnostics = qaoa_mis_statevector(
        n_qubits,
        edges,
        gammas,
        betas,
        qubit_order=[2, 4, 1, 3, 0],
        max_bond=2,
        return_diagnostics=True,
    )

    expected = [
        (layer, stage)
        for layer in range(len(gammas))
        for stage in ("cost_layer", "mixer_layer")
    ]
    observed = [(entry["layer"], entry["stage"]) for entry in diagnostics["truncations"]]
    assert diagnostics["truncate_after"] == ["cost_layer", "mixer_layer"]
    assert observed == expected
    assert len(diagnostics["truncations"]) == 2 * len(gammas)


def test_no_truncation_is_equivalent_for_arbitrary_orders() -> None:
    n_qubits, edges, gammas, betas = _problem()
    exact = qaoa_mis_statevector(n_qubits, edges, gammas, betas)

    for order in ([0, 1, 2, 3, 4], [4, 2, 0, 3, 1], [1, 3, 4, 0, 2]):
        reconstructed = truncate_state_tt_svd(
            exact,
            n_qubits,
            qubit_order=order,
            max_bond=1 << (n_qubits // 2),
            relative_cutoff=0.0,
        )
        layerwise = qaoa_mis_statevector(
            n_qubits,
            edges,
            gammas,
            betas,
            qubit_order=order,
            max_bond=1 << (n_qubits // 2),
            relative_cutoff=0.0,
        )
        assert np.allclose(reconstructed, exact, atol=2e-12, rtol=2e-12)
        assert np.allclose(layerwise, exact, atol=2e-12, rtol=2e-12)


def test_event_probability_is_in_range_and_accepts_multiple_event_forms() -> None:
    n_qubits, edges, gammas, betas = _problem()
    state = qaoa_mis_statevector(n_qubits, edges, gammas, betas, max_bond=2)
    event = maximum_independent_set_indices(n_qubits, edges)

    probability = event_probability(state, event)
    string_probability = event_probability(state, [format(index, f"0{n_qubits}b") for index in event])
    predicate_probability = event_probability(state, lambda index: index in set(event))

    assert 0.0 <= probability <= 1.0
    assert np.isclose(probability, string_probability, atol=1e-15)
    assert np.isclose(probability, predicate_probability, atol=1e-15)


def test_hardware_surrogate_noise_is_deterministic_and_normalized() -> None:
    n_qubits, edges, gammas, betas = _problem()
    kwargs = dict(
        n_qubits=n_qubits,
        edges=edges,
        gammas=gammas,
        betas=betas,
        angle_sigma=0.03,
        edge_sigma=0.04,
        readout_flip=0.025,
        depolarizing=0.08,
    )
    first, first_metadata = hardware_surrogate_distribution(
        **kwargs, seed=1729, return_metadata=True
    )
    second, second_metadata = hardware_surrogate_distribution(
        **kwargs, seed=1729, return_metadata=True
    )
    different = hardware_surrogate_distribution(**kwargs, seed=1730)

    assert np.array_equal(first, second)
    assert first_metadata == second_metadata
    assert np.isclose(first.sum(), 1.0, atol=1e-15)
    assert np.all((first >= 0.0) & (first <= 1.0))
    assert not np.allclose(first, different, atol=1e-12, rtol=1e-12)


def test_zero_noise_surrogate_matches_exact_distribution() -> None:
    n_qubits, edges, gammas, betas = _problem()
    exact = qaoa_mis_statevector(n_qubits, edges, gammas, betas)
    surrogate = hardware_surrogate_distribution(
        n_qubits=n_qubits,
        edges=edges,
        gammas=gammas,
        betas=betas,
        seed=7,
    )
    assert np.allclose(surrogate, np.abs(exact) ** 2, atol=1e-14, rtol=1e-14)
