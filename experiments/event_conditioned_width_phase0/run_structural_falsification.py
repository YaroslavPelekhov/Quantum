"""Run the exact small-n falsification of the natural joint-width proxy."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from itertools import permutations
from math import log2
from pathlib import Path
from time import perf_counter


REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.event_conditioned_width_phase0.structural_core import (
    BooleanEvent,
    InteractionGraph,
    audit_joint_rank_collapse,
    build_structural_tables,
    crossing_edge_count,
    event_unfolding_rank,
    exact_integer_matrix_rank,
    exhaustive_permutation_search,
    factorial_permutation_count,
    order_profile,
    synthetic_instance,
)


RESULTS = REPO / "results" / "event_conditioned_width_phase0"

GLOBAL_REDUCTION_LEMMA = (
    "Let E:{0,1}^V->{0,1}. For every edge e={u,v} and copy c in [q], "
    "introduce distinct half-edge bits z_(u,e,c), z_(v,e,c), and let "
    "B_G,q(z)=product_(e,c) 1[z_(u,e,c)=z_(v,e,c)]. Form the single tensor "
    "T=E tensor B_G,q and group x_v together with all half-edge bits incident "
    "to v as site v. Then, simultaneously for every S subset V, "
    "rank(T_(S|V\\S))=rank(E_(S|V\\S))*2^(q*|delta_G(S)|)."
)

GLOBAL_REDUCTION_PROOF = (
    "After row/column permutations, T_(S|V\\S) is the Kronecker product of "
    "E_(S|V\\S) and the unfoldings of all equality factors. An equality "
    "factor internal to either side is a nonzero 4-by-1 or 1-by-4 vector and "
    "has rank one. A crossing equality factor is the 2-by-2 identity and has "
    "rank two. All half-edge variables are distinct, so these factor "
    "unfoldings combine by Kronecker product. Multiplicativity of matrix rank "
    "gives the formula for every S using the same globally defined T."
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def explicit_site_grouped_tensor_unfolding(
    event: BooleanEvent,
    graph: InteractionGraph,
    equality_copies: int,
    left_mask: int,
    *,
    max_entries: int = 100_000,
) -> tuple[tuple[int, ...], ...]:
    """Materialize a small unfolding of the single tensor in the lemma."""

    if event.n != graph.n:
        raise ValueError("event and graph must use the same number of sites")
    if (
        isinstance(equality_copies, bool)
        or not isinstance(equality_copies, int)
        or equality_copies < 0
    ):
        raise ValueError("equality_copies must be a non-negative integer")
    full_mask = (1 << event.n) - 1
    if isinstance(left_mask, bool) or not isinstance(left_mask, int):
        raise ValueError("left_mask must be an integer")
    if not 0 <= left_mask <= full_mask:
        raise ValueError("left_mask contains sites outside the graph")

    variables_by_site: list[list[tuple]] = [
        [("x", vertex)] for vertex in range(event.n)
    ]
    for edge_index, (u, v) in enumerate(graph.edges):
        for copy in range(equality_copies):
            variables_by_site[u].append(("z", edge_index, copy, u))
            variables_by_site[v].append(("z", edge_index, copy, v))
    row_variables = tuple(
        variable
        for vertex in range(event.n)
        if left_mask & (1 << vertex)
        for variable in variables_by_site[vertex]
    )
    column_variables = tuple(
        variable
        for vertex in range(event.n)
        if not left_mask & (1 << vertex)
        for variable in variables_by_site[vertex]
    )
    variable_order = row_variables + column_variables
    total_entries = 1 << len(variable_order)
    if total_entries > max_entries:
        raise ValueError(
            f"explicit site-grouped tensor needs {total_entries} entries, "
            f"above limit {max_entries}"
        )

    row_count = 1 << len(row_variables)
    column_count = 1 << len(column_variables)
    column_mask = column_count - 1
    support = set(event.support)
    matrix = [[0] * column_count for _ in range(row_count)]
    for flat_index in range(total_entries):
        values = {
            variable: (flat_index >> (len(variable_order) - position - 1)) & 1
            for position, variable in enumerate(variable_order)
        }
        word = tuple(values[("x", vertex)] for vertex in range(event.n))
        if word not in support:
            continue
        if any(
            values[("z", edge_index, copy, u)]
            != values[("z", edge_index, copy, v)]
            for edge_index, (u, v) in enumerate(graph.edges)
            for copy in range(equality_copies)
        ):
            continue
        row = flat_index >> len(column_variables)
        column = flat_index & column_mask
        matrix[row][column] = 1
    return tuple(tuple(row) for row in matrix)


def explicit_global_reduction_check(
    event: BooleanEvent,
    graph: InteractionGraph,
    equality_copies: int,
    left_mask: int,
    *,
    max_entries: int = 100_000,
) -> dict:
    """Compare an explicit full-tensor unfolding rank with the lemma."""

    matrix = explicit_site_grouped_tensor_unfolding(
        event,
        graph,
        equality_copies,
        left_mask,
        max_entries=max_entries,
    )
    event_rank = event_unfolding_rank(event, left_mask)
    crossing_edges = crossing_edge_count(graph, left_mask)
    edge_factor_rank = 1 << (equality_copies * crossing_edges)
    predicted_rank = event_rank * edge_factor_rank
    explicit_rank = exact_integer_matrix_rank(matrix)
    return {
        "n": event.n,
        "edges": graph.edges,
        "left_mask": left_mask,
        "equality_copies": equality_copies,
        "event_rank": event_rank,
        "crossing_edges": crossing_edges,
        "edge_factor_rank": edge_factor_rank,
        "predicted_rank": predicted_rank,
        "explicit_rank": explicit_rank,
        "matrix_shape": (
            len(matrix),
            len(matrix[0]) if matrix else 0,
        ),
        "passed": explicit_rank == predicted_rank,
    }


def run_global_reduction_controls() -> dict:
    """Run small full-tensor checks covering crossing and internal edges."""

    full_two_bit_event = BooleanEvent.from_support(
        ["00", "01", "10", "11"], n=2
    )
    one_edge = InteractionGraph.from_edges(2, [(0, 1)])
    x0_equals_x2 = BooleanEvent.from_support(
        ["000", "010", "101", "111"], n=3
    )
    path = InteractionGraph.from_edges(3, [(0, 1), (1, 2)])
    internal_only = InteractionGraph.from_edges(3, [(0, 1)])
    controls = [
        {
            "name": "one_crossing_equality_has_rank_two",
            **explicit_global_reduction_check(
                full_two_bit_event, one_edge, 1, 0b01
            ),
        },
        {
            "name": "one_internal_and_one_crossing_edge_two_copies",
            **explicit_global_reduction_check(
                x0_equals_x2, path, 2, 0b011
            ),
        },
        {
            "name": "two_crossing_edges_two_copies",
            **explicit_global_reduction_check(
                x0_equals_x2, path, 2, 0b010
            ),
        },
        {
            "name": "internal_edge_does_not_increase_rank",
            **explicit_global_reduction_check(
                x0_equals_x2, internal_only, 2, 0b011
            ),
        },
    ]
    return {
        "passed": all(control["passed"] for control in controls),
        "checks": controls,
    }


def _order_scores(order, tables, depth: int, circuit_copies: int = 2) -> tuple[int, int, int]:
    """Compute all three max-cut scores without branch-and-bound pruning."""

    mask = 0
    event_score = 0
    circuit_score = 0
    joint_score = 0
    for variable in order[:-1]:
        mask |= 1 << variable
        event_rank = tables.event_ranks[mask]
        crossing_edges = tables.crossing_edges[mask]
        exponent = circuit_copies * depth * crossing_edges
        event_score = max(event_score, event_rank)
        circuit_score = max(circuit_score, crossing_edges)
        joint_score = max(joint_score, event_rank * (1 << exponent))
    return event_score, circuit_score, joint_score


def _update_one_sided_optimum(
    state: dict | None,
    *,
    objective_score: int,
    joint_score: int,
    order: tuple[int, ...],
) -> dict:
    """Track the complete argmin set and the range of joint scores within it."""

    if state is None or objective_score < state["best_score"]:
        return {
            "best_score": objective_score,
            "optimal_order_count": 1,
            "best_joint_score": joint_score,
            "best_joint_order_count": 1,
            "best_joint_order": order,
            "worst_joint_score": joint_score,
            "worst_joint_order_count": 1,
            "worst_joint_order": order,
        }
    if objective_score > state["best_score"]:
        return state

    state["optimal_order_count"] += 1
    if joint_score < state["best_joint_score"]:
        state["best_joint_score"] = joint_score
        state["best_joint_order_count"] = 1
        state["best_joint_order"] = order
    elif joint_score == state["best_joint_score"]:
        state["best_joint_order_count"] += 1
    if joint_score > state["worst_joint_score"]:
        state["worst_joint_score"] = joint_score
        state["worst_joint_order_count"] = 1
        state["worst_joint_order"] = order
    elif joint_score == state["worst_joint_score"]:
        state["worst_joint_order_count"] += 1
    return state


def _update_joint_optimum(
    state: dict | None, *, score: int, order: tuple[int, ...]
) -> dict:
    if state is None or score < state["best_score"]:
        return {
            "best_score": score,
            "optimal_order_count": 1,
            "representative_order": order,
        }
    if score == state["best_score"]:
        state["optimal_order_count"] += 1
    return state


def independent_exhaustive_audit(
    tables,
    depth: int,
    searches: dict,
    *,
    circuit_copies: int = 2,
) -> dict:
    """Independently verify exact search results and audit all objective ties.

    Unlike ``exhaustive_permutation_search``, this pass evaluates every cut of
    every order and performs no incumbent-based pruning. It therefore checks
    both the factorial enumeration counts and the reported optimum/tie counts.
    """

    event_state = None
    circuit_state = None
    joint_state = None
    evaluated = 0
    for order in permutations(range(tables.event.n)):
        evaluated += 1
        event_score, circuit_score, joint_score = _order_scores(
            order, tables, depth, circuit_copies
        )
        event_state = _update_one_sided_optimum(
            event_state,
            objective_score=event_score,
            joint_score=joint_score,
            order=order,
        )
        circuit_state = _update_one_sided_optimum(
            circuit_state,
            objective_score=circuit_score,
            joint_score=joint_score,
            order=order,
        )
        joint_state = _update_joint_optimum(
            joint_state, score=joint_score, order=order
        )

    assert event_state is not None
    assert circuit_state is not None
    assert joint_state is not None
    expected = factorial_permutation_count(tables.event.n)
    states = {
        "event": event_state,
        "circuit": circuit_state,
        "joint": joint_state,
    }
    search_checks = {}
    for objective, state in states.items():
        search = searches[objective]
        checks = {
            "best_score_matches": search.best_score == state["best_score"],
            "optimal_order_count_matches": (
                search.optimal_order_count == state["optimal_order_count"]
            ),
            "search_permutation_count_matches": (
                search.permutations_evaluated == expected
            ),
        }
        checks["passed"] = all(checks.values())
        search_checks[objective] = checks

    return {
        "passed": (
            evaluated == expected
            and all(check["passed"] for check in search_checks.values())
        ),
        "permutations_expected": expected,
        "permutations_evaluated_independently": evaluated,
        "search_checks": search_checks,
        "event_optimal_set": event_state,
        "circuit_optimal_set": circuit_state,
        "joint_optimum": joint_state,
    }


def tie_aware_headroom(exhaustive_audit: dict) -> dict:
    """Return a conservative headroom claim that is invariant to tie order."""

    event_joint = exhaustive_audit["event_optimal_set"]["best_joint_score"]
    circuit_joint = exhaustive_audit["circuit_optimal_set"]["best_joint_score"]
    one_sided_joint = min(event_joint, circuit_joint)
    joint_optimum = exhaustive_audit["joint_optimum"]["best_score"]
    if joint_optimum:
        ratio = one_sided_joint / joint_optimum
        log2_ratio = log2(one_sided_joint) - log2(joint_optimum)
    else:
        ratio = 1.0 if one_sided_joint == 0 else None
        log2_ratio = 0.0 if one_sided_joint == 0 else None
    return {
        "definition": (
            "min J over the complete event-optimal or circuit-optimal argmin "
            "sets, divided by the global minimum J"
        ),
        "tie_policy": (
            "optimistic null: use the lowest J attained anywhere in each "
            "complete one-sided argmin set"
        ),
        "best_event_optimal_joint_score": event_joint,
        "best_circuit_optimal_joint_score": circuit_joint,
        "best_one_sided_joint_score": one_sided_joint,
        "joint_optimum_score": joint_optimum,
        "ratio": ratio,
        "log2_ratio": log2_ratio,
        "strict_headroom": one_sided_joint > joint_optimum,
        "tie_break_sensitive": (
            exhaustive_audit["event_optimal_set"]["best_joint_score"]
            != exhaustive_audit["event_optimal_set"]["worst_joint_score"]
            or exhaustive_audit["circuit_optimal_set"]["best_joint_score"]
            != exhaustive_audit["circuit_optimal_set"]["worst_joint_score"]
        ),
    }


def binding_verdict(rows: list[dict], global_reduction_controls: dict) -> dict:
    """State only conclusions established by this structural experiment."""

    reduction_established = (
        bool(rows)
        and global_reduction_controls["passed"]
        and all(row["collapse"]["passed"] for row in rows)
    )
    return {
        "exhaustive_searches_independently_verified": bool(rows) and all(
            row["exhaustive_audit"]["passed"] for row in rows
        ),
        "proxy_kronecker_rank_identity_verified": bool(rows) and all(
            row["collapse"]["passed"] for row in rows
        ),
        "explicit_kronecker_rank_checks_performed": sum(
            row["collapse"]["explicit_checks"] for row in rows
        ),
        "explicit_kronecker_rank_checks_skipped": sum(
            row["collapse"]["explicit_checks_skipped"] for row in rows
        ),
        "global_site_grouped_tensor_reduction_established": reduction_established,
        "natural_proxy_equals_linear_tt_rank_width_of_artificial_tensor": (
            reduction_established
        ),
        "actual_circuit_unfolding_equivalence_established": False,
        "protocol_kill_gate": "K6" if reduction_established else None,
        "a_star_novelty_survives": False if reduction_established else None,
        "scope": (
            "K6 applies only to the natural product proxy as the linear TT-rank "
            "width of the artificial event-times-equality tensor T. It does not "
            "identify T with an actual QAOA circuit tensor or establish an "
            "actual QAOA circuit-width formula."
        ),
        "verdict": (
            "The natural proxy is exactly the maximum site-prefix unfolding "
            "rank of one globally defined artificial tensor T=E tensor B_G,2p, "
            "so it is an ordinary linear TT-rank ordering objective and fails "
            "K6 as a new width. This conclusion is deliberately silent about "
            "the width and contraction cost of the actual QAOA network."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--min-n", type=int, default=4)
    parser.add_argument("--max-n", type=int, default=9)
    parser.add_argument("--depths", nargs="+", type=int, default=[1, 2])
    parser.add_argument(
        "--families",
        nargs="+",
        default=["aligned", "anti_aligned", "event_easy", "circuit_hard"],
    )
    arguments = parser.parse_args()
    if arguments.min_n > arguments.max_n:
        parser.error("--min-n must not exceed --max-n")

    rows = []
    started_all = perf_counter()
    global_reduction_controls = run_global_reduction_controls()
    if not global_reduction_controls["passed"]:
        raise AssertionError("explicit global tensor reduction control failed")
    for n in range(arguments.min_n, arguments.max_n + 1):
        for depth in arguments.depths:
            for family in arguments.families:
                instance = synthetic_instance(family, n=n, depth=depth)
                tables = build_structural_tables(instance.event, instance.graph)
                started = perf_counter()
                searches = {
                    objective: exhaustive_permutation_search(
                        instance.event,
                        instance.graph,
                        depth,
                        objective=objective,
                        tables=tables,
                    )
                    for objective in ("event", "circuit", "joint")
                }
                exhaustive_audit = independent_exhaustive_audit(
                    tables, depth, searches
                )
                if not exhaustive_audit["passed"]:
                    raise AssertionError(
                        f"independent exhaustive audit failed for {family}, "
                        f"n={n}, p={depth}"
                    )
                headroom = tie_aware_headroom(exhaustive_audit)
                joint_order = searches["joint"].retained_optimal_orders[0]
                event_order = tuple(
                    exhaustive_audit["event_optimal_set"]["best_joint_order"]
                )
                circuit_order = tuple(
                    exhaustive_audit["circuit_optimal_set"]["best_joint_order"]
                )
                profiles = {
                    "event_optimum_order": order_profile(
                        instance.event, instance.graph, depth, event_order, tables=tables
                    ),
                    "circuit_optimum_order": order_profile(
                        instance.event,
                        instance.graph,
                        depth,
                        circuit_order,
                        tables=tables,
                    ),
                    "joint_optimum_order": order_profile(
                        instance.event, instance.graph, depth, joint_order, tables=tables
                    ),
                }
                collapse = audit_joint_rank_collapse(
                    instance.event, instance.graph, depth, joint_order
                )
                row = {
                    "family": family,
                    "n": n,
                    "depth": depth,
                    "support_size": len(instance.event.support),
                    "permutations_expected": factorial_permutation_count(n),
                    "searches": {key: asdict(value) for key, value in searches.items()},
                    "exhaustive_audit": exhaustive_audit,
                    "profiles": {key: asdict(value) for key, value in profiles.items()},
                    "profile_selection": {
                        "event_optimum_order": (
                            "lowest-J order in the complete event-optimal set"
                        ),
                        "circuit_optimum_order": (
                            "lowest-J order in the complete circuit-optimal set"
                        ),
                        "joint_optimum_order": "first retained global J optimum",
                    },
                    "headroom": headroom,
                    "best_one_sided_over_joint": headroom["ratio"],
                    "collapse": {
                        "passed": collapse.passed,
                        "identity": "rank(E_cut tensor I_q) = rank(E_cut) * q",
                        "scope": (
                            "per-cut implicit proxy witness only; I_q is not an "
                            "actual circuit unfolding and the witnesses are not "
                            "one globally consistent tensor"
                        ),
                        "cuts": len(collapse.cuts),
                        "explicit_checks": collapse.explicit_checks,
                        "explicit_checks_skipped": (
                            len(collapse.cuts) - collapse.explicit_checks
                        ),
                    },
                    "seconds": perf_counter() - started,
                }
                rows.append(row)
                print(
                    family,
                    f"n={n}",
                    f"p={depth}",
                    f"headroom={headroom['ratio']:.4g}",
                    f"collapse={collapse.passed}",
                    flush=True,
                )

    payload = {
        "schema_version": 3,
        "stage": "event_conditioned_width_natural_proxy_falsification",
        "created_at": utc_now(),
        "natural_proxy": "max_cut event_rank(S) * 2^(2*p*crossing_edges_G(S))",
        "candidate_claim": "natural joint event/circuit sweep width is new",
        "global_reduction": {
            "tensor": (
                "T = E(x) tensor product over edges e={u,v} and copies "
                "c=1..2p of 1[z_(u,e,c)=z_(v,e,c)], with all local variables "
                "grouped by graph site"
            ),
            "lemma": GLOBAL_REDUCTION_LEMMA,
            "proof": GLOBAL_REDUCTION_PROOF,
            "explicit_full_tensor_controls": global_reduction_controls,
        },
        "binding_verdict": binding_verdict(rows, global_reduction_controls),
        "row_count": len(rows),
        "elapsed_seconds": perf_counter() - started_all,
        "rows": rows,
    }
    atomic_json(RESULTS / "natural_proxy_falsification.json", payload)
    print(json.dumps(payload["binding_verdict"], indent=2))


if __name__ == "__main__":
    main()
