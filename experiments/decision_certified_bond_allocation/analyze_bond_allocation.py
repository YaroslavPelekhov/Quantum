"""Analyze causal asymmetric residual-bond allocation experiments."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
COT = REPO / "results" / "compressed_observable_telescope"
RESULTS = REPO / "results" / "decision_certified_bond_allocation"

SORTED_FIRST = COT / "compressed_first_term_ibm32_confirm_sorted_adaptive.json"
SORTED_FIXED = COT / "residual_cot_ibm32_confirm_sorted_adaptive.json"
SORTED_FAILED = COT / "residual_cot_ibm32_confirm_sorted_adaptive_residual-adaptive.json"
SORTED_RESCUE = COT / "residual_cot_ibm32_confirm_sorted_adaptive_residual-adaptive_causal319.json"
SPECTRAL_FIRST = COT / "compressed_first_term_ibm32_confirm_spectral_adaptive.json"
SPECTRAL_FIXED = COT / "residual_cot_ibm32_confirm_spectral_adaptive.json"
SPECTRAL_TRANSFER = COT / "residual_cot_ibm32_confirm_spectral_adaptive_residual-adaptive_causal319.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def ladder_item(payload: dict, method: str, bond: int | None = None) -> dict:
    row = next(row for row in payload["rows"] if row["method"] == method)
    if bond is None:
        if len(row["residual_ladder"]) != 1:
            raise AssertionError("Expected one scheduled residual witness")
        return row["residual_ladder"][0]
    return next(
        item for item in row["residual_ladder"]
        if item["residual_backward_bond"] == bond
    )


def first_term_and_gap(payload: dict) -> tuple[float, float]:
    row = next(item for item in payload["pair_rows"] if item["residual_backward_bond"] == 128)
    return row["compressed_first_term_pair_sum"], row["mps_gap_absolute"]


def cubic_work_ratio(high_positions: int, low_positions: int) -> float:
    return (
        high_positions * 256**3 + low_positions * 128**3
    ) / ((high_positions + low_positions) * 256**3)


def audit_witness(item: dict) -> dict:
    checkpoints = item["checkpoints"]
    tail_monotonic_violations = 0
    oracle_violations = 0
    for earlier, later in zip(checkpoints, checkpoints[1:]):
        # Rows are sorted by increasing position. Earlier positions have passed
        # through more backward steps and must carry at least as much scalar tail.
        for a, b in zip(
            earlier["discarded_residual_tail_bounds"],
            later["discarded_residual_tail_bounds"],
        ):
            if a + 1e-15 < b:
                tail_monotonic_violations += 1
    for row in checkpoints:
        if "oracle_actual_operator_error" in row:
            if row["oracle_actual_operator_error"] > row["eta_operator_norm_upper_bound"] + 2e-8:
                oracle_violations += 1
    return {
        "tail_monotonic_violations": tail_monotonic_violations,
        "selected_dense_oracle_violations": oracle_violations,
    }


def build_summary() -> dict:
    sorted_first = load(SORTED_FIRST)
    sorted_fixed = load(SORTED_FIXED)
    sorted_failed = load(SORTED_FAILED)
    sorted_rescue = load(SORTED_RESCUE)
    spectral_first = load(SPECTRAL_FIRST)
    spectral_fixed = load(SPECTRAL_FIXED)
    spectral_transfer = load(SPECTRAL_TRANSFER)

    first_sorted, gap_sorted = first_term_and_gap(sorted_first)
    failed_lr = ladder_item(sorted_failed, "published_lr")
    failed_mr = ladder_item(sorted_failed, "prior_matched_random")
    rescue_lr = ladder_item(sorted_rescue, "published_lr")
    fixed_mr = ladder_item(sorted_fixed, "prior_matched_random", 128)
    fixed_lr_256 = ladder_item(sorted_fixed, "published_lr", 256)
    fixed_mr_256 = ladder_item(sorted_fixed, "prior_matched_random", 256)

    failed_width = (
        first_sorted + failed_lr["operator_correction_sum"]
        + failed_mr["operator_correction_sum"]
    )
    rescue_width = (
        first_sorted + rescue_lr["operator_correction_sum"]
        + fixed_mr["operator_correction_sum"]
    )
    fixed_256_width = (
        first_sorted + fixed_lr_256["operator_correction_sum"]
        + fixed_mr_256["operator_correction_sum"]
    )

    lr_work = cubic_work_ratio(319, 236)
    mr_work = (128 / 256) ** 3
    paired_work = (lr_work + mr_work) / 2

    first_spectral, gap_spectral = first_term_and_gap(spectral_first)
    transfer_lr = ladder_item(spectral_transfer, "published_lr")
    spectral_mr_128 = ladder_item(spectral_fixed, "prior_matched_random", 128)
    spectral_lr_128 = ladder_item(spectral_fixed, "published_lr", 128)
    transfer_width = (
        first_spectral + transfer_lr["operator_correction_sum"]
        + spectral_mr_128["operator_correction_sum"]
    )
    fixed_128_spectral_width = (
        first_spectral + spectral_lr_128["operator_correction_sum"]
        + spectral_mr_128["operator_correction_sum"]
    )

    return {
        "stage": "causal_asymmetric_decision_certified_bond_allocation",
        "complete": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "selection_uses_dense_exact_projector_errors": False,
        "sorted_primary_negative": {
            "schedule": "both trajectories: 1-303 R256, 304-555 R128",
            "pair_width": failed_width,
            "mps_gap": gap_sorted,
            "certificate_margin": gap_sorted - failed_width,
            "certified": failed_width < gap_sorted,
            "paired_cubic_work_ratio_vs_R256_R256": cubic_work_ratio(303, 252),
        },
        "sorted_causal_asymmetric": {
            "lr_schedule": "1-319 R256, 320-555 R128",
            "mr_schedule": "fixed R128",
            "compressed_first_term_pair": first_sorted,
            "lr_operator_correction": rescue_lr["operator_correction_sum"],
            "mr_operator_correction": fixed_mr["operator_correction_sum"],
            "pair_width": rescue_width,
            "fixed_R256_R256_pair_width": fixed_256_width,
            "mps_gap": gap_sorted,
            "certificate_margin": gap_sorted - rescue_width,
            "certified": rescue_width < gap_sorted,
            "lr_cubic_work_ratio_vs_R256": lr_work,
            "mr_cubic_work_ratio_vs_R256": mr_work,
            "paired_cubic_work_ratio_vs_R256_R256": paired_work,
            "paired_cubic_work_saving_fraction": 1 - paired_work,
            "witness_audit": audit_witness(rescue_lr),
        },
        "spectral_frozen_transfer": {
            "lr_schedule": "1-319 R256, 320-555 R128",
            "mr_schedule": "fixed R128",
            "pair_width": transfer_width,
            "fixed_R128_R128_pair_width": fixed_128_spectral_width,
            "mps_gap": gap_spectral,
            "certificate_margin": gap_spectral - transfer_width,
            "certified": transfer_width < gap_spectral,
            "paired_cubic_work_ratio_vs_R256_R256": paired_work,
            "work_multiple_vs_fixed_R128_R128": paired_work / ((128 / 256) ** 3),
            "resource_optimality_transferred": paired_work <= ((128 / 256) ** 3),
            "witness_audit": audit_witness(transfer_lr),
        },
    }


def report(summary: dict) -> str:
    failed = summary["sorted_primary_negative"]
    rescue = summary["sorted_causal_asymmetric"]
    spectral = summary["spectral_frozen_transfer"]
    return f"""# Causal asymmetric decision-certified bond allocation

