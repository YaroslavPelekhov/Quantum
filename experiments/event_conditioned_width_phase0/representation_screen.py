"""Phase-0 representation/path-cost screen for event-conditioned QAOA.

The screen compares two *exactly equivalent* encodings of the event

    x is an independent set of G and |x| == k:

1. a fixed-order, rank-minimal tensor train lifted to a diagonal MPO; and
2. local MIS edge factors plus an exact finite-state cardinality chain.

Both encodings are attached to the same bra--ket QAOA tensor network.  Path
search consumes only tensor shapes and mode incidences: it never inspects tensor
values and it never performs the expensive contraction.  ``opt_einsum`` is used
when available; a dependency-free multi-start shape-greedy optimizer is always
available as a reproducible fallback.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import itertools
import json
import math
from pathlib import Path
import random
from typing import Iterable, Sequence

import networkx as nx
import numpy as np


Bitstring = str
Order = tuple[int, ...]


def _canonical_edges(graph: nx.Graph) -> tuple[tuple[int, int], ...]:
    if graph.is_directed() or graph.is_multigraph():
        raise ValueError("expected a simple undirected graph")
    nodes = sorted(graph.nodes())
    if nodes != list(range(len(nodes))):
        raise ValueError("graph nodes must be consecutive integers starting at zero")
    edges = []
    for left, right in graph.edges():
        if left == right:
            raise ValueError("self loops are not valid MIS constraints")
        edges.append(tuple(sorted((int(left), int(right)))))
    return tuple(sorted(set(edges)))


def _validate_order(order: Sequence[int], qubits: int) -> Order:
    result = tuple(int(value) for value in order)
    if sorted(result) != list(range(qubits)):
        raise ValueError("order must be a permutation of all qubits")
    return result


def enumerate_independent_set_support(
    graph: nx.Graph, target_cardinality: int | None = None
) -> tuple[int, tuple[Bitstring, ...]]:
    """Enumerate a small exact MIS/cardinality event in q0-first notation."""
    edges = _canonical_edges(graph)
    qubits = graph.number_of_nodes()
    if target_cardinality is not None and not 0 <= target_cardinality <= qubits:
        raise ValueError("target cardinality is outside [0, number of qubits]")

    independent: list[Bitstring] = []
    best = -1
    for bits in itertools.product((0, 1), repeat=qubits):
        if any(bits[left] and bits[right] for left, right in edges):
            continue
        weight = sum(bits)
        if target_cardinality is None:
            if weight > best:
                independent = []
                best = weight
            if weight == best:
                independent.append("".join(map(str, bits)))
        elif weight == target_cardinality:
            independent.append("".join(map(str, bits)))

    target = best if target_cardinality is None else target_cardinality
    if not independent:
        raise ValueError(f"the graph has no independent set of cardinality {target}")
    return target, tuple(sorted(independent))


def _incidence_factorization(bitstrings: Sequence[str], cut: int):
    """Exact rank factorization of a support prefix/suffix incidence matrix."""
    import sympy as sp

    prefixes = sorted({value[:cut] for value in bitstrings})
    suffixes = sorted({value[cut:] for value in bitstrings})
    prefix_index = {value: index for index, value in enumerate(prefixes)}
    suffix_index = {value: index for index, value in enumerate(suffixes)}
    matrix = sp.MutableSparseMatrix(len(prefixes), len(suffixes), {})
    for value in bitstrings:
        matrix[prefix_index[value[:cut]], suffix_index[value[cut:]]] = 1
    matrix = sp.ImmutableSparseMatrix(matrix)

    # Pivot columns of M.T select a row basis of M.  Coordinates in that basis
    # give a rank-minimal transition realization at every cut.
    independent_rows = [int(index) for index in matrix.T.rref()[1]]
    basis = matrix.extract(independent_rows, range(matrix.cols))
    independent_columns = [int(index) for index in basis.rref()[1]]
    square = basis.extract(range(basis.rows), independent_columns)
    coordinates = matrix.extract(range(matrix.rows), independent_columns) * square.inv()
    if coordinates * basis != matrix:
        raise AssertionError(f"support rank factorization failed at cut {cut}")
    return prefixes, [prefixes[index] for index in independent_rows], coordinates


@dataclass(frozen=True)
class SupportTT:
    """Rank-minimal exact indicator TT in one fixed qubit order."""

    qubits: int
    order: Order
    support: tuple[Bitstring, ...]
    cores: tuple[np.ndarray, ...]

    @property
    def ranks(self) -> tuple[int, ...]:
        return (self.cores[0].shape[0],) + tuple(
            int(core.shape[-1]) for core in self.cores
        )

    @property
    def max_rank(self) -> int:
        return max(self.ranks)


def compile_rank_minimal_support_tt(
    support: Sequence[Bitstring], order: Sequence[int] | None = None
) -> SupportTT:
    """Compile a duplicate-free finite support to a fixed-order minimal TT."""
    values = tuple(sorted(set(support)))
    if not values or len(values) != len(tuple(support)):
        raise ValueError("support must be non-empty and duplicate-free")
    qubits = len(values[0])
    if qubits == 0 or any(
        len(value) != qubits or set(value) - {"0", "1"} for value in values
    ):
        raise ValueError("support contains an invalid bitstring")
    physical_order = _validate_order(
        range(qubits) if order is None else order, qubits
    )
    ordered_values = tuple(
        "".join(value[qubit] for qubit in physical_order) for value in values
    )

    cuts = []
    for cut in range(qubits + 1):
        prefixes, basis_prefixes, coordinates = _incidence_factorization(
            ordered_values, cut
        )
        cuts.append(
            {
                "prefixes": prefixes,
                "prefix_index": {
                    value: index for index, value in enumerate(prefixes)
                },
                "basis_prefixes": basis_prefixes,
                "coordinates": coordinates,
            }
        )

    cores: list[np.ndarray] = []
    for site in range(qubits):
        left_basis = cuts[site]["basis_prefixes"]
        right = cuts[site + 1]
        core = np.zeros(
            (len(left_basis), 2, len(right["basis_prefixes"])), dtype=np.float64
        )
        for left_index, prefix in enumerate(left_basis):
            for bit in (0, 1):
                row = right["prefix_index"].get(prefix + str(bit))
                if row is None:
                    continue
                for right_index, coefficient in enumerate(
                    right["coordinates"].row(row)
                ):
                    core[left_index, bit, right_index] = float(coefficient)
        cores.append(core)

    if cores[0].shape[0] != 1 or cores[-1].shape[-1] != 1:
        raise AssertionError("TT boundary ranks must be one")
    return SupportTT(qubits, physical_order, values, tuple(cores))


def evaluate_support_tt(encoding: SupportTT, bitstring: Bitstring) -> float:
    if len(bitstring) != encoding.qubits or set(bitstring) - {"0", "1"}:
        raise ValueError("invalid bitstring")
    value = np.ones((1,), dtype=np.float64)
    for site, core in enumerate(encoding.cores):
        value = value @ core[:, int(bitstring[encoding.order[site]]), :]
    return float(value.item())


@dataclass(frozen=True)
class LocalMISCardinality:
    """Local edge constraints and an exact cardinality finite-state chain."""

    qubits: int
    edges: tuple[tuple[int, int], ...]
    target_cardinality: int
    order: Order
    cardinality_cores: tuple[np.ndarray, ...]

    @property
    def count_ranks(self) -> tuple[int, ...]:
        return (self.cardinality_cores[0].shape[0],) + tuple(
            int(core.shape[-1]) for core in self.cardinality_cores
        )


def compile_local_mis_cardinality(
    graph: nx.Graph, target_cardinality: int, order: Sequence[int] | None = None
) -> LocalMISCardinality:
    """Build edge factors and the minimal feasible-count automaton for |x|=k."""
    edges = _canonical_edges(graph)
    qubits = graph.number_of_nodes()
    if not 0 <= target_cardinality <= qubits:
        raise ValueError("target cardinality is outside [0, number of qubits]")
    physical_order = _validate_order(
        range(qubits) if order is None else order, qubits
    )

    states: list[tuple[int, ...]] = []
    for cut in range(qubits + 1):
        lower = max(0, target_cardinality - (qubits - cut))
        upper = min(cut, target_cardinality)
        states.append(tuple(range(lower, upper + 1)))

    cores: list[np.ndarray] = []
    for site in range(qubits):
        left_states = states[site]
        right_states = states[site + 1]
        right_index = {count: index for index, count in enumerate(right_states)}
        core = np.zeros((len(left_states), 2, len(right_states)), dtype=np.float64)
        for left_index, count in enumerate(left_states):
            for bit in (0, 1):
                destination = right_index.get(count + bit)
                if destination is not None:
                    core[left_index, bit, destination] = 1.0
        cores.append(core)
    return LocalMISCardinality(
        qubits, edges, target_cardinality, physical_order, tuple(cores)
    )


def evaluate_local_mis_cardinality(
    encoding: LocalMISCardinality, bitstring: Bitstring
) -> float:
    if len(bitstring) != encoding.qubits or set(bitstring) - {"0", "1"}:
        raise ValueError("invalid bitstring")
    if any(
        bitstring[left] == bitstring[right] == "1"
        for left, right in encoding.edges
    ):
        return 0.0
    value = np.ones((1,), dtype=np.float64)
    for site, core in enumerate(encoding.cardinality_cores):
        bit = int(bitstring[encoding.order[site]])
        value = value @ core[:, bit, :]
    return float(value.item())


@dataclass(frozen=True)
class TensorSpec:
    """A tensor's dense shape and named modes; deliberately no values."""

    name: str
    shape: tuple[int, ...]
    modes: tuple[int, ...]

    @property
    def elements(self) -> int:
        return math.prod(self.shape)


