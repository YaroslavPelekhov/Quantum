"""Checkpointed, memory-gated driver for the frozen exact-case Aer pilot."""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import psutil

from rankcert_inputs import CASES, METHODS, ORDERINGS, RESULTS, SETTINGS, atomic_json, validate_inputs


HERE = Path(__file__).resolve().parent
RUNS = RESULTS / "runs"
CHECKPOINT = RESULTS / "rankcert_schedule_rows.json"
CSV_OUTPUT = RESULTS / "rankcert_schedule_rows.csv"
FAILURES = RESULTS / "run_failures.json"
FINAL_STATUS = RESULTS / "FINAL_STATUS.md"


def slug(value: float) -> str:
    return format(value, ".0e").replace("+", "").replace("-0", "-")


def stem(case: str, setting: dict, method: str, ordering: str) -> str:
    return f"{case}__{setting['name']}__{method}__{ordering}"


def required_free_gib(case: str, bond: int) -> float:
    if case == "aves-sparrow-social":
        return 10.0 if bond <= 64 else (14.0 if bond <= 128 else 24.0)
    if case == "ibm32":
        return 6.0 if bond <= 128 else 10.0
    return 2.0


def load_completed_rows(runs: Path = RUNS) -> list[dict]:
    rows = []
    if not runs.exists():
        return rows
    for path in runs.glob("*.json"):
        if path.name.endswith(".events.json"):
            continue
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if row.get("complete") and row.get("stage") == "rankcert_aer_schedule_run":
            rows.append(row)
    rows.sort(key=lambda row: (CASES.index(row["case"]), row["setting"], METHODS.index(row["method"]), ORDERINGS.index(row["ordering"])))
    identities = [(row["case"], row["setting"], row["method"], row["ordering"]) for row in rows]
    if len(identities) != len(set(identities)):
        raise AssertionError("Duplicate completed schedule keys")
    return rows


def write_checkpoint() -> None:
    rows = load_completed_rows()
    atomic_json(CHECKPOINT, {
        "stage": "rankcert_aer_exact_cases", "complete": len(rows) == 100,
        "updated_at": datetime.now(timezone.utc).isoformat(), "expected_rows": 100, "rows": rows,
    })
    CSV_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = CSV_OUTPUT.with_suffix(".csv.tmp")
    fields = [
        "case", "qubits", "setting", "bond", "cutoff", "schedule", "method", "ordering",
        "p_bks_exact", "p_bks_mps", "actual_bks_error", "true_tvd", "epsilon_mps",
        "certificate_slack_bks", "certificate_slack_tvd", "number_of_truncations",
        "sum_discarded_weight", "max_discarded_weight", "max_bond_seen", "runtime_seconds",
        "peak_memory_bytes", "circuit_sha256", "raw_log_path",
    ]
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, CSV_OUTPUT)


def record_failure(payload: dict) -> None:
    prior = json.loads(FAILURES.read_text(encoding="utf-8")) if FAILURES.exists() else {"failures": []}
    prior["failures"].append(payload)
    prior["updated_at"] = datetime.now(timezone.utc).isoformat()
    atomic_json(FAILURES, prior)


