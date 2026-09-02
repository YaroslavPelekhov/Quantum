"""Validate and freeze the completed Phase-0 falsification package."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULTS = REPO / "results" / "event_conditioned_width_phase0"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def structural_summary(payload: dict) -> dict:
    rows = payload["rows"]
    verdict = payload["binding_verdict"]
    if payload.get("schema_version") != 3 or len(rows) != 48:
        raise AssertionError("expected the complete 48-row schema-v3 structural run")
    if verdict.get("protocol_kill_gate") != "K6":
        raise AssertionError("the global reduction did not establish K6")
    if not verdict.get("global_site_grouped_tensor_reduction_established"):
        raise AssertionError("the single-tensor reduction is missing")
    if verdict.get("actual_circuit_unfolding_equivalence_established"):
        raise AssertionError("the proxy must not be identified with the QAOA tensor")
    if not all(row["exhaustive_audit"]["passed"] for row in rows):
        raise AssertionError("an independent exhaustive audit failed")
    if not all(row["collapse"]["passed"] for row in rows):
        raise AssertionError("a per-cut rank identity audit failed")
    ratios = [float(row["headroom"]["ratio"]) for row in rows]
    if any(abs(ratio - 1.0) > 1e-12 for ratio in ratios):
        raise AssertionError("the tie-aware development headroom is not uniformly one")
    independent_permutations = sum(
        int(row["exhaustive_audit"]["permutations_evaluated_independently"])
        for row in rows
    )
    optimizer_permutations = sum(
        int(search["permutations_evaluated"])
        for row in rows
        for search in row["searches"].values()
    )
    return {
        "rows": len(rows),
        "families": sorted({row["family"] for row in rows}),
        "qubit_range": [min(row["n"] for row in rows), max(row["n"] for row in rows)],
        "depths": sorted({row["depth"] for row in rows}),
        "independently_evaluated_permutations": independent_permutations,
        "optimizer_evaluated_permutations": optimizer_permutations,
        "tie_sensitive_rows": sum(
            bool(row["headroom"]["tie_break_sensitive"]) for row in rows
        ),
        "strict_joint_headroom_rows": sum(
            bool(row["headroom"]["strict_headroom"]) for row in rows
        ),
        "tie_aware_headroom_min": min(ratios),
        "tie_aware_headroom_max": max(ratios),
        "explicit_global_tensor_controls_passed": payload["global_reduction"]
        ["explicit_full_tensor_controls"]["passed"],
        "global_reduction": verdict[
            "natural_proxy_equals_linear_tt_rank_width_of_artificial_tensor"
        ],
        "actual_qaoa_unfolding_equivalence": verdict[
            "actual_circuit_unfolding_equivalence_established"
        ],
    }


def development_summary(payload: dict) -> dict:
    summary = payload["summary"]
    if not payload.get("complete") or len(payload["cases"]) != 48:
        raise AssertionError("development representation sweep is incomplete")
    if not summary["all_semantic_audits_passed"]:
        raise AssertionError("a development semantic audit failed")
    winners = summary["best_order_flop_winners"]
    if winners["rank_minimal_support_mpo"] != 48:
        raise AssertionError("expected the recorded 48/48 support-MPO wins")
    ratio = summary["best_order_per_representation_flop_ratio"]
    peak = summary["best_order_per_representation_peak_ratio"]
    return {
        "cases": len(payload["cases"]),
        "semantic_audits_passed": True,
        "optimizer": payload["optimizer"],
        "support_mpo_flop_wins": winners["rank_minimal_support_mpo"],
        "local_factor_flop_wins": winners["local_mis_plus_cardinality"],
        "local_over_support_mpo_flop_ratio": ratio,
        "local_over_support_mpo_peak_ratio": peak,
        "limitations": payload["limitations"],
    }


def real_path_summary(payload: dict) -> dict:
    rows = payload["rows"]
    expected = {
        (ordering, depth, representation)
        for ordering in ("spectral", "sorted")
        for depth in (1, 2, 3)
        for representation in ("minimal_mpo", "local_mis")
    }
    indexed = {
        (row["ordering"], int(row["qaoa_layers"]), row["representation"]): row
        for row in rows
    }
    if set(indexed) != expected or len(rows) != len(expected):
        raise AssertionError("expected exactly 12 real path-search rows")
    if not all(row["path_complete"] for row in rows):
        raise AssertionError("a real path search is incomplete")
    comparisons = []
    for ordering in ("spectral", "sorted"):
        for depth in (1, 2, 3):
            mpo = indexed[(ordering, depth, "minimal_mpo")]
            local = indexed[(ordering, depth, "local_mis")]
            ratio = float(local["opt_cost"]) / float(mpo["opt_cost"])
            comparisons.append(
                {
                    "ordering": ordering,
                    "depth": depth,
                    "minimal_mpo_opt_cost": float(mpo["opt_cost"]),
                    "local_mis_opt_cost": float(local["opt_cost"]),
                    "local_over_mpo_opt_cost": ratio,
                    "winner": "minimal_mpo" if ratio > 1 else "local_mis",
                }
            )
    best_by_depth = []
    for depth in (1, 2, 3):
        mpo = min(
            (
                indexed[(ordering, depth, "minimal_mpo")]
                for ordering in ("spectral", "sorted")
            ),
            key=lambda row: float(row["opt_cost"]),
        )
        local = min(
            (
                indexed[(ordering, depth, "local_mis")]
                for ordering in ("spectral", "sorted")
            ),
            key=lambda row: float(row["opt_cost"]),
        )
        best_by_depth.append(
            {
                "depth": depth,
                "best_mpo_ordering": mpo["ordering"],
                "best_local_ordering": local["ordering"],
                "best_local_over_best_mpo_opt_cost": (
                    float(local["opt_cost"]) / float(mpo["opt_cost"])
                ),
            }
        )
    return {
        "case": "es60fst02",
        "qubits": 55,
        "rows": len(rows),
        "path_search_only": payload["path_search_only"],
        "optimizer": payload["optimizer"],
        "paired_comparisons": comparisons,
        "best_tested_order_by_depth": best_by_depth,
        "confirmatory_status": "exploratory sentinel; excluded from locked counts",
    }


def build_decision() -> dict:
    structural = structural_summary(
        read_json(RESULTS / "natural_proxy_falsification.json")
    )
    development = development_summary(
        read_json(RESULTS / "development_representation_sweep.json")
    )
    real = real_path_summary(
        read_json(RESULTS / "real_qoblib_representation_paths.json")
    )
    not_evaluated = {
        "status": "NOT_EVALUATED",
        "reason": "the corresponding locked full-network study was not executed",
    }
    return {
        "schema_version": 1,
        "created_at": utc_now(),
        "protocol": "experiments/event_conditioned_width_phase0/PROTOCOL.md",
        "final_verdict": "INCOMPLETE_NO_PROMOTION",
        "program_scope": "the full registered event-conditioned-width Phase 0",
        "subclaim_verdicts": {
            "natural_product_proxy_as_new_width": {
                "verdict": "KILLED_AS_ASTAR_SOURCE",
                "kill_gate": "K6",
                "scope": (
                    "max_cut rank(E_cut)*2^(2*p*crossing_edges), not the "
                    "actual QAOA tensor and not every pair-dependent algorithm"
                ),
            }
        },
        "gate_status": {
            "K0": {
                "status": "NOT_TRIGGERED_IN_COMPLETED_CHECKS",
                "reason": "all completed semantic, rank, and path-completeness audits pass",
            },
            "K1": not_evaluated,
            "K2": not_evaluated,
            "K3": not_evaluated,
            "K4": not_evaluated,
            "K5": not_evaluated,
            "K6": {
                "status": "TRIGGERED_FOR_NATURAL_PROXY_ONLY",
                "reason": (
                    "the proxy is exactly the maximum prefix unfolding rank of "
                    "one site-grouped artificial tensor, hence an ordinary exact "
                    "linear TT-rank ordering objective"
                ),
            },
            "K7": {
                "status": "NOT_TRIGGERED",
                "reason": "the registered resource budget has not been exhausted",
            },
        },
        "promotion_gates": {
            name: {
                "status": "NOT_ESTABLISHED",
                "reason": "the registered locked full-network study was not executed",
            }
            for name in ("P0", "P1", "P2", "P3", "P4", "P5")
        },
        "evidence": {
            "structural": structural,
            "development_representation": development,
            "real_path_sentinel": real,
        },
        "scope_limits": {
            "actual_qaoa_circuit_width_theorem_established": False,
            "broader_algebraic_pair_dependent_algorithm_killed": False,
            "locked_holdout_opened": False,
            "qpu_jobs_submitted": 0,
            "hardware_claim": False,
        },
        "next_admissible_hypothesis": (
            "a pair-dependent algebraic mechanism using actual circuit amplitudes or "
            "cancellations, with an infinite separation from TT/BDD, augmented-TN, "
            "WMC/DD, and selected-amplitude baselines"
        ),
    }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_paths(real_payload: dict) -> list[Path]:
    paths = [
        path
        for root in (HERE, RESULTS)
        for path in root.rglob("*")
        if path.is_file()
        and path.name != "MANIFEST.json"
        and path.suffix not in {".pyc", ".tmp"}
        and "__pycache__" not in path.parts
    ]
    external = [
        REPO / "README.md",
        REPO / "experiments" / "exact_event_contraction" / "run_event_projector.py",
        REPO / "experiments" / "exact_event_contraction" / "run_exact_event_contraction.py",
        REPO / "results" / "exact_event_contraction" / "event_support.json",
        REPO / "results" / "exact_event_contraction" / "event_tt_es60fst02_sorted.npz",
        REPO / "results" / "exact_event_contraction" / "event_tt_es60fst02_spectral.npz",
        REPO / "results" / "exact_event_contraction" / "mpo_audit_es60fst02_sorted.json",
        REPO / "results" / "exact_event_contraction" / "mpo_audit_es60fst02_spectral.json",
        REPO
        / "experiments"
        / "evoq_mis_full_qoblib"
        / "results"
        / "cutensornet"
        / "export_manifest.json",
    ]
    external.extend(REPO / row["circuit"] for row in real_payload["rows"])
    for path in external:
        if not path.is_file():
            raise FileNotFoundError(path)
    return sorted(set(paths + external), key=lambda path: path.relative_to(REPO).as_posix())


def build_manifest() -> dict:
    real = read_json(RESULTS / "real_qoblib_representation_paths.json")
    files = {}
    for path in artifact_paths(real):
        relative = path.relative_to(REPO).as_posix()
        files[relative] = {"sha256": sha256(path), "bytes": path.stat().st_size}
    return {
        "schema_version": 1,
        "created_at": utc_now(),
        "root": ".",
        "exclusions": ["MANIFEST.json itself", "__pycache__", "*.pyc", "*.tmp"],
        "file_count": len(files),
        "files": files,
    }


def main() -> None:
    report = RESULTS / "FALSIFICATION_REPORT.md"
    if not report.is_file():
        raise FileNotFoundError(report)
    decision = build_decision()
    atomic_json(RESULTS / "PHASE0_DECISION.json", decision)
    atomic_json(RESULTS / "MANIFEST.json", build_manifest())
    natural = decision["subclaim_verdicts"]["natural_product_proxy_as_new_width"]
    print(decision["final_verdict"], natural["verdict"], natural["kill_gate"])
    print("manifest files", read_json(RESULTS / "MANIFEST.json")["file_count"])


if __name__ == "__main__":
    main()