@dataclass(frozen=True)
class TensorNetworkSpec:
    tensors: tuple[TensorSpec, ...]

    def mode_dimensions(self) -> dict[int, int]:
        dimensions: dict[int, int] = {}
        for tensor in self.tensors:
            if len(tensor.shape) != len(tensor.modes):
                raise ValueError(f"shape/mode mismatch in {tensor.name}")
            if len(set(tensor.modes)) != len(tensor.modes):
                raise ValueError(f"repeated mode inside {tensor.name}")
            for mode, dimension in zip(tensor.modes, tensor.shape, strict=True):
                if dimension < 1:
                    raise ValueError(f"non-positive dimension in {tensor.name}")
                previous = dimensions.setdefault(mode, dimension)
                if previous != dimension:
                    raise ValueError(f"inconsistent dimension for mode {mode}")
        return dimensions

    def validate_closed(self) -> None:
        self.mode_dimensions()
        incidence: dict[int, int] = {}
        for tensor in self.tensors:
            for mode in tensor.modes:
                incidence[mode] = incidence.get(mode, 0) + 1
        invalid = {mode: count for mode, count in incidence.items() if count != 2}
        if invalid:
            raise ValueError(f"network is not a closed ordinary TN: {invalid}")


class _NetworkBuilder:
    def __init__(self) -> None:
        self._dimensions: dict[int, int] = {}
        self._tensors: list[TensorSpec] = []
        self._next_mode = 0

    def mode(self, dimension: int) -> int:
        mode = self._next_mode
        self._next_mode += 1
        self._dimensions[mode] = int(dimension)
        return mode

    def tensor(self, name: str, modes: Iterable[int]) -> None:
        mode_tuple = tuple(modes)
        shape = tuple(self._dimensions[mode] for mode in mode_tuple)
        self._tensors.append(TensorSpec(name, shape, mode_tuple))

    def finish(self) -> TensorNetworkSpec:
        network = TensorNetworkSpec(tuple(self._tensors))
        network.validate_closed()
        return network


