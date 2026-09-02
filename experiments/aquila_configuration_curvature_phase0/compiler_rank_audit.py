"""Exact finite-field audit of the one-mask weak-curvature compiler ranks."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "results" / "aquila_configuration_curvature_phase0"
PRIME = 2**31 - 1

# Exact rational two-dimensional inverse-sixth witnesses.  Coordinates and
# onsite energies are hard-coded so the certificate does not depend on a
# pseudo-random-number implementation.  The coordinate unit and C6 scale are
# arbitrary: this is a geometric algebraic-rank witness, not a live-device
# feasibility claim.
GEOMETRY_WITNESSES = {
    3: {
        "positions": ((66, 24), (25, 13), (1, 64)),
        "onsite": (750162, 614660, 97379),
    },
    4: {
        "positions": ((66, 24), (25, 13), (1, 64), (74, 61)),
        "onsite": (97379, 489954, 134087, 481641),
    },
    5: {
        "positions": ((66, 24), (25, 13), (1, 64), (74, 61), (8, 48)),
        "onsite": (134087, 481641, 447068, 759237, 997820),
    },
    6: {
        "positions": ((66, 24), (25, 13), (1, 64), (74, 61), (8, 48), (12, 47)),
        "onsite": (447068, 759237, 997820, 587330, 477565, 158881),
    },
}


def cube_complex(n: int):
    vertices = tuple(range(1 << n))
    edges = tuple((state, site) for state in vertices for site in range(n) if not state & (1 << site))
    edge_index = {edge: index for index, edge in enumerate(edges)}
    faces = tuple(
        (state, first, second)
        for state in vertices
        for first in range(n)
        for second in range(first + 1, n)
        if not state & (1 << first) and not state & (1 << second)
    )
    coboundary = np.zeros((len(faces), len(edges)), dtype=np.int64)
    for row, (state, first, second) in enumerate(faces):
        coboundary[row, edge_index[(state, first)]] += 1
        coboundary[row, edge_index[(state | (1 << first), second)]] += 1
        coboundary[row, edge_index[(state | (1 << second), first)]] -= 1
        coboundary[row, edge_index[(state, second)]] -= 1
    # Keep the signed incidence matrix here.  Reducing ``-1`` to ``p - 1``
    # before the matrix products below would make NumPy accumulate products of
    # order p**2 in int64 and can silently overflow.  ``rank_mod`` performs the
    # modular reduction itself, while signed matrix products stay small.
    return vertices, edges, faces, coboundary


def rank_mod(matrix: np.ndarray, prime: int = PRIME) -> int:
    work = np.asarray(matrix, dtype=np.int64).copy() % prime
    rows, columns = work.shape
    rank = 0
    for column in range(columns):
        pivots = np.flatnonzero(work[rank:, column])
        if len(pivots) == 0:
            continue
        pivot = rank + int(pivots[0])
        if pivot != rank:
            work[[rank, pivot]] = work[[pivot, rank]]
        inverse = pow(int(work[rank, column]), prime - 2, prime)
        work[rank] = (work[rank] * inverse) % prime
        for row in range(rows):
            if row != rank and work[row, column]:
                work[row] = (work[row] - int(work[row, column]) * work[rank]) % prime
        rank += 1
        if rank == rows:
            break
    return rank


def incremental_column_ranks(columns: list[np.ndarray], prime: int = PRIME) -> list[int]:
    basis: dict[int, np.ndarray] = {}
    ranks = []
    for column in columns:
        vector = np.asarray(column, dtype=np.int64).copy() % prime
        while True:
            nonzero = np.flatnonzero(vector)
            if len(nonzero) == 0:
                break
            pivot = int(nonzero[0])
            if pivot not in basis:
                inverse = pow(int(vector[pivot]), prime - 2, prime)
                basis[pivot] = (vector * inverse) % prime
                break
            vector = (vector - int(vector[pivot]) * basis[pivot]) % prime
        ranks.append(len(basis))
    return ranks


def inverse_sixth_frequencies(
    n: int, edges: tuple[tuple[int, int], ...], prime: int = PRIME
) -> tuple[np.ndarray, np.ndarray]:
    witness = GEOMETRY_WITNESSES[n]
    positions = witness["positions"]
    onsite = witness["onsite"]
    interactions = np.zeros((n, n), dtype=np.int64)
    for first in range(n):
        for second in range(first + 1, n):
            dx = positions[first][0] - positions[second][0]
            dy = positions[first][1] - positions[second][1]
            squared_distance = dx * dx + dy * dy
            denominator = pow(squared_distance, 3, prime)
            value = pow(denominator, prime - 2, prime)
            interactions[first, second] = interactions[second, first] = value
    frequencies = []
    for state, site in edges:
        value = int(onsite[site])
        for occupied in range(n):
            if state & (1 << occupied):
                value += int(interactions[site, occupied])
        frequencies.append(value % prime)
    return np.asarray(frequencies, dtype=np.int64), interactions


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    summary_rows = []
    profile_rows = []
    all_checks = True
    for n in range(3, 7):
        vertices, edges, faces, coboundary = cube_complex(n)
        full_rank = rank_mod(coboundary)
        formula_rank = (n - 2) * 2 ** (n - 1) + 1
        frequencies, interactions = inverse_sixth_frequencies(n, edges)
        distinct = len(set(map(int, frequencies))) == len(frequencies)

        first_order = np.zeros((len(faces), n), dtype=np.int64)
        for row, (_, first, second) in enumerate(faces):
            coupling = int(interactions[first, second])
            first_order[row, first] = (first_order[row, first] - coupling) % PRIME
            first_order[row, second] = (first_order[row, second] + coupling) % PRIME
        first_order_rank = rank_mod(first_order)

        powers = np.ones(len(edges), dtype=np.int64)
        curvature_columns = []
        for degree in range(full_rank + 2):
            if degree > 0:
                powers = np.asarray([int(a) * int(b) % PRIME for a, b in zip(powers, frequencies)], dtype=np.int64)
            curvature_columns.append((coboundary @ powers) % PRIME)
        ranks = incremental_column_ranks(curvature_columns)
        for degree, rank in enumerate(ranks):
            profile_rows.append({"n": n, "polynomial_degree": degree, "finite_field_rank": rank})
        first_full_degree = next(degree for degree, rank in enumerate(ranks) if rank == full_rank)
        expected_profile = all(rank == min(max(0, degree - 1), full_rank) for degree, rank in enumerate(ranks))
        row = {
            "n": n,
            "vertices": len(vertices),
            "edges": len(edges),
            "plaquettes": len(faces),
            "coboundary_rank_mod_p": full_rank,
            "cycle_rank_formula": formula_rank,
            "generic_frequency_classes": len(set(map(int, frequencies))),
            "all_frequencies_distinct_mod_p": distinct,
            "inverse_sixth_2d_geometry": True,
            "one_affine_mask_realisable": True,
            "first_interaction_order_rank": first_order_rank,
            "first_interaction_order_formula": n - 1,
            "first_full_polynomial_degree": first_full_degree,
            "expected_polynomial_profile": expected_profile,
        }
        summary_rows.append(row)
        all_checks &= (
            full_rank == formula_rank
            and distinct
            and first_order_rank == n - 1
            and first_full_degree == full_rank + 1
            and expected_profile
        )
        print(json.dumps(row), flush=True)

    with (OUTPUT / "compiler_rank_audit.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary_rows[0]))
        writer.writeheader()
        writer.writerows(summary_rows)
    with (OUTPUT / "compiler_polynomial_rank_profile.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(profile_rows[0]))
        writer.writeheader()
        writer.writerows(profile_rows)
    geometry_payload = {}
    for n, witness in GEOMETRY_WITNESSES.items():
        onsite = witness["onsite"]
        minimum = min(onsite)
        denominator = max(onsite) - minimum
        geometry_payload[str(n)] = {
            "positions_integer_2d": witness["positions"],
            "onsite_integer": onsite,
            "mask_numerators": [value - minimum for value in onsite],
            "mask_denominator": denominator,
            "interaction": "V_ij = 1 / ||r_i-r_j||^6 over Q, represented modulo p",
        }
    (OUTPUT / "compiler_geometry_witnesses.json").write_text(
        json.dumps(
            {
                "scope": "exact geometric algebraic witness; not a live-device feasibility packet",
                "prime": PRIME,
                "witnesses": geometry_payload,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    payload = {
        "prime": PRIME,
        "tested_n": [3, 4, 5, 6],
        "all_exact_checks_pass": bool(all_checks),
        "verdict": "KILL_ONE_MASK_LOW_RANK_CURVATURE_HYPOTHESIS",
        "scope": (
            "exact modular inverse-sixth 2D witnesses for tested sizes; polynomial profile is not "
            "asserted as a proof for all n"
        ),
        "resource_conclusion": (
            "generic weak-drive algebraic curvature rank is full; the exponential time-bandwidth "
            "bound currently applies only to arbitrary edge-response compilation, not curvature-only targets"
        ),
    }
    (OUTPUT / "compiler_rank_summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if not all_checks:
        raise AssertionError("compiler rank audit failed a frozen algebraic identity")


if __name__ == "__main__":
    main()
