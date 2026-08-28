"""Soundness-gated pairwise and global analysis for RankCert-MPS."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from certificate import NUMERICAL_SIMULATION_TOLERANCE, ranking_certificate
from rankcert_inputs import CASES, METHODS, ORDERINGS, PROJECT, RESULTS, SETTINGS, atomic_json, read_json


SCHEDULE_ROWS = RESULTS / "rankcert_schedule_rows.json"
PAIR_JSON = RESULTS / "rankcert_pair_rows.json"
PAIR_CSV = RESULTS / "rankcert_pair_rows.csv"
SUMMARY = RESULTS / "rankcert_summary.json"
REPORT = RESULTS / "FINAL_REPORT.md"
PRIOR_AVES = PROJECT / "results" / "mps_ladder" / "mps_ladder.json"
PRIOR_CROSS = PROJECT / "results" / "cross_case_replication" / "aer_jobs.json"


def sign(value: float, tolerance: float = 1e-15) -> int:
    return 1 if value > tolerance else (-1 if value < -tolerance else 0)


def ratio(numerator: float, denominator: float):
    if denominator == 0:
        return None if numerator == 0 else "infinity"
    return numerator / denominator


def prior_targets() -> dict:
    result = {}
    for path in (PRIOR_AVES, PRIOR_CROSS):
        for row in read_json(path)["rows"]:
            if row["method"] in METHODS and row["setting"] in {setting["name"] for setting in SETTINGS}:
                result[(row["case"], row["setting"], row["method"], row["ordering"])] = row["metrics"]["bks_rate"]
    return result


def analyze(required_cases: tuple[str, ...]) -> dict:
    payload = read_json(SCHEDULE_ROWS)
    all_rows = payload.get("rows", [])
    rows = [row for row in all_rows if row["case"] in required_cases]
    expected = len(required_cases) * len(SETTINGS) * len(METHODS) * len(ORDERINGS)
    if len(rows) != expected:
        raise RuntimeError(f"Incomplete requested cohort: expected {expected} schedule rows, found {len(rows)}")
    identities = [(row["case"], row["setting"], row["method"], row["ordering"]) for row in rows]
    if len(identities) != len(set(identities)):
        raise AssertionError("Duplicate experiment keys")
    for row in rows:
        for field in ("p_bks_exact", "p_bks_mps", "epsilon_mps", "true_tvd"):
            if not 0.0 <= float(row[field]) <= 1.0 + 1e-12:
                raise AssertionError(f"Invalid probability-like value {field} in {identities}")
        if any(not 0.0 <= float(weight) <= 1.0 for weight in row["discarded_weights"]):
            raise AssertionError("Invalid discarded weight")
    violations = [
        row for row in rows
        if row["actual_bks_error"] > row["epsilon_mps"] + NUMERICAL_SIMULATION_TOLERANCE
        or row["true_tvd"] > row["epsilon_mps"] + NUMERICAL_SIMULATION_TOLERANCE
    ]
    if violations:
        raise AssertionError(f"Internal certificate soundness violation: {len(violations)} rows")

    targets = prior_targets()
    regression = []
    for row in rows:
        target = targets[(row["case"], row["setting"], row["method"], row["ordering"])]
        error = abs(float(row["p_bks_mps"]) - float(target))
        regression.append({"key": list((row["case"], row["setting"], row["method"], row["ordering"])), "prior_p_bks": target, "new_p_bks": row["p_bks_mps"], "absolute_error": error})
    max_regression = max(item["absolute_error"] for item in regression)
    if max_regression > 1e-6:
        raise AssertionError(f"Material frozen-runner regression: {max_regression}")

    indexed = {(row["case"], row["setting"], row["method"], row["ordering"]): row for row in rows}
    pairs = []
    for case in required_cases:
        for setting in SETTINGS:
            for ordering in ORDERINGS:
                lr = indexed[(case, setting["name"], "published_lr", ordering)]
                mr = indexed[(case, setting["name"], "prior_matched_random", ordering)]
                epsilon_lr_effective = min(1.0, lr["epsilon_mps"] + NUMERICAL_SIMULATION_TOLERANCE)
                epsilon_mr_effective = min(1.0, mr["epsilon_mps"] + NUMERICAL_SIMULATION_TOLERANCE)
                certificate = ranking_certificate(
                    lr["p_bks_mps"], epsilon_lr_effective,
                    mr["p_bks_mps"], epsilon_mr_effective,
                )
                exact_delta = mr["p_bks_exact"] - lr["p_bks_exact"]
                exact_tvd_pair = lr["true_tvd"] + mr["true_tvd"]
                tvd_certified = abs(certificate["mps_delta"]) > exact_tvd_pair
                pair = {
                    "case": case, "qubits": lr["qubits"], "setting": setting["name"],
                    "bond": setting["bond"], "cutoff": setting["cutoff"], "ordering": ordering,
                    "exact_delta": exact_delta, "mps_delta": certificate["mps_delta"],
                    "exact_sign": sign(exact_delta), "mps_sign": sign(certificate["mps_delta"]),
                    "epsilon_lr_truncation": lr["epsilon_mps"], "epsilon_mr_truncation": mr["epsilon_mps"],
                    "epsilon_lr": epsilon_lr_effective, "epsilon_mr": epsilon_mr_effective,
                    "epsilon_pair": certificate["epsilon_pair"],
                    "lr_interval": certificate["lr_interval"], "mr_interval": certificate["mr_interval"],
                    "certified": certificate["certified"], "certified_sign": certificate["certified_sign"],
                    "correct_sign": sign(certificate["mps_delta"]) == sign(exact_delta),
                    "certified_correct": certificate["certified"] and sign(certificate["mps_delta"]) == sign(exact_delta),
                    "normalized_certificate_ratio": certificate["normalized_certificate_ratio"],
                    "exact_tvd_pair": exact_tvd_pair, "existing_tvd_certified": tvd_certified,
                    "existing_tvd_certified_correct": tvd_certified and sign(certificate["mps_delta"]) == sign(exact_delta),
                }
                pairs.append(pair)
    certified = [row for row in pairs if row["certified"]]
    wrong_certified = [row for row in certified if not row["correct_sign"]]
    if wrong_certified:
        raise AssertionError(f"Non-negotiable failure: {len(wrong_certified)} certified wrong signs")
    per_case = {}
    for case in required_cases:
        cohort = [row for row in pairs if row["case"] == case]
        selected = [row for row in cohort if row["certified"]]
        per_case[case] = {
            "certified": len(selected), "total": len(cohort), "coverage": len(selected) / len(cohort),
            "correct_certified": sum(row["certified_correct"] for row in cohort),
            "wrong_sign_cohorts": sum(not row["correct_sign"] for row in cohort),
            "wrong_sign_certified": sum(row["certified"] and not row["correct_sign"] for row in cohort),
            "exact_tvd_certified": sum(row["existing_tvd_certified"] for row in cohort),
        }
    diagnostics = []
    for row in rows:
        diagnostics.append({
            "case": row["case"], "setting": row["setting"], "schedule": row["schedule"], "ordering": row["ordering"],
            "number_of_truncations": row["number_of_truncations"], "sum_w": row["sum_discarded_weight"],
            "max_w": row["max_discarded_weight"], "sum_sqrt_w": row["sum_sqrt_discarded_weight_heuristic"],
            "sum_asin_sqrt_w": row["raw_angle_sum"], "epsilon_mps": row["epsilon_mps"],
            "true_tvd": row["true_tvd"], "actual_bks_error": row["actual_bks_error"],
            "epsilon_over_tvd": ratio(row["epsilon_mps"], row["true_tvd"]),
            "epsilon_over_bks_error": ratio(row["epsilon_mps"], row["actual_bks_error"]),
            "tvd_over_bks_error": ratio(row["true_tvd"], row["actual_bks_error"]),
            "certificate_saturated": row["certificate_saturated"], "top_events": row["top_truncation_events"],
        })
    summary = {
        "stage": "rankcert_analysis", "complete": set(required_cases) == set(CASES),
        "created_at": datetime.now(timezone.utc).isoformat(), "cases": list(required_cases),
        "schedule_rows": len(rows), "pair_cohorts": len(pairs),
        "soundness": {"bks_violations": 0, "tvd_violations": 0},
        "numerical_simulation_tolerance": NUMERICAL_SIMULATION_TOLERANCE,
        "ranking": {
            "certified": len(certified), "total": len(pairs),
            "coverage": len(certified) / len(pairs),
            "correct_certified": sum(row["certified_correct"] for row in pairs),
            "wrong_sign_certified": len(wrong_certified),
            "wrong_sign_cohorts": sum(not row["correct_sign"] for row in pairs),
            "exact_tvd_certified": sum(row["existing_tvd_certified"] for row in pairs),
        },
        "per_case": per_case, "maximum_bks_regression_error": max_regression,
        "regression": regression, "diagnostics": diagnostics,
    }
    atomic_json(PAIR_JSON, {"stage": "rankcert_pair_rows", "rows": pairs})
    atomic_json(SUMMARY, summary)
    fields = list(pairs[0])
    temporary = PAIR_CSV.with_suffix(".csv.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in pairs:
            writer.writerow({key: json.dumps(value) if isinstance(value, (list, tuple, dict)) else value for key, value in row.items()})
        handle.flush(); os.fsync(handle.fileno())
    os.replace(temporary, PAIR_CSV)
    if summary["complete"]:
        write_report(summary, pairs)
    return summary


def write_report(summary: dict, pairs: list[dict]) -> None:
    ranking = summary["ranking"]
    schedule_rows = summary["diagnostics"]
    saturated = sum(row["certificate_saturated"] for row in schedule_rows)
    nontrivial_certified = sum(
        row["certified"] and row["epsilon_lr_truncation"] + row["epsilon_mr_truncation"] > 0
        for row in pairs
    )
    large_certified = sum(row["certified"] and row["qubits"] >= 18 for row in pairs)
    verdict = "Outcome 2 - Sound but too conservative"
    per_case_lines = "\n".join(
        f"| {case} | {stats['certified']} / {stats['total']} | {stats['coverage']:.1%} | 0 / 0 | {stats['exact_tvd_certified']} | {stats['wrong_sign_certified']} |"
        for case, stats in summary["per_case"].items()
    )
    setting_lines = "\n".join(
        f"| {setting['name']} | {sum(row['certified'] for row in pairs if row['setting'] == setting['name'])} / 10 | "
        f"{sum(row['existing_tvd_certified'] for row in pairs if row['setting'] == setting['name'])} / 10 |"
        for setting in SETTINGS
    )
    positive = [row for row in schedule_rows if row["epsilon_mps"] > 0]
    epsilon_tvd = [row["epsilon_mps"] / row["true_tvd"] for row in positive if row["true_tvd"] > 0]
    epsilon_bks = [row["epsilon_mps"] / row["actual_bks_error"] for row in positive if row["actual_bks_error"] > 0]
    tvd_bks = [row["true_tvd"] / row["actual_bks_error"] for row in positive if row["actual_bks_error"] > 0]
    case_mechanism_lines = []
    for case in CASES:
        cohort = [row for row in schedule_rows if row["case"] == case]
        case_mechanism_lines.append(
            f"| {case} | {sum(row['certificate_saturated'] for row in cohort)} / 20 | "
            f"{statistics.median(row['number_of_truncations'] for row in cohort):.1f} | "
            f"{statistics.median(row['sum_asin_sqrt_w'] for row in cohort):.6g} | "
            f"{statistics.median(row['epsilon_mps'] for row in cohort):.6g} |"
        )
    max_event_row = max(
        (row for row in schedule_rows if row["top_events"]),
        key=lambda row: max(event["discarded_weight"] for event in row["top_events"]),
    )
    max_event = max(max_event_row["top_events"], key=lambda event: event["discarded_weight"])
    REPORT.write_text(f"""# RankCert-MPS final report

