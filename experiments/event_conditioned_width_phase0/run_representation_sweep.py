"""Aggregate the Phase-0 development representation/path-cost screen.

This runner intentionally remains a cheap, dense, shape-only falsification
screen.  It never contracts the tensor networks.  The fixed development matrix
covers path, cycle, star, and seeded random graphs for n=5..8 and QAOA p=1..2.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import platform
import statistics
import sys
from time import perf_counter
from typing import Iterable, Sequence

import networkx as nx

from representation_screen import run_representation_screen


REPO = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = (
    REPO
    / "results"
    / "event_conditioned_width_phase0"
    / "development_representation_sweep.json"
)
GRAPH_FAMILIES = ("path", "cycle", "star", "random")
QUBIT_COUNTS = (5, 6, 7, 8)
QAOA_DEPTHS = (1, 2)
RANDOM_GRAPH_SEEDS = (260902, 260903, 260904)
OPTIMIZER_SEED = 260921


LIMITATIONS = (
    "The path optimizer sees only dense tensor shapes and mode incidences; it "
    "does not see coefficients, zeros, Boolean semantics, or algebraic cancellations.",
    "COPY tensors, diagonal QAOA gates, and diagonal MPO physical legs are costed "
    "as dense tensors, so sparse or structure-aware executors can change the ranking.",
    "The estimate is scalar arithmetic plus peak element count, not GPU/CPU wall "
    "time; kernel fusion, slicing, parallelism, memory traffic, and compilation are absent.",
    "No numerical contraction is executed and no probability or amplitude is computed.",
    "The support MPO is allowed to start from an explicitly enumerated exact support; "
    "support-enumeration and TT-compilation costs are excluded, while the local factor "
    "encoding does not require the support list.",
    "Shape-greedy is a reproducible heuristic, not a certificate of the globally "
    "optimal contraction path.",
    "Only small n=5..8 development instances are covered; ratios must not be "
    "extrapolated as asymptotic separations.",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def case_matrix() -> tuple[dict, ...]:
    """Return the immutable 48-case development matrix."""
    cases = []
    for family in GRAPH_FAMILIES:
        seeds: tuple[int | None, ...] = (
            RANDOM_GRAPH_SEEDS if family == "random" else (None,)
        )
        for graph_seed in seeds:
            for qubits in QUBIT_COUNTS:
                for depth in QAOA_DEPTHS:
                    seed_part = "" if graph_seed is None else f"_s{graph_seed}"
                    cases.append(
                        {
                            "case_id": f"{family}{seed_part}_n{qubits:02d}_p{depth}",
                            "family": family,
                            "graph_seed": graph_seed,
                            "qubits": qubits,
                            "depth": depth,
                        }
                    )
    return tuple(cases)


def build_graph(family: str, qubits: int, graph_seed: int | None) -> nx.Graph:
    if family == "path":
        return nx.path_graph(qubits)
    if family == "cycle":
        return nx.cycle_graph(qubits)
    if family == "star":
        return nx.star_graph(qubits - 1)
    if family != "random" or graph_seed is None:
        raise ValueError((family, graph_seed))
    graph = nx.gnp_random_graph(qubits, 0.35, seed=graph_seed)
    if not nx.is_connected(graph):
        components = [
            sorted(component) for component in nx.connected_components(graph)
        ]
        for left, right in zip(components, components[1:], strict=False):
            graph.add_edge(left[0], right[0])
    return graph


def _ratio_summary(values: Iterable[float]) -> dict:
    rows = tuple(float(value) for value in values)
    if not rows or any(value <= 0 or not math.isfinite(value) for value in rows):
        raise ValueError("ratio summary requires finite positive values")
    return {
        "count": len(rows),
        "geometric_mean": math.exp(sum(math.log(value) for value in rows) / len(rows)),
        "median": statistics.median(rows),
        "minimum": min(rows),
        "maximum": max(rows),
    }


def _winner_counts(ratios: Sequence[float]) -> dict:
    tolerance = 1e-12
    return {
        "rank_minimal_support_mpo": sum(value > 1.0 + tolerance for value in ratios),
        "local_mis_plus_cardinality": sum(value < 1.0 - tolerance for value in ratios),
        "ties": sum(abs(value - 1.0) <= tolerance for value in ratios),
    }


def _paired_order_rows(case: dict) -> list[dict]:
    groups: dict[str, dict[str, dict]] = {}
    for row in case["screen"]["rows"]:
        groups.setdefault(row["order_name"], {})[row["representation"]] = row
    comparisons = []
    for order_name, representations in sorted(groups.items()):
        tt = representations["rank_minimal_support_mpo"]
        local = representations["local_mis_plus_cardinality"]
        comparisons.append(
            {
                "case_id": case["case_id"],
                "family": case["family"],
                "qubits": case["qubits"],
                "depth": case["depth"],
                "graph_seed": case["graph_seed"],
                "order_name": order_name,
                "order": tt["order"],
                "local_over_tt_flops": (
                    local["path"]["estimated_flops"]
                    / tt["path"]["estimated_flops"]
                ),
                "local_over_tt_peak_elements": (
                    local["path"]["peak_elements"]
                    / tt["path"]["peak_elements"]
                ),
                "tt_flops": tt["path"]["estimated_flops"],
                "local_flops": local["path"]["estimated_flops"],
                "tt_peak_elements": tt["path"]["peak_elements"],
                "local_peak_elements": local["path"]["peak_elements"],
                "tt_event_max_bond_rank": tt["event_max_bond_rank"],
                "local_cardinality_max_bond_rank": local["event_max_bond_rank"],
            }
        )
    return comparisons


def _best_representation_rows(case: dict) -> dict:
    by_representation = {}
    for representation in (
        "rank_minimal_support_mpo",
        "local_mis_plus_cardinality",
    ):
        candidates = [
            row
            for row in case["screen"]["rows"]
            if row["representation"] == representation
        ]
        by_representation[representation] = min(
            candidates,
            key=lambda row: (
                row["path"]["estimated_flops"],
                row["path"]["peak_elements"],
            ),
        )
    tt = by_representation["rank_minimal_support_mpo"]
    local = by_representation["local_mis_plus_cardinality"]
    return {
        "case_id": case["case_id"],
        "family": case["family"],
        "qubits": case["qubits"],
        "depth": case["depth"],
        "graph_seed": case["graph_seed"],
        "tt_best_order_name": tt["order_name"],
        "tt_best_order": tt["order"],
        "local_best_order_name": local["order_name"],
        "local_best_order": local["order"],
        "tt_best_flops": tt["path"]["estimated_flops"],
        "local_best_flops": local["path"]["estimated_flops"],
        "local_over_tt_best_flops": (
            local["path"]["estimated_flops"] / tt["path"]["estimated_flops"]
        ),
        "tt_best_peak_elements": tt["path"]["peak_elements"],
        "local_best_peak_elements": local["path"]["peak_elements"],
        "local_over_tt_best_peak_elements": (
            local["path"]["peak_elements"] / tt["path"]["peak_elements"]
        ),
    }


def _group_summary(rows: Sequence[dict], field: str, group_field: str) -> dict:
    groups: dict[str, list[float]] = {}
    for row in rows:
        key = str(row[group_field])
        groups.setdefault(key, []).append(float(row[field]))
    return {key: _ratio_summary(values) for key, values in sorted(groups.items())}


def summarize_cases(cases: Sequence[dict]) -> dict:
    paired = [comparison for case in cases for comparison in _paired_order_rows(case)]
    best = [_best_representation_rows(case) for case in cases]
    paired_flops = [row["local_over_tt_flops"] for row in paired]
    paired_peak = [row["local_over_tt_peak_elements"] for row in paired]
    best_flops = [row["local_over_tt_best_flops"] for row in best]
    best_peak = [row["local_over_tt_best_peak_elements"] for row in best]
    if not cases:
        return {
            "case_count": 0,
            "paired_order_comparison_count": 0,
            "all_semantic_audits_passed": True,
            "paired_order_comparisons": [],
            "best_per_representation_by_case": [],
        }
    all_audits_passed = all(
        audit["passed"]
        for case in cases
        for audit in case["screen"]["semantic_audits"]
    )
    return {
        "case_count": len(cases),
        "paired_order_comparison_count": len(paired),
        "all_semantic_audits_passed": all_audits_passed,
        "ratio_definition": (
            "local_mis_plus_cardinality / rank_minimal_support_mpo; values above "
            "one favor the support MPO under this dense shape-only model"
        ),
        "paired_order_flop_ratio": _ratio_summary(paired_flops),
        "paired_order_peak_ratio": _ratio_summary(paired_peak),
        "paired_order_flop_winners": _winner_counts(paired_flops),
        "paired_order_peak_winners": _winner_counts(paired_peak),
        "best_order_per_representation_flop_ratio": _ratio_summary(best_flops),
        "best_order_per_representation_peak_ratio": _ratio_summary(best_peak),
        "best_order_flop_winners": _winner_counts(best_flops),
        "best_order_peak_winners": _winner_counts(best_peak),
        "best_flop_ratio_by_family": _group_summary(
            best, "local_over_tt_best_flops", "family"
        ),
        "best_flop_ratio_by_qubits": _group_summary(
            best, "local_over_tt_best_flops", "qubits"
        ),
        "best_flop_ratio_by_depth": _group_summary(
            best, "local_over_tt_best_flops", "depth"
        ),
        "paired_order_comparisons": paired,
        "best_per_representation_by_case": best,
    }


def _base_payload(
    *, backend: str, trials: int, optimizer_seed: int, started_at: str
) -> dict:
    return {
        "schema_version": 1,
        "stage": "event_conditioned_width_phase0_development_representation_sweep",
        "started_at": started_at,
        "complete": False,
        "development_matrix": {
            "graph_families": list(GRAPH_FAMILIES),
            "qubit_counts": list(QUBIT_COUNTS),
            "qaoa_depths": list(QAOA_DEPTHS),
            "random_graph_seeds": list(RANDOM_GRAPH_SEEDS),
            "case_count": len(case_matrix()),
        },
        "optimizer": {
            "backend": backend,
            "trials": trials,
            "seed": optimizer_seed,
            "shape_only": True,
            "performs_contraction": False,
        },
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "networkx": nx.__version__,
        },
        "limitations": list(LIMITATIONS),
        "cases": [],
        "summary": summarize_cases([]),
    }


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def run_sweep(
    *,
    output: Path = DEFAULT_OUTPUT,
    backend: str = "shape-greedy",
    trials: int = 6,
    optimizer_seed: int = OPTIMIZER_SEED,
    resume: bool = False,
) -> dict:
    started_at = utc_now()
    payload = _base_payload(
        backend=backend,
        trials=trials,
        optimizer_seed=optimizer_seed,
        started_at=started_at,
    )
    if resume and output.exists():
        previous = json.loads(output.read_text(encoding="utf-8"))
        if previous.get("stage") != payload["stage"]:
            raise ValueError("existing output is not a representation sweep")
        if previous.get("development_matrix") != payload["development_matrix"]:
            raise ValueError("existing output uses a different development matrix")
        if previous.get("optimizer") != payload["optimizer"]:
            raise ValueError("existing output uses different optimizer settings")
        payload = previous
        payload["complete"] = False

    completed = {case["case_id"] for case in payload["cases"]}
    matrix = case_matrix()
    started = perf_counter()
    for index, specification in enumerate(matrix, start=1):
        if specification["case_id"] in completed:
            continue
        graph = build_graph(
            specification["family"],
            specification["qubits"],
            specification["graph_seed"],
        )
        case_started = perf_counter()
        screen = run_representation_screen(
            graph,
            depth=specification["depth"],
            backend=backend,
            trials=trials,
            seed=optimizer_seed,
        )
        case = {
            **specification,
            "elapsed_seconds": perf_counter() - case_started,
            "screen": screen,
        }
        payload["cases"].append(case)
        payload["summary"] = summarize_cases(payload["cases"])
        payload["updated_at"] = utc_now()
        atomic_json(output, payload)
        best = payload["summary"]["best_per_representation_by_case"][-1]
        print(
            f"[{index:02d}/{len(matrix)}] {specification['case_id']} "
            f"local/TT flops={best['local_over_tt_best_flops']:.4g} "
            f"peak={best['local_over_tt_best_peak_elements']:.4g} "
            f"sec={case['elapsed_seconds']:.2f}",
            flush=True,
        )

    payload["summary"] = summarize_cases(payload["cases"])
    payload["complete"] = len(payload["cases"]) == len(matrix)
    payload["completed_at"] = utc_now()
    payload["runner_elapsed_seconds"] = perf_counter() - started
    atomic_json(output, payload)
    return payload


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--backend",
        choices=("shape-greedy", "auto", "opt_einsum"),
        default="shape-greedy",
    )
    parser.add_argument("--trials", type=int, default=6)
    parser.add_argument("--optimizer-seed", type=int, default=OPTIMIZER_SEED)
    parser.add_argument("--resume", action="store_true")
    arguments = parser.parse_args(argv)
    payload = run_sweep(
        output=arguments.output,
        backend=arguments.backend,
        trials=arguments.trials,
        optimizer_seed=arguments.optimizer_seed,
        resume=arguments.resume,
    )
    summary = payload["summary"]
    print(
        json.dumps(
            {
                "complete": payload["complete"],
                "output": str(arguments.output),
                "case_count": summary["case_count"],
                "paired_order_flop_ratio": summary["paired_order_flop_ratio"],
                "best_order_per_representation_flop_ratio": summary[
                    "best_order_per_representation_flop_ratio"
                ],
                "best_order_flop_winners": summary["best_order_flop_winners"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if payload["complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
