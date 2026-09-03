"""Reduce the last SCF facet atom to an explicit scalar inequality."""

from __future__ import annotations

import argparse
import itertools
import json
from fractions import Fraction
from pathlib import Path

import networkx as nx
import numpy as np
import sympy as sp


LIGHT = [0, 1, 2, 4, 6]
HEAVY = [3, 5, 7, 8]
CYCLES = [
    (0, 5, 6, 7),
    (0, 3, 4, 8),
    (1, 4, 6, 8),
    (2, 4, 5, 6),
    (3, 4, 6, 7),
    (3, 4, 6, 8),
    (4, 5, 6, 7),
    (4, 5, 6, 8),
]


def multiply_words(graph: nx.Graph, left: tuple[int, ...], right: tuple[int, ...]):
    word = list(left) + list(right)
    sign = 1
    index = 0
    while index < len(word) - 1:
        if word[index] == word[index + 1]:
            del word[index : index + 2]
            index = max(0, index - 1)
        elif word[index] > word[index + 1]:
            first, second = word[index], word[index + 1]
            word[index], word[index + 1] = second, first
            if graph.has_edge(first, second):
                sign *= -1
            index = max(0, index - 1)
        else:
            index += 1
    return tuple(word), sign


def chordless_four_cycles(graph: nx.Graph) -> list[tuple[int, ...]]:
    cycles = set()
    for cycle in itertools.permutations(graph.nodes(), 4):
        if cycle[0] != min(cycle) or cycle[1] > cycle[-1]:
            continue
        if all(graph.has_edge(cycle[i], cycle[(i + 1) % 4]) for i in range(4)):
            if graph.subgraph(cycle).number_of_edges() == 4:
                # Store the two coloring classes consecutively, as in h_C.
                cycles.add(tuple(sorted((cycle[0], cycle[2]))) + tuple(sorted((cycle[1], cycle[3]))))
    return sorted(cycles)


def scalar_gap(points: np.ndarray, graph: nx.Graph) -> np.ndarray:
    light = points[:, LIGHT].sum(axis=1)
    heavy = points[:, HEAVY].sum(axis=1)
    target = 3.0 * light + 1.5 * heavy
    nonedges = [
        pair
        for pair in itertools.combinations(range(len(graph)), 2)
        if not graph.has_edge(*pair)
    ]
    q0 = sum(points[:, left] * points[:, right] for left, right in nonedges)
    radical = sum(np.prod(points[:, cycle], axis=1) for cycle in CYCLES)
    cubic = points[:, 0] * points[:, 1] * points[:, 2] * target
    lhs = (light + 0.25 * heavy) ** 2
    return lhs - q0 - 2.0 * np.sqrt(radical) - 2.0 * np.sqrt(cubic)


def normalized_scalar_value(points: np.ndarray, graph: nx.Graph) -> tuple[np.ndarray, np.ndarray]:
    """Return the scalar left side and the sharper fixed-L face envelope."""
    light = points[:, LIGHT].sum(axis=1)
    heavy = points[:, HEAVY].sum(axis=1)
    scale = 2.0 * light + heavy
    normalized = points / scale[:, None]
    light = normalized[:, LIGHT].sum(axis=1)
    value = (light + 0.25 * normalized[:, HEAVY].sum(axis=1)) ** 2
    value -= scalar_gap(normalized, graph)
    envelope = np.where(
        light <= 1.0 / 6.0,
        light * (1.0 - 2.0 * light),
        (0.25 + 0.5 * light) ** 2,
    )
    return value, envelope


def audit_hole_support_faces(
    graph: nx.Graph, rng: np.random.Generator, samples_per_face: int
) -> dict:
    """Falsify the analytic one-hole-face envelope independently on all holes."""
    rows = []
    for cycle in CYCLES:
        support = sorted(set((0, 1, 2)).union(cycle))
        active_channels = [
            index for index, other in enumerate(CYCLES) if set(other).issubset(support)
        ]
        restricted = np.zeros((samples_per_face, 9))
        restricted[:, support] = rng.dirichlet(np.ones(len(support)), size=samples_per_face)
        value, envelope = normalized_scalar_value(restricted, graph)
        rows.append(
            {
                "cycle": list(cycle),
                "support": support,
                "active_hole_channels": active_channels,
                "samples": samples_per_face,
                "maximum_value_minus_envelope": float(np.max(value - envelope)),
                "minimum_envelope_slack": float(np.min(envelope - value)),
            }
        )
    if [len(row["active_hole_channels"]) for row in rows] != [1, 1, 1, 1, 1, 3, 3, 3]:
        raise AssertionError(rows)
    return {
        "faces": rows,
        "maximum_value_minus_envelope": max(row["maximum_value_minus_envelope"] for row in rows),
    }


