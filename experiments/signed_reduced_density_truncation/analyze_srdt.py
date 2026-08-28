"""Validate the frozen SRDT output and build its report/manifest."""

from __future__ import annotations

import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULTS = REPO / "results" / "signed_reduced_density_truncation"
sys.path.insert(0, str(HERE))

from srdt_core import atomic_json, sha256


def main() -> None:
    benchmark_path = RESULTS / "benchmark.json"
    payload = json.loads(benchmark_path.read_text(encoding="utf-8"))
    if not payload.get("complete"):
        raise AssertionError("Benchmark is incomplete")
    heldout_path = RESULTS / "end_to_end_heldout.json"
    heldout = json.loads(heldout_path.read_text(encoding="utf-8"))
    if not heldout.get("complete") or heldout.get("success"):
        raise AssertionError("Unexpected end-to-end held-out verdict")

    all_rows = []
    transfer_rows = []
    for cohort in payload["real"]:
        for cut in cohort["cuts"]:
            for row in cut["rows"]:
                record = {
                    "case": cohort["case"],
                    "ordering": cohort["ordering"],
                    "cut": cut["cut"],
                    **row,
                }
                all_rows.append(record)
                if row["rank"] == 8 and cut["cut"] == 5:
                    transfer_rows.append(record)
                if row["signed_optimal_error"] > row["state_averaged_contrast_error"] + 2e-10:
                    raise AssertionError((cohort["case"], cohort["ordering"], cut["cut"], row["rank"]))

    if len(transfer_rows) != 4:
        raise AssertionError("Frozen transfer slice is incomplete")
    transfer_pass = all(row["improvement_factor"] >= 2.0 for row in transfer_rows)
    if not transfer_pass:
        raise AssertionError("Frozen 2x transfer criterion failed")

    finite_factors = [row["improvement_factor"] for row in all_rows if row["improvement_factor"] is not None]
    synthetic_last = payload["synthetic"][-1]
    lines = [
        "# Signed reduced-density truncation report",
        "",
        "## Verdict",
        "",
        "The signed reduced-density rule is a **supported local comparison primitive**.",
        "It has an exact minimax trace-norm certificate, an explicit pure-state",
        "rank separation, and it passes the frozen real-data transfer criterion.",
        "Its decision-conditioned successor now preserves the global BKS gap as",
        "a local operator trace, but neither result is yet a scalable simulator.",
        "",
        "## Frozen real-data transfer slice",
        "",
        "Equal retained subspace dimension `k=8`, cut 5:",
        "",
        "| case | ordering | signed relative error | state-averaged relative error | improvement |",
        "|---|---|---:|---:|---:|",
    ]
    for row in transfer_rows:
        lines.append(
            f"| {row['case']} | {row['ordering']} | {row['signed_relative_error']:.4%} | "
            f"{row['state_averaged_relative_error']:.4%} | {row['improvement_factor']:.2f}x |"
        )
    lines.extend([
        "",
        "All four prespecified rows exceed the 2x threshold. Across the complete",
        f"nonzero-tail ladder, observed improvement ranges from `{min(finite_factors):.2f}x`",
        f"to `{max(finite_factors):.2f}x`; no row violates signed optimality.",
        "",
        "## Synthetic separation",
        "",
        "The constructed pair consists of two pure states with a shared maximally",
        "entangled component and branch-specific Schmidt modes. At 16 total qubits:",
        "",
        f"- rank required by either state for 0.99 fidelity: `{synthetic_last['state_a_required_schmidt_rank']}`;",
        f"- exact signed reduced-density rank: `{synthetic_last['contrast_exact_rank']}`;",
        f"- rank ratio: `{synthetic_last['state_to_contrast_rank_ratio']:.1f}x`;",
        f"- norm-one witness contrast: `{synthetic_last['witness_delta']:.3f}`.",
        "",
        "The state rank grows as `2^m`, while the signed rank remains two.",
        "This separates local comparison from faithful representation of either",
        "state; it does not by itself separate SRDT from every observable-specific",
        "or multi-state algorithm.",
        "",
        "## The certified object",
        "",
        "For `Gamma_L = rho_L^B-rho_L^A`, retain the `k` eigenmodes with largest",
        "absolute eigenvalues. The discarded sum `sum_{i>k}|lambda_i|` is both:",
        "",
        "1. the exact trace-norm error of the rank-k approximation; and",
        "2. a simultaneous error bound for every local observable with operator norm at most one.",
        "",
        "This is a different optimization target from the positive state average",
        "`(rho_A+rho_B)/2`, which minimizes state-representation loss.",
        "",
        "## End-to-end successor result",
        "",
        "The current result is terminal-state and cut-local. The QAOA BKS projector",
        "is global, so this report does not claim an end-to-end BKS speedup.",
        "A frozen rank-1 `karate` test of the forward-only contrast-augmented",
        "successor failed: it was numerically indistinguishable from state averaging",
        "on one ordering and therefore did not satisfy strict improvement on both.",
        "Subsequent backward-environment Petrov--Galerkin experiments are reported",
        "separately under `results/decision_balanced_truncation`; their held-out",
        "schedule-pair transfer also fails the universal criterion (3/6).",
        "The successful successor instead changes the compressed object itself:",
        "`K_L=Tr_R({E,Gamma}/2)` combines the signed contrast with the BKS effect.",
        "It reduces to SRDT for `E=I`, retains the exact global BKS gap in its trace,",
        "and passes a frozen 4/4 development plus 4/4 held-out transfer benchmark.",
        "See `results/decision_conditioned_srdt/REPORT.md`. It remains an exact-state",
        "feasibility oracle rather than a finished simulator.",
        "",
        "## Reproduction",
        "",
        "```powershell",
        "$py = 'C:\\Users\\psgpe\\Downloads\\Taiwan\\.venv\\Scripts\\python.exe'",
        "& $py -m unittest experiments.signed_reduced_density_truncation.test_srdt -v",
        "& $py .\\experiments\\signed_reduced_density_truncation\\run_srdt.py",
        "& $py .\\experiments\\signed_reduced_density_truncation\\run_end_to_end_heldout.py",
        "& $py .\\experiments\\signed_reduced_density_truncation\\analyze_srdt.py",
        "```",
        "",
    ])
    report_path = RESULTS / "REPORT.md"
    report_path.write_text("\n".join(lines), encoding="utf-8", newline="\n")

    tracked = [
        HERE / "PROTOCOL.md", HERE / "THEORY.md", HERE / "NOVELTY_POSITIONING.md",
        HERE / "srdt_core.py", HERE / "run_srdt.py", HERE / "analyze_srdt.py",
        HERE / "END_TO_END_HELDOUT_PROTOCOL.md", HERE / "contrast_augmented.py",
        HERE / "run_end_to_end_heldout.py", HERE / "test_srdt.py",
        benchmark_path, heldout_path, report_path,
    ]
    manifest = {
        "complete": True,
        "frozen_transfer_pass": transfer_pass,
        "end_to_end_heldout_success": False,
        "files": {str(path.relative_to(REPO)): sha256(path) for path in tracked},
    }
    atomic_json(RESULTS / "manifest.json", manifest)
    print(json.dumps({
        "report": str(report_path),
        "manifest_entries": len(manifest["files"]),
        "transfer_pass": transfer_pass,
    }, indent=2))


if __name__ == "__main__":
    main()
