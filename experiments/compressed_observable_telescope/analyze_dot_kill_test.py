"""Aggregate the frozen DOT local test and exploratory cut sensitivity sweep."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULTS = REPO / "results" / "dot_mps_kill_test"
CUTS = tuple(range(6, 13))


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_text(path: Path, text: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def main() -> None:
    rows = {
        cut: read(RESULTS / f"ibm32_confirm_sorted_lr_position502_cut{cut}.json")
        for cut in CUTS
    }
    primary = rows[11]
    primary_rank = next(row for row in primary["rank_rows"] if row["chi"] == 40)
    sensitivity = []
    for cut, payload in rows.items():
        rank = next(row for row in payload["rank_rows"] if row["chi"] == 40)
        sensitivity.append({
            "cut": cut,
            "standard_bks_error": rank["standard_top_schmidt"]["absolute_bks_error"],
            "goal_aware_bks_error": rank["goal_aware_subset"]["absolute_bks_error"],
            "improvement_factor": rank["bks_error_improvement_factor"],
            "standard_fidelity": rank["standard_top_schmidt"]["state_fidelity"],
            "goal_aware_fidelity": rank["goal_aware_subset"]["state_fidelity"],
            "selected_mode_overlap": rank["selected_mode_overlap"],
            "mass_importance_spearman": payload["mode_diagnostics"][
                "schmidt_mass_vs_leave_one_decision_importance_spearman"
            ],
            "tenfold_success": rank["goal_aware_subset"]["absolute_bks_error"]
            <= rank["standard_top_schmidt"]["absolute_bks_error"] / 10,
        })
    summary = {
        "stage": "dot_mps_local_kill_test_summary",
        "complete": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "protocol_primary_passed": primary["primary_success"],
        "primary_cut": 11,
        "primary_chi": 40,
        "primary_standard_bks_error": primary_rank["standard_top_schmidt"]["absolute_bks_error"],
        "primary_goal_aware_bks_error": primary_rank["goal_aware_subset"]["absolute_bks_error"],
        "primary_improvement_factor": primary_rank["bks_error_improvement_factor"],
        "primary_standard_fidelity": primary_rank["standard_top_schmidt"]["state_fidelity"],
        "primary_goal_aware_fidelity": primary_rank["goal_aware_subset"]["state_fidelity"],
        "primary_mass_importance_spearman": primary["mode_diagnostics"][
            "schmidt_mass_vs_leave_one_decision_importance_spearman"
        ],
        "actual_aer_checkpoint_bks_error": primary["actual_aer_local_bks_error"],
        "maximum_exploratory_improvement_factor_chi40": max(
            row["improvement_factor"] for row in sensitivity
        ),
        "minimum_exploratory_mass_importance_spearman": min(
            row["mass_importance_spearman"] for row in sensitivity
        ),
        "exploratory_tenfold_successes": sum(row["tenfold_success"] for row in sensitivity),
        "sensitivity_rows": sensitivity,
        "verdict": (
            "The frozen Schmidt-subset DOT endpoint fails: top-Schmidt and decision "
            "importance are nearly aligned at the diagnosed real checkpoint. Do not "
            "implement a DOT-MPS simulator from this evidence."
        ),
    }
    atomic_text(RESULTS / "summary.json", json.dumps(summary, indent=2) + "\n")

    lines = "\n".join(
        f"| {row['cut']} | {row['standard_bks_error']:.3e} | "
        f"{row['goal_aware_bks_error']:.3e} | {row['improvement_factor']:.3f}x | "
        f"{row['mass_importance_spearman']:.5f} | {row['selected_mode_overlap']}/40 |"
        for row in sensitivity
    )
    report = f"""# DOT-MPS local kill-test

## Verdict

The prespecified decision-optimal Schmidt-subset test **failed**. On the real
`ibm32/confirm/sorted` LR checkpoint 502, cut 11, and rank 40, top-Schmidt has
BKS error `{summary['primary_standard_bks_error']:.6e}` and the best constructed
goal-aware subset has `{summary['primary_goal_aware_bks_error']:.6e}`: only
`{summary['primary_improvement_factor']:.3f}x` improvement, far below the frozen
10x success threshold.

