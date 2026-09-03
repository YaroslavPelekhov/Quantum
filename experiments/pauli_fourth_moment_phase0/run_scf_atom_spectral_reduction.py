"""Reduce the last SCF facet atom to an explicit scalar inequality."""

from __future__ import annotations

import argparse
import itertools
import json
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=1_000_000)
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

    rng = np.random.default_rng(args.seed)
    points = rng.dirichlet(np.ones(9), size=args.samples)
    gaps = scalar_gap(points, graph)
    equal_point = np.zeros((1, 9))
    equal_point[0, :3] = 1.0 / 3.0
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
        "falsification": {
            "seed": args.seed,
            "dirichlet_samples": args.samples,
            "minimum_interior_gap": float(gaps.min()),
            "equal_light_triple_boundary_gap": float(scalar_gap(equal_point, graph)[0]),
        },
        "status": "operator_reduction_proved_scalar_inequality_survived_not_proved",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], **result["falsification"]}, indent=2))


if __name__ == "__main__":
    main()
