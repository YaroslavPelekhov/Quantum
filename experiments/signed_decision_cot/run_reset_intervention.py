"""Run frozen equal-work residual reset-window interventions."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path[:0] = [
    str(REPO / "experiments" / "compressed_observable_telescope"),
    str(REPO / "experiments" / "rankcert_mps"),
    str(REPO / "experiments" / "evoq_mis_full_qoblib"),
]

from rankcert_inputs import atomic_json, load_specs
from run_backward_feasibility import rankcert_index
from run_residual_cot import parse_primary_schedule, run_method


RESULTS = REPO / "results" / "signed_decision_cot"
COT = REPO / "results" / "compressed_observable_telescope"
PRIMARY_TEXT = "1-319:512,320-383:384,384-447:256,448-511:128,512-555:64"
WINDOWS = ((129, 192), (193, 256), (257, 320), (321, 384))


def reset_schedule(start: int, end: int) -> list[tuple[int, int, int]]:
    rows = []
    if start > 1:
        rows.append((1, start - 1, 128))
    rows.append((start, end, 32))
    if end < 555:
        rows.append((end + 1, 555, 128))
    return rows


def intervention_configs() -> list[dict]:
    return [
        {
            "key": f"reset_{start}_{end}",
            "constant_bond": None,
            "schedule": reset_schedule(start, end),
        }
        for start, end in WINDOWS
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ordering", choices=("sorted", "spectral"), required=True)
    parser.add_argument(
        "--methods",
        default="published_lr,prior_matched_random",
        help="Comma-separated method subset",
    )
    args = parser.parse_args()
    methods = tuple(x.strip() for x in args.methods.split(",") if x.strip())
    if not methods or not set(methods) <= {"published_lr", "prior_matched_random"}:
        raise ValueError(methods)

    RESULTS.mkdir(parents=True, exist_ok=True)
    output = RESULTS / f"reset_intervention_{args.ordering}.json"
    primary_schedule = parse_primary_schedule(PRIMARY_TEXT, 64)
    configs = intervention_configs()
    frozen = rankcert_index()
    specs = {
        row["method"]: row
        for row in load_specs()
        if row["case"] == "ibm32"
        and row["ordering"] == args.ordering
        and row["method"] in methods
    }

    archived = COT / f"residual_cot_ibm32_confirm_{args.ordering}_adaptive.json"
    archived_payload = json.loads(archived.read_text(encoding="utf-8"))
    forward_rows = {row["method"]: row["forward_groups"] for row in archived_payload["rows"]}

    rows = []
    for method in methods:
        print(f"[reset intervention start] {args.ordering} {method}", flush=True)
        rows.append(run_method(
            specs[method],
            frozen[("ibm32", "confirm", method, args.ordering)],
            64,
            primary_schedule,
            [],
            None,
            forward_rows[method],
            configs,
        ))
        atomic_json(output, {
            "stage": "signed_decision_equal_work_reset_intervention",
            "complete": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "ordering": args.ordering,
            "protocol": "experiments/signed_decision_cot/RESET_INTERVENTION_PROTOCOL.md",
            "configs": configs,
            "rows": rows,
        })

    payload = {
        "stage": "signed_decision_equal_work_reset_intervention",
        "complete": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "ordering": args.ordering,
        "protocol": "experiments/signed_decision_cot/RESET_INTERVENTION_PROTOCOL.md",
        "uses_exact_values_for_selection": False,
        "dense_exact_vectors_used_for_audit_only": True,
        "primary_backward_schedule": primary_schedule,
        "configs": configs,
        "rows": rows,
    }
    atomic_json(output, payload)
    print(json.dumps({
        row["method"]: {
            item["residual_config_key"]: item["operator_correction_sum"]
            for item in row["residual_ladder"]
        }
        for row in rows
    }, indent=2))


if __name__ == "__main__":
    main()