def run_one(case: str, setting: dict, method: str, ordering: str, git_sha: str, timeout: int) -> bool:
    name = stem(case, setting, method, ordering)
    output = RUNS / f"{name}.json"
    if output.exists():
        try:
            prior = json.loads(output.read_text(encoding="utf-8"))
            if prior.get("complete"):
                print(f"[resume] {name}", flush=True)
                return True
        except json.JSONDecodeError:
            pass
    needed = required_free_gib(case, setting["bond"])
    available = psutil.virtual_memory().available / (1 << 30)
    if available < needed:
        message = f"Memory preflight blocked {name}: {available:.2f} GiB available, {needed:.2f} GiB required"
        print(f"[blocked] {message}", flush=True)
        FINAL_STATUS.write_text(
            "# RankCert-MPS status\n\n"
            f"Execution paused safely before `{name}`.\n\n"
            f"Available physical memory: {available:.2f} GiB; conservative requirement: {needed:.2f} GiB.\n\n"
            "No frozen artifact was changed and no partial cohort is interpreted. Close/restart the memory-heavy "
            "Telegram process, then resume with:\n\n"
            f"```powershell\n& '{sys.executable}' '{Path(__file__).resolve()}' --phase {args_phase_global}\n```\n",
            encoding="utf-8",
        )
        return False
    RUNS.mkdir(parents=True, exist_ok=True)
    raw_log = RUNS / f"{name}.mps.log"
    events = RUNS / f"{name}.events.json"
    command = [
        sys.executable, str(HERE / "run_rankcert_worker.py"),
        "--case", case, "--method", method, "--ordering", ordering,
        "--setting", setting["name"], "--bond", str(setting["bond"]),
        "--cutoff", repr(setting["cutoff"]), "--git-sha", git_sha,
        "--output", str(output), "--raw-log", str(raw_log), "--events", str(events),
    ]
    print(f"[start] {name}; free={available:.2f} GiB; timeout={timeout}s", flush=True)
    started = time.monotonic()
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    next_heartbeat = started + 30
    while process.poll() is None:
        elapsed = time.monotonic() - started
        if elapsed > timeout:
            process.terminate()
            try:
                process.wait(30)
            except subprocess.TimeoutExpired:
                process.kill()
            record_failure({"name": name, "kind": "timeout", "timeout_seconds": timeout})
            print(f"[timeout] {name}", flush=True)
            return False
        if time.monotonic() >= next_heartbeat:
            free = psutil.virtual_memory().available / (1 << 30)
            try:
                rss = psutil.Process(process.pid).memory_info().rss / (1 << 30)
            except psutil.Error:
                rss = float("nan")
            print(f"[running] {name}; elapsed={elapsed:.0f}s; child_rss={rss:.2f} GiB; free={free:.2f} GiB", flush=True)
            next_heartbeat += 30
        time.sleep(1)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        record_failure({"name": name, "kind": "worker_error", "returncode": process.returncode, "stdout": stdout[-4000:], "stderr": stderr[-8000:]})
        print(f"[failed] {name}: {stderr[-1200:]}", flush=True)
        return False
    print(f"[complete] {name}: {stdout.strip()}", flush=True)
    write_checkpoint()
    row = json.loads(output.read_text(encoding="utf-8"))
    if not row["bks_bound_holds"] or not row["tvd_bound_holds"]:
        record_failure({"name": name, "kind": "soundness_violation", "row": row})
        print(f"[STOP] soundness violation in {name}", flush=True)
        return False
    return True


def main(args) -> None:
    global args_phase_global
    args_phase_global = args.phase
    validation = validate_inputs(hash_references=not args.skip_reference_hashes)
    if not validation["complete"]:
        raise RuntimeError("Full reference hash validation is required before execution")
    environment = json.loads((RESULTS / "environment.json").read_text(encoding="utf-8"))
    git_sha = environment["repository"]["initial_state_before_modification"]["commit"]
    phase_cases = {
        "aves": ("aves-sparrow-social",),
        "ibm32": ("ibm32",),
        "all": CASES,
    }[args.phase]
    for case in phase_cases:
        for setting in SETTINGS:
            for method in METHODS:
                for ordering in ORDERINGS:
                    if not run_one(case, setting, method, ordering, git_sha, args.timeout):
                        write_checkpoint()
                        raise SystemExit(2)
    write_checkpoint()
    print(json.dumps({"phase": args.phase, "completed_rows": len(load_completed_rows()), "checkpoint": str(CHECKPOINT)}, indent=2), flush=True)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--phase", choices=("aves", "ibm32", "all"), required=True)
    result.add_argument("--timeout", type=int, default=7200)
    result.add_argument("--skip-reference-hashes", action="store_true", help=argparse.SUPPRESS)
    return result


args_phase_global = "aves"
if __name__ == "__main__":
    main(parser().parse_args())
