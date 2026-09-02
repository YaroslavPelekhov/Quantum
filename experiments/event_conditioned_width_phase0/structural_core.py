"""Exact small-n structural engine for event-conditioned contraction Phase 0.

The engine deliberately separates three objects which are easy to conflate:

* ``event_rank`` is the exact rank over the rationals of a Boolean event
  unfolding.  It is the minimal exact TT/MPO bond for that cut.
* ``circuit_cut_term`` is the topological upper-bound exponent
  ``copies * depth * crossing_edges``.  The default ``copies=2`` models the
  doubled network used for an expectation value.  It is not asserted to be
  the actual Schmidt rank of a QAOA state.
* ``joint_rank_product`` is the natural product proxy
  ``event_rank * 2**circuit_cut_term``.  Its logarithm is the additive score
  usually written ``log2(event_rank) + circuit_cut_term``.

All ranks are exact.  Exhaustive search is guarded at ten variables and uses
precomputed values for every subset, so it enumerates permutations without
recomputing unfoldings.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations, product
from math import factorial, gcd, log2
from typing import Iterable, Iterator, Literal, Sequence


BitWord = tuple[int, ...]
Edge = tuple[int, int]
Objective = Literal["joint", "event", "circuit"]


def _validate_nonnegative_integer(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def _normalise_word(word: str | Sequence[int], n: int | None) -> BitWord:
    if isinstance(word, str):
        if set(word) - {"0", "1"}:
            raise ValueError(f"invalid Boolean word: {word!r}")
        result = tuple(int(bit) for bit in word)
    else:
        result = tuple(word)
        if any(isinstance(bit, bool) or bit not in (0, 1) for bit in result):
            raise ValueError(f"invalid Boolean word: {word!r}")
    if n is not None and len(result) != n:
        raise ValueError(f"word has length {len(result)}, expected {n}")
    return result


@dataclass(frozen=True)
class BooleanEvent:
    """A finite Boolean support with a fixed number of variables."""

    n: int
    support: tuple[BitWord, ...]

    @classmethod
    def from_support(
        cls,
        support: Iterable[str | Sequence[int]],
        *,
        n: int | None = None,
    ) -> "BooleanEvent":
        if n is not None:
            _validate_nonnegative_integer(n, "n")
        raw = list(support)
        if n is None:
            if not raw:
                raise ValueError("n is required for an empty support")
            first = _normalise_word(raw[0], None)
            n = len(first)
            words = [first]
            words.extend(_normalise_word(word, n) for word in raw[1:])
        else:
            words = [_normalise_word(word, n) for word in raw]
        if len(set(words)) != len(words):
            raise ValueError("event support contains duplicate words")
        return cls(n=n, support=tuple(sorted(words)))

    @property
    def is_empty(self) -> bool:
        return not self.support


@dataclass(frozen=True)
class InteractionGraph:
    """A simple undirected graph on vertices ``range(n)``."""

    n: int
    edges: tuple[Edge, ...]

    @classmethod
    def from_edges(cls, n: int, edges: Iterable[Sequence[int]]) -> "InteractionGraph":
        _validate_nonnegative_integer(n, "n")
        normalised: set[Edge] = set()
        for edge in edges:
            pair = tuple(edge)
            if len(pair) != 2:
                raise ValueError(f"edge must have two endpoints: {edge!r}")
            u, v = pair
            if any(isinstance(x, bool) or not isinstance(x, int) for x in pair):
                raise ValueError(f"edge endpoints must be integers: {edge!r}")
            if not (0 <= u < n and 0 <= v < n):
                raise ValueError(f"edge endpoint outside range(n): {edge!r}")
            if u == v:
                raise ValueError(f"self-loops are not supported: {edge!r}")
            normalised.add((min(u, v), max(u, v)))
        return cls(n=n, edges=tuple(sorted(normalised)))


def _assignment_index(word: BitWord, variables: Sequence[int]) -> int:
    value = 0
    for variable in variables:
        value = (value << 1) | word[variable]
    return value


def event_unfolding(
    event: BooleanEvent,
    left_mask: int,
    *,
    compact: bool = False,
) -> tuple[tuple[int, ...], ...]:
    """Return the exact 0/1 unfolding for ``left_mask | complement``.

    With ``compact=True``, all-zero rows and columns are omitted.  This does
    not change rank and makes exhaustive rank-table construction much faster
    for sparse supports.
    """

    full_mask = (1 << event.n) - 1
    if isinstance(left_mask, bool) or not isinstance(left_mask, int):
        raise ValueError("left_mask must be an integer")
    if left_mask < 0 or left_mask > full_mask:
        raise ValueError("left_mask contains variables outside the event")
    left = tuple(i for i in range(event.n) if left_mask & (1 << i))
    right = tuple(i for i in range(event.n) if not left_mask & (1 << i))

    if compact:
        if not event.support:
            return tuple()
        row_keys = sorted({_assignment_index(word, left) for word in event.support})
        col_keys = sorted({_assignment_index(word, right) for word in event.support})
        row_position = {value: i for i, value in enumerate(row_keys)}
        col_position = {value: i for i, value in enumerate(col_keys)}
        matrix = [[0] * len(col_keys) for _ in row_keys]
        for word in event.support:
            matrix[row_position[_assignment_index(word, left)]][
                col_position[_assignment_index(word, right)]
            ] = 1
        return tuple(tuple(row) for row in matrix)

    matrix = [[0] * (1 << len(right)) for _ in range(1 << len(left))]
    for word in event.support:
        matrix[_assignment_index(word, left)][_assignment_index(word, right)] = 1
    return tuple(tuple(row) for row in matrix)


def exact_integer_matrix_rank(matrix: Sequence[Sequence[int]]) -> int:
    """Compute matrix rank over Q using fraction-free integer elimination."""

    rows = [list(row) for row in matrix]
    if not rows:
        return 0
    columns = len(rows[0])
    if any(len(row) != columns for row in rows):
        raise ValueError("matrix rows have inconsistent lengths")
    if columns == 0:
        return 0
    if any(isinstance(value, bool) or not isinstance(value, int) for row in rows for value in row):
        raise ValueError("exact rank expects integer entries")

    pivot_row = 0
    for column in range(columns):
        pivot = next(
            (row for row in range(pivot_row, len(rows)) if rows[row][column]),
            None,
        )
        if pivot is None:
            continue
        rows[pivot_row], rows[pivot] = rows[pivot], rows[pivot_row]
        pivot_value = rows[pivot_row][column]
        for row in range(pivot_row + 1, len(rows)):
            entry = rows[row][column]
            if entry == 0:
                continue
            common = gcd(abs(pivot_value), abs(entry))
            row_multiplier = pivot_value // common
            pivot_multiplier = entry // common
            for col in range(column, columns):
                rows[row][col] = (
                    row_multiplier * rows[row][col]
                    - pivot_multiplier * rows[pivot_row][col]
                )
            divisor = 0
            for value in rows[row][column + 1 :]:
                divisor = gcd(divisor, abs(value))
            if divisor > 1:
                for col in range(column + 1, columns):
                    rows[row][col] //= divisor
        pivot_row += 1
        if pivot_row == len(rows):
            break
    return pivot_row


def event_unfolding_rank(event: BooleanEvent, left_mask: int) -> int:
    return exact_integer_matrix_rank(event_unfolding(event, left_mask, compact=True))


def event_rank_table(event: BooleanEvent) -> tuple[int, ...]:
    """Return exact event ranks for every subset mask.

    Complementary masks are transposes, so only one of each pair is reduced.
    """

    size = 1 << event.n
    full_mask = size - 1
    output = [-1] * size
    for mask in range(size):
        if output[mask] >= 0:
            continue
        rank = event_unfolding_rank(event, mask)
        output[mask] = rank
        output[full_mask ^ mask] = rank
    return tuple(output)


def crossing_edge_count(graph: InteractionGraph, left_mask: int) -> int:
    full_mask = (1 << graph.n) - 1
    if isinstance(left_mask, bool) or not isinstance(left_mask, int):
        raise ValueError("left_mask must be an integer")
    if left_mask < 0 or left_mask > full_mask:
        raise ValueError("left_mask contains vertices outside the graph")
    return sum(
        bool(left_mask & (1 << u)) != bool(left_mask & (1 << v))
        for u, v in graph.edges
    )


def crossing_edge_table(graph: InteractionGraph) -> tuple[int, ...]:
    return tuple(crossing_edge_count(graph, mask) for mask in range(1 << graph.n))


@dataclass(frozen=True)
class StructuralTables:
    event: BooleanEvent
    graph: InteractionGraph
    event_ranks: tuple[int, ...]
    crossing_edges: tuple[int, ...]


def build_structural_tables(
    event: BooleanEvent, graph: InteractionGraph
) -> StructuralTables:
    if event.n != graph.n:
        raise ValueError("event and graph must use the same number of variables")
    return StructuralTables(
        event=event,
        graph=graph,
        event_ranks=event_rank_table(event),
        crossing_edges=crossing_edge_table(graph),
    )


def _validate_order(order: Sequence[int], n: int) -> tuple[int, ...]:
    result = tuple(order)
    if len(result) != n or set(result) != set(range(n)):
        raise ValueError("order must be a permutation of range(n)")
    return result


@dataclass(frozen=True)
class CutRecord:
    cut: int
    prefix: tuple[int, ...]
    prefix_mask: int
    event_rank: int
    crossing_edges: int
    circuit_cut_term: int
    circuit_rank_factor: int
    joint_rank_product: int
    joint_log2_cost: float


@dataclass(frozen=True)
class OrderProfile:
    order: tuple[int, ...]
    depth: int
    circuit_copies: int
    cuts: tuple[CutRecord, ...]
    max_event_rank: int
    max_crossing_edges: int
    max_circuit_cut_term: int
    max_joint_rank_product: int
    joint_J: float


def order_profile(
    event: BooleanEvent,
    graph: InteractionGraph,
    depth: int,
    order: Sequence[int],
    *,
    circuit_copies: int = 2,
    tables: StructuralTables | None = None,
) -> OrderProfile:
    """Compute the exact event profile and natural joint proxy for one order."""

    depth = _validate_nonnegative_integer(depth, "depth")
    circuit_copies = _validate_nonnegative_integer(circuit_copies, "circuit_copies")
    order = _validate_order(order, event.n)
    if event.n != graph.n:
        raise ValueError("event and graph must use the same number of variables")
    if tables is None:
        tables = build_structural_tables(event, graph)
    elif tables.event != event or tables.graph != graph:
        raise ValueError("structural tables do not match the event and graph")

    records: list[CutRecord] = []
    mask = 0
    for cut, variable in enumerate(order[:-1], start=1):
        mask |= 1 << variable
        event_rank = tables.event_ranks[mask]
        crossing = tables.crossing_edges[mask]
        exponent = circuit_copies * depth * crossing
        circuit_factor = 1 << exponent
        joint = event_rank * circuit_factor
        records.append(
            CutRecord(
                cut=cut,
                prefix=order[:cut],
                prefix_mask=mask,
                event_rank=event_rank,
                crossing_edges=crossing,
                circuit_cut_term=exponent,
                circuit_rank_factor=circuit_factor,
                joint_rank_product=joint,
                joint_log2_cost=(float("-inf") if joint == 0 else log2(joint)),
            )
        )

    max_event = max((record.event_rank for record in records), default=0)
    max_crossing = max((record.crossing_edges for record in records), default=0)
    max_exponent = max((record.circuit_cut_term for record in records), default=0)
    max_joint = max((record.joint_rank_product for record in records), default=0)
    return OrderProfile(
        order=order,
        depth=depth,
        circuit_copies=circuit_copies,
        cuts=tuple(records),
        max_event_rank=max_event,
        max_crossing_edges=max_crossing,
        max_circuit_cut_term=max_exponent,
        max_joint_rank_product=max_joint,
        joint_J=(float("-inf") if max_joint == 0 else log2(max_joint)),
    )


def _cut_score(
    objective: Objective,
    event_rank: int,
    crossing_edges: int,
    exponent: int,
) -> int:
    if objective == "event":
        return event_rank
    if objective == "circuit":
        return crossing_edges
    if objective == "joint":
        return event_rank * (1 << exponent)
    raise ValueError(f"unknown objective: {objective!r}")


@dataclass(frozen=True)
class ExhaustiveSearchResult:
    objective: Objective
    depth: int
    circuit_copies: int
    best_score: int
    best_joint_J: float | None
    optimal_order_count: int
    retained_optimal_orders: tuple[tuple[int, ...], ...]
    permutations_evaluated: int


def exhaustive_permutation_search(
    event: BooleanEvent,
    graph: InteractionGraph,
    depth: int,
    *,
    objective: Objective = "joint",
    circuit_copies: int = 2,
    max_n: int = 10,
    retain_optimal_orders: int = 32,
    tables: StructuralTables | None = None,
) -> ExhaustiveSearchResult:
    """Enumerate every variable permutation and minimize a max-cut objective."""

    depth = _validate_nonnegative_integer(depth, "depth")
    circuit_copies = _validate_nonnegative_integer(circuit_copies, "circuit_copies")
    max_n = _validate_nonnegative_integer(max_n, "max_n")
    retain_optimal_orders = _validate_nonnegative_integer(
        retain_optimal_orders, "retain_optimal_orders"
    )
    if objective not in ("joint", "event", "circuit"):
        raise ValueError(f"unknown objective: {objective!r}")
    if event.n != graph.n:
        raise ValueError("event and graph must use the same number of variables")
    if event.n > max_n:
        raise ValueError(
            f"exhaustive permutation search is guarded at n <= {max_n}; got {event.n}"
        )
    if tables is None:
        tables = build_structural_tables(event, graph)
    elif tables.event != event or tables.graph != graph:
        raise ValueError("structural tables do not match the event and graph")

    best: int | None = None
    best_count = 0
    retained: list[tuple[int, ...]] = []
    evaluated = 0
    for order in permutations(range(event.n)):
        evaluated += 1
        mask = 0
        worst = 0
        for variable in order[:-1]:
            mask |= 1 << variable
            crossing = tables.crossing_edges[mask]
            exponent = circuit_copies * depth * crossing
            score = _cut_score(
                objective, tables.event_ranks[mask], crossing, exponent
            )
            if score > worst:
                worst = score
            if best is not None and worst > best:
                break
        if best is None or worst < best:
            best = worst
            best_count = 1
            retained = [order] if retain_optimal_orders else []
        elif worst == best:
            best_count += 1
            if len(retained) < retain_optimal_orders:
                retained.append(order)

    assert best is not None
    return ExhaustiveSearchResult(
        objective=objective,
        depth=depth,
        circuit_copies=circuit_copies,
        best_score=best,
        best_joint_J=(
            float("-inf") if objective == "joint" and best == 0
            else log2(best) if objective == "joint"
            else None
        ),
        optimal_order_count=best_count,
        retained_optimal_orders=tuple(retained),
        permutations_evaluated=evaluated,
    )


@dataclass(frozen=True)
class ImplicitProxyKroneckerUnfolding:
    """Implicit witness for the natural product proxy ``E tensor I_q``.

    ``I_q`` is a canonical full-rank factor of dimension equal to the circuit
    cut-rank upper bound.  It verifies the algebraic product collapse only; it
    must not be interpreted as the actual unfolding of a particular circuit.
    """

    event_matrix: tuple[tuple[int, ...], ...]
    circuit_dimension: int

    @property
    def event_rank(self) -> int:
        return exact_integer_matrix_rank(self.event_matrix)

    @property
    def exact_rank(self) -> int:
        return self.event_rank * self.circuit_dimension

    @property
    def shape(self) -> tuple[int, int]:
        rows = len(self.event_matrix)
        columns = len(self.event_matrix[0]) if rows else 0
        return rows * self.circuit_dimension, columns * self.circuit_dimension

    @property
    def entries(self) -> int:
        rows, columns = self.shape
        return rows * columns

    def materialize(self, *, max_entries: int = 1_000_000) -> tuple[tuple[int, ...], ...]:
        """Materialize ``event_matrix tensor I`` for small audit cases."""

        max_entries = _validate_nonnegative_integer(max_entries, "max_entries")
        if self.entries > max_entries:
            raise ValueError(
                f"explicit Kronecker witness needs {self.entries} entries, "
                f"above limit {max_entries}"
            )
        q = self.circuit_dimension
        rows = len(self.event_matrix)
        columns = len(self.event_matrix[0]) if rows else 0
        output = [[0] * (columns * q) for _ in range(rows * q)]
        for event_row, source_row in enumerate(self.event_matrix):
            for event_column, value in enumerate(source_row):
                if value == 0:
                    continue
                for diagonal in range(q):
                    output[event_row * q + diagonal][event_column * q + diagonal] = value
        return tuple(tuple(row) for row in output)


@dataclass(frozen=True)
class CollapseCutAudit:
    cut: int
    event_rank: int
    circuit_dimension: int
    predicted_joint_rank: int
    implicit_joint_rank: int
    explicit_joint_rank: int | None

    @property
    def passed(self) -> bool:
        return self.predicted_joint_rank == self.implicit_joint_rank and (
            self.explicit_joint_rank is None
            or self.explicit_joint_rank == self.predicted_joint_rank
        )


@dataclass(frozen=True)
class CollapseAudit:
    order: tuple[int, ...]
    cuts: tuple[CollapseCutAudit, ...]

    @property
    def explicit_checks(self) -> int:
        return sum(cut.explicit_joint_rank is not None for cut in self.cuts)

    @property
    def passed(self) -> bool:
        return all(cut.passed for cut in self.cuts)


def audit_joint_rank_collapse(
    event: BooleanEvent,
    graph: InteractionGraph,
    depth: int,
    order: Sequence[int],
    *,
    circuit_copies: int = 2,
    max_explicit_entries: int = 250_000,
) -> CollapseAudit:
    """Verify ``J_cut = rank(E_cut tensor I_circuit)`` at every cut."""

    max_explicit_entries = _validate_nonnegative_integer(
        max_explicit_entries, "max_explicit_entries"
    )
    tables = build_structural_tables(event, graph)
    profile = order_profile(
        event,
        graph,
        depth,
        order,
        circuit_copies=circuit_copies,
        tables=tables,
    )
    audits: list[CollapseCutAudit] = []
    for record in profile.cuts:
        witness = ImplicitProxyKroneckerUnfolding(
            event_matrix=event_unfolding(event, record.prefix_mask),
            circuit_dimension=record.circuit_rank_factor,
        )
        explicit_rank = None
        if witness.entries <= max_explicit_entries:
            explicit_rank = exact_integer_matrix_rank(
                witness.materialize(max_entries=max_explicit_entries)
            )
        audit = CollapseCutAudit(
            cut=record.cut,
            event_rank=record.event_rank,
            circuit_dimension=record.circuit_rank_factor,
            predicted_joint_rank=record.joint_rank_product,
            implicit_joint_rank=witness.exact_rank,
            explicit_joint_rank=explicit_rank,
        )
        if not audit.passed:
            raise AssertionError(f"joint-rank collapse failed at cut {record.cut}")
        audits.append(audit)
    return CollapseAudit(order=profile.order, cuts=tuple(audits))


def path_edges(order: Sequence[int]) -> tuple[Edge, ...]:
    order = tuple(order)
    if len(set(order)) != len(order):
        raise ValueError("path order contains duplicate vertices")
    return tuple((min(u, v), max(u, v)) for u, v in zip(order, order[1:]))


def complete_graph_edges(n: int) -> tuple[Edge, ...]:
    _validate_nonnegative_integer(n, "n")
    return tuple((u, v) for u in range(n) for v in range(u + 1, n))


def paired_equality_support(n: int) -> tuple[BitWord, ...]:
    """Words satisfying x[2j] == x[2j+1] for every complete pair."""

    _validate_nonnegative_integer(n, "n")
    pairs = n // 2
    free = pairs + (n % 2)
    words: list[BitWord] = []
    for values in product((0, 1), repeat=free):
        word: list[int] = []
        for pair in range(pairs):
            word.extend((values[pair], values[pair]))
        if n % 2:
            word.append(values[-1])
        words.append(tuple(word))
    return tuple(words)


def interleaved_pair_order(n: int) -> tuple[int, ...]:
    """Split paired variables: first endpoints, then second endpoints."""

    _validate_nonnegative_integer(n, "n")
    first = tuple(range(0, n - 1, 2))
    second = tuple(range(1, n, 2))
    tail = (n - 1,) if n % 2 else tuple()
    return first + second + tail


@dataclass(frozen=True)
class SyntheticInstance:
    name: str
    event: BooleanEvent
    graph: InteractionGraph
    depth: int
    event_favoured_order: tuple[int, ...]
    circuit_favoured_order: tuple[int, ...]
    description: str


def synthetic_instance(name: str, *, n: int = 6, depth: int = 1) -> SyntheticInstance:
    """Build deterministic aligned/conflicting Phase-0 falsification families."""

    _validate_nonnegative_integer(n, "n")
    depth = _validate_nonnegative_integer(depth, "depth")
    if n < 4:
        raise ValueError("synthetic ordering families require n >= 4")
    key = name.lower().replace("-", "_")
    natural = tuple(range(n))
    interleaved = interleaved_pair_order(n)
    paired_event = BooleanEvent.from_support(paired_equality_support(n), n=n)
    singleton_event = BooleanEvent.from_support(["0" * n], n=n)

    if key == "aligned":
        return SyntheticInstance(
            name=key,
            event=paired_event,
            graph=InteractionGraph.from_edges(n, path_edges(natural)),
            depth=depth,
            event_favoured_order=natural,
            circuit_favoured_order=natural,
            description="Equality pairs and the circuit path favour the same layout.",
        )
    if key in ("anti_aligned", "antialigned"):
        return SyntheticInstance(
            name="anti_aligned",
            event=paired_event,
            graph=InteractionGraph.from_edges(n, path_edges(interleaved)),
            depth=depth,
            event_favoured_order=natural,
            circuit_favoured_order=interleaved,
            description="The path-optimal circuit layout splits every event equality pair.",
        )
    if key == "event_easy":
        return SyntheticInstance(
            name=key,
            event=singleton_event,
            graph=InteractionGraph.from_edges(n, path_edges(interleaved)),
            depth=depth,
            event_favoured_order=natural,
            circuit_favoured_order=interleaved,
            description="A rank-one event leaves only circuit ordering structure.",
        )
    if key == "circuit_hard":
        return SyntheticInstance(
            name=key,
            event=paired_event,
            graph=InteractionGraph.from_edges(n, complete_graph_edges(n)),
            depth=depth,
            event_favoured_order=natural,
            circuit_favoured_order=natural,
            description="A clique has large, order-invariant cut profiles.",
        )
    raise ValueError(
        "unknown synthetic family; choose aligned, anti_aligned, event_easy, "
        "or circuit_hard"
    )


def iter_synthetic_instances(*, n: int = 6, depth: int = 1) -> Iterator[SyntheticInstance]:
    for name in ("aligned", "anti_aligned", "event_easy", "circuit_hard"):
        yield synthetic_instance(name, n=n, depth=depth)


def factorial_permutation_count(n: int) -> int:
    """Small public helper used by experiment reports and tests."""

    _validate_nonnegative_integer(n, "n")
    return factorial(n)