def _add_qaoa_branch(
    builder: _NetworkBuilder,
    tag: str,
    qubits: int,
    edges: Sequence[tuple[int, int]],
    depth: int,
) -> dict[int, int]:
    current: dict[int, int] = {}
    for qubit in range(qubits):
        current[qubit] = builder.mode(2)
        builder.tensor(f"{tag}:plus[{qubit}]", (current[qubit],))

    for layer in range(depth):
        for qubit in range(qubits):
            output = builder.mode(2)
            builder.tensor(
                f"{tag}:rz[{layer},{qubit}]", (current[qubit], output)
            )
            current[qubit] = output
        for edge_index, (left, right) in enumerate(edges):
            left_output, right_output = builder.mode(2), builder.mode(2)
            builder.tensor(
                f"{tag}:rzz[{layer},{edge_index}]",
                (
                    current[left],
                    current[right],
                    left_output,
                    right_output,
                ),
            )
            current[left], current[right] = left_output, right_output
        for qubit in range(qubits):
            output = builder.mode(2)
            builder.tensor(
                f"{tag}:rx[{layer},{qubit}]", (current[qubit], output)
            )
            current[qubit] = output
    return current


def _add_support_mpo(
    builder: _NetworkBuilder,
    encoding: SupportTT,
    ket_outputs: dict[int, int],
    bra_outputs: dict[int, int],
) -> None:
    bonds = [
        builder.mode(encoding.cores[site].shape[-1])
        for site in range(encoding.qubits - 1)
    ]
    for site, qubit in enumerate(encoding.order):
        modes = []
        if site:
            modes.append(bonds[site - 1])
        modes.extend((ket_outputs[qubit], bra_outputs[qubit]))
        if site + 1 < encoding.qubits:
            modes.append(bonds[site])
        builder.tensor(f"event:tt[{site}|q{qubit}]", modes)


