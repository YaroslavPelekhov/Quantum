"""Rigorous observable-rank certificates for the completed 24q MPS ladders."""

from __future__ import annotations

import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EXACT = ROOT / "results" / "mps_ladder" / "exact_references.json"
AER = ROOT / "results" / "mps_ladder" / "mps_ladder.json"
CUTN = ROOT / "results" / "independent_ladder" / "mps_jobs.json"
OUTPUT = ROOT / "results" / "rank_certificates.json"
REPORT = ROOT / "RANK_CERTIFICATE_REPORT.md"
SETTINGS = ("released", "confirm", "bond128", "cutoff1e-4", "cutoff1e-5")
ORDERINGS = ("sorted", "spectral")
METHOD_A = "published_lr"
METHOD_B = "prior_matched_random"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_write(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def certificate_row(backend: str, setting: str, ordering: str, rows: dict, exact: dict) -> dict:
    lr = rows[(setting, METHOD_A, ordering)]
    matched = rows[(setting, METHOD_B, ordering)]
    exact_effect = (
        exact[(METHOD_B, ordering)]["metrics"]["bks_rate"]
        - exact[(METHOD_A, ordering)]["metrics"]["bks_rate"]
    )
    approximate_effect = matched["metrics"]["bks_rate"] - lr["metrics"]["bks_rate"]
    actual_effect_error = abs(approximate_effect - exact_effect)
    tvd_bound = (
        matched["comparison"]["total_variation_distance"]
        + lr["comparison"]["total_variation_distance"]
    )
    fidelity_bound = math.sqrt(max(0.0, 1.0 - matched["comparison"]["state_fidelity"])) + math.sqrt(
        max(0.0, 1.0 - lr["comparison"]["state_fidelity"])
    )
    return {
        "backend": backend,
        "setting": setting,
        "ordering": ordering,
        "exact_effect": exact_effect,
        "approximate_effect": approximate_effect,
        "actual_effect_error": actual_effect_error,
        "tvd_effect_error_bound": tvd_bound,
        "fidelity_effect_error_bound": fidelity_bound,
        "bound_valid": actual_effect_error <= tvd_bound + 1e-12,
        "exact_margin_tvd_certified": abs(exact_effect) > tvd_bound,
        "approximate_margin_tvd_certified": abs(approximate_effect) > tvd_bound,
        "exact_margin_fidelity_certified": abs(exact_effect) > fidelity_bound,
        "sign_correct": math.copysign(1.0, approximate_effect) == math.copysign(1.0, exact_effect),
        "tvd_bound_slack": tvd_bound - actual_effect_error,
        "bound_tightness": actual_effect_error / tvd_bound if tvd_bound else 0.0,
    }


def main() -> None:
    exact_payload, aer_payload, cutn_payload = load(EXACT), load(AER), load(CUTN)
    if not exact_payload.get("complete") or len(exact_payload.get("rows", [])) != 6:
        raise RuntimeError("Complete exact references are required")
    if not aer_payload.get("complete") or not cutn_payload.get("complete"):
        raise RuntimeError("Both completed backend ladders are required")
    exact = {(row["method"], row["ordering"]): row for row in exact_payload["rows"]}
    backend_rows = {
        "Aer": {(row["setting"], row["method"], row["ordering"]): row for row in aer_payload["rows"]},
        "cuTensorNet": {
            (row["setting"], row["method"], row["ordering"]): row
            for row in cutn_payload["rows"]
        },
    }
    rows = [
        certificate_row(backend, setting, ordering, mapping, exact)
        for backend, mapping in backend_rows.items()
        for setting in SETTINGS
        for ordering in ORDERINGS
    ]
    if not all(row["bound_valid"] for row in rows):
        raise AssertionError("A measured effect error exceeded its TVD union bound")
    payload = {
        "stage": "posthoc_observable_rank_certificates",
        "complete": True,
        "theorem": (
            "For event A and schedules i,j, |(q_i(A)-q_j(A))-(p_i(A)-p_j(A))| "
            "<= TVD(q_i,p_i)+TVD(q_j,p_j)."
        ),
        "rows": rows,
        "summary": {
            "cohorts": len(rows),
            "sign_correct": sum(row["sign_correct"] for row in rows),
            "exact_margin_tvd_certified": sum(row["exact_margin_tvd_certified"] for row in rows),
            "approximate_margin_tvd_certified": sum(
                row["approximate_margin_tvd_certified"] for row in rows
            ),
            "exact_margin_fidelity_certified": sum(
                row["exact_margin_fidelity_certified"] for row in rows
            ),
        },
    }
    atomic_write(OUTPUT, payload)
    write_report(payload)
    print(json.dumps(payload["summary"], indent=2))


def write_report(payload: dict) -> None:
    lines = [
        "# Observable-rank certificate audit",
        "",
        "For a BKS event and two schedules, the absolute error of their probability",
        "difference is bounded by the sum of their two total-variation distances.",
        "This is a sufficient, observable-level rank certificate; it is deliberately",
        "more conservative than checking the realized sign against exact.",
        "",
        "| Backend | Setting | Order | Approx effect | Actual error | TVD bound | Exact-margin certified | Sign correct |",
        "|---|---|---|---:|---:|---:|---|---|",
    ]
    for row in payload["rows"]:
        lines.append(
            "| {backend} | {setting} | {ordering} | {approximate_effect:+.8f} | "
            "{actual_effect_error:.8f} | {tvd_effect_error_bound:.8f} | "
            "{exact_margin_tvd_certified} | {sign_correct} |".format(**row)
        )
    lines.extend(["", f"Summary: `{json.dumps(payload['summary'], sort_keys=True)}`", ""])
    REPORT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