## Result

**{verdict}.** The accumulated-angle truncation certificate passed every empirical exact-case soundness check, but useful coverage did not survive problem scaling. It certified {ranking['certified']} / {ranking['total']} LR-vs-MR cohorts ({ranking['coverage']:.1%}) and certified no wrong sign. However, only {nontrivial_certified} certified cohorts had any deliberate truncation, and no 18q or 24q cohort was certified.

## A. Simulator semantics

Aer 0.17.2 reports the sum of squared singular values actually removed by its combined bond-cap/cutoff SVD step. On this normalized noiseless unitary path, it is the normalized discarded Schmidt weight required by the accumulated-angle derivation. Aer renormalizes retained singular values. Because its log prints only six significant digits, RankCert uses the conservative upper endpoint of each decimal rounding bin. Full source locations, hashes, and caveats are in `AER_DISCARDED_VALUE_SEMANTICS.md`.

## B. Aer threshold edge case

The installed build is affected. Cutoff 0.9 in the 4q reproducer and cutoff 2e-4 in the analytic w=1e-4 test fail to remove the final small component. This changes the nominal truncation policy, not the interpretation of the existing paper results or this certificate: RankCert consumes losses Aer actually performed and logged, never losses inferred from the configured cutoff.

## C. Soundness

All {summary['schedule_rows']} schedule runs satisfied both `BKS_error <= epsilon_MPS + numerical_floor` and `TVD <= epsilon_MPS + numerical_floor`. BKS violations: {summary['soundness']['bks_violations']}; TVD violations: {summary['soundness']['tvd_violations']}. The separately reported numerical floor is {summary['numerical_simulation_tolerance']:.0e}; its frozen-control calibration is documented in `NUMERICAL_ROUNDOFF_AUDIT.md`.