def _add_local_event_network(
    builder: _NetworkBuilder,
    encoding: LocalMISCardinality,
    ket_outputs: dict[int, int],
    bra_outputs: dict[int, int],
) -> None:
    card_bits: dict[int, int] = {
        qubit: builder.mode(2) for qubit in range(encoding.qubits)
    }
    count_bonds = [
        builder.mode(encoding.cardinality_cores[site].shape[-1])
        for site in range(encoding.qubits - 1)
    ]
    for site, qubit in enumerate(encoding.order):
        modes = []
        if site:
            modes.append(count_bonds[site - 1])
        modes.append(card_bits[qubit])
        if site + 1 < encoding.qubits:
            modes.append(count_bonds[site])
        builder.tensor(f"event:cardinality[{site}|q{qubit}]", modes)

    edge_legs: dict[int, list[int]] = {
        qubit: [] for qubit in range(encoding.qubits)
    }
    for edge_index, (left, right) in enumerate(encoding.edges):
        left_leg, right_leg = builder.mode(2), builder.mode(2)
        edge_legs[left].append(left_leg)
        edge_legs[right].append(right_leg)
        builder.tensor(f"event:mis_edge[{edge_index}]", (left_leg, right_leg))

    for qubit in range(encoding.qubits):
        # This ordinary COPY tensor replaces a Boolean hyperedge.  The generic
        # optimizer is consequently free to contract in any order.
        modes = (
            ket_outputs[qubit],
            bra_outputs[qubit],
            card_bits[qubit],
            *edge_legs[qubit],
        )
        builder.tensor(f"event:copy[q{qubit}]", modes)


def build_qaoa_density_network(
    graph: nx.Graph,
    depth: int,
    event_encoding: SupportTT | LocalMISCardinality,
) -> TensorNetworkSpec:
    """Attach an event encoding to a structural bra--ket QAOA network."""
    if depth < 0:
        raise ValueError("depth must be non-negative")
    edges = _canonical_edges(graph)
    qubits = graph.number_of_nodes()
    if event_encoding.qubits != qubits:
        raise ValueError("event and circuit qubit counts differ")
    builder = _NetworkBuilder()
    ket = _add_qaoa_branch(builder, "ket", qubits, edges, depth)
    bra = _add_qaoa_branch(builder, "bra", qubits, edges, depth)
    if isinstance(event_encoding, SupportTT):
        _add_support_mpo(builder, event_encoding, ket, bra)
    elif isinstance(event_encoding, LocalMISCardinality):
        _add_local_event_network(builder, event_encoding, ket, bra)
    else:  # pragma: no cover - guarded by the public type and useful to callers
        raise TypeError(f"unsupported event encoding: {type(event_encoding)!r}")
    return builder.finish()


@dataclass(frozen=True)
class PathCost:
    backend: str
    path: tuple[tuple[int, int], ...]
    estimated_flops: int
    peak_elements: int

    @property
    def log10_flops(self) -> float:
        return math.log10(max(1, self.estimated_flops))

    @property
    def log2_peak_elements(self) -> float:
        return math.log2(max(1, self.peak_elements))

    def as_dict(self) -> dict:
        return {
            "backend": self.backend,
            "path_format": "dynamic_operand_positions",
            "path": [list(pair) for pair in self.path],
            "path_length": len(self.path),
            "estimated_flops": self.estimated_flops,
            "log10_estimated_flops": self.log10_flops,
            "peak_elements": self.peak_elements,
            "log2_peak_elements": self.log2_peak_elements,
        }