def audit_residual_wedge(
    graph: nx.Graph, rng: np.random.Generator, samples: int, chunk_size: int
) -> dict:
    """Target the only light-variable wedge allowed by the stationarity lemma."""
    best_gap = np.inf
    best_point = None
    best_wedge = None
    best_proposal = None
    accepted = 0
    generated = 0
    chunk_index = 0
    while generated < samples:
        count = min(chunk_size, samples - generated)
        if chunk_index % 3 == 0:
            raw = rng.dirichlet(np.full(9, 0.35), size=count)
            proposal = "boundary_dirichlet"
        elif chunk_index % 3 == 1:
            raw = rng.dirichlet(np.ones(9), size=count)
            proposal = "uniform_dirichlet"
        else:
            raw = np.exp(rng.normal(0.0, 2.2, size=(count, 9)))
            raw /= raw.sum(axis=1, keepdims=True)
            proposal = "lognormal"
        scale = 2.0 * raw[:, LIGHT].sum(axis=1) + raw[:, HEAVY].sum(axis=1)
        points = raw / scale[:, None]
        wedge = (
            points[:, 0] * (points[:, 4] + points[:, 6])
            + (points[:, 0] - points[:, 2]) * (points[:, 0] - points[:, 1])
        )
        selected = wedge <= 0.0
        accepted += int(np.count_nonzero(selected))
        if np.any(selected):
            candidates = points[selected]
            gaps = scalar_gap(candidates, graph)
            index = int(np.argmin(gaps))
            if gaps[index] < best_gap:
                best_gap = float(gaps[index])
                best_point = candidates[index].tolist()
                best_wedge = float(wedge[selected][index])
                best_proposal = proposal
        generated += count
        chunk_index += 1
    return {
        "generated_points": generated,
        "accepted_wedge_points": accepted,
        "acceptance_rate": accepted / generated,
        "proposal_cycle": ["boundary_dirichlet_alpha_0.35", "uniform_dirichlet", "lognormal_sigma_2.2"],
        "minimum_gap": best_gap,
        "minimum_gap_point": best_point,
        "wedge_value_at_minimum": best_wedge,
        "proposal_at_minimum": best_proposal,
        "interpretation": "targeted falsification only; it is not used as proof",
    }


def verify_univariate_factorization() -> None:
    """Check the two exact polynomial identities behind the face lemma over Q."""
    # After x + y + z = L, maximizing over x*z sets x=z=(L-y)/2.
    # Put y=s^2/6.  The radical disappears and the remaining expression is
    # E= -(-12L^2+12Ls^2-24Ls+s^4+4s^3-8s^2)/48.
    # The following checks the derivative and target-gap coefficient identities
    # at enough rational points to catch an implementation/transcription error.
    for numerator_l in range(1, 4):
        for denominator_l in range(7, 13):
            light = Fraction(numerator_l, denominator_l)
            for numerator_s in range(0, 7):
                s = Fraction(numerator_s, 5)
                energy = -(
                    -12 * light**2
                    + 12 * light * s**2
                    - 24 * light * s
                    + s**4
                    + 4 * s**3
                    - 8 * s**2
                ) / 48
                target = (Fraction(1, 4) + light / 2) ** 2
                factored_gap = (s - 1) ** 2 * (
                    12 * light + s**2 + 6 * s + 3
                ) / 48
                if target - energy != factored_gap:
                    raise AssertionError((light, s, target - energy, factored_gap))

                derivative = -(
                    (s - 1) * (6 * light + s**2 + 4 * s)
                ) / 12
                direct_derivative = -(
                    24 * light * s
                    - 24 * light
                    + 4 * s**3
                    + 12 * s**2
                    - 16 * s
                ) / 48
                if derivative != direct_derivative:
                    raise AssertionError((light, s, derivative, direct_derivative))


def verify_heavy_split_hessian_factorization() -> None:
    """Check the exact determinant identity for an interior heavy-split point."""
    # Put X=p3+p5, Y=p7+p8, x=p5/X and y=p8/Y.  Holding the
    # light variables and X,Y fixed, the nonconstant objective is
    # A*x+B*y+2*sqrt(R0+R1*x+R2*y-K*x*y).  At a stationary point,
    # R_x=-A*sqrt(R), R_y=-B*sqrt(R), and the Hessian determinant is
    # -K*(K+A*B)/R.  This rational check guards the sign and factor of two.
    for a_num in range(-2, 3):
        for b_num in range(-3, 4):
            for root_num in range(1, 4):
                slope_a = Fraction(a_num, 3)
                slope_b = Fraction(b_num, 5)
                root_r = Fraction(root_num, 4)
                coupling = Fraction(root_num + 1, 7)
                h_xx = -slope_a**2 / (2 * root_r)
                h_yy = -slope_b**2 / (2 * root_r)
                h_xy = -coupling / root_r - slope_a * slope_b / (2 * root_r)
                determinant = h_xx * h_yy - h_xy**2
                expected = -coupling * (coupling + slope_a * slope_b) / root_r**2
                if determinant != expected:
                    raise AssertionError(
                        (slope_a, slope_b, root_r, coupling, determinant, expected)
                    )