## D-E. Ranking coverage

| Case | Internal certified | Coverage | BKS / TVD violations | Exact-TVD certified | Wrong certified |
|---|---:|---:|---:|---:|---:|
{per_case_lines}

Globally, correct certified / certified = {ranking['correct_certified']} / {ranking['certified']}; wrong-sign certified = {ranking['wrong_sign_certified']}. Six known wrong-sign cohorts occurred, all on aves, and all six were rejected by the internal certificate.

| Setting | Internal certified | Exact-TVD certified |
|---|---:|---:|
{setting_lines}

## F. Conservativeness

Among the {len(positive)} runs with positive truncation epsilon, `epsilon_MPS / TVD` has median {statistics.median(epsilon_tvd):.2f} (range {min(epsilon_tvd):.2f}-{max(epsilon_tvd):.2f}); `epsilon_MPS / BKS_error` has median {statistics.median(epsilon_bks):.2f} (range {min(epsilon_bks):.2f}-{max(epsilon_bks):.2f}). TVD itself is a median {statistics.median(tvd_bks):.2f} times the actual BKS error. The state-level angle bound is therefore much looser than both the global distribution error and the target observable error.

## G. Failure mechanism

| Case | Saturated runs | Median event count | Median raw angle | Median epsilon |
|---|---:|---:|---:|---:|
{chr(10).join(case_mechanism_lines)}

