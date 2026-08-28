"""Analyze signed, recentered decision intervals from frozen COT artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
COT = REPO / "results" / "compressed_observable_telescope"
OBS = REPO / "results" / "observable_telescope"
RESULTS = REPO / "results" / "signed_decision_cot"
METHOD_A = "published_lr"
METHOD_B = "prior_matched_random"
PAIR_TOLERANCE = 4e-8


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gap_from_observable_telescope(ordering: str) -> tuple[float, float]:
    payload = read(OBS / f"ibm32_confirm_{ordering}.json")
    rows = {row["method"]: row for row in payload["rows"]}
    mps = rows[METHOD_B]["p_bks_mps"] - rows[METHOD_A]["p_bks_mps"]
    exact = rows[METHOD_B]["p_bks_exact"] - rows[METHOD_A]["p_bks_exact"]
    return mps, exact


def correction_ladder(
    paths: list[Path],
) -> tuple[dict[int, dict[str, float]], list[dict]]:
    ladder: dict[int, dict[str, float]] = {}
    regressions = []
    for path in paths:
        if not path.exists():
            continue
        payload = read(path)
        if not payload.get("complete"):
            raise AssertionError(f"Incomplete residual artifact: {path}")
        for method_row in payload["rows"]:
            method = method_row["method"]
            for item in method_row["residual_ladder"]:
                bond = item["residual_backward_bond"]
                if bond is None:
                    continue
                value = item["operator_correction_sum"]
                old = ladder.setdefault(int(bond), {}).get(method)
                if old is not None:
                    regressions.append({
                        "bond": int(bond),
                        "method": method,
                        "archived_value": old,
                        "repeated_value": value,
                        "absolute_difference": abs(old - value),
                        "passes_frozen_1e-10_threshold": abs(old - value) <= 1e-10,
                    })
                ladder[int(bond)][method] = value
    return ladder, regressions


def path_dependence_diagnostics(path: Path | None) -> dict[str, dict] | None:
    if path is None or not path.exists():
        return None
    payload = read(path)
    if not payload.get("complete"):
        return None
    diagnostics = {}
    for method_row in payload["rows"]:
        ladders = {
            int(item["residual_backward_bond"]): item
            for item in method_row["residual_ladder"]
            if item["residual_backward_bond"] is not None
        }
        bonds = sorted(ladders)
        inversions = []
        for lower_bond, higher_bond in zip(bonds, bonds[1:]):
            low_eta = {int(k): v for k, v in ladders[lower_bond]["eta_by_position"].items()}
            high_eta = {int(k): v for k, v in ladders[higher_bond]["eta_by_position"].items()}
            positions = sorted(set(low_eta) & set(high_eta))
            tighter = [p for p in positions if low_eta[p] + 1e-15 < high_eta[p]]
            inversions.append({
                "lower_bond": lower_bond,
                "higher_bond": higher_bond,
                "lower_bond_tighter_checkpoint_count": len(tighter),
                "checkpoint_count": len(positions),
                "fraction": len(tighter) / len(positions) if positions else 0.0,
            })
        dense_rows = [
            checkpoint
            for item in ladders.values()
            for checkpoint in item["checkpoints"]
            if "oracle_actual_operator_error" in checkpoint
        ]
        diagnostics[method_row["method"]] = {
            "operator_corrections": {
                str(bond): ladders[bond]["operator_correction_sum"] for bond in bonds
            },
            "adjacent_bond_order_inversions": inversions,
            "dense_operator_checkpoints": len(dense_rows),
            "dense_operator_violations": sum(
                row["oracle_actual_operator_error"]
                > row["eta_operator_norm_upper_bound"] + 2e-8
                for row in dense_rows
            ),
        }
    return diagnostics


def analyze_ordering(ordering: str, extra_residual: Path | None) -> dict:
    first_path = COT / f"compressed_first_term_ibm32_confirm_{ordering}_adaptive.json"
    base_residual = COT / f"residual_cot_ibm32_confirm_{ordering}_adaptive.json"
    first = read(first_path)
    centers = {
        row["method"]: row["compressed_signed_sum_diagnostic"]
        for row in first["rows"]
    }
    absolute_first = {
        row["method"]: row["compressed_first_term_sum"]
        for row in first["rows"]
    }
    residual_paths = [base_residual]
    if extra_residual is not None:
        residual_paths.append(extra_residual)
    corrections, regressions = correction_ladder(residual_paths)
    mps_gap, exact_gap = gap_from_observable_telescope(ordering)
    error_center = centers[METHOD_B] - centers[METHOD_A]
    corrected_gap = mps_gap - error_center
    rows = []
    for bond in sorted(corrections):
        if set(corrections[bond]) != {METHOD_A, METHOD_B}:
            continue
        remainder = math.fsum(corrections[bond].values()) + PAIR_TOLERANCE
        lower = corrected_gap - remainder
        upper = corrected_gap + remainder
        signed_certified = lower > 0.0 or upper < 0.0
        legacy_width = math.fsum(absolute_first.values()) + remainder
        legacy_certified = abs(mps_gap) > legacy_width
        exact_inside = lower <= exact_gap <= upper
        if signed_certified:
            signed_margin = min(abs(lower), abs(upper))
        else:
            signed_margin = -min(abs(lower), abs(upper))
        rows.append({
            "residual_bond": bond,
            "paired_operator_remainder": remainder,
            "signed_interval_lower": lower,
            "signed_interval_upper": upper,
            "signed_interval_width": 2.0 * remainder,
            "signed_certified": signed_certified,
            "signed_certificate_margin": signed_margin,
            "legacy_absolute_sum_width": legacy_width,
            "legacy_certified": legacy_certified,
            "exact_gap_inside_interval_audit": exact_inside,
            "correct_sign_audit": (corrected_gap > 0.0) == (exact_gap > 0.0),
            "paired_cubic_work_ratio_vs_R256": (bond / 256.0) ** 3,
            "paired_cubic_work_saving_fraction": 1.0 - (bond / 256.0) ** 3,
        })
    grid_rows = []
    for bond_a in sorted(corrections):
        for bond_b in sorted(corrections):
            if METHOD_A not in corrections[bond_a] or METHOD_B not in corrections[bond_b]:
                continue
            remainder = (
                corrections[bond_a][METHOD_A]
                + corrections[bond_b][METHOD_B]
                + PAIR_TOLERANCE
            )
            lower = corrected_gap - remainder
            upper = corrected_gap + remainder
            certified = lower > 0.0 or upper < 0.0
            work = 0.5 * ((bond_a / 256.0) ** 3 + (bond_b / 256.0) ** 3)
            grid_rows.append({
                "published_lr_bond": bond_a,
                "prior_matched_random_bond": bond_b,
                "paired_operator_remainder": remainder,
                "signed_interval_lower": lower,
                "signed_interval_upper": upper,
                "signed_certified": certified,
                "exact_gap_inside_interval_audit": lower <= exact_gap <= upper,
                "paired_cubic_work_ratio_vs_R256_R256": work,
                "paired_cubic_work_saving_fraction": 1.0 - work,
            })
    return {
        "ordering": ordering,
        "mps_gap": mps_gap,
        "exact_gap_audit_only": exact_gap,
        "signed_centers": centers,
        "paired_error_center": error_center,
        "recentered_gap": corrected_gap,
        "recentered_gap_error_audit": corrected_gap - exact_gap,
        "legacy_absolute_first_term_pair": math.fsum(absolute_first.values()),
        "signed_center_cancellation_factor": (
            math.fsum(absolute_first.values()) / abs(error_center)
            if error_center else None
        ),
        "rows": rows,
        "asymmetric_grid": grid_rows,
        "bond_path_diagnostics": path_dependence_diagnostics(extra_residual),
        "duplicate_bond_regression": regressions,
        "inputs": [str(first_path.relative_to(REPO))]
        + [
            str(path.resolve().relative_to(REPO))
            for path in residual_paths if path.exists()
        ],
    }


def render_report(payload: dict) -> str:
    lines = [
        "# Signed Decision-Gap COT",
        "",
        "The interval is centered at the MPS gap corrected by the signed compressed",
        "observable-telescope residual. Exact gaps are audit-only.",
        "",
    ]
    for result in payload["orderings"]:
        lines.extend([
            f"## ibm32/confirm/{result['ordering']}",
            "",
            f"MPS gap: `{result['mps_gap']:.9f}`; paired signed error center: "
            f"`{result['paired_error_center']:.9f}`; recentered gap: "
            f"`{result['recentered_gap']:.9f}`.  The legacy absolute first term is "
            f"`{result['legacy_absolute_first_term_pair']:.9f}`, a "
            f"`{result['signed_center_cancellation_factor']:.3f}x` inflation over the "
            "magnitude of the signed pair center.",
            "",
            "| R | signed interval | signed | margin | legacy width | legacy | saving |",
            "|---:|---:|:---:|---:|---:|:---:|---:|",
        ])
        for row in result["rows"]:
            lines.append(
                f"| {row['residual_bond']} | [{row['signed_interval_lower']:.6f}, "
                f"{row['signed_interval_upper']:.6f}] | "
                f"{'yes' if row['signed_certified'] else 'no'} | "
                f"{row['signed_certificate_margin']:.6f} | "
                f"{row['legacy_absolute_sum_width']:.6f} | "
                f"{'yes' if row['legacy_certified'] else 'no'} | "
                f"{100*row['paired_cubic_work_saving_fraction']:.2f}% |"
            )
        lines.extend([
            "",
            f"Audit-only exact gap: `{result['exact_gap_audit_only']:.9f}`; "
            f"recentered error: `{result['recentered_gap_error_audit']:.3e}`.",
            "",
        ])
        diagnostics = result.get("bond_path_diagnostics")
        if diagnostics:
            lines.extend(["### Path-dependence audit", ""])
            for method, item in diagnostics.items():
                inversion_text = ", ".join(
                    f"R{x['lower_bond']}<R{x['higher_bond']}: "
                    f"{x['lower_bond_tighter_checkpoint_count']}/{x['checkpoint_count']}"
                    for x in item["adjacent_bond_order_inversions"]
                )
                lines.append(
                    f"- `{method}` lower-bond-tighter checkpoints: {inversion_text}; "
                    f"dense violations {item['dense_operator_violations']}/"
                    f"{item['dense_operator_checkpoints']}."
                )
            lines.append("")
        regressions = result.get("duplicate_bond_regression", [])
        if regressions:
            lines.extend(["### Repeated-bond regression", ""])
            for item in regressions:
                lines.append(
                    f"- `{item['method']}` R{item['bond']}: absolute difference "
                    f"`{item['absolute_difference']:.3e}`; frozen `1e-10` criterion "
                    f"{'passes' if item['passes_frozen_1e-10_threshold'] else 'fails'}."
                )
            lines.append("")
    selected = payload.get("sorted_minimum_work_pair")
    if selected is not None:
        transfer = payload.get("spectral_transfer_of_sorted_pair")
        lines.extend([
            "## Minimum-work asymmetric policy",
            "",
            f"Sorted selects LR R{selected['published_lr_bond']} / MR "
            f"R{selected['prior_matched_random_bond']} at "
            f"{100*selected['paired_cubic_work_saving_fraction']:.2f}% saving.",
            "",
        ])
        if transfer is not None:
            lines.extend([
                f"Frozen spectral transfer is "
                f"{'certified' if transfer['signed_certified'] else 'not certified'} "
                f"with interval [{transfer['signed_interval_lower']:.6f}, "
                f"{transfer['signed_interval_upper']:.6f}].",
                "",
            ])
    lines.extend([
        "## Claim boundary",
        "",
        "This is a center-plus-certified-remainder interval. It retains signed",
        "cancellation only in the computable center and keeps the unknown remainder",
        "fully adversarial. It proves feasibility for the evaluated policy points,",
        "not global resource optimality or general scaling.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sorted-extra", type=Path)
    parser.add_argument("--spectral-extra", type=Path)
    args = parser.parse_args()
    RESULTS.mkdir(parents=True, exist_ok=True)
    orderings = [
        analyze_ordering("sorted", args.sorted_extra),
        analyze_ordering("spectral", args.spectral_extra),
    ]
    sorted_certified = [
        row for row in orderings[0]["asymmetric_grid"] if row["signed_certified"]
    ]
    selected = min(
        sorted_certified,
        key=lambda row: (
            row["paired_cubic_work_ratio_vs_R256_R256"],
            max(row["published_lr_bond"], row["prior_matched_random_bond"]),
            row["published_lr_bond"] + row["prior_matched_random_bond"],
            row["published_lr_bond"], row["prior_matched_random_bond"],
        ),
    ) if sorted_certified else None
    transfer = None
    if selected is not None:
        transfer = next((
            row for row in orderings[1]["asymmetric_grid"]
            if row["published_lr_bond"] == selected["published_lr_bond"]
            and row["prior_matched_random_bond"] == selected["prior_matched_random_bond"]
        ), None)
    payload = {
        "stage": "signed_decision_gap_cot",
        "complete": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "exact_values_used_for_construction": False,
        "pair_numerical_tolerance": PAIR_TOLERANCE,
        "orderings": orderings,
        "sorted_minimum_work_pair": selected,
        "spectral_transfer_of_sorted_pair": transfer,
    }
    summary_path = RESULTS / "summary.json"
    report_path = RESULTS / "REPORT.md"
    summary_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(render_report(payload), encoding="utf-8")
    manifest_paths = [
        summary_path,
        report_path,
        RESULTS / "RESEARCH_REPORT.md",
        HERE / "THEORY.md",
        HERE / "PROTOCOL.md",
        HERE / "SPECTRAL_TRANSFER_PROTOCOL.md",
        HERE / "NOVELTY_POSITIONING.md",
    ]
    for result in orderings:
        manifest_paths.extend(REPO / path for path in result["inputs"])
    manifest_paths = sorted(
        {path.resolve() for path in manifest_paths if path.exists()},
        key=str,
    )
    manifest = {
        "complete": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "files": [
            {"path": str(path.relative_to(REPO)), "sha256": sha256(path)}
            for path in manifest_paths
        ],
    }
    (RESULTS / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(render_report(payload))


if __name__ == "__main__":
    main()
