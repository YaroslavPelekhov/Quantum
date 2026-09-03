"""Reduce the last SCF facet atom to an explicit scalar inequality."""

from __future__ import annotations

import argparse
import itertools
import json
from fractions import Fraction
from pathlib import Path

import networkx as nx
import numpy as np


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=1_000_000)
    parser.add_argument("--face-samples", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()
    graph = nx.from_graph6_bytes(b"HEhu|x|")
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

    rng = np.random.default_rng(args.seed)
    points = rng.dirichlet(np.ones(9), size=args.samples)
    gaps = scalar_gap(points, graph)
    equal_point = np.zeros((1, 9))
    equal_point[0, :3] = 1.0 / 3.0
    face_audit = audit_hole_support_faces(graph, rng, args.face_samples)
    result = {
        "experiment": "last_SCF_atom_exact_spectral_reduction",
        "support_graph6": "HEhu|x|",
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
        "falsification": {
            "seed": args.seed,
            "dirichlet_samples": args.samples,
            "minimum_interior_gap": float(gaps.min()),
            "equal_light_triple_boundary_gap": float(scalar_gap(equal_point, graph)[0]),
        },
        "status": "operator_reduction_and_five_primitive_faces_proved_full_scalar_inequality_open",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": result["status"],
                **result["falsification"],
                "hole_support_face_maximum_excess": face_audit["maximum_value_minus_envelope"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