def verify_full_heavy_simplex_exclusion() -> None:
    """Check the exact determinant/discriminant proof excluding a heavy interior max."""
    # In the only wedge left by the two-split lemma, use graph symmetry to put
    # b=a+x and c=a-y with x>=0 and 0<y<a.  At a stationary point of the full
    # three-dimensional heavy simplex, sqrt(R) times the Hessian is
    # M=Hess(R)-vv^T/2.  Its determinant is a*P(x)/2.  The leading coefficient
    # of P is a*d^2 and its discriminant has the nonpositive factor y-a.
    for a_num in range(2, 5):
        for d_num in range(1, 4):
            for e_num in range(1, 4):
                for y_num in range(1, a_num):
                    a = Fraction(a_num, 7)
                    d = Fraction(d_num, 11)
                    e = Fraction(e_num, 13)
                    y = a * Fraction(y_num, a_num)
                    coefficient_2 = a * d**2
                    coefficient_1 = (
                        -2 * a * d**3
                        + 2 * a * d * e**2
                        - 2 * a * d * e * y
                        - 4 * d**2 * e * y
                        - 4 * d * e**2 * y
                    )
                    coefficient_0 = (
                        4 * a**2 * d**2 * e
                        + 4 * a**2 * d * e**2
                        + a * d**4
                        + 4 * a * d**3 * e
                        + 6 * a * d**2 * e**2
                        - 2 * a * d**2 * e * y
                        + 4 * a * d * e**3
                        + a * e**4
                        + 2 * a * e**3 * y
                        + a * e**2 * y**2
                    )
                    discriminant = coefficient_1**2 - 4 * coefficient_2 * coefficient_0
                    factored = (
                        16
                        * d**2
                        * e
                        * (y - a)
                        * (d + e)
                        * (a * d + e * y)
                        * (a + d + e)
                    )
                    if discriminant != factored or discriminant >= 0:
                        raise AssertionError((a, d, e, y, discriminant, factored))
                    for x_num in range(0, 4):
                        x = Fraction(x_num, 9)
                        b = a + x
                        c = a - y
                        q_hessian = [
                            [-2 * a * d - 2 * d * e, -a * d - 2 * d * e, -a * d],
                            [-a * d - 2 * d * e, -2 * d * e, a * e],
                            [-a * d, a * e, Fraction(0)],
                        ]
                        slope = [c + d - a - e, d - e, b - a]
                        matrix = [
                            [
                                q_hessian[row][column]
                                - slope[row] * slope[column] / 2
                                for column in range(3)
                            ]
                            for row in range(3)
                        ]
                        determinant = (
                            matrix[0][0]
                            * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1])
                            - matrix[0][1]
                            * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0])
                            + matrix[0][2]
                            * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0])
                        )
                        polynomial = coefficient_2 * x**2 + coefficient_1 * x + coefficient_0
                        if determinant != a * polynomial / 2:
                            raise AssertionError((a, d, e, x, y, determinant, polynomial))


