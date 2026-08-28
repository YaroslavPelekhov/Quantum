"""Build the DCS-RDT report and integrity manifest."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULTS = REPO / "results" / "decision_conditioned_srdt"
sys.path.insert(0, str(REPO / "experiments" / "contrastive_tensor_simulation"))

from contrastive_core import atomic_json, sha256


def read(name: str) -> dict:
    payload = json.loads((RESULTS / name).read_text(encoding="utf-8"))
    if not payload.get("complete"):
        raise AssertionError(f"Incomplete artifact: {name}")
    return payload


def fixed_row(cohort: dict, row: dict) -> dict:
    return next(item for item in row["rows"] if item["rank"] == cohort["fixed_rank"])


def first_rank(row: dict, method: str, field: str) -> int | None:
    return next(
        (item["rank"] for item in row["rows"] if item["methods"][method][field]),
        None,
    )


def numerical_rank(row: dict, method: str) -> int | None:
    return next(
        (
            item["rank"]
            for item in row["rows"]
            if item["methods"][method]["trace_norm_bound"] <= 1e-12
        ),
        None,
    )


def bound_text(value: float) -> str:
    return "<1e-15" if value <= 1e-15 else f"{value:.6f}"


def factor_text(row: dict, control: str) -> str:
    value = row["fixed_rank_factors"][control]
    prefix = ">" if row["fixed_rank_factor_is_lower_bound"] else ""
    return f"{prefix}{value:.2f}x" if value < 1e4 else f"{prefix}{value:.2e}x"


def main() -> None:
    development = read("development.json")
    transfer = read("transfer.json")
    if not development["success"] or development["passed_rows"] != 4:
        raise AssertionError("Unexpected development verdict")
    if not transfer["success"] or transfer["passed_rows"] != 4:
        raise AssertionError("Unexpected held-out verdict")
    if development["protocol_sha256"] != transfer["protocol_sha256"]:
        raise AssertionError("Protocol changed between stages")
    if development["protocol_sha256"] != sha256(HERE / "PROTOCOL.md"):
        raise AssertionError("Current protocol does not match executed stages")

    lines = [
        "# Decision-conditioned signed reduced-density truncation report",
        "",
        "## Verdict",
        "",
        "Decision-conditioned SRDT (DCS-RDT) is a **supported comparison-oriented",
        "truncation primitive**. It strictly generalizes SRDT, preserves the exact",
        "global BKS gap as a local operator trace, has a spectral tail certificate,",
        "passes the frozen 4/4 development criterion, and transfers 4/4 to two",
        "held-out cases without retuning.",
        "",
        "This is an exact-state feasibility result, not yet a scalable simulator.",
        "",
        "## Construction and theorem",
        "",
        "For `Gamma=|B><B|-|A><A|`, decision effect `E`, and split `L|R`, define",
        "",
        "`K_L = Tr_R((E Gamma + Gamma E)/2)`.",
        "",
        "Then `K_L` is Hermitian and `Tr(K_L)=Tr(E Gamma)`, the exact global",
        "decision gap. For `E=I`, it reduces to the original signed reduced density",
        "`rho_L^B-rho_L^A`. Keeping the `k` eigenmodes with largest absolute",
        "eigenvalues gives the optimal rank-k approximation in every Schatten norm.",
        "For discarded eigenvalues `lambda_i`, the actual gap error is",
        "`|sum_i lambda_i|` and is certified by `sum_i |lambda_i|`.",
        "",
        "## Frozen fixed-rank results",
        "",
        "| stage | case | ordering | rank | exact gap | DCS bound | vs SRDT | vs state avg | pass |",
        "|---|---|---|---:|---:|---:|---:|---:|:---:|",
    ]
    for cohort in (development, transfer):
        for row in cohort["rows"]:
            fixed = fixed_row(cohort, row)
            target = fixed["methods"]["decision_conditioned"]
            lines.append(
                f"| {cohort['stage']} | {row['case']} | {row['ordering']} | "
                f"{cohort['fixed_rank']} | {row['exact_delta']:+.6f} | "
                f"{bound_text(target['trace_norm_bound'])} | "
                f"{factor_text(row, 'srdt_basis')} | "
                f"{factor_text(row, 'state_averaged_basis')} | "
                f"{'yes' if row['fixed_rank_pass'] else 'no'} |"
            )
    lines.extend([
        "",
        "Factors marked `>` are conservative lower bounds obtained by replacing a",
        "machine-zero denominator with `1e-15`; they should be read as exact-at-rank,",
        "not as meaningful fourteen-digit speedup estimates.",
        "",
        "## Certification and numerical rank",
        "",
        "| case | ordering | first sign-certified rank | numerical DCS rank |",
        "|---|---|---:|---:|",
    ])
    for cohort in (development, transfer):
        for row in cohort["rows"]:
            certified = first_rank(row, "decision_conditioned", "sign_certified")
            rank = numerical_rank(row, "decision_conditioned")
            lines.append(
                f"| {row['case']} | {row['ordering']} | "
                f"{certified if certified is not None else 'not on ladder'} | "
                f"{rank if rank is not None else 'above ladder'} |"
            )
    lines.extend([
        "",
        "DCS-RDT certifies the decision sign within the tested ladder on all eight",
        "rows. The hardest row is `aves-sparrow-social/sorted`: rank 8 certifies",
        "the small negative gap and rank 16 makes the contribution operator exact.",
        "At rank 8 its finite residual improvement is 5.12x over SRDT and 8.65x",
        "over the state-averaged basis.",
        "",
        "## Novelty boundary",
        "",
        "The Jordan product, difference densities, observable-focused tensor-network",
        "methods, and spectral low-rank truncation all predate this experiment. The",
        "candidate novelty is their specific combination into a spatially reduced",
        "paired-decision contribution operator with an exact gap trace, signed spectral",
        "certificate, and frozen equal-rank transfer benchmark. A targeted search found",
        "no exact match, but absence from search is not proof of priority. See",
        "`experiments/decision_conditioned_srdt/PRIOR_ART.md`.",
        "",
        "## Limitations and next step",
        "",
        "The current oracle constructs `K_L` from exact terminal states and the full",
        "BKS effect. It proves comparison compressibility, not cheap constructibility.",
        "The next real algorithmic question is whether `K_L` or its dominant signed",
        "modes can be accumulated directly as a tensor network with a propagated tail",
        "certificate, without first materializing either exact state.",
        "",
    ])
    report = RESULTS / "REPORT.md"
    report.write_text("\n".join(lines), encoding="utf-8", newline="\n")

    tracked = [
        HERE / "PROTOCOL.md",
        HERE / "PRIOR_ART.md",
        HERE / "dcsrdt_core.py",
        HERE / "run_dcsrdt.py",
        HERE / "analyze_dcsrdt.py",
        HERE / "test_dcsrdt.py",
        HERE / "README.md",
        RESULTS / "development.json",
        RESULTS / "transfer.json",
        report,
    ]
    manifest = {
        "complete": True,
        "development_success": True,
        "transfer_success": True,
        "files": {str(path.relative_to(REPO)): sha256(path) for path in tracked},
    }
    atomic_json(RESULTS / "manifest.json", manifest)
    print(json.dumps({
        "report": str(report),
        "development_passed": development["passed_rows"],
        "transfer_passed": transfer["passed_rows"],
        "manifest_entries": len(tracked),
    }, indent=2))


if __name__ == "__main__":
    main()
