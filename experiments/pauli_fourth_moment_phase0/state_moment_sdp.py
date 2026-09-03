"""Real state-moment SDP hierarchy ported from Wang et al.'s BetaNumber.jl."""

from __future__ import annotations

import itertools

import cvxpy as cp
import networkx as nx
import numpy as np


Monomial = tuple[tuple[int, ...], int]


def word_basis(count: int) -> list[tuple[int, ...]]:
    return sorted(
        tuple(combination)
        for size in range(count + 1)
        for combination in itertools.combinations(range(count), size)
    )


def reduce_word(word: list[int], edges: set[tuple[int, int]]) -> tuple[tuple[int, ...], int]:
    value = 1
    index = 0
    while index < len(word) - 1:
        if word[index] == word[index + 1]:
            del word[index : index + 2]
            index = max(0, index - 1)
        elif word[index] > word[index + 1]:
            word[index], word[index + 1] = word[index + 1], word[index]
            if (word[index], word[index + 1]) in edges:
                value *= -1
            index = max(0, index - 1)
        else:
            index += 1
    return tuple(word), value


def monomial_basis(graph: nx.Graph, order: int) -> tuple[list[Monomial], list[tuple[int, ...]]]:
    count = len(graph)
    words = word_basis(count)
    location = {word: index for index, word in enumerate(words)}
    identity = location[()]
    singleton = [location[(index,)] for index in range(count)]
    basis: list[Monomial] = [((identity,), identity)]
    basis.extend(((singleton[index],), singleton[index]) for index in range(count))
    if order >= 2:
        for left in range(count - 1):
            for right in range(left + 1, count):
                pair = location[(left, right)]
                if not graph.has_edge(left, right):
                    basis.append(((singleton[left], pair), singleton[right]))
                    basis.append(((singleton[right], pair), singleton[left]))
                basis.append(((singleton[left], singleton[right]), pair))
    if order >= 3:
        for left in range(count - 1):
            for right in range(left + 1, count):
                if graph.has_edge(left, right):
                    continue
                pair = location[(left, right)]
                for third in (node for node in range(count) if node not in (left, right)):
                    triple = location[tuple(sorted((left, right, third)))]
                    basis.append((tuple(sorted((pair, singleton[third]))), triple))
                    left_third = location[tuple(sorted((left, third)))]
                    basis.append(
                        (
                            tuple(sorted((pair, singleton[right], singleton[third]))),
                            left_third,
                        )
                    )
                    basis.append(
                        (
                            tuple(
                                sorted(
                                    (
                                        pair,
                                        singleton[left],
                                        singleton[right],
                                        singleton[third],
                                    )
                                )
                            ),
                            singleton[third],
                        )
                    )
        for first, second, third in itertools.combinations(range(count), 3):
            triple = location[(first, second, third)]
            basis.append(
                (
                    tuple(sorted((singleton[first], singleton[second], singleton[third]))),
                    triple,
                )
            )
    return basis, words


def multiply_monomials(
    left: Monomial,
    right: Monomial,
    words: list[tuple[int, ...]],
    word_location: dict[tuple[int, ...], int],
    edges: set[tuple[int, int]],
) -> tuple[tuple[int, ...] | None, int | None]:
    product, sign = reduce_word(list(reversed(words[left[1]])) + list(words[right[1]]), edges)
    reverse_product, reverse_sign = reduce_word(
        list(reversed(words[right[1]])) + list(words[left[1]]), edges
    )
    if product != reverse_product or sign != reverse_sign:
        return None, None
    identity = word_location[()]
    factors = [factor for factor in left[0] + right[0] if factor != identity]
    operator = word_location[product]
    if operator != identity:
        factors.append(operator)
    key = tuple(sorted(factors)) if factors else (identity,)
    return key, sign


def beta_state_moment_upper(
    graph: nx.Graph,
    weights: np.ndarray,
    order: int = 2,
    solver: str = "CLARABEL",
    solver_options: dict | None = None,
) -> tuple[float, dict]:
    basis, words = monomial_basis(graph, order)
    word_location = {word: index for index, word in enumerate(words)}
    edges = {tuple(sorted(edge)) for edge in graph.edges()}
    products = []
    keys = {(word_location[()],)}
    for left in basis:
        row = []
        for right in basis:
            key, sign = multiply_monomials(
                left, right, words, word_location, edges
            )
            row.append((key, sign))
            if key is not None:
                keys.add(key)
        products.append(row)
    ordered_keys = sorted(keys)
    key_location = {key: index for index, key in enumerate(ordered_keys)}
    moments = cp.Variable(len(ordered_keys))
    matrix_rows = []
    for row in products:
        matrix_rows.append(
            [
                0.0 if key is None else sign * moments[key_location[key]]
                for key, sign in row
            ]
        )
    moment_matrix = cp.bmat(matrix_rows)
    identity_key = (word_location[()],)
    objective_terms = []
    for index in range(len(graph)):
        singleton = word_location[(index,)]
        squared_expectation_key = tuple(sorted((singleton, singleton)))
        objective_terms.append(moments[key_location[squared_expectation_key]])
    constraints = [moment_matrix >> 0, moments[key_location[identity_key]] == 1]
    problem = cp.Problem(cp.Maximize(weights @ cp.hstack(objective_terms)), constraints)
    problem.solve(solver=solver, **(solver_options or {}))
    if problem.status not in {cp.OPTIMAL, cp.OPTIMAL_INACCURATE}:
        raise RuntimeError(f"state-moment SDP failed: {problem.status}")
    return float(problem.value), {
        "order": order,
        "basis_size": len(basis),
        "moment_variables": len(ordered_keys),
        "solver": solver,
        "status": problem.status,
    }