def _pair_statistics(
    left: tuple[int, ...], right: tuple[int, ...], dimensions: dict[int, int]
) -> tuple[tuple[int, ...], int, int, int]:
    shared = set(left).intersection(right)
    output = tuple(mode for mode in left if mode not in shared) + tuple(
        mode for mode in right if mode not in shared
    )
    union_elements = math.prod(dimensions[mode] for mode in set(left).union(right))
    output_elements = math.prod(dimensions[mode] for mode in output)
    # Dense multiplications plus additions.  For an outer product this reduces
    # to exactly union_elements; for a true contraction it is 2U - |output|.
    flops = 2 * union_elements - output_elements if shared else union_elements
    shared_elements = math.prod(dimensions[mode] for mode in shared)
    return output, flops, output_elements, shared_elements


def _evaluate_dynamic_path(
    network: TensorNetworkSpec,
    path: Sequence[Sequence[int]],
    backend: str,
) -> PathCost:
    dimensions = network.mode_dimensions()
    current = [tensor.modes for tensor in network.tensors]
    peak = max(tensor.elements for tensor in network.tensors)
    total = 0
    normalized_path: list[tuple[int, int]] = []
    for raw_pair in path:
        if len(raw_pair) != 2:
            raise ValueError("only pairwise contraction paths are supported")
        left_index, right_index = sorted(map(int, raw_pair))
        if left_index == right_index or right_index >= len(current):
            raise ValueError(f"invalid path step {raw_pair} for {len(current)} operands")
        output, flops, output_elements, _ = _pair_statistics(
            current[left_index], current[right_index], dimensions
        )
        total += flops
        peak = max(peak, output_elements)
        del current[right_index]
        del current[left_index]
        current.append(output)
        normalized_path.append((left_index, right_index))
    if len(current) != 1 or current[0]:
        raise ValueError("path did not reduce the closed network to a scalar")
    return PathCost(backend, tuple(normalized_path), total, peak)


def _shape_greedy_path(
    network: TensorNetworkSpec, trials: int, seed: int
) -> PathCost:
    if trials < 1:
        raise ValueError("trials must be positive")
    dimensions = network.mode_dimensions()
    rng = random.Random(seed)
    best: PathCost | None = None

    for trial in range(trials):
        current = [tensor.modes for tensor in network.tensors]
        path: list[tuple[int, int]] = []
        while len(current) > 1:
            candidates = []
            for left_index in range(len(current)):
                for right_index in range(left_index + 1, len(current)):
                    if not set(current[left_index]).intersection(current[right_index]):
                        continue
                    output, flops, output_elements, shared_elements = _pair_statistics(
                        current[left_index], current[right_index], dimensions
                    )
                    removed = (
                        output_elements
                        - math.prod(dimensions[m] for m in current[left_index])
                        - math.prod(dimensions[m] for m in current[right_index])
                    )
                    strategy = trial % 3
                    if strategy == 0:
                        score = (flops, output_elements, -shared_elements)
                    elif strategy == 1:
                        score = (output_elements, flops, -shared_elements)
                    else:
                        score = (removed, flops, output_elements)
                    candidates.append(
                        (score, left_index, right_index, output)
                    )
            if not candidates:
                # This is only needed for disconnected networks; retain generic
                # correctness by permitting an outer product.
                for left_index in range(len(current)):
                    for right_index in range(left_index + 1, len(current)):
                        output, flops, output_elements, shared_elements = _pair_statistics(
                            current[left_index], current[right_index], dimensions
                        )
                        candidates.append(
                            (
                                (flops, output_elements, -shared_elements),
                                left_index,
                                right_index,
                                output,
                            )
                        )
            candidates.sort(key=lambda row: (row[0], row[1], row[2]))
            if trial < 3:
                chosen = candidates[0]
            else:
                chosen = candidates[rng.randrange(min(4, len(candidates)))]
            _, left_index, right_index, output = chosen
            path.append((left_index, right_index))
            del current[right_index]
            del current[left_index]
            current.append(output)

        result = _evaluate_dynamic_path(network, path, "shape-greedy")
        if best is None or (result.estimated_flops, result.peak_elements) < (
            best.estimated_flops,
            best.peak_elements,
        ):
            best = result
    assert best is not None
    return best


