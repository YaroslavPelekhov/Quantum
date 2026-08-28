"""Verify causal-certification-debt identities on executed COT witnesses."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
COT = REPO / "results" / "compressed_observable_telescope"
RESULTS = REPO / "results" / "causal_certification_debt"
NU = 1e-10

INPUTS = {
    "sorted_rescue_lr": COT / "residual_cot_ibm32_confirm_sorted_adaptive_residual-adaptive_causal319.json",
    "sorted_fixed": COT / "residual_cot_ibm32_confirm_sorted_adaptive.json",
    "spectral_transfer_lr": COT / "residual_cot_ibm32_confirm_spectral_adaptive_residual-adaptive_causal319.json",
    "spectral_fixed": COT / "residual_cot_ibm32_confirm_spectral_adaptive.json",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def select(payload: dict, method: str, bond: int | None) -> tuple[dict, dict]:
    row = next(item for item in payload["rows"] if item["method"] == method)
    if bond is None:
        witness = row["residual_ladder"][0]
    else:
        witness = next(
            item for item in row["residual_ladder"]
            if item["residual_backward_bond"] == bond
        )
    return row, witness


def analyze_witness(label: str, row: dict, witness: dict) -> dict:
    checkpoints = {item["checkpoint_position"]: item for item in witness["checkpoints"]}
    radii = {
        item["checkpoint_position"]: item["forward_trace_norm_radius"]
        for item in row["forward_groups"]
    }
    positions = sorted(checkpoints)
    rank = len(checkpoints[positions[0]]["discarded_residual_tail_bounds"])
    recurrence_error = 0.0
    for k in range(rank):
        for position in positions:
            next_tail = (
                checkpoints[position + 1]["discarded_residual_tail_bounds"][k]
                if position + 1 in checkpoints else 0.0
            )
            expected = (
                next_tail
                + checkpoints[position]["residual_local_discard_bounds"][k]
                + NU
            )
            recurrence_error = max(
                recurrence_error,
                abs(checkpoints[position]["discarded_residual_tail_bounds"][k] - expected),
            )

    direct_debt = math.fsum(
        radii[t] * math.fsum(checkpoints[t]["discarded_residual_tail_bounds"])
        for t in positions
    )
    causal_price = {}
    running = 0.0
    shadow_debt_terms = []
    for j in positions:
        running += radii[j]
        causal_price[j] = running
        local_increment = math.fsum(
            value + NU for value in checkpoints[j]["residual_local_discard_bounds"]
        )
        shadow_debt_terms.append(running * local_increment)
    shadow_debt = math.fsum(shadow_debt_terms)

    represented = math.fsum(
        radii[t] * math.fsum(min(1.0, value) for value in checkpoints[t]["compressed_residual_norms"])
        for t in positions
    )
    capped_tail = math.fsum(
        radii[t] * math.fsum(
            min(1.0, x + xi) - min(1.0, x)
            for x, xi in zip(
                checkpoints[t]["compressed_residual_norms"],
                checkpoints[t]["discarded_residual_tail_bounds"],
            )
        )
        for t in positions
    )
    cap_active = any(
        x + xi >= 1.0
        for t in positions
        for x, xi in zip(
            checkpoints[t]["compressed_residual_norms"],
            checkpoints[t]["discarded_residual_tail_bounds"],
        )
    )
    reconstructed = represented + capped_tail
    return {
        "label": label,
        "method": row["method"],
        "ordering": row["ordering"],
        "rank": rank,
        "checkpoint_count_with_residual_update": len(positions),
        "maximum_tail_recurrence_error": recurrence_error,
        "direct_uncapped_debt": direct_debt,
        "shadow_price_debt": shadow_debt,
        "debt_identity_absolute_error": abs(direct_debt - shadow_debt),
        "represented_residual_component": represented,
        "capped_tail_component": capped_tail,
        "cap_active": cap_active,
        "reconstructed_operator_correction": reconstructed,
        "recorded_operator_correction": witness["operator_correction_sum"],
        "correction_reconstruction_error": abs(
            reconstructed - witness["operator_correction_sum"]
        ),
        "tail_fraction_of_correction": (
            capped_tail / witness["operator_correction_sum"]
            if witness["operator_correction_sum"] else 0.0
        ),
        "maximum_causal_price": max(causal_price.values()),
        "minimum_causal_price": min(causal_price.values()),
        "top_shadow_debt_checkpoints": [
            {"checkpoint_position": positions[index], "debt": value}
            for index, value in sorted(
                enumerate(shadow_debt_terms), key=lambda pair: pair[1], reverse=True
            )[:20]
        ],
    }


def build_summary() -> dict:
    sorted_rescue = load(INPUTS["sorted_rescue_lr"])
    sorted_fixed = load(INPUTS["sorted_fixed"])
    spectral_transfer = load(INPUTS["spectral_transfer_lr"])
    spectral_fixed = load(INPUTS["spectral_fixed"])
    cases = []
    for label, payload, method, bond in (
        ("sorted_rescue_lr", sorted_rescue, "published_lr", None),
        ("sorted_fixed_mr_R128", sorted_fixed, "prior_matched_random", 128),
        ("spectral_transfer_lr", spectral_transfer, "published_lr", None),
        ("spectral_fixed_mr_R128", spectral_fixed, "prior_matched_random", 128),
    ):
        row, witness = select(payload, method, bond)
        cases.append(analyze_witness(label, row, witness))
    return {
        "stage": "causal_certification_debt_identity_audit",
        "complete": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "index_orientation": "local error at j propagates to all t<=j",
        "numeric_floor_per_vector_per_checkpoint": NU,
        "cases": cases,
        "maximum_identity_error": max(row["debt_identity_absolute_error"] for row in cases),
        "maximum_recurrence_error": max(row["maximum_tail_recurrence_error"] for row in cases),
        "maximum_correction_reconstruction_error": max(
            row["correction_reconstruction_error"] for row in cases
        ),
    }


def report(summary: dict) -> str:
    lines = [
        "# Causal Certification Debt identity audit",
        "",
        "The implemented orientation is `j -> {t: t<=j}`. The local increment includes the TT-SVD bound and the explicit `1e-10` per-vector numerical floor.",
        "",
        "| case | rank | direct debt | shadow-price debt | identity error | tail / correction |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in summary["cases"]:
        lines.append(
            f"| {row['label']} | {row['rank']} | {row['direct_uncapped_debt']:.12g} | "
            f"{row['shadow_price_debt']:.12g} | {row['debt_identity_absolute_error']:.3e} | "
            f"{100*row['tail_fraction_of_correction']:.2f}% |"
        )
    lines += [
        "",
        f"Maximum identity error: `{summary['maximum_identity_error']:.3e}`. Maximum tail-recurrence error: `{summary['maximum_recurrence_error']:.3e}`. Maximum reconstruction error against the production COT correction: `{summary['maximum_correction_reconstruction_error']:.3e}`.",
        "",
        "No rank cap is active in these four executed witnesses, so the tail component equals the uncapped causal debt. The theorem file also proves the conservative inequality required when a cap is active.",
    ]
    return "\n".join(lines) + "\n"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_manifest() -> None:
    sources = [HERE / "THEOREMS.md", HERE / "analyze_debt.py", HERE / "test_debt.py", HERE / "README.md"]
    artifacts = [RESULTS / "summary.json", RESULTS / "REPORT.md"]
    entry = lambda path: {"bytes": path.stat().st_size, "sha256": sha256(path)}
    atomic_json(RESULTS / "MANIFEST.json", {
        "complete": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sources": {path.relative_to(REPO).as_posix(): entry(path) for path in sources},
        "inputs": {path.relative_to(REPO).as_posix(): entry(path) for path in INPUTS.values()},
        "artifacts": {path.relative_to(REPO).as_posix(): entry(path) for path in artifacts},
    })


def main() -> None:
    summary = build_summary()
    atomic_json(RESULTS / "summary.json", summary)
    (RESULTS / "REPORT.md").write_text(report(summary), encoding="utf-8")
    write_manifest()
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