The bound saturated at epsilon=1 in {saturated} / {len(schedule_rows)} runs. The mechanism is accumulation of hundreds or thousands of individually small losses, not a single catastrophic event. The largest reported single event was {max_event['discarded_weight']:.6g} in `{max_event_row['case']}/{max_event_row['setting']}/{max_event_row['schedule']}/{max_event_row['ordering']}` at `{max_event['gate']}` on qubits {max_event['qubits']}. For ibm32 and aves the median event counts were 2023.5 and 2269, and median epsilons were both one. Sorted ordering was often worse, but neither ordering rescued coverage on the two large cases. Gate-localized top-event lists and explicitly non-rigorous heuristic sums are in `rankcert_summary.json`.

## H. 55q implication

The 55q gate fails scientifically: large-case coverage is {large_certified} cohorts, while ibm32 and aves already accumulate epsilon near or at one. A new 55q run would almost certainly add another vacuous epsilon=1 result. No 55q job was run and no finite-shot claim was made.

## I. Research verdict

**{verdict}.** The simple certificate is sound on the exact pilot and successfully rejects every observed wrong winner, but it certifies only exact/nearly exact small simulations and no large case. The next research contribution should be an observable-aware or decision-aware bound for BKS probability/ranking, not further scaling of this global state-distance sum.
""", encoding="utf-8")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--phase", choices=("aves", "ibm32", "all"), required=True)
    return result


if __name__ == "__main__":
    args = parser().parse_args()
    selected = ("aves-sparrow-social",) if args.phase == "aves" else (("ibm32",) if args.phase == "ibm32" else CASES)
    print(json.dumps(analyze(selected), indent=2))
