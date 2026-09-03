"""Build the deterministic 4,922,775-row six-qubit Lagrangian cache."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np

from stabilizer_core import lagrangians, rref_basis


def symplectic(left: int, right: int) -> int:
    x_left, z_left = left & 31, left >> 5
    x_right, z_right = right & 31, right >> 5
    return ((x_left & z_right).bit_count() + (z_left & x_right).bit_count()) & 1


def solve_dual(hyperplane: tuple[int, ...], outside: int) -> int:
    rows = []
    for label, rhs in [(label, 0) for label in hyperplane] + [(outside, 1)]:
        x, z = label & 31, label >> 5
        rows.append([z | (x << 5), rhs])
    pivots: list[int] = []
    row = 0
    for column in range(10):
        pivot = next(
            (index for index in range(row, len(rows)) if (rows[index][0] >> column) & 1),
            None,
        )
        if pivot is None:
            continue
        rows[row], rows[pivot] = rows[pivot], rows[row]
        for index in range(len(rows)):
            if index != row and (rows[index][0] >> column) & 1:
                rows[index][0] ^= rows[row][0]
                rows[index][1] ^= rows[row][1]
        pivots.append(column)
        row += 1
    solution = 0
    for (_, rhs), column in zip(rows[:row], pivots):
        if rhs:
            solution |= 1 << column
    if not all(symplectic(solution, label) == 0 for label in hyperplane):
        raise AssertionError("dual solution does not centralize hyperplane")
    if symplectic(solution, outside) != 1:
        raise AssertionError("dual solution misses outside generator")
    return solution


def embed(label: int) -> int:
    return (label & 31) | ((label >> 5) << 6)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-dir", type=Path, default=Path(".cache"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    contexts5 = lagrangians(5, args.cache_dir)
    started = time.time()
    hyperplanes: dict[tuple[int, ...], tuple[int, int]] = {}
    for basis in contexts5:
        for mask in range(1, 32):
            pivot = (mask & -mask).bit_length() - 1
            rows = [
                basis[index] ^ (basis[pivot] if (mask >> index) & 1 else 0)
                for index in range(5)
                if index != pivot
            ]
            key = rref_basis(rows, 5)
            if key not in hyperplanes:
                outside = basis[pivot]
                hyperplanes[key] = (outside, solve_dual(key, outside))
    if len(hyperplanes) != 782_595:
        raise AssertionError(len(hyperplanes))

    total = 4_922_775
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output = np.lib.format.open_memmap(
        args.output, mode="w+", dtype=np.uint16, shape=(total, 6)
    )
    position = 0
    x6, z6 = 1 << 5, 1 << 11
    for basis in contexts5:
        embedded = np.asarray([embed(label) for label in basis], dtype=np.uint16)
        for final in (x6, z6, x6 ^ z6):
            output[position, :5] = embedded
            output[position, 5] = final
            position += 1
    pairs = ((1, 2), (1, 3), (2, 1), (2, 3), (3, 1), (3, 2))
    for hyperplane, (outside, dual) in hyperplanes.items():
        embedded = np.asarray([embed(label) for label in hyperplane], dtype=np.uint16)
        cosets = (0, embed(outside), embed(dual), embed(outside ^ dual))
        for left, right in pairs:
            output[position, :4] = embedded
            output[position, 4] = x6 ^ cosets[left]
            output[position, 5] = z6 ^ cosets[right]
            position += 1
    if position != total:
        raise AssertionError(position)
    output.flush()
    print(
        f"wrote {args.output} shape={output.shape} bytes={output.nbytes} "
        f"seconds={time.time() - started:.3f}"
    )


if __name__ == "__main__":
    main()