The goal-aware subset has slightly worse fidelity
(`{summary['primary_goal_aware_fidelity']:.9f}` versus
`{summary['primary_standard_fidelity']:.9f}`), but the decision gain is only
about 1.9%. This is not the proposed killer result.

## Why the negative result is informative

The Spearman correlation between Schmidt mass and leave-one-mode BKS importance
is `{summary['primary_mass_importance_spearman']:.6f}`. Standard state-mass and
decision-importance rankings are therefore almost identical at this diagnosed
checkpoint. The selected subsets overlap in 39 of 40 modes.

The actual frozen Aer checkpoint BKS change is
`{summary['actual_aer_checkpoint_bks_error']:.6e}`, larger than either isolated
single-cut approximation error because the logical Aer transition contains
multiple internal swap/SVD truncations. The local test does not reproduce the
entire multi-truncation update.

## Exploratory neighboring-cut sensitivity

This sweep was performed only after the frozen cut-11 endpoint failed and is
labelled exploratory.

| Cut | Top-Schmidt error | Goal-aware error | Improvement | Spearman | Mode overlap |
|---:|---:|---:|---:|---:|---:|
{lines}

No cut reaches the 10x criterion. The largest improvement is
`{summary['maximum_exploratory_improvement_factor_chi40']:.3f}x`; all mass versus
decision-importance correlations exceed
`{summary['minimum_exploratory_mass_importance_spearman']:.5f}`.

## Conceptual issue with the unconstrained DOT objective

Minimizing only

`|<psi|O|psi> - <phi|O|phi>|`

over low-Schmidt-rank `phi` does not require `phi` to remain a useful
approximation to `psi`. A low-rank state can match one scalar while destroying
other observables, phases needed by later gates, or the next truncation step.
Consequently the unconstrained arbitrary-subspace objective can be degenerate.

A defensible successor would instead solve a constrained or regularized
problem, for example:

`maximize fidelity(psi,phi) subject to |J(psi)-J(phi)| <= epsilon`,

or

`minimize ||psi-phi||^2 + lambda |J(psi)-J(phi)|^2`,

using multiple future observables or a residual subspace rather than one scalar.
Such a formulation requires a new theorem and a new frozen test; it is not
supported by the present subset result.

## Decision

Do not build a custom DOT-MPS simulator yet. Retain COT as a diagnostic, report
this negative result, and only revisit goal-aware truncation after formulating a
non-degenerate constrained primitive or finding a checkpoint where Schmidt mass
and decision importance demonstrably separate.
"""
    atomic_text(RESULTS / "REPORT.md", report)

    sources = [
        HERE / "DOT_KILL_TEST_PROTOCOL.md",
        HERE / "run_dot_kill_test.py",
        HERE / "analyze_dot_kill_test.py",
    ]
    artifacts = [
        RESULTS / f"ibm32_confirm_sorted_lr_position502_cut{cut}.json"
        for cut in CUTS
    ] + [RESULTS / "summary.json", RESULTS / "REPORT.md"]
    manifest = {
        "stage": "dot_mps_local_kill_test_manifest",
        "complete": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sources": {
            str(path.relative_to(REPO)).replace("\\", "/"): {
                "bytes": path.stat().st_size, "sha256": sha256(path)
            } for path in sources
        },
        "artifacts": {
            str(path.relative_to(REPO)).replace("\\", "/"): {
                "bytes": path.stat().st_size, "sha256": sha256(path)
            } for path in artifacts
        },
    }
    atomic_text(RESULTS / "MANIFEST.json", json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({
        "protocol_primary_passed": summary["protocol_primary_passed"],
        "primary_improvement_factor": summary["primary_improvement_factor"],
        "maximum_exploratory_improvement_factor_chi40": summary[
            "maximum_exploratory_improvement_factor_chi40"
        ],
        "minimum_exploratory_mass_importance_spearman": summary[
            "minimum_exploratory_mass_importance_spearman"
        ],
    }, indent=2))


if __name__ == "__main__":
    main()
