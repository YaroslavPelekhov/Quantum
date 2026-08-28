"""Analyze equal-work residual reset-window interventions."""

from __future__ import annotations

import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))

from analyze_signed_decision import (
    METHOD_A,
    METHOD_B,
    PAIR_TOLERANCE,
    gap_from_observable_telescope,
)


RESULTS = REPO / "results" / "signed_decision_cot"
COT = REPO / "results" / "compressed_observable_telescope"
EXPECTED = {"sorted": "reset_193_256", "spectral": "reset_129_192"}
POLICY_ORDER = (
    "reset_129_192",
    "reset_193_256",
    "reset_257_320",
    "reset_321_384",
)


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def policy_work(schedule: list[list[int]] | list[tuple[int, int, int]]) -> float:
    work = math.fsum((end - start + 1) * (bond / 256.0) ** 3 for start, end, bond in schedule)
    return work / 555.0


def analyze_ordering(ordering: str) -> dict:
    path = RESULTS / f"reset_intervention_{ordering}.json"
    payload = read(path)
    if not payload.get("complete"):
        raise AssertionError(f"Incomplete intervention: {path}")
    first = read(COT / f"compressed_first_term_ibm32_confirm_{ordering}_adaptive.json")
    centers = {row["method"]: row["compressed_signed_sum_diagnostic"] for row in first["rows"]}
    mps_gap, exact_gap = gap_from_observable_telescope(ordering)
    paired_center = centers[METHOD_B] - centers[METHOD_A]
    recentered_gap = mps_gap - paired_center

    methods = {}
    dense_violations = 0
    dense_checks = 0
    for method_row in payload["rows"]:
        policy_rows = {}
        for item in method_row["residual_ladder"]:
            key = item["residual_config_key"]
            checkpoints = item["checkpoints"]
            audited = [row for row in checkpoints if "oracle_actual_operator_error" in row]
            violations = sum(
                row["oracle_actual_operator_error"]
                > row["eta_operator_norm_upper_bound"] + 2e-8
                for row in audited
            )
            dense_checks += len(audited)
            dense_violations += violations
            start = int(key.split("_")[1])
            post_position = start - 1
            post_row = next(row for row in checkpoints if row["checkpoint_position"] == post_position)
            policy_rows[key] = {
                "operator_correction": item["operator_correction_sum"],
                "work_ratio_vs_R256": policy_work(item["residual_backward_schedule"]),
                "post_window_position": post_position,
                "post_window_eta": post_row["eta_operator_norm_upper_bound"],
                "dense_checks": len(audited),
                "dense_violations": violations,
            }
        methods[method_row["method"]] = policy_rows

    pair_rows = []
    for key in POLICY_ORDER:
        remainder = (
            methods[METHOD_A][key]["operator_correction"]
            + methods[METHOD_B][key]["operator_correction"]
            + PAIR_TOLERANCE
        )
        lower, upper = recentered_gap - remainder, recentered_gap + remainder
        certified = lower > 0.0 or upper < 0.0
        margin = min(abs(lower), abs(upper)) if certified else -min(abs(lower), abs(upper))
        pair_rows.append({
            "policy": key,
            "paired_remainder": remainder,
            "interval_lower": lower,
            "interval_upper": upper,
            "certified": certified,
            "margin": margin,
            "exact_gap_inside_interval_audit": lower <= exact_gap <= upper,
            "work_ratio_vs_R256_R256": methods[METHOD_A][key]["work_ratio_vs_R256"],
        })

    expected = EXPECTED[ordering]
    expected_index = POLICY_ORDER.index(expected)
    neighbors = [
        POLICY_ORDER[i]
        for i in (expected_index - 1, expected_index + 1)
        if 0 <= i < len(POLICY_ORDER)
    ]
    lr_values = {key: methods[METHOD_A][key]["operator_correction"] for key in POLICY_ORDER}
    pair_values = {row["policy"]: row["paired_remainder"] for row in pair_rows}
    lr_min = min(lr_values, key=lambda key: (lr_values[key], POLICY_ORDER.index(key)))
    pair_min = min(pair_values, key=lambda key: (pair_values[key], POLICY_ORDER.index(key)))
    prediction = {
        "expected_policy": expected,
        "adjacent_controls": neighbors,
        "lr_minimum_policy": lr_min,
        "pair_minimum_policy": pair_min,
        "expected_beats_adjacent_lr": all(lr_values[expected] < lr_values[key] for key in neighbors),
        "expected_beats_adjacent_pair": all(pair_values[expected] < pair_values[key] for key in neighbors),
        "lr_prediction_passes": lr_min == expected,
        "pair_prediction_passes": pair_min == expected,
    }
    prediction["mechanism_prediction_passes"] = all((
        prediction["expected_beats_adjacent_lr"],
        prediction["expected_beats_adjacent_pair"],
        prediction["lr_prediction_passes"],
        prediction["pair_prediction_passes"],
    ))

    return {
        "ordering": ordering,
        "input": str(path.relative_to(REPO)),
        "mps_gap": mps_gap,
        "exact_gap_audit_only": exact_gap,
        "paired_signed_center": paired_center,
        "recentered_gap": recentered_gap,
        "methods": methods,
        "pair_rows": pair_rows,
        "prediction": prediction,
        "dense_checks": dense_checks,
        "dense_violations": dense_violations,
    }


