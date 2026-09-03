"""Exact small-n stabilizer and Pauli utilities for the phase-0 audit."""

from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csc_matrix


def rref_basis(rows: list[int] | tuple[int, ...], qubits: int) -> tuple[int, ...]:
    work = [int(row) for row in rows if row]
    output: list[int] = []
    for column in range(2 * qubits - 1, -1, -1):
        pivot = next(
            (index for index, row in enumerate(work) if (row >> column) & 1),
            None,
        )
        if pivot is None:
            continue
        row = work.pop(pivot)
        work = [other ^ row if (other >> column) & 1 else other for other in work]
        output = [
            other ^ row if (other >> column) & 1 else other for other in output
        ]
        output.append(row)
    return tuple(sorted(output, reverse=True))


def _transform(label: int, gate: tuple[str, int, int], qubits: int) -> int:
    kind, left, right = gate
    mask = (1 << qubits) - 1
    x = label & mask
    z = label >> qubits
    if kind == "H":
        if ((x >> left) & 1) != ((z >> left) & 1):
            x ^= 1 << left
            z ^= 1 << left
    elif kind == "S":
        if (x >> left) & 1:
            z ^= 1 << left
    else:
        if (x >> left) & 1:
            x ^= 1 << right
        if (z >> right) & 1:
            z ^= 1 << left
    return x | (z << qubits)


def lagrangians(qubits: int, cache_dir: Path) -> list[tuple[int, ...]]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache = cache_dir / f"lagrangians_n{qubits}.pkl"
    if cache.exists():
        with cache.open("rb") as handle:
            return pickle.load(handle)
    gates = (
        [("H", index, 0) for index in range(qubits)]
        + [("S", index, 0) for index in range(qubits)]
        + [
            ("C", left, right)
            for left in range(qubits)
            for right in range(qubits)
            if left != right
        ]
    )
    start = rref_basis([1 << (qubits + index) for index in range(qubits)], qubits)
    seen = {start}
    queue = [start]
    position = 0
    while position < len(queue):
        basis = queue[position]
        position += 1
        for gate in gates:
            transformed = rref_basis(
                [_transform(label, gate, qubits) for label in basis], qubits
            )
            if transformed not in seen:
                seen.add(transformed)
                queue.append(transformed)
    with cache.open("wb") as handle:
        pickle.dump(queue, handle)
    return queue


def multiply_phase(left: int, right: int, qubits: int) -> tuple[int, int]:
    mask = (1 << qubits) - 1
    x_left, z_left = left & mask, left >> qubits
    x_right, z_right = right & mask, right >> qubits
    x, z = x_left ^ x_right, z_left ^ z_right
    exponent = (
        (x_left & z_left).bit_count()
        + (x_right & z_right).bit_count()
        - (x & z).bit_count()
        + 2 * (z_left & x_right).bit_count()
    ) % 4
    phase = (1j) ** exponent
    if abs(phase.imag) > 1e-12:
        raise ValueError("basis contains anticommuting generators")
    return int(round(phase.real)), x | (z << qubits)


def stabilizer_matrix(qubits: int, cache_dir: Path) -> tuple[csc_matrix, list]:
    contexts = lagrangians(qubits, cache_dir)
    rows: list[int] = []
    columns: list[int] = []
    data: list[int] = []
    column = 0
    dimension = 1 << qubits
    for basis in contexts:
        phases = [1] * dimension
        labels = [0] * dimension
        for subset in range(1, dimension):
            bit = subset & -subset
            generator = bit.bit_length() - 1
            previous = subset ^ bit
            phase, label = multiply_phase(labels[previous], basis[generator], qubits)
            phases[subset] = phases[previous] * phase
            labels[subset] = label
        for eigenmask in range(dimension):
            for subset in range(1, dimension):
                eigenvalue = -1 if (subset & eigenmask).bit_count() & 1 else 1
                rows.append(labels[subset] - 1)
                columns.append(column)
                data.append(phases[subset] * eigenvalue)
            column += 1
    matrix = csc_matrix(
        (np.asarray(data, dtype=float), (rows, columns)),
        shape=((1 << (2 * qubits)) - 1, column),
    )
    expected = (1 << qubits) * np.prod(
        [2**index + 1 for index in range(1, qubits + 1)]
    )
    if column != expected:
        raise AssertionError((column, expected))
    return matrix, contexts


def pauli_expectations(state: np.ndarray, qubits: int) -> np.ndarray:
    dimension = 1 << qubits
    mask = dimension - 1
    indices = np.arange(dimension, dtype=np.uint32)
    output = np.empty(dimension * dimension - 1)
    for label in range(1, dimension * dimension):
        x, z = label & mask, label >> qubits
        permutation = indices ^ x
        phase = (1j) ** ((x & z).bit_count())
        signs = 1 - 2 * np.asarray(
            [(int(index) & z).bit_count() & 1 for index in indices]
        )
        output[label - 1] = np.vdot(
            state[permutation], phase * signs * state
        ).real
    return output


def stabilizer_gauge(matrix: csc_matrix, coefficients: np.ndarray):
    return linprog(
        np.ones(matrix.shape[1]),
        A_eq=matrix,
        b_eq=coefficients,
        bounds=(0, None),
        method="highs",
        options={
            "dual_feasibility_tolerance": 1e-9,
            "primal_feasibility_tolerance": 1e-9,
        },
    )


def random_state(dimension: int, rng: np.random.Generator) -> np.ndarray:
    state = rng.normal(size=dimension) + 1j * rng.normal(size=dimension)
    return state / np.linalg.norm(state)