def verify_three_heavy_boundary_classification() -> None:
    """Symbolically close the relative interiors of all four heavy facets."""
    a, d, e, h, x = sp.symbols("a d e h x")

    # Facet p5=0.  Positivity and the heavy KKT equations give b=a+x,
    # z=d(e+h), x>0, h>0.  Three linear equations then determine p2,p7,p8.
    # After that elimination, the remaining KKT, normalization, and radical
    # equations have the four numerators below.
    first = (
        2 * a * d * e
        + 2 * a * d * h
        + 2 * a * e**2
        - 2 * a * e * x
        - a * h * x
        - 2 * e * h * x
        + h * x**2
    )
    cross = (
        -4 * a**2 * d * e
        - 4 * a**2 * d * h
        - 4 * a**2 * e**2
        + 16 * a**2 * e * x
        + 16 * a**2 * h * x
        + 13 * a * e * h * x
        + 12 * a * e * x**2
        - 3 * a * h**2 * x
        + 12 * a * h * x**2
        + 9 * e * h * x**2
        - 3 * h**2 * x**2
    )
    normalization = (
        -2 * a**2 * d * e
        - 2 * a**2 * d * h
        - 2 * a**2 * e**2
        + 6 * a**2 * e * x
        + 6 * a**2 * h * x
        + 5 * a * e * h * x
        + 4 * a * e * x**2
        - a * e * x
        + a * h**2 * x
        + 4 * a * h * x**2
        - a * h * x
        + 3 * e * h * x**2
        + h**2 * x**2
    )
    light_radical = (
        -2 * a**3 * d * e
        - 2 * a**3 * d * h
        - 2 * a**3 * e**2
        + 2 * a**3 * e * x
        + 2 * a**3 * h * x
        + 4 * a**2 * d * e * h
        + 4 * a**2 * d * h**2
        + 4 * a**2 * e**2 * h
        - 2 * a**2 * e * h * x
        - 3 * a**2 * e * x
        - 4 * a**2 * h**2 * x
        - 3 * a**2 * h * x
        - 2 * a * d * e * h**2
        - 2 * a * d * h**3
        - 2 * a * e**2 * h**2
        - 2 * a * e * h**2 * x
        + 2 * a * h**3 * x
        + 2 * e * h**3 * x
    )
    d_solution = -(
        2 * a * e**2 - 2 * a * e * x - a * h * x - 2 * e * h * x + h * x**2
    ) / (2 * a * (e + h))
    cross_factor = 12 * a * e + 14 * a * h + 9 * e * h - 3 * h**2
    normalization_reduced = (
        4 * a**2 * e
        + 5 * a**2 * h
        + 3 * a * e * h
        + 4 * a * e * x
        - a * e
        + a * h**2
        + 5 * a * h * x
        - a * h
        + 3 * e * h * x
        + h**2 * x
    )
    radical_reduced = (
        a**3 * h
        - 3 * a**2 * e
        - 2 * a**2 * h**2
        + a**2 * h * x
        - 3 * a**2 * h
        + a * h**3
        - 2 * a * h**2 * x
        + h**3 * x
    )
    identities = [
        sp.factor(first.subs(d, d_solution)),
        sp.factor(cross.subs(d, d_solution) - x * (a + x) * cross_factor),
        sp.factor(normalization.subs(d, d_solution) - x * normalization_reduced),
        sp.factor(light_radical.subs(d, d_solution) - x * radical_reduced),
    ]
    if identities != [0, 0, 0, 0]:
        raise AssertionError(identities)

    # Put v=h/e>3 and y=x/e>0.  The cross equation fixes a/e, while the
    # normalization and light-radical equations give two formulas for e.
    # Their difference has the unique positive zero v=42/5.
    v, y = sp.symbols("v y")
    a_over_e = 3 * v * (v - 3) / (2 * (7 * v + 6))
    common = v * (3 * v**2 + 14 * v * y - 9 * v + 12 * y)
    e_from_normalization = (
        6 * (v - 3) * (v + 1) * (7 * v + 6)
        / ((29 * v + 21) * common)
    )
    e_from_radical = (
        54 * (v - 3) ** 2 * (v + 1) * (7 * v + 6)
        / ((11 * v + 21) ** 2 * common)
    )
    difference = sp.factor(e_from_normalization - e_from_radical)
    expected_difference = (
        -24
        * (v - 3)
        * (v + 1)
        * (5 * v - 42)
        * (7 * v + 6) ** 2
        / (
            v
            * (11 * v + 21) ** 2
            * (29 * v + 21)
            * (3 * v**2 + 14 * v * y - 9 * v + 12 * y)
        )
    )
    if sp.factor(difference - expected_difference) != 0:
        raise AssertionError(difference)
    if sp.factor(a_over_e.subs(v, sp.Rational(42, 5)) - sp.Rational(21, 20)) != 0:
        raise AssertionError(a_over_e)

    # Reconstruct the complete normalized stationary ridge and verify its
    # constant gap and its strict ascent direction into the missing p5 channel.
    rho = sp.symbols("rho")
    ridge_a = sp.Rational(21, 20) * rho
    ridge_b = sp.Rational(47, 686)
    ridge_c = sp.Rational(235, 117649) / rho
    ridge_d = (
        sp.Rational(54, 343)
        - sp.Rational(41, 20) * rho
        - sp.Rational(235, 117649) / rho
    )
    ridge_e = rho
    ridge_r = sp.Rational(188, 343) - sp.Rational(47, 5) * rho
    ridge_t = sp.Rational(94, 343)
    ridge_u = sp.Rational(47, 5) * rho - sp.Rational(94, 343)
    ridge_z = sp.Rational(47, 5) * ridge_d * rho
    ridge_w = sp.Rational(141, 9604)
    ridge_l = ridge_a + ridge_b + ridge_c + ridge_d + ridge_e
    ridge_h = ridge_r + ridge_t + ridge_u
    ridge_q = (
        ridge_a * ridge_b
        + ridge_a * ridge_c
        + ridge_b * ridge_c
        + ridge_a * ridge_u
        + ridge_b * ridge_d
        + ridge_b * ridge_t
        + ridge_c * ridge_r
        + ridge_c * ridge_e
        + ridge_d * ridge_r
        + ridge_e * ridge_t
        + ridge_e * ridge_u
    )
    ridge_gap = sp.factor(
        (ridge_l + ridge_h / 4) ** 2 - ridge_q - 2 * ridge_z - 2 * ridge_w
    )
    if sp.factor(2 * ridge_l + ridge_h - 1) != 0 or ridge_gap != sp.Rational(48, 2401):
        raise AssertionError((ridge_l, ridge_h, ridge_gap))
    missing_derivative = sp.factor(
        ridge_d
        - ridge_e
        + (
            ridge_a * ridge_e * ridge_t
            + ridge_c * ridge_d * ridge_e
            + ridge_d * ridge_e * (ridge_t + ridge_u)
            - ridge_a * ridge_r * ridge_d
            - ridge_b * ridge_d * ridge_e
            - ridge_d * ridge_e * ridge_r
        )
        / ridge_z
    )
    expected_derivative = (
        3
        * (343 * rho - 10)
        * (2470629 * rho**2 - 579670 * rho + 9400)
        / (33614 * rho * (4823609 * rho**2 - 370440 * rho + 4700))
    )
    if sp.factor(missing_derivative - expected_derivative) != 0:
        raise AssertionError(missing_derivative)

    # Facet p3=0.  The heavy KKT equation gives b=a+x, z=e*k and
    # p5=(d(a+x)-x*k)/a.  Exact row reduction of the p4-p6, p5-p8,
    # and z^2=R equations gives (d-k)*p7=0.
    c0, k, t0, u0 = sp.symbols("c0 k t0 u0")
    b0 = a + x
    s0 = (d * b0 - x * k) / a
    z0 = e * k
    r0 = e * (a * s0 * t0 + b0 * d * u0 + c0 * d * s0 + d * s0 * (t0 + u0))
    equation_de = sp.together(
        -a * s0 * t0
        - b0 * d * u0
        + b0 * e * u0
        + b0 * z0
        - c0 * d * s0
        + c0 * e * s0
        - c0 * z0
        - d * s0 * t0
        - d * s0 * u0
        + e * s0 * t0
        + e * s0 * u0
        + s0 * z0
        - t0 * z0
        - u0 * z0
    ).as_numer_denom()[0]
    equation_su = sp.together(
        a * e * t0
        - b0 * d * e
        + c0 * d * e
        - d * e * s0
        + d * e * t0
        + d * e * u0
        + d * z0
        - e * z0
    ).as_numer_denom()[0]
    equation_r = sp.together(z0**2 - r0).as_numer_denom()[0]
    matrix, vector = sp.linear_eq_to_matrix(
        [equation_de, equation_su, equation_r], [c0, t0, u0]
    )
    determinant = sp.factor(matrix.det())
    t_matrix = matrix.copy()
    t_matrix[:, 1] = vector
    t_determinant = sp.factor(t_matrix.det())
    expected_determinant = -a**3 * d * e**3 * (a + x) ** 2 * (d - k)
    if sp.factor(determinant - expected_determinant) != 0 or t_determinant != 0:
        raise AssertionError((determinant, t_determinant))
    r_bracket = a * t0 + a * u0 + c0 * d - d * e + d * t0 + d * u0 + u0 * x
    su_bracket = a * d - a * t0 - c0 * d + d * e - d * t0 - d * u0 + d * x
    if sp.factor(r_bracket + su_bracket - (a + x) * (d + u0)) != 0:
        raise AssertionError((r_bracket, su_bracket))

    # Two-heavy face {p3,p8}.  Maximizing its heavy split is the top
    # eigenvalue of the displayed 2x2 matrix.  Its trace and determinant turn
    # the rest into the already-proved three-variable envelope, with two
    # explicitly nonnegative slack terms.  Symmetry handles {p5,p7}.
    b1, c1 = sp.symbols("b1 c1")
    heavy_matrix = sp.Matrix(
        [[c1 + d, sp.sqrt(d * (a + e))], [sp.sqrt(d * (a + e)), a + e]]
    )
    matrix_trace = sp.factor(sp.trace(heavy_matrix))
    matrix_determinant = sp.factor(heavy_matrix.det())
    light_q = a * b1 + a * c1 + b1 * c1 + b1 * d + c1 * e
    envelope_q = b1 * matrix_trace + matrix_determinant
    if matrix_trace != a + c1 + d + e:
        raise AssertionError(matrix_trace)
    if matrix_determinant != c1 * (a + e):
        raise AssertionError(matrix_determinant)
    if sp.factor(envelope_q - light_q - b1 * e) != 0:
        raise AssertionError((envelope_q, light_q))
    if sp.factor(b1 * matrix_determinant - a * b1 * c1 - b1 * c1 * e) != 0:
        raise AssertionError(matrix_determinant)