def _opt_einsum_path(network: TensorNetworkSpec) -> PathCost:
    try:
        import opt_einsum as oe
    except ImportError as error:  # pragma: no cover - environment dependent
        raise RuntimeError("opt_einsum is not installed") from error

    interleaved: list[object] = []
    for tensor in network.tensors:
        interleaved.extend((tensor.shape, tensor.modes))
    interleaved.append(())
    path, _ = oe.contract_path(*interleaved, shapes=True, optimize="greedy")
    return _evaluate_dynamic_path(network, path, "opt_einsum-greedy")


def optimize_contraction_path(
    network: TensorNetworkSpec,
    *,
    backend: str = "auto",
    trials: int = 24,
    seed: int = 260902,
) -> PathCost:
    """Optimize a cost-only unrestricted pairwise contraction path."""
    network.validate_closed()
    if backend not in {"auto", "shape-greedy", "opt_einsum"}:
        raise ValueError("backend must be auto, shape-greedy, or opt_einsum")
    greedy = None
    if backend in {"auto", "shape-greedy"}:
        greedy = _shape_greedy_path(network, trials, seed)
    if backend == "shape-greedy":
        assert greedy is not None
        return greedy
    try:
        external = _opt_einsum_path(network)
    except RuntimeError:
        if backend == "opt_einsum":
            raise
        assert greedy is not None
        return greedy
    if greedy is None or (external.estimated_flops, external.peak_elements) < (
        greedy.estimated_flops,
        greedy.peak_elements,
    ):
        return external
    return PathCost(
        "best-of(shape-greedy,opt_einsum-greedy)",
        greedy.path,
        greedy.estimated_flops,
        greedy.peak_elements,
    )


def default_orders(graph: nx.Graph) -> tuple[tuple[str, Order], ...]:
    qubits = graph.number_of_nodes()
    candidates = [
        ("natural", tuple(range(qubits))),
        ("reverse", tuple(reversed(range(qubits)))),
        (
            "degree_ascending",
            tuple(sorted(range(qubits), key=lambda q: (graph.degree[q], q))),
        ),
        (
            "degree_descending",
            tuple(sorted(range(qubits), key=lambda q: (-graph.degree[q], q))),
        ),
    ]
    unique: list[tuple[str, Order]] = []
    seen: set[Order] = set()
    for name, order in candidates:
        if order not in seen:
            seen.add(order)
            unique.append((name, order))
    return tuple(unique)


def _semantic_audit(
    graph: nx.Graph,
    target: int,
    support: Sequence[str],
    tt: SupportTT,
    local: LocalMISCardinality,
) -> dict:
    support_set = set(support)
    failures = []
    for bits in itertools.product((0, 1), repeat=graph.number_of_nodes()):
        value = "".join(map(str, bits))
        expected = float(value in support_set)
        observed_tt = evaluate_support_tt(tt, value)
        observed_local = evaluate_local_mis_cardinality(local, value)
        if not (
            abs(observed_tt - expected) <= 1e-10
            and abs(observed_local - expected) <= 1e-10
        ):
            failures.append((value, expected, observed_tt, observed_local))
    return {
        "assignments_checked": 1 << graph.number_of_nodes(),
        "target_cardinality": target,
        "passed": not failures,
        "failure_count": len(failures),
        "first_failure": list(failures[0]) if failures else None,
    }


