"""Joint decision-certified resource allocation for two MPS trajectories.

The selection rule only sees approximate BKS values, certified telescope radii,
and measured resource costs.  Exact BKS values are used after selection solely
for a soundness/direction audit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
TELESCOPE = REPO / "results" / "observable_telescope"
RANKCERT = REPO / "results" / "rankcert_mps" / "rankcert_schedule_rows.json"
RESULTS = REPO / "results" / "decision_certified_allocation"
SETTINGS = ("released", "confirm", "bond128", "cutoff1e-4", "cutoff1e-5")
METHODS = ("published_lr", "prior_matched_random")
CERTIFICATE_NUMERICAL_SLACK = 2e-8


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest() -> None:
    sources = [
        HERE / "analyze_allocation.py",
        HERE / "test_allocation.py",
        HERE / "README.md",
        HERE / "NOVELTY_AND_THEOREM.md",
        HERE / "LITERATURE_POSITIONING.md",
        HERE / "SPECTRAL_HELDOUT_PROTOCOL.md",
    ]
    artifacts = [
        RESULTS / "summary.json",
        RESULTS / "pairs_sorted.json",
        RESULTS / "REPORT.md",
    ]
    inputs = [RANKCERT] + [
        TELESCOPE / f"ibm32_{setting}_sorted.json" for setting in SETTINGS
    ] + [
        TELESCOPE / f"ibm32_{setting}_spectral.json"
        for setting in ("released", "confirm")
    ]
    record = lambda path: {"bytes": path.stat().st_size, "sha256": sha256(path)}
    atomic_json(RESULTS / "MANIFEST.json", {
        "stage": "decision_certified_allocation_manifest",
        "complete": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sources": {
            path.relative_to(REPO).as_posix(): record(path) for path in sources
        },
        "inputs": {
            path.relative_to(REPO).as_posix(): record(path) for path in inputs
        },
        "artifacts": {
            path.relative_to(REPO).as_posix(): record(path) for path in artifacts
        },
    })


def cost_index(ordering: str) -> dict[tuple[str, str], dict]:
    rows = load_json(RANKCERT)["rows"]
    return {
        (row["setting"], row["method"]): row
        for row in rows
        if row["case"] == "ibm32" and row["ordering"] == ordering
    }


def trajectory_index(ordering: str, settings: tuple[str, ...]) -> dict[tuple[str, str], dict]:
    index = {}
    for setting in settings:
        path = TELESCOPE / f"ibm32_{setting}_{ordering}.json"
        payload = load_json(path)
        if not payload.get("complete"):
            raise AssertionError(f"Incomplete telescope result: {path}")
        for row in payload["rows"]:
            index[(setting, row["method"])] = row
    return index


def direction(value: float) -> int:
    return 1 if value > 0 else (-1 if value < 0 else 0)


def pair_row(lr_setting: str, mr_setting: str, trajectories: dict, costs: dict) -> dict:
    lr = trajectories[(lr_setting, "published_lr")]
    mr = trajectories[(mr_setting, "prior_matched_random")]
    lr_radius = lr["observable_telescope_bound"] + CERTIFICATE_NUMERICAL_SLACK / 2
    mr_radius = mr["observable_telescope_bound"] + CERTIFICATE_NUMERICAL_SLACK / 2
    lr_interval = [lr["p_bks_mps"] - lr_radius, lr["p_bks_mps"] + lr_radius]
    mr_interval = [mr["p_bks_mps"] - mr_radius, mr["p_bks_mps"] + mr_radius]
    delta = mr["p_bks_mps"] - lr["p_bks_mps"]
    width = lr_radius + mr_radius
    margin = abs(delta) - width
    certified_direction = -1 if mr_interval[1] < lr_interval[0] else (
        1 if lr_interval[1] < mr_interval[0] else 0
    )
    exact_delta = mr["p_bks_exact"] - lr["p_bks_exact"]
    lr_cost = costs[(lr_setting, "published_lr")]
    mr_cost = costs[(mr_setting, "prior_matched_random")]
    return {
        "lr_setting": lr_setting,
        "mr_setting": mr_setting,
        "lr_bks_mps": lr["p_bks_mps"],
        "mr_bks_mps": mr["p_bks_mps"],
        "lr_radius": lr_radius,
        "mr_radius": mr_radius,
        "lr_interval": lr_interval,
        "mr_interval": mr_interval,
        "mps_delta_mr_minus_lr": delta,
        "pair_width": width,
        "certificate_margin": margin,
        "certified": certified_direction != 0,
        "certified_direction": certified_direction,
        "exact_delta_audit_only": exact_delta,
        "correct_direction_audit_only": certified_direction == direction(exact_delta)
        if certified_direction else None,
        "individual_bounds_sound_audit_only": (
            abs(lr["p_bks_mps"] - lr["p_bks_exact"]) <= lr_radius
            and abs(mr["p_bks_mps"] - mr["p_bks_exact"]) <= mr_radius
        ),
        "lr_simulation_seconds": lr_cost["simulation_seconds"],
        "mr_simulation_seconds": mr_cost["simulation_seconds"],
        "total_simulation_seconds": (
            lr_cost["simulation_seconds"] + mr_cost["simulation_seconds"]
        ),
        "peak_memory_bytes": max(lr_cost["peak_memory_bytes"], mr_cost["peak_memory_bytes"]),
        "lr_max_bond_seen": lr_cost["max_bond_seen"],
        "mr_max_bond_seen": mr_cost["max_bond_seen"],
    }


def pareto_front(rows: list[dict]) -> list[dict]:
    """Minimize cost and maximize certificate margin."""
    front = []
    for row in rows:
        dominated = any(
            other["total_simulation_seconds"] <= row["total_simulation_seconds"]
            and other["certificate_margin"] >= row["certificate_margin"]
            and (
                other["total_simulation_seconds"] < row["total_simulation_seconds"]
                or other["certificate_margin"] > row["certificate_margin"]
            )
            for other in rows
        )
        if not dominated:
            front.append(row)
    return sorted(front, key=lambda row: row["total_simulation_seconds"])


def analyze(ordering: str, settings: tuple[str, ...] = SETTINGS) -> dict:
    trajectories = trajectory_index(ordering, settings)
    costs = cost_index(ordering)
    rows = [
        pair_row(lr_setting, mr_setting, trajectories, costs)
        for lr_setting in settings
        for mr_setting in settings
    ]
    certified = [row for row in rows if row["certified"]]
    if not certified:
        raise AssertionError("Candidate grid contains no certified allocation")
    oracle = min(certified, key=lambda row: row["total_simulation_seconds"])
    symmetric = min(
        (row for row in certified if row["lr_setting"] == row["mr_setting"]),
        key=lambda row: row["total_simulation_seconds"],
    )
    wrong = [row for row in certified if not row["correct_direction_audit_only"]]
    unsound = [row for row in rows if not row["individual_bounds_sound_audit_only"]]
    return {
        "ordering": ordering,
        "settings": list(settings),
        "candidate_pairs": len(rows),
        "certified_pairs": len(certified),
        "wrong_certificates_audit_only": len(wrong),
        "unsound_pair_inputs_audit_only": len(unsound),
        "oracle_minimum_cost_certified": oracle,
        "best_symmetric_certified": symmetric,
        "simulation_time_saving_fraction": 1.0 - (
            oracle["total_simulation_seconds"] / symmetric["total_simulation_seconds"]
        ),
        "pareto_front": pareto_front(rows),
        "rows": sorted(rows, key=lambda row: row["total_simulation_seconds"]),
    }


def report(summary: dict) -> str:
    design = summary["design_sorted"]
    oracle = design["oracle_minimum_cost_certified"]
    symmetric = design["best_symmetric_certified"]
    lines = [
        "# Decision-certified asymmetric allocation pilot",
        "",
        "## Frozen design result",
        "",
        f"The complete 5 x 5 sorted grid contains {design['certified_pairs']} certified "
        f"pairs out of {design['candidate_pairs']}. No certified pair has the wrong "
        f"exact direction in the audit.",
        "",
        "| policy | LR setting | matched-random setting | simulation s | pair width | margin |",
        "|---|---:|---:|---:|---:|---:|",
        f"| joint minimum | {oracle['lr_setting']} | {oracle['mr_setting']} | "
        f"{oracle['total_simulation_seconds']:.6f} | {oracle['pair_width']:.6f} | "
        f"{oracle['certificate_margin']:.6f} |",
        f"| best symmetric | {symmetric['lr_setting']} | {symmetric['mr_setting']} | "
        f"{symmetric['total_simulation_seconds']:.6f} | {symmetric['pair_width']:.6f} | "
        f"{symmetric['certificate_margin']:.6f} |",
        "",
        f"Measured forward-simulation saving: {100 * design['simulation_time_saving_fraction']:.2f}%.",
        "",
        "The selection objective uses only approximate values, certified telescope radii, "
        "and costs. Exact values are excluded from selection and retained only for the "
        "post-selection soundness audit.",
    ]
    heldout = summary.get("heldout_spectral")
    if heldout:
        chosen = heldout["frozen_design_allocation"]
        baseline = heldout["frozen_symmetric_baseline"]
        lines += [
            "",
            "## Frozen spectral held-out result",
            "",
            "| policy | LR setting | matched-random setting | simulation s | certified | margin | correct |",
            "|---|---:|---:|---:|---:|---:|---:|",
            f"| transferred joint | {chosen['lr_setting']} | {chosen['mr_setting']} | "
            f"{chosen['total_simulation_seconds']:.6f} | {chosen['certified']} | "
            f"{chosen['certificate_margin']:.6f} | {chosen['correct_direction_audit_only']} |",
            f"| symmetric baseline | {baseline['lr_setting']} | {baseline['mr_setting']} | "
            f"{baseline['total_simulation_seconds']:.6f} | {baseline['certified']} | "
            f"{baseline['certificate_margin']:.6f} | {baseline['correct_direction_audit_only']} |",
            "",
            f"Frozen-transfer measured saving: "
            f"{100 * heldout['simulation_time_saving_fraction']:.2f}%.",
        ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-spectral", action="store_true")
    args = parser.parse_args()
    design = analyze("sorted")
    summary = {
        "stage": "decision_certified_asymmetric_allocation",
        "complete": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "certificate_numerical_slack": CERTIFICATE_NUMERICAL_SLACK,
        "selection_uses_exact_values": False,
        "design_sorted": design,
    }
    if args.include_spectral:
        spectral_settings = ("released", "confirm")
        spectral = analyze("spectral", spectral_settings)
        by_pair = {
            (row["lr_setting"], row["mr_setting"]): row for row in spectral["rows"]
        }
        summary["heldout_spectral"] = {
            "settings_evaluated": list(spectral_settings),
            "allocation_was_frozen_before_execution": True,
            "frozen_design_allocation": by_pair[("released", "confirm")],
            "frozen_symmetric_baseline": by_pair[("confirm", "confirm")],
            "simulation_time_saving_fraction": 1.0 - (
                by_pair[("released", "confirm")]["total_simulation_seconds"]
                / by_pair[("confirm", "confirm")]["total_simulation_seconds"]
            ),
            "all_four_rows_for_audit": spectral["rows"],
        }
    atomic_json(RESULTS / "summary.json", summary)
    atomic_json(RESULTS / "pairs_sorted.json", {
        "complete": True, "rows": design["rows"]
    })
    (RESULTS / "REPORT.md").write_text(report(summary), encoding="utf-8")
    write_manifest()
    print(json.dumps({
        "oracle": design["oracle_minimum_cost_certified"],
        "best_symmetric": design["best_symmetric_certified"],
        "saving_fraction": design["simulation_time_saving_fraction"],
        "heldout": summary.get("heldout_spectral"),
    }, indent=2))


if __name__ == "__main__":
    main()
