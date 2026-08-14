"""Exact plus seeded Aer-MPS pilot on the new screen-selected QOBLIB cases."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import psutil

import run_cycle as rc
import run_resource_aware_cycle as rr


HERE = Path(__file__).resolve().parent
PROTOCOL = HERE / "EXPANDED_QOBLIB_PILOT_PROTOCOL.md"
SCREEN = HERE / "results" / "qoblib_cohort_screen" / "selected_cases.json"
RESULTS = HERE / "results" / "expanded_qoblib_pilot"
EXACT = RESULTS / "exact.json"
MPS = RESULTS / "mps.json"
ANALYSIS = RESULTS / "analysis.json"
DEPTH = 15
NEW_CASES = ("es60fst01", "es60fst03", "mammalia-kangaroo-interactions")
METHODS = {
    "published_lr": [0.7, 0.4, 1.0, 1.0],
    "prior_evolutionary": [0.5175030726816078, 0.7719741612274684, 1.0773373543262421, 1.7543477389249704],
    "prior_matched_random": [0.6424738670407446, 0.7593921349176262, 1.776791693083474, 0.9917239502490107],
}
ORDERINGS = ("sorted", "spectral")
SETTINGS = {
    "released": {"bond": 64, "cutoff": 1e-3},
    "confirm": {"bond": 128, "cutoff": 1e-4},
}
SEEDS = (41001, 41002, 41003)
SHOTS = 500
MIN_AVAILABLE_GIB = 8.0
MAX_PROCESS_GIB = 8.0


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def git_commit(path: Path) -> str:
    try:
        return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def provenance() -> dict:
    import qiskit
    import qiskit_aer

    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "qiskit": qiskit.__version__,
        "qiskit_aer": qiskit_aer.__version__,
        "numpy": np.__version__,
        "protocol_sha256": sha256(PROTOCOL),
        "screen_sha256": sha256(SCREEN),
        "qoblib_commit": git_commit(rc.QOBLIB),
        "qoblib_solutions_commit": git_commit(rc.BASELINE_REPO),
    }


def safety_check() -> dict:
    virtual = psutil.virtual_memory()
    process_gib = psutil.Process(os.getpid()).memory_info().rss / (1024**3)
    available_gib = virtual.available / (1024**3)
    if available_gib < MIN_AVAILABLE_GIB:
        raise RuntimeError(f"Safety stop: only {available_gib:.2f} GiB RAM available")
    if process_gib > MAX_PROCESS_GIB:
        raise RuntimeError(f"Safety stop: process RSS is {process_gib:.2f} GiB")
    return {"available_gib": available_gib, "process_rss_gib": process_gib}


def configuration() -> tuple[dict[str, int], dict[str, int]]:
    screen = read_json(SCREEN)
    selected = {row["case"]: row for row in screen["selected_cases"]}
    missing = set(NEW_CASES) - set(selected)
    if missing:
        raise RuntimeError(f"New cases missing from frozen screen: {sorted(missing)}")
    cases = {name: int(selected[name]["cap"]) for name in NEW_CASES}
    bks = {name: int(selected[name]["bks"]) for name in NEW_CASES}
    rc.BKS.update(bks)
    return cases, bks


def exact_identity(row: dict) -> tuple:
    return row["case"], row["method"], row["ordering"]


def mps_identity(row: dict) -> tuple:
    return row["case"], row["method"], row["ordering"], row["setting"], int(row["seed"])


def run_exact() -> dict:
    cases, bks = configuration()
    checkpoint = read_json(EXACT) if EXACT.exists() else {"complete": False, "rows": [], "errors": []}
    unique = {exact_identity(row): row for row in checkpoint["rows"]}
    for name, cap in cases.items():
        prepared = {ordering: rr.prepare_case(name, cap, ordering) for ordering in ORDERINGS}
        for method, genome in METHODS.items():
            for ordering, case in prepared.items():
                key = (name, method, ordering)
                if key in unique:
                    print("[resume exact]", "/".join(key), flush=True)
                    continue
                memory = safety_check()
                print("[start exact]", "/".join(key), flush=True)
                result = rr.exact_evaluate(case, np.asarray(genome), DEPTH)
                unique[key] = {
                    "case": name, "bks": bks[name], "cap": cap, "qubits": case.qubits,
                    "method": method, "genome": genome, "ordering": ordering, "depth": DEPTH,
                    "memory_before": memory, **result,
                }
                write_json(EXACT, {"complete": False, "protocol_sha256": sha256(PROTOCOL), "rows": list(unique.values()), "errors": []})
    rows = sorted(unique.values(), key=exact_identity)
    expected = len(cases) * len(METHODS) * len(ORDERINGS)
    if len(rows) != expected:
        raise AssertionError(f"Expected {expected} exact rows, found {len(rows)}")
    payload = {"complete": True, "provenance": provenance(), "cases": cases, "expected_rows": expected, "rows": rows, "errors": []}
    write_json(EXACT, payload)
    return payload


def run_mps() -> dict:
    cases, bks = configuration()
    checkpoint = read_json(MPS) if MPS.exists() else {"complete": False, "rows": [], "errors": []}
    unique = {mps_identity(row): row for row in checkpoint["rows"]}
    errors = checkpoint.get("errors", [])
    for name, cap in cases.items():
        prepared = {ordering: rr.prepare_case(name, cap, ordering) for ordering in ORDERINGS}
        for method, genome in METHODS.items():
            for ordering, case in prepared.items():
                for setting_name, setting in SETTINGS.items():
                    for seed in SEEDS:
                        key = (name, method, ordering, setting_name, seed)
                        if key in unique:
                            continue
                        memory = safety_check()
                        print("[start mps]", "/".join(map(str, key)), flush=True)
                        try:
                            result = rr.mps_evaluate(case, np.asarray(genome), DEPTH, SHOTS, seed, setting["bond"], setting["cutoff"])
                        except Exception as exc:
                            errors.append({"identity": list(key), "type": type(exc).__name__, "message": str(exc)})
                            write_json(MPS, {"complete": False, "protocol_sha256": sha256(PROTOCOL), "rows": list(unique.values()), "errors": errors})
                            raise
                        unique[key] = {
                            "case": name, "bks": bks[name], "cap": cap, "qubits": case.qubits,
                            "method": method, "genome": genome, "ordering": ordering, "depth": DEPTH,
                            "setting": setting_name, **setting, "seed": seed, "shots": SHOTS,
                            "memory_before": memory, **result,
                        }
                        write_json(MPS, {"complete": False, "protocol_sha256": sha256(PROTOCOL), "rows": list(unique.values()), "errors": errors})
    rows = sorted(unique.values(), key=mps_identity)
    expected = len(cases) * len(METHODS) * len(ORDERINGS) * len(SETTINGS) * len(SEEDS)
    if len(rows) != expected:
        raise AssertionError(f"Expected {expected} MPS rows, found {len(rows)}")
    payload = {"complete": True, "provenance": provenance(), "cases": cases, "settings": SETTINGS, "seeds": SEEDS, "shots": SHOTS, "expected_rows": expected, "rows": rows, "errors": errors}
    write_json(MPS, payload)
    return payload


def sign(value: float, tolerance: float = 1e-12) -> int:
    return 1 if value > tolerance else -1 if value < -tolerance else 0


def analyze() -> dict:
    exact = read_json(EXACT)
    mps = read_json(MPS)
    if not exact.get("complete") or not mps.get("complete"):
        raise RuntimeError("Complete exact and MPS checkpoints required")
    exact_lookup = {(r["case"], r["method"], r["ordering"]): r for r in exact["rows"]}
    groups: dict[tuple, list[dict]] = {}
    for row in mps["rows"]:
        groups.setdefault((row["case"], row["method"], row["ordering"], row["setting"]), []).append(row)
    aggregates = []
    for key, jobs in sorted(groups.items()):
        total = sum(job["metrics"]["total_shots"] for job in jobs)
        aggregates.append({
            "case": key[0], "method": key[1], "ordering": key[2], "setting": key[3],
            "jobs": len(jobs), "total_shots": total,
            "bks_rate": sum(job["metrics"]["bks_hits"] for job in jobs) / total,
            "near_bks_rate": sum(job["metrics"]["near_bks_hits"] for job in jobs) / total,
            "feasible_rate": sum(job["metrics"]["feasible_shots"] for job in jobs) / total,
            "median_elapsed_seconds": float(np.median([job["elapsed_seconds"] for job in jobs])),
        })
    agg_lookup = {(r["case"], r["method"], r["ordering"], r["setting"]): r for r in aggregates}
    effects = []
    for case in NEW_CASES:
        for ordering in ORDERINGS:
            for candidate in ("prior_evolutionary", "prior_matched_random"):
                exact_effect = exact_lookup[(case, candidate, ordering)]["metrics"]["bks_rate"] - exact_lookup[(case, "published_lr", ordering)]["metrics"]["bks_rate"]
                for setting in SETTINGS:
                    approximate_effect = agg_lookup[(case, candidate, ordering, setting)]["bks_rate"] - agg_lookup[(case, "published_lr", ordering, setting)]["bks_rate"]
                    effects.append({
                        "case": case, "ordering": ordering, "candidate": candidate, "setting": setting,
                        "exact_effect": exact_effect, "approximate_effect": approximate_effect,
                        "exact_sign": sign(exact_effect), "approximate_sign": sign(approximate_effect),
                        "sign_correct": sign(exact_effect) == sign(approximate_effect),
                        "absolute_effect_error": abs(approximate_effect - exact_effect),
                    })
    payload = {
        "complete": True, "provenance": provenance(),
        "summary": {
            "cases": len(NEW_CASES), "exact_rows": len(exact["rows"]), "mps_rows": len(mps["rows"]),
            "effect_cohorts": len(effects), "sign_correct": sum(row["sign_correct"] for row in effects),
            "max_absolute_effect_error": max(row["absolute_effect_error"] for row in effects),
            "total_shots": sum(row["shots"] for row in mps["rows"]),
        },
        "aggregates": aggregates, "effects": effects,
    }
    write_json(ANALYSIS, payload)
    print(json.dumps(payload["summary"], indent=2), flush=True)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("exact", "mps", "analyze", "all"), nargs="?", default="all")
    command = parser.parse_args().command
    if command in ("exact", "all"):
        run_exact()
    if command in ("mps", "all"):
        run_mps()
    if command in ("analyze", "all"):
        analyze()


if __name__ == "__main__":
    main()
