"""Build the GDBC development verdict and integrity manifest."""

from __future__ import annotations

import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULTS = REPO / "results" / "global_decision_balanced_contraction"
sys.path.insert(0, str(REPO / "experiments" / "contrastive_tensor_simulation"))

from contrastive_core import atomic_json, sha256


def main() -> None:
    development_path = RESULTS / "development.json"
    development = json.loads(development_path.read_text(encoding="utf-8"))
    if not development.get("complete"):
        raise AssertionError("Incomplete development result")
    if development.get("success") or development.get("passed_rows") != 2:
        raise AssertionError("Unexpected GDBC development verdict")
    if (RESULTS / "transfer.json").exists():
        raise AssertionError("Held-out transfer must not run after development failure")

    rows = development["rows"]
    candidate_better = sum(row["candidate_better"] for row in rows)
    candidate_correct = sum(
        row["methods"]["global_balanced"]["sign_correct"] for row in rows
    )
    baseline_correct = sum(
        row["methods"]["orthogonal_baseline"]["sign_correct"] for row in rows
    )
    factors = [row["error_improvement_factor"] for row in rows]
    candidate_norms = [
        row["methods"]["global_balanced"][key]
        for row in rows
        for key in ("final_norm_a", "final_norm_b")
    ]
    max_biorthogonality_error = max(
        row["methods"]["global_balanced"]["maximum_biorthogonality_error"]
        for row in rows
    )
    fallbacks = sum(
        row["methods"]["global_balanced"]["fallback_count"] for row in rows
    )

    lines = [
        "# Global decision-balanced contraction report",
        "",
        "## Verdict",
        "",
        "The prespecified development claim is **closed**. A single linear",
        "two-pass Petrov--Galerkin contraction does not reliably preserve the",
        "paired BKS decision, even when its bases use exact forward and backward",
        "dense Gramians. The held-out schedule pair was not run.",
        "",
        "## Frozen equal-rank development test",
        "",
        "| case | ordering | exact Delta | GDBC error | orthogonal error | factor | sign | pass |",
        "|---|---|---:|---:|---:|---:|:---:|:---:|",
    ]
    for row in rows:
        candidate = row["methods"]["global_balanced"]
        baseline = row["methods"]["orthogonal_baseline"]
        lines.append(
            f"| {row['case']} | {row['ordering']} | {row['exact_delta']:+.6f} | "
            f"{candidate['absolute_error']:.6f} | {baseline['absolute_error']:.6f} | "
            f"{row['error_improvement_factor']:.2f}x | "
            f"{'yes' if candidate['sign_correct'] else 'no'} | "
            f"{'yes' if row['candidate_pass'] else 'no'} |"
        )
    lines.extend([
        "",
        f"- Strict passes: `{development['passed_rows']}/6` (required `6/6`).",
        f"- Lower absolute error: `{candidate_better}/6`.",
        f"- Correct candidate signs: `{candidate_correct}/6`; equal-rank orthogonal control: `{baseline_correct}/6`.",
        f"- Error factors: `{min(factors):.2f}x` to `{max(factors):.2f}x`.",
        f"- Candidate final-state norms: `{min(candidate_norms):.3f}` to `{max(candidate_norms):.3f}`.",
        f"- Maximum biorthogonality error: `{max_biorthogonality_error:.2e}`; fallbacks: `{fallbacks}`.",
        "",
        "The last diagnostic rules out numerical loss of biorthogonality as the",
        "explanation. Instead, many individually aggressive low-rank maps compose",
        "into severe loss of state mass. Using a globally linear recurrence removes",
        "the earlier normalization feedback, but it does not remove accumulated",
        "projection bias or guarantee the sign of a small probability difference.",
        "",
        "## Claim boundary",
        "",
        "This experiment supports a negative result only: exact local forward/backward",
        "Gramians plus a 99% local Hankel-energy rule are insufficient for a universal",
        "end-to-end paired-decision advantage. Because development failed, running the",
        "frozen `prior_evolutionary` held-out pair would not be confirmatory and was",
        "forbidden by the protocol.",
        "",
        "The implementation is an exact dense feasibility oracle, not a scalable",
        "algorithm. The remaining positive result in this research line is the local",
        "signed reduced-density truncation primitive and its trace-norm certificate;",
        "no end-to-end universal superiority claim survives.",
        "",
    ])
    report = RESULTS / "REPORT.md"
    report.write_text("\n".join(lines), encoding="utf-8", newline="\n")

    tracked = [
        HERE / "PROTOCOL.md",
        HERE / "gdbc_core.py",
        HERE / "run_gdbc.py",
        HERE / "analyze_gdbc.py",
        HERE / "test_gdbc.py",
        HERE / "README.md",
        development_path,
        report,
    ]
    manifest = {
        "complete": True,
        "development_success": False,
        "development_passed_rows": development["passed_rows"],
        "transfer_promoted": False,
        "files": {str(path.relative_to(REPO)): sha256(path) for path in tracked},
    }
    atomic_json(RESULTS / "manifest.json", manifest)
    print(json.dumps({
        "report": str(report),
        "manifest_entries": len(tracked),
        "development_passed": development["passed_rows"],
        "transfer_promoted": False,
    }, indent=2))


if __name__ == "__main__":
    main()