def render(payload: dict) -> str:
    lines = [
        "# Equal-work residual reset intervention",
        "",
        "Four policies use R32 in one 64-checkpoint window and R128 elsewhere.",
        "All policies have identical cubic residual work.",
        "",
    ]
    for result in payload["orderings"]:
        lines.extend([
            f"## {result['ordering']}",
            "",
            "| policy | LR correction | MR correction | paired remainder | margin | certified |",
            "|---|---:|---:|---:|---:|:---:|",
        ])
        for pair in result["pair_rows"]:
            key = pair["policy"]
            lines.append(
                f"| {key} | {result['methods'][METHOD_A][key]['operator_correction']:.9f} | "
                f"{result['methods'][METHOD_B][key]['operator_correction']:.9f} | "
                f"{pair['paired_remainder']:.9f} | {pair['margin']:.9f} | "
                f"{'yes' if pair['certified'] else 'no'} |"
            )
        p = result["prediction"]
        lines.extend([
            "",
            f"Frozen expected policy: `{p['expected_policy']}`. LR minimum: "
            f"`{p['lr_minimum_policy']}`; pair minimum: `{p['pair_minimum_policy']}`. "
            f"Mechanism prediction: **{'pass' if p['mechanism_prediction_passes'] else 'fail'}**.",
            "",
            f"Dense violations: `{result['dense_violations']}/{result['dense_checks']}`.",
            "",
        ])
    return "\n".join(lines)


def main() -> None:
    orderings = [analyze_ordering("sorted"), analyze_ordering("spectral")]
    payload = {
        "stage": "equal_work_residual_reset_intervention_analysis",
        "complete": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "exact_values_used_for_construction": False,
        "orderings": orderings,
    }
    summary = RESULTS / "reset_intervention_summary.json"
    report = RESULTS / "RESET_INTERVENTION_REPORT.md"
    summary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    report.write_text(render(payload), encoding="utf-8")
    manifest_paths = [
        summary,
        report,
        HERE / "RESET_INTERVENTION_PROTOCOL.md",
        HERE / "SORTED_RESET_RESULT_FREEZE.md",
        HERE / "run_reset_intervention.py",
        HERE / "analyze_reset_intervention.py",
    ] + [REPO / result["input"] for result in orderings]
    manifest = {
        "complete": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "files": [
            {"path": str(path.relative_to(REPO)), "sha256": sha256(path)}
            for path in manifest_paths
        ],
    }
    (RESULTS / "RESET_INTERVENTION_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(render(payload))


if __name__ == "__main__":
    main()