def verify_residual_two_heavy_faces() -> None:
    """Symbolically close the last three two-heavy relative interiors."""
    a, b, d, e, x = sp.symbols("a b d e x")

    # Representative {p3,p5}.  Heavy stationarity gives p2=a+x,
    # sqrt(R)=(a+x)*d*e/x and p5=(a+x)*d*e/x^2, with x>0.
    # The p1-p6 equation gives b=(a+x)(x-e)/x; hence positivity gives x>e.
    b_solution = (a + x) * (x - e) / x
    equation_de = a * d - 2 * a * e + 6 * a * x + 3 * d * x + 4 * x**2 - x
    equation_cross = -4 * a * d - 2 * a * e + 10 * a * x + 6 * d * x + 8 * x**2 + x
    equation_ce = (
        2 * a * d * e
        - 2 * a * e * x
        + 6 * a * x**2
        + 3 * d * x**2
        + 4 * x**3
        - x**2
    )
    if sp.factor(equation_ce - x * equation_de - a * d * (2 * e - x)) != 0:
        raise AssertionError((equation_ce, equation_de))

    # Thus x=2e.  The remaining radical equation joins the two linear KKT
    # equations.  Its lexicographic basis isolates the sole positive root.
    equation_de_2 = sp.factor(equation_de.subs(x, 2 * e))
    equation_cross_2 = sp.factor(-equation_cross.subs(x, 2 * e) / 2)
    equation_radical_2 = a * (d - 2 * e) ** 2 - 12 * e**2
    basis = sp.groebner(
        [equation_de_2, equation_cross_2, equation_radical_2], a, d, e, order="lex"
    )
    terminal = sp.factor(basis.polys[-1].as_expr())
    if terminal != e**2 * (4 * e + 7) * (1372 * e - 5):
        raise AssertionError(terminal)

    ridge = {
        "a": sp.Rational(3, 49),
        "b": sp.Rational(47, 1372),
        "c": sp.Rational(47, 686),
        "d": sp.Rational(20, 343),
        "e": sp.Rational(5, 1372),
        "r": sp.Rational(94, 343),
        "s": sp.Rational(94, 343),
        "z": sp.Rational(235, 117649),
        "w": sp.Rational(141, 9604),
    }
    light_sum = sum(ridge[key] for key in ["a", "b", "c", "d", "e"])
    heavy_sum = ridge["r"] + ridge["s"]
    q_value = (
        ridge["a"] * ridge["b"]
        + ridge["a"] * ridge["c"]
        + ridge["b"] * ridge["c"]
        + ridge["b"] * ridge["d"]
        + ridge["c"] * ridge["e"]
        + ridge["r"] * (ridge["c"] + ridge["d"])
        + ridge["s"] * (ridge["a"] + ridge["d"])
    )
    gap = sp.factor(
        (light_sum + heavy_sum / 4) ** 2
        - q_value
        - 2 * ridge["z"]
        - 2 * ridge["w"]
    )
    missing_p8_derivative = sp.factor(
        ridge["a"]
        + ridge["e"]
        + ridge["d"]
        * (
            ridge["a"] * ridge["r"]
            + ridge["b"] * ridge["e"]
            + ridge["e"] * heavy_sum
        )
        / ridge["z"]
        - ridge["c"]
        - ridge["d"]
    )
    if light_sum * 2 + heavy_sum != 1:
        raise AssertionError((light_sum, heavy_sum))
    if gap != sp.Rational(48, 2401) or missing_p8_derivative != sp.Rational(24, 49):
        raise AssertionError((gap, missing_p8_derivative))
    if sp.factor(b_solution.subs(x, 2 * e).subs({a: ridge["a"], e: ridge["e"]}) - ridge["b"]) != 0:
        raise AssertionError(b_solution)

    # Invariant face {p5,p8}.  Put sqrt(R)=d*e*k.  Heavy stationarity,
    # d/e light stationarity and z^2=R give the following exact expressions.
    k, s, u = sp.symbols("k s u")
    b_expression = (d * k - s) * (e * k + s) / (s + u)
    c_expression = (d * k + u) * (e * k - u) / (s + u)
    w_expression = -a * (s - d * k) * (u - e * k) / (s + u)
    # b,c>0 force d*k>s and e*k>u, making w_expression strictly negative,
    # contradicting w=sqrt(3abc/2)>0.
    if sp.factor(w_expression + a * (d * k - s) * (e * k - u) / (s + u)) != 0:
        raise AssertionError(w_expression)
    if sp.factor(b_expression * (s + u) - (d * k - s) * (e * k + s)) != 0:
        raise AssertionError(b_expression)
    if sp.factor(c_expression * (s + u) - (d * k + u) * (e * k - u)) != 0:
        raise AssertionError(c_expression)


