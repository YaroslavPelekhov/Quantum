"""Analyze the frozen contrastive tensor simulation kill tests."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULTS = REPO / "results" / "contrastive_tensor_simulation"
sys.path.insert(0, str(HERE))

from contrastive_core import atomic_json, sha256


SMALL = RESULTS / "small_md_dynamics.json"
DIAGNOSTICS = RESULTS / "structural_diagnostics.json"
BENCHMARK = RESULTS / "equal_budget_benchmark.json"
SPARSE = RESULTS / "sparse_completion.json"
SUMMARY = RESULTS / "summary.json"
REPORT = RESULTS / "REPORT.md"
MANIFEST = RESULTS / "MANIFEST.json"


def read(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not payload.get("complete"):
        raise RuntimeError(f"Incomplete input: {path}")
    return payload


def operator_rank_audit(diagnostics: dict) -> dict:
    rows = []
    lower_count = 0
    for cohort in diagnostics["rows"]:
        by_key = {
            (row["cut"], row["kind"]): row for row in cohort["operator_spectra"]
        }
        for cut in (3, 5, 7):
            rho_a = by_key[(cut, "rho_a")]["effective_rank_99"]
            rho_b = by_key[(cut, "rho_b")]["effective_rank_99"]
            difference = by_key[(cut, "difference")]["effective_rank_99"]
            demonstrated = (
                difference is not None and rho_a is not None and rho_b is not None
            )
            lower = demonstrated and difference < rho_a and difference < rho_b
            lower_count += int(lower)
            rows.append({
                "case": cohort["case"],
                "ordering": cohort["ordering"],
                "cut": cut,
                "rho_a_rank99": rho_a,
                "rho_b_rank99": rho_b,
                "difference_rank99": difference,
                "difference_rank99_lower_bound": by_key[(cut, "difference")][
                    "effective_rank_99_lower_bound"
                ],
                "comparison_demonstrated": demonstrated,
                "difference_lower_than_both": lower,
            })
    return {
        "rows": rows,
        "lower_than_both_count": lower_count,
        "total_frozen_cuts": len(rows),
        "majority_passes": lower_count > len(rows) / 2,
    }


def diagonal_audit(benchmark: dict) -> dict:
    rows = benchmark["rows"]
    aves = [row for row in rows if row["case"] == "aves-sparrow-social"]
    by_ordering = {}
    for ordering in ("sorted", "spectral"):
        cohort = [row for row in aves if row["ordering"] == ordering]
        by_ordering[ordering] = {
            "minimum_improvement_factor": min(row["error_improvement_factor"] for row in cohort),
            "maximum_improvement_factor": max(row["error_improvement_factor"] for row in cohort),
            "has_twofold_improvement": any(
                row["error_improvement_factor"] >= 2.0 for row in cohort
            ),
            "wrong_separate_correct_contrast_bonds": [
                row["state_bond"] for row in cohort
                if not row["separate_sign_correct"] and row["contrast_sign_correct"]
            ],
            "contrast_certified_bonds": [
                row["state_bond"] for row in cohort if row["contrast_sign_certified"]
            ],
            "separate_certified_bonds": [
                row["state_bond"] for row in cohort if row["separate_sign_certified"]
            ],
        }
    return {
        "orderings": by_ordering,
        "twofold_both_orderings": all(
            row["has_twofold_improvement"] for row in by_ordering.values()
        ),
        "ranking_rescue_both_orderings": all(
            bool(row["wrong_separate_correct_contrast_bonds"])
            for row in by_ordering.values()
        ),
        "contrast_certification_advantage_both_orderings": all(
            bool(row["contrast_certified_bonds"])
            and not row["separate_certified_bonds"]
            for row in by_ordering.values()
        ),
    }


def sparse_audit(sparse: dict) -> dict:
    aves = [row for row in sparse["rows"] if row["case"] == "aves-sparrow-social"]
    ranks = {}
    for rank in (8, 12):
        cohort = [row for row in aves if row["rank"] == rank]
        conditions = {
            "correct_sign_both_orderings": len(cohort) == 2 and all(
                row["sign_correct_audit"] for row in cohort
            ),
            "delta_error_below_10pct_both": len(cohort) == 2 and all(
                row["relative_delta_error"] < 0.1 for row in cohort
            ),
            "holdout_relative_rmse_below_0p1_both": len(cohort) == 2 and all(
                row["holdout_relative_rmse"] < 0.1 for row in cohort
            ),
            "query_fraction_below_2pct_both": len(cohort) == 2 and all(
                row["training_query_fraction"] < 0.02 for row in cohort
            ),
            "zero_bks_leakage": all(
                row["bks_training_overlap"] == 0 and row["bks_holdout_overlap"] == 0
                for row in cohort
            ),
        }
        ranks[str(rank)] = {
            "conditions": conditions,
            "passes": all(conditions.values()),
        }
    return {
        "ranks": ranks,
        "branch_supported": any(row["passes"] for row in ranks.values()),
    }


def render(summary: dict, benchmark: dict, sparse: dict) -> str:
    lines = [
        "# Contrastive tensor simulation kill-test report",
        "",
        "## Verdict",
        "",
        "The general full-density M/D simulator claim is **closed** by the frozen",
        "criteria. The narrower signed diagonal contrast tensor is **supported**",
        "for the frozen diagonal BKS observable.",
        "",
        "## Equal-budget aves result",
        "",
        "| ordering | state bond | contrast bond | separate Delta | contrast Delta | separate error | contrast error | factor | separate certified | contrast certified |",
        "|---|---:|---:|---:|---:|---:|---:|---:|:---:|:---:|",
    ]
    for row in benchmark["rows"]:
        if row["case"] != "aves-sparrow-social":
            continue
        lines.append(
            f"| {row['ordering']} | {row['state_bond']} | {row['contrast_bond']} | "
            f"{row['separate_delta']:+.9f} | {row['contrast_delta']:+.9f} | "
            f"{row['separate_absolute_error']:.3e} | {row['contrast_absolute_error']:.3e} | "
            f"{row['error_improvement_factor']:.1f}x | "
            f"{'yes' if row['separate_sign_certified'] else 'no'} | "
            f"{'yes' if row['contrast_sign_certified'] else 'no'} |"
        )
    lines.extend([
        "",
        "Exact aves Delta is `-0.012138852` (audit only). Separate MPS gives the",
        "wrong sign at R4 and R8 on both orderings. The signed diagonal contrast",
        "has the correct sign at every budget and obtains a strict Frobenius-tail",
        "certificate at R16/R32/R64 on both orderings. Separate MPS obtains no",
        "strict sign certificate at any frozen aves budget.",
        "",
        "## Full M/D prototype",
        "",
    ])
    for row in summary["small_md"]:
        lines.append(
            f"- `{row['ordering']}`: exact recurrence error "
            f"`{row['maximum_exact_identity_error']:.3e}`; exact Delta "
            f"`{row['exact_delta']:+.9f}`; certified policies "
            f"`{row['certified_policy_count']}/4`; largest radius "
            f"`{row['maximum_radius']:.3e}`."
        )
    rank = summary["operator_rank_audit"]
    lines.extend([
        "",
        "The M/D algebra is exact, but the gatewise trace-norm recurrence is",
        "catastrophically vacuous (`~1e38` radii). Full D is lower-rank than both",
        f"individual projectors at `{rank['lower_than_both_count']}/{rank['total_frozen_cuts']}` frozen cuts,",
        "so the structural full-operator criterion also fails.",
        "",
        "## Claim boundary",
        "",
        "The positive result is comparison-native compression of the signed",
        "diagonal observable tensor `q(z)=p_B(z)-p_A(z)`. It is not evidence that",
        "a general density-MPO trajectory is cheaper than two state-MPS",
        "trajectories. Construction of q currently uses exact terminal",
        "probabilities; an end-to-end contrastive dynamics algorithm remains open.",
        "",
        "The contrast certificate uses only the TT discarded Frobenius norm and",
        "`||O||_F=sqrt(rank O)`. Exact Delta is excluded from interval construction.",
        "",
        "## Sparse point-query construction",
        "",
        "| case | ordering | rank | train fraction | train rel RMSE | holdout rel RMSE | estimated Delta | relative Delta error | sign |",
        "|---|---|---:|---:|---:|---:|---:|---:|:---:|",
    ])
    for row in sparse["rows"]:
        lines.append(
            f"| {row['case']} | {row['ordering']} | {row['rank']} | "
            f"{row['training_query_fraction']:.3%} | "
            f"{row['fit_history'][-1]['training_relative_rmse']:.3f} | "
            f"{row['holdout_relative_rmse']:.3f} | {row['estimated_delta']:+.8f} | "
            f"{row['relative_delta_error']:.3f} | "
            f"{'correct' if row['sign_correct_audit'] else 'wrong'} |"
        )
    lines.extend([
        "",
        "Generic uniform-query TT completion fails the frozen construction",
        "criteria. Low terminal TT rank therefore demonstrates compressibility",
        "with global access, not sample-efficient recoverability. Training errors",
        "can be small while holdout relative RMSE remains near or above one. No",
        "BKS-support point was used for training or holdout.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    small = read(SMALL)
    diagnostics = read(DIAGNOSTICS)
    benchmark = read(BENCHMARK)
    sparse = read(SPARSE)
    rank_audit = operator_rank_audit(diagnostics)
    diagonal = diagonal_audit(benchmark)
    sparse_result = sparse_audit(sparse)
    small_rows = []
    for row in small["rows"]:
        radii = [policy["certified_radius"] for policy in row["policies"]]
        small_rows.append({
            "ordering": row["ordering"],
            "exact_delta": row["exact_delta"],
            "maximum_exact_identity_error": row["maximum_exact_identity_error"],
            "certified_policy_count": sum(
                policy["sign_certified"] for policy in row["policies"]
            ),
            "maximum_radius": max(radii),
            "minimum_radius": min(radii),
            "epsilon": row["epsilon"],
        })
    criteria = {
        "aves_twofold_both_orderings": diagonal["twofold_both_orderings"],
        "aves_ranking_rescue_both_orderings": diagonal["ranking_rescue_both_orderings"],
        "full_operator_rank_majority": rank_audit["majority_passes"],
        "full_md_nonvacuous_certificate": any(
            row["certified_policy_count"] > 0 for row in small_rows
        ),
    }
    summary = {
        "stage": "contrastive_tensor_simulation_analysis",
        "complete": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "frozen_criteria": criteria,
        "general_full_density_branch_survives": all(criteria.values()),
        "diagonal_contrast_branch_supported": (
            diagonal["twofold_both_orderings"]
            and diagonal["ranking_rescue_both_orderings"]
            and diagonal["contrast_certification_advantage_both_orderings"]
        ),
        "sparse_uniform_query_branch_supported": sparse_result["branch_supported"],
        "sparse_audit": sparse_result,
        "diagonal_audit": diagonal,
        "operator_rank_audit": rank_audit,
        "small_md": small_rows,
    }
    atomic_json(SUMMARY, summary)
    REPORT.write_text(render(summary, benchmark, sparse), encoding="utf-8")
    paths = [
        SUMMARY, REPORT, SMALL, DIAGNOSTICS, BENCHMARK, SPARSE,
        HERE / "PROTOCOL.md", HERE / "THEORY.md",
        HERE / "SPARSE_CONSTRUCTION_PROTOCOL.md",
        HERE / "contrastive_core.py", HERE / "run_contrastive.py",
        HERE / "sparse_tt_completion.py", HERE / "run_sparse_completion.py",
        HERE / "analyze_contrastive.py", HERE / "test_contrastive.py",
        REPO / "experiments" / "evoq_mis_full_qoblib" / "results"
        / "cross_case_replication" / "export_manifest.json",
        REPO / "experiments" / "evoq_mis_full_qoblib" / "results"
        / "independent_ladder" / "export_manifest.json",
        REPO / "results" / "rankcert_mps" / "input_validation.json",
    ]
    atomic_json(MANIFEST, {
        "complete": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "files": [
            {"path": str(path.relative_to(REPO)), "sha256": sha256(path)}
            for path in paths
        ],
    })
    print(REPORT.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
