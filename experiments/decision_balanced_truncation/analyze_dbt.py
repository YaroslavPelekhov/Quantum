"""Build the decision-balanced truncation verdict and integrity manifest."""

from __future__ import annotations

import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULTS = REPO / "results" / "decision_balanced_truncation"
sys.path.insert(0, str(REPO / "experiments" / "contrastive_tensor_simulation"))

from contrastive_core import atomic_json, sha256


def read(name: str) -> dict:
    payload = json.loads((RESULTS / name).read_text(encoding="utf-8"))
    if not payload.get("complete"):
        raise AssertionError(f"Incomplete: {name}")
    return payload


def main() -> None:
    fixed = read("prospective.json")
    adaptive = read("adaptive_exploratory.json")
    transfer = read("adaptive_transfer.json")
    if fixed["success"] or fixed["passed_rows"] != 3:
        raise AssertionError("Unexpected fixed-rank verdict")
    if adaptive["candidate_better_rows"] != 6 or adaptive["candidate_correct_rows"] != 6:
        raise AssertionError("Unexpected adaptive exploratory result")
    if transfer["success"] or transfer["passed_rows"] != 3:
        raise AssertionError("Unexpected held-out transfer verdict")

    fixed_wrong = sum(not row["methods"]["decision_balanced"]["sign_correct"] for row in fixed["rows"])
    transfer_correct = sum(row["candidate_sign_correct"] for row in transfer["rows"])
    transfer_factors = [row["error_improvement_factor"] for row in transfer["rows"]]
    lines = [
        "# Decision-balanced truncation report",
        "",
        "## Verdict",
        "",
        "The universal end-to-end claim is **closed**. Decision-balanced",
        "Petrov--Galerkin truncation is promising on the development schedule",
        "pair but does not transfer uniformly to a held-out schedule pair.",
        "",
        "## Frozen fixed-rank prospective test",
        "",
        f"- Passed rows: `{fixed['passed_rows']}/6`.",
        f"- Wrong candidate signs: `{fixed_wrong}/6`.",
        "- Result: fixed cut-4/rank-2 balancing is unstable and fails the",
        "  prespecified universal criterion.",
        "",
        "## Equal-work adaptive exploration",
        "",
        "The smallest rank in 1..8 retaining 99% of squared Hankel singular",
        "energy was selected at every gate. The state-averaged baseline received",
        "the identical rank schedule.",
        "",
        f"- Lower error: `{adaptive['candidate_better_rows']}/6`.",
        f"- Correct signs: `{adaptive['candidate_correct_rows']}/6`.",
        "- Typical mean retained rank: 1.5--2.6.",
        "",
        "This is a positive development-set result, not validation.",
        "",
        "## Frozen held-out schedule-pair transfer",
        "",
        "| case | ordering | exact Delta | DBT error | matched baseline error | factor | pass |",
        "|---|---|---:|---:|---:|---:|:---:|",
    ]
    for row in transfer["rows"]:
        lines.append(
            f"| {row['case']} | {row['ordering']} | {row['exact_delta']:+.6f} | "
            f"{row['candidate_error']:.6f} | {row['baseline_error']:.6f} | "
            f"{row['error_improvement_factor']:.2f}x | {'yes' if row['pass'] else 'no'} |"
        )
    lines.extend([
        "",
        f"The candidate preserves the correct sign on `{transfer_correct}/6` rows,",
        f"but lowers error on only `{transfer['passed_rows']}/6`. Observed held-out",
        f"factors range from `{min(transfer_factors):.2f}x` to `{max(transfer_factors):.2f}x`.",
        "The strict 6/6 criterion fails, so no threshold retuning is allowed.",
        "",
        "## Scientific conclusion",
        "",
        "Backward decision environments are genuinely informative: they rescue",
        "some wrong signs and can beat fidelity-oriented bases at identical rank",
        "schedules. But a local Hankel-energy criterion is not sufficient to",
        "control nonlinear error after repeated projection and renormalization.",
        "A publishable end-to-end successor needs a propagated decision-error",
        "certificate or a globally optimized contraction, not another local",
        "rank threshold.",
        "",
        "The dense backward-vector implementation is an oracle and carries no",
        "scalability claim.",
        "",
    ])
    report = RESULTS / "REPORT.md"
    report.write_text("\n".join(lines), encoding="utf-8", newline="\n")

    tracked = [
        HERE / "PROTOCOL.md", HERE / "ADAPTIVE_TRANSFER_PROTOCOL.md",
        HERE / "dbt_core.py", HERE / "run_prospective.py",
        HERE / "run_adaptive_exploratory.py", HERE / "run_adaptive_transfer.py",
        HERE / "analyze_dbt.py", HERE / "test_dbt.py", HERE / "README.md",
        RESULTS / "prospective.json", RESULTS / "adaptive_exploratory.json",
        RESULTS / "adaptive_transfer.json", report,
    ]
    manifest = {
        "complete": True,
        "fixed_rank_success": False,
        "adaptive_transfer_success": False,
        "files": {str(path.relative_to(REPO)): sha256(path) for path in tracked},
    }
    atomic_json(RESULTS / "manifest.json", manifest)
    print(json.dumps({
        "report": str(report),
        "manifest_entries": len(tracked),
        "heldout_passed": transfer["passed_rows"],
    }, indent=2))


if __name__ == "__main__":
    main()