def run_representation_screen(
    graph: nx.Graph,
    *,
    target_cardinality: int | None = None,
    depth: int = 1,
    orders: Sequence[tuple[str, Sequence[int]]] | None = None,
    backend: str = "auto",
    trials: int = 24,
    seed: int = 260902,
) -> dict:
    """Run the complete cost-only Phase-0 screen on one small graph."""
    edges = _canonical_edges(graph)
    qubits = graph.number_of_nodes()
    target, support = enumerate_independent_set_support(graph, target_cardinality)
    named_orders = default_orders(graph) if orders is None else tuple(
        (name, _validate_order(order, qubits)) for name, order in orders
    )
    if not named_orders:
        raise ValueError("at least one order is required")

    rows = []
    audits = []
    for order_name, order in named_orders:
        tt = compile_rank_minimal_support_tt(support, order)
        local = compile_local_mis_cardinality(graph, target, order)
        audit = _semantic_audit(graph, target, support, tt, local)
        audit.update({"order_name": order_name, "order": list(order)})
        audits.append(audit)
        if not audit["passed"]:
            raise AssertionError(audit)

        encodings: tuple[tuple[str, object], ...] = (
            ("rank_minimal_support_mpo", tt),
            ("local_mis_plus_cardinality", local),
        )
        for representation, encoding in encodings:
            network = build_qaoa_density_network(graph, depth, encoding)
            path = optimize_contraction_path(
                network, backend=backend, trials=trials, seed=seed
            )
            event_tensors = [
                tensor for tensor in network.tensors if tensor.name.startswith("event:")
            ]
            row = {
                "order_name": order_name,
                "order": list(order),
                "representation": representation,
                "support_size": len(support),
                "event_tensor_count": len(event_tensors),
                "event_dense_elements": sum(tensor.elements for tensor in event_tensors),
                "network_tensor_count": len(network.tensors),
                "network_dense_input_elements": sum(
                    tensor.elements for tensor in network.tensors
                ),
                "path": path.as_dict(),
            }
            if isinstance(encoding, SupportTT):
                row.update(
                    {
                        "event_bond_ranks": list(encoding.ranks),
                        "event_max_bond_rank": encoding.max_rank,
                    }
                )
            else:
                row.update(
                    {
                        "cardinality_bond_ranks": list(encoding.count_ranks),
                        "event_max_bond_rank": max(encoding.count_ranks),
                    }
                )
            rows.append(row)

    best = min(
        rows,
        key=lambda row: (
            row["path"]["estimated_flops"],
            row["path"]["peak_elements"],
        ),
    )
    return {
        "schema_version": 1,
        "stage": "event_conditioned_width_phase0_representation_screen",
        "question": (
            "Does a generic shape-only path optimizer erase or reverse the apparent "
            "advantage of a rank-minimal event-MPO representation?"
        ),
        "graph": {
            "qubits": qubits,
            "edges": [list(edge) for edge in edges],
            "edge_count": len(edges),
        },
        "qaoa_depth": depth,
        "event": {
            "predicate": "independent_set_and_exact_cardinality",
            "target_cardinality": target,
            "support_size": len(support),
            "support": list(support),
        },
        "optimizer": {
            "requested_backend": backend,
            "shape_only": True,
            "unrestricted_pairwise_path": True,
            "performs_contraction": False,
            "trials": trials,
            "seed": seed,
        },
        "semantic_audits": audits,
        "rows": rows,
        "best": {
            "order_name": best["order_name"],
            "order": best["order"],
            "representation": best["representation"],
            "estimated_flops": best["path"]["estimated_flops"],
            "peak_elements": best["path"]["peak_elements"],
        },
    }


def _make_graph(name: str, qubits: int, seed: int) -> nx.Graph:
    if qubits < 2:
        raise ValueError("the CLI screen requires at least two qubits")
    if name == "path":
        return nx.path_graph(qubits)
    if name == "cycle":
        return nx.cycle_graph(qubits)
    if name == "star":
        return nx.star_graph(qubits - 1)
    if name == "random":
        graph = nx.gnp_random_graph(qubits, 0.35, seed=seed)
        # A connected graph makes the path comparison easier to interpret.
        if not nx.is_connected(graph):
            components = [sorted(component) for component in nx.connected_components(graph)]
            for left, right in zip(components, components[1:], strict=False):
                graph.add_edge(left[0], right[0])
        return graph
    raise ValueError(name)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph", choices=("path", "cycle", "star", "random"), default="cycle")
    parser.add_argument("--qubits", type=int, default=5)
    parser.add_argument("--depth", type=int, default=1)
    parser.add_argument("--target-cardinality", type=int)
    parser.add_argument(
        "--backend", choices=("auto", "shape-greedy", "opt_einsum"), default="auto"
    )
    parser.add_argument("--trials", type=int, default=24)
    parser.add_argument("--seed", type=int, default=260902)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args(argv)

    graph = _make_graph(arguments.graph, arguments.qubits, arguments.seed)
    report = run_representation_screen(
        graph,
        target_cardinality=arguments.target_cardinality,
        depth=arguments.depth,
        backend=arguments.backend,
        trials=arguments.trials,
        seed=arguments.seed,
    )
    encoded = json.dumps(report, indent=2, sort_keys=True)
    if arguments.output is not None:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