def verify_zero_light_boundary_certificates() -> None:
    """Check the exact boundary identities that complete the scalar theorem."""
    b, c, d, e, r, s, t, u = sp.symbols("b c d e r s t u", nonnegative=True)
    light = b + c + d + e
    heavy = r + s + t + u
    target = (light + heavy / 4) ** 2
    q = b * c + b * d + b * t + c * r + c * e + d * r + d * s + e * t + e * u
    channel = b * u + c * s + (r + s) * (t + u)
    residual = sp.factor(target - q)
    square = 4 * b - 4 * c + r - 4 * d + s + 4 * e - t - u
    certificate = square**2 + 48 * b * c + 48 * b * d + 12 * b * u + 12 * c * s + 48 * c * e
    if sp.factor(16 * (residual - 4 * d * e - channel / 4) - certificate) != 0:
        raise AssertionError(certificate)
    if sp.factor((4 * d * e + channel / 4) ** 2 - 4 * d * e * channel - (4 * d * e - channel / 4) ** 2) != 0:
        raise AssertionError(channel)

    # The only boundary not covered by p0=0, its symmetric consequences, or
    # p4/p6=0 has p1=p2=0.  Here a second pair of short identities suffices.
    a = sp.symbols("a", nonnegative=True)
    light = a + d + e
    target = (light + heavy / 4) ** 2
    q = a * (s + u) + d * (r + s) + e * (t + u)
    radicand = d * e * (r + s) * (t + u) + a * d * r * u + a * e * s * t
    residual = sp.factor(target - q)
    majorant = a * (r + t) + d * (t + u) + e * (r + s)
    base_square = 4 * a + 4 * d + 4 * e - r - s - t - u
    if sp.factor(16 * residual - base_square**2 - 16 * majorant) != 0:
        raise AssertionError((residual, majorant))

    x1, x2, x3, x4, x5, x6 = (
        a * r,
        a * t,
        d * t,
        d * u,
        e * r,
        e * s,
    )
    radical_square = (x1 - x2 - x3 - x4 + x5 + x6) ** 2
    radical_certificate = radical_square + 4 * x1 * x2 + 4 * x1 * x3 + 4 * x2 * x5
    if sp.factor(majorant**2 - 4 * radicand - radical_certificate) != 0:
        raise AssertionError(radical_certificate)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=1_000_000)
    parser.add_argument("--face-samples", type=int, default=100_000)
    parser.add_argument("--wedge-samples", type=int, default=10_000_000)
    parser.add_argument("--wedge-chunk-size", type=int, default=250_000)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()
    graph = nx.from_graph6_bytes(b"HEhu|x|")
    atom_automorphisms = list(
        nx.algorithms.isomorphism.GraphMatcher(graph, graph).isomorphisms_iter()
    )
    orbit_swap = {0: 0, 1: 2, 2: 1, 3: 7, 4: 6, 5: 8, 6: 4, 7: 3, 8: 5}
    if len(atom_automorphisms) != 2 or orbit_swap not in atom_automorphisms:
        raise AssertionError(atom_automorphisms)
    detected_cycles = chordless_four_cycles(graph)
    if {frozenset(cycle) for cycle in detected_cycles} != {frozenset(cycle) for cycle in CYCLES}:
        raise AssertionError((detected_cycles, CYCLES))

    commuting_pairs = []
    for left, right in itertools.combinations(range(len(CYCLES)), 2):
        _, forward = multiply_words(graph, CYCLES[left], CYCLES[right])
        _, reverse = multiply_words(graph, CYCLES[right], CYCLES[left])
        if forward == reverse:
            commuting_pairs.append([left, right])
    if commuting_pairs != [[4, 7], [5, 6]]:
        raise AssertionError(commuting_pairs)
    cancellation_left = multiply_words(graph, CYCLES[4], CYCLES[7])
    cancellation_right = multiply_words(graph, CYCLES[5], CYCLES[6])
    if cancellation_left[0] != cancellation_right[0] or cancellation_left[1] != -cancellation_right[1]:
        raise AssertionError((cancellation_left, cancellation_right))

    verify_univariate_factorization()
    verify_heavy_split_hessian_factorization()
    verify_full_heavy_simplex_exclusion()
    verify_three_heavy_boundary_classification()
    verify_residual_two_heavy_faces()
    verify_zero_light_boundary_certificates()

    rng = np.random.default_rng(args.seed)
    points = rng.dirichlet(np.ones(9), size=args.samples)
    gaps = scalar_gap(points, graph)
    equal_point = np.zeros((1, 9))
    equal_point[0, :3] = 1.0 / 3.0
    face_audit = audit_hole_support_faces(graph, rng, args.face_samples)
    wedge_audit = audit_residual_wedge(
        graph, rng, args.wedge_samples, args.wedge_chunk_size
    )
    result = {
        "experiment": "last_SCF_atom_exact_spectral_reduction",
        "support_graph6": "HEhu|x|",
        "nontrivial_automorphism": orbit_swap,
        "light_vertices": LIGHT,
        "heavy_vertices": HEAVY,
        "induced_four_holes": [list(cycle) for cycle in CYCLES],
        "hole_operator_commuting_pairs": commuting_pairs,
        "cancelling_products": {
            "common_word": list(cancellation_left[0]),
            "first_sign": cancellation_left[1],
            "second_sign": cancellation_right[1],
        },
        "exact_reduction": {
            "variables": "p_i=b_i^2>=0; L=sum_{0,1,2,4,6}p_i; H=sum_{3,5,7,8}p_i",
            "target": "D=3L+(3/2)H",
            "e1": "L+H",
            "e3": "p0*p1*p2",
            "q": "q0+2*sqrt(R), where q0=sum over graph nonedges p_i*p_j and R=sum over the eight four-holes product_{i in C}p_i",
            "remaining_inequality": "(L+H/4)^2 >= q0+2*sqrt(R)+2*sqrt(p0*p1*p2*D)",
            "consequence": "the remaining inequality implies beta(G,w)<=3/2 via the three-mode characteristic polynomial",
        },
        "proved_primitive_face_lemma": {
            "scope": "support contained in {0,1,2} union C for C in the first five listed holes; these are exactly the supports on which only the named quartic monomial in R survives",
            "normalization": "2L+H=1, hence 0<=L<=1/2 and D=3/2",
            "three_variable_reduction": "x+y+z=L, y>=z: E=xy+xz+yz+(1-2L)y+2*sqrt((3/2)xyz)",
            "fifth_face_note": "on the fifth face the 2x2 determinant K obeys p0*p1*p2<=x*K, so the same three-variable expression is an upper bound",
            "one_variable_substitution": "for fixed y, E increases with sqrt(xz), so x=z=(L-y)/2; set y=s^2/6",
            "derivative_identity": "dE/ds=-(s-1)(6L+s^2+4s)/12",
            "target_gap_identity": "(1/4+L/2)^2-E=(s-1)^2(12L+s^2+6s+3)/48",
            "fixed_L_maximum": "L(1-2L) for 0<=L<=1/6; (1/4+L/2)^2 for 1/6<=L<=1/2",
            "consequence": "inequality (A) is proved on all five primitive one-channel support faces; the other three listed hole supports activate three quartic monomials and remain only numerically audited",
            "exact_factorization_check": "passed over rational arithmetic",
            "independent_face_falsification": face_audit,
        },
        "proved_coupled_channel_stationarity_lemma": {
            "heavy_pair_coordinates": "X=p3+p5, Y=p7+p8, x=p5/X, y=p8/Y",
            "fixed_data": "p0,...,p6 and X,Y; the p7,p8 and p3,p5 splits vary through x,y",
            "split_objective": "constant+A*x+B*y+2*sqrt(R0+R1*x+R2*y-K*x*y)",
            "coefficients": "A=X*(p0-p2), B=Y*(p0-p1), K=p0*(p4+p6)*X*Y",
            "stationary_hessian_determinant": "-K*(K+A*B)/R",
            "necessary_condition_for_fully_interior_local_maximum": "p0*(p4+p6)+(p0-p2)*(p0-p1)<=0",
            "consequence": "outside the wedge where p0 lies strictly between p1 and p2 with sufficient separation, a coupled-channel maximum must move to a heavy-split boundary",
            "exact_factorization_check": "passed over rational arithmetic",
        },
        "proved_full_heavy_interior_exclusion": {
            "scope": "the four heavy coordinates p3,p5,p7,p8 with all five light coordinates held fixed and positive",
            "prior_wedge": "by the two-split lemma, only p0 strictly between p1 and p2 can remain; use symmetry to write p1=p0+x and p2=p0-y with x>=0 and 0<y<p0",
            "stationary_hessian": "sqrt(R)*Hess(objective)=M=Hess(R)-v*v^T/2 on the three-dimensional heavy simplex",
            "determinant": "det(M)=p0*P(x)/2, where P is quadratic in x with leading coefficient p0*p4^2",
            "discriminant": "disc_x(P)=16*p4^2*p6*(y-p0)*(p4+p6)*(p0*p4+p6*y)*(p0+p4+p6)<0",
            "consequence": "det(M)>0, whereas a negative-semidefinite 3x3 Hessian has nonpositive determinant; therefore no fully interior heavy-simplex local maximum exists",
            "remaining_boundary": "for every fixed light profile, a maximizer has at least one of p3,p5,p7,p8 equal to zero",
            "exact_factorization_check": "passed over rational arithmetic",
        },
        "proved_three_heavy_relative_interior_classification": {
            "scope": "all five light coordinates positive and exactly one of p3,p5,p7,p8 zero",
            "p5_zero_parameterization": "write p1=p0+x, sqrt(R)=p4*(p6+h); KKT positivity gives x,h>0",
            "p5_zero_elimination": "after three linear KKT eliminations, the remaining equations force h/p6=42/5 and p0/p6=21/20",
            "p5_zero_complete_ridge": {
                "parameter": "rho=p6",
                "p0": "21*rho/20",
                "p1": "47/686",
                "p2": "235/(117649*rho)",
                "p4": "54/343-41*rho/20-235/(117649*rho)",
                "p3": "188/343-47*rho/5",
                "p7": "94/343",
                "p8": "47*rho/5-94/343",
                "positivity_interval_from_p3_p8": "10/343<rho<20/343",
                "gap": "48/2401",
            },
            "p5_zero_missing_direction": "d/dp5-d/dp8 = 3*(343*rho-10)*(2470629*rho^2-579670*rho+9400)/(33614*rho*(4823609*rho^2-370440*rho+4700)) > 0 on the positive ridge",
            "p3_zero_exclusion": "with p1=p0+x and sqrt(R)=p6*k, exact row reduction gives (p4-k)*p7=0; p7>0 forces k=p4 and then the two remaining heavy equations sum to p1*(p4+p8)>0, a contradiction",
            "symmetry": "the atom automorphism maps p5-zero to p8-zero and p3-zero to p7-zero",
            "consequence": "a global maximizer with all five light coordinates positive has at least two heavy coordinates equal to zero",
            "exact_symbolic_factorization_check": "passed",
            "remaining_boundary": "two-or-fewer-heavy strata and strata with a zero light coordinate",
        },
        "proved_two_heavy_spectral_faces": {
            "already_primitive": "the {p3,p7} face is the fifth primitive face",
            "new_faces": ["{p3,p8}", "{p5,p7}"],
            "representative_matrix": "[[p2+p4,sqrt(p4*(p0+p6))],[sqrt(p4*(p0+p6)),p0+p6]]",
            "trace": "p0+p2+p4+p6",
            "determinant": "p2*(p0+p6)",
            "envelope_slack": "p1*p6 in the quadratic part and p1*p2*p6 in the radical product",
            "consequence": "the primitive three-variable envelope proves these two faces exactly",
            "symmetry": "the atom automorphism maps {p3,p8} to {p5,p7}",
            "exact_symbolic_factorization_check": "passed",
            "remaining_two_heavy_faces": ["{p3,p5}", "{p7,p8}", "{p5,p8}"],
        },
        "proved_residual_two_heavy_relative_interiors": {
            "p3_p5_stationarity": "the positive KKT equations force p2-p0=2*p6 and isolate one rational point",
            "p3_p5_unique_point": {
                "p0": "3/49",
                "p1": "47/1372",
                "p2": "47/686",
                "p4": "20/343",
                "p6": "5/1372",
                "p3": "94/343",
                "p5": "94/343",
                "gap": "48/2401",
                "missing_p8_derivative": "24/49",
            },
            "p7_p8": "closed by the atom automorphism",
            "p5_p8_exclusion": "with sqrt(R)=p4*p6*k, positivity forces p4*k>p5 and p6*k>p8, while the light KKT equation gives sqrt(3*p0*p1*p2/2)=-p0*(p5-p4*k)*(p8-p6*k)/(p5+p8)<0",
            "consequence": "no two-heavy relative interior can maximize the full problem; supports with at most one heavy coordinate lie in a proved primitive face",
            "exact_symbolic_factorization_check": "passed",
            "remaining_boundary": "strata with at least one of p0,p1,p2,p4,p6 equal to zero",
        },
        "proved_zero_light_boundary": {
            "p0_zero": "write R=p4*p6*K with K=p1*p8+p2*p5+(p3+p5)*(p7+p8); 16*(T-q-4*p4*p6-K/4)=(4*p1-4*p2+p3-4*p4+p5+4*p6-p7-p8)^2+48*p1*p2+48*p1*p4+12*p1*p8+12*p2*p5+48*p2*p6",
            "p0_zero_radical_step": "4*p4*p6+K/4>=2*sqrt(p4*p6*K) by exact AM-GM",
            "p4_zero": "the heavy maximum is one of the p3 vertex, p8 vertex, or the {p5,p7} 2x2 spectral block; every branch lies in a proved primitive face",
            "symmetry": "p6=0 follows from p4=0",
            "p1_or_p2_zero": "if the other two of p0,p1,p2 are positive, turning on the missing coordinate gains order sqrt(epsilon) from the light radical against only order epsilon changes elsewhere, so such a point cannot maximize the violation",
            "p1_p2_zero": "with K=p0*(p3+p7)+p4*(p7+p8)+p6*(p3+p5), 16*(T-q)=(4*p0+4*p4+4*p6-p3-p5-p7-p8)^2+16*K and K^2-4*R=(x1-x2-x3-x4+x5+x6)^2+4*x1*x2+4*x1*x3+4*x2*x5 for x=(p0*p3,p0*p7,p4*p7,p4*p8,p6*p3,p6*p5)",
            "consequence": "the scalar inequality is proved on the complete normalized simplex",
            "exact_symbolic_factorization_check": "passed",
        },
        "residual_wedge_falsification": wedge_audit,
        "falsification": {
            "seed": args.seed,
            "dirichlet_samples": args.samples,
            "minimum_interior_gap": float(gaps.min()),
            "equal_light_triple_boundary_gap": float(scalar_gap(equal_point, graph)[0]),
        },
        "status": "last_scf_atom_scalar_inequality_proved",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": result["status"],
                **result["falsification"],
                "hole_support_face_maximum_excess": face_audit["maximum_value_minus_envelope"],
                "wedge_points": wedge_audit["accepted_wedge_points"],
                "wedge_minimum_gap": wedge_audit["minimum_gap"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