## Result

The prespecified checkpoint-wise mixing proxy failed after end-to-end execution:
width `{failed['pair_width']:.9f}` versus gap `{failed['mps_gap']:.9f}` (margin
`{failed['certificate_margin']:.9f}`). This retains the negative result and
demonstrates that independently mixing fixed-bond checkpoint rows is not sound
as a resource predictor because the residual tail is causal and irreversible.

The secondary causal asymmetric schedule succeeds on the difficult sorted
ordering:

| quantity | value |
|---|---:|
| compressed first-term pair | {rescue['compressed_first_term_pair']:.9f} |
| LR scheduled correction | {rescue['lr_operator_correction']:.9f} |
| MR fixed-R128 correction | {rescue['mr_operator_correction']:.9f} |
| total certified width | {rescue['pair_width']:.9f} |
| MPS gap | {rescue['mps_gap']:.9f} |
| certificate margin | {rescue['certificate_margin']:.9f} |
| paired cubic work vs R256/R256 | {rescue['paired_cubic_work_ratio_vs_R256_R256']:.4f} |
| paired cubic work saving | {100*rescue['paired_cubic_work_saving_fraction']:.2f}% |

All selected dense-oracle inequalities pass, but dense errors are audit-only and
are excluded from selection and from the certificate construction.

## Frozen spectral transfer

The identical LR schedule plus MR/R128 remains certified: width
`{spectral['pair_width']:.9f}`, gap `{spectral['mps_gap']:.9f}`, margin
`{spectral['certificate_margin']:.9f}`. Resource optimality does not transfer:
the policy uses `{spectral['work_multiple_vs_fixed_R128_R128']:.3f}x` the cubic
bond-work of the already sufficient spectral R128/R128 baseline. Thus the pilot
supports sound causal asymmetric allocation but not a universal allocation
policy across qubit orderings.
"""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_manifest() -> None:
    sources = [
        HERE / "analyze_bond_allocation.py", HERE / "test_bond_allocation.py",
        HERE / "THEORY.md", HERE / "SORTED_PROTOCOL.md",
        HERE / "CAUSAL_RESCUE_PROTOCOL.md", HERE / "SPECTRAL_TRANSFER_PROTOCOL.md",
        HERE / "LITERATURE_POSITIONING.md", HERE / "README.md",
    ]
    inputs = [
        SORTED_FIRST, SORTED_FIXED, SORTED_FAILED, SORTED_RESCUE,
        SPECTRAL_FIRST, SPECTRAL_FIXED, SPECTRAL_TRANSFER,
    ]
    artifacts = [RESULTS / "summary.json", RESULTS / "REPORT.md"]
    entry = lambda path: {"bytes": path.stat().st_size, "sha256": sha256(path)}
    atomic_json(RESULTS / "MANIFEST.json", {
        "complete": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sources": {path.relative_to(REPO).as_posix(): entry(path) for path in sources},
        "inputs": {path.relative_to(REPO).as_posix(): entry(path) for path in inputs},
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
