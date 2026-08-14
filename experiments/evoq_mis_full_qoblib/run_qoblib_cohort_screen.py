"""Frozen, checkpointed screen for an expanded QOBLIB MIS cohort."""

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
from time import perf_counter

import numpy as np
import psutil
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_array

import run_cycle as rc


HERE = Path(__file__).resolve().parent
PROTOCOL = HERE / "QOBLIB_COHORT_SCREEN_PROTOCOL.md"
RESULTS = HERE / "results" / "qoblib_cohort_screen"
CHECKPOINT = RESULTS / "screen.json"
SELECTION = RESULTS / "selected_cases.json"
CAPS = (32, 24, 20, 16, 12, 10, 8, 6, 4)
MAX_QUBITS = 24
MILP_TIME_LIMIT = 30.0
TARGET_CASES = 15
ANCHORS = (
    "aves-sparrow-social",
    "chesapeake",
    "football",
    "ibm32",
    "karate",
)


def peak_process_rss_mib() -> float:
    memory = psutil.Process(os.getpid()).memory_info()
    return float(getattr(memory, "peak_wset", memory.rss)) / (1024**2)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_commit(path: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(path), "rev-parse", "HEAD"], text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def load_bks_table() -> dict[str, dict]:
    path = rc.QOBLIB / "07-independentset" / "solutions" / "README.md"
    table: dict[str, dict] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = [field.strip() for field in line.split("|")]
        if len(fields) < 6 or not fields[2].isdigit():
            continue
        table[fields[1]] = {"bks": int(fields[2]), "status": fields[3]}
    return table


def family(name: str) -> str:
    prefixes = (
        "brock", "frb", "hamming", "johnson", "sloane", "socfb", "sorrell",
        "es60", "insecta", "p_hat", "R_", "C", "c-fat", "keller",
    )
    for prefix in prefixes:
        if name.startswith(prefix):
            return prefix.rstrip("_-").lower()
    if name in {"karate", "football", "chesapeake", "farm"}:
        return "named_network"
    if name in {"aves-sparrow-social", "mammalia-kangaroo-interactions"}:
        return "animal_network"
    if name == "ibm32":
        return "hardware_graph"
    if name == "MANN-a9":
        return "mann"
    if name.startswith("gen"):
        return "generated_random"
    return "other"


def qubit_stratum(qubits: int) -> str:
    if qubits <= 7:
        return "01-07"
    if qubits <= 12:
        return "08-12"
    if qubits <= 18:
        return "13-18"
    return "19-24"


def provenance() -> dict:
    import networkx
    import scipy

    return {
        "created_at": utc_now(),
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "networkx": networkx.__version__,
        "protocol_sha256": sha256(PROTOCOL),
        "qoblib_commit": git_commit(rc.QOBLIB),
        "qoblib_solutions_commit": git_commit(rc.BASELINE_REPO),
        "caps": list(CAPS),
        "max_qubits": MAX_QUBITS,
        "milp_time_limit_seconds": MILP_TIME_LIMIT,
    }


def exact_candidate(name: str, bks: int, cap: int) -> dict:
    graph_path = rc.QOBLIB / "07-independentset" / "instances" / f"{name}.gph"
    graph = rc.parse_gph_file(graph_path)
    start = perf_counter()
    reduction = rc.reduce_graph_for_quantum(graph, max_degree=cap)
    reduced = reduction.reduced_graph
    reduction_seconds = perf_counter() - start
    base = {
        "case": name,
        "family": family(name),
        "bks": bks,
        "cap": cap,
        "original_vertices": graph.number_of_nodes(),
        "original_edges": graph.number_of_edges(),
        "qubits": reduced.number_of_nodes(),
        "reduced_edges": reduced.number_of_edges(),
        "forced_selected_vertices": len(reduction.nodes_to_add),
        "heuristically_pruned_vertices": len(reduction.pruned_nodes),
        "reduction_seconds": reduction_seconds,
        "input_sha256": sha256(graph_path),
    }
    if reduced.number_of_nodes() == 0:
        decoded = rc.MISPostprocessor(graph, reduction, repair_samples=False).decode("")
        return {
            **base,
            "status": "empty_deterministic_kernel",
            "decoded_size": int(decoded.raw_selected),
            "raw_feasible": bool(decoded.raw_feasible),
            "bks_reachable": bool(decoded.raw_feasible and decoded.raw_selected >= bks),
            "milp_seconds": 0.0,
        }
    if reduced.number_of_nodes() > MAX_QUBITS:
        return {
            **base,
            "status": "above_qubit_limit",
            "decoded_size": None,
            "raw_feasible": None,
            "bks_reachable": False,
            "milp_seconds": 0.0,
        }

    nodes = sorted(reduced.nodes())
    index = {node: i for i, node in enumerate(nodes)}
    rows: list[int] = []
    cols: list[int] = []
    for row, (u, v) in enumerate(reduced.edges()):
        rows.extend((row, row))
        cols.extend((index[u], index[v]))
    matrix = coo_array(
        (np.ones(len(rows)), (rows, cols)),
        shape=(reduced.number_of_edges(), len(nodes)),
    ).tocsr()
    solve_start = perf_counter()
    result = milp(
        -np.ones(len(nodes)),
        integrality=np.ones(len(nodes)),
        bounds=Bounds(0, 1),
        constraints=LinearConstraint(matrix, -np.inf, 1),
        options={"time_limit": MILP_TIME_LIMIT, "mip_rel_gap": 0.0, "presolve": True},
    )
    solve_seconds = perf_counter() - solve_start
    if not result.success or result.x is None:
        return {
            **base,
            "status": "milp_incomplete",
            "milp_message": str(result.message),
            "decoded_size": None,
            "raw_feasible": None,
            "bks_reachable": False,
            "milp_seconds": solve_seconds,
        }
    selected = {node for node, value in zip(nodes, result.x) if value > 0.5}
    bitstring = "".join("1" if node in selected else "0" for node in nodes)
    decoded = rc.MISPostprocessor(graph, reduction, repair_samples=False).decode(bitstring)
    return {
        **base,
        "status": "certified",
        "reduced_optimum": len(selected),
        "decoded_size": int(decoded.raw_selected),
        "raw_feasible": bool(decoded.raw_feasible),
        "bks_reachable": bool(decoded.raw_feasible and decoded.raw_selected >= bks),
        "milp_seconds": solve_seconds,
        "milp_gap": float(getattr(result, "mip_gap", 0.0) or 0.0),
    }


def select_cases(rows: list[dict], table: dict[str, dict]) -> dict:
    successful: dict[str, dict] = {}
    for row in rows:
        if (
            row["status"] == "certified"
            and row["bks_reachable"]
            and 0 < row["qubits"] <= MAX_QUBITS
            and row["case"] not in successful
        ):
            successful[row["case"]] = row

    primary = {
        name: {**row, "bks_status": table[name]["status"], "stratum": qubit_stratum(row["qubits"])}
        for name, row in successful.items()
        if table[name]["status"].lower() == "optimal"
    }
    exploratory = {
        name: {**row, "bks_status": table[name]["status"], "stratum": qubit_stratum(row["qubits"])}
        for name, row in successful.items()
        if table[name]["status"].lower() != "optimal"
    }
    selected = [name for name in ANCHORS if name in primary]
    candidates = [row for name, row in primary.items() if name not in selected]
    candidates.sort(key=lambda row: (row["stratum"], row["family"], row["case"]))
    used_pairs: set[tuple[str, str]] = set()
    while candidates and len(selected) < TARGET_CASES:
        index = next(
            (i for i, row in enumerate(candidates) if (row["stratum"], row["family"]) not in used_pairs),
            0,
        )
        row = candidates.pop(index)
        selected.append(row["case"])
        used_pairs.add((row["stratum"], row["family"]))
        if len(used_pairs) == len({(item["stratum"], item["family"]) for item in candidates}):
            used_pairs.clear()
    return {
        "complete": True,
        "selection_rule": "anchors_then_deterministic_stratum_family_round_robin",
        "target_cases": TARGET_CASES,
        "selected_cases": [{**primary[name], "anchor": name in ANCHORS} for name in selected],
        "primary_eligible": sorted(primary.values(), key=lambda row: row["case"]),
        "exploratory_eligible": sorted(exploratory.values(), key=lambda row: row["case"]),
    }


def run() -> None:
    table = load_bks_table()
    instances = sorted(
        path.stem for path in (rc.QOBLIB / "07-independentset" / "instances").glob("*.gph")
    )
    if set(instances) != set(table):
        raise RuntimeError("QOBLIB instance/BKS table mismatch")
    payload = json.loads(CHECKPOINT.read_text(encoding="utf-8")) if CHECKPOINT.exists() else {
        "complete": False,
        "provenance": provenance(),
        "instances": instances,
        "rows": [],
    }
    rows = payload["rows"]
    completed = {(row["case"], int(row["cap"])) for row in rows}
    start = perf_counter()
    for index, name in enumerate(instances, 1):
        if any(row["case"] == name and row.get("bks_reachable") and row["status"] == "certified" for row in rows):
            print(f"[resume {index:02d}/{len(instances)}] {name}: already eligible", flush=True)
            continue
        for cap in CAPS:
            if (name, cap) in completed:
                row = next(row for row in rows if row["case"] == name and row["cap"] == cap)
            else:
                print(f"[screen {index:02d}/{len(instances)}] {name}/cap{cap}", flush=True)
                row = {**exact_candidate(name, table[name]["bks"], cap), "bks_status": table[name]["status"]}
                rows.append(row)
                completed.add((name, cap))
                payload.update({
                    "updated_at": utc_now(),
                    "elapsed_this_run_seconds": perf_counter() - start,
                    "peak_process_rss_mib": peak_process_rss_mib(),
                    "rows": rows,
                })
                write_json(CHECKPOINT, payload)
            if row["status"] == "certified" and row["bks_reachable"]:
                print(f"  eligible: q={row['qubits']} cap={cap} decoded={row['decoded_size']}", flush=True)
                break
    selection = select_cases(rows, table)
    payload.update({
        "complete": True,
        "completed_at": utc_now(),
        "elapsed_this_run_seconds": perf_counter() - start,
        "peak_process_rss_mib": peak_process_rss_mib(),
        "rows": rows,
        "summary": {
            "instances": len(instances),
            "attempts": len(rows),
            "primary_eligible": len(selection["primary_eligible"]),
            "exploratory_eligible": len(selection["exploratory_eligible"]),
            "selected": len(selection["selected_cases"]),
        },
    })
    write_json(CHECKPOINT, payload)
    write_json(SELECTION, {"provenance": payload["provenance"], **selection})
    print(json.dumps(payload["summary"], indent=2), flush=True)
    print("selected:", ", ".join(row["case"] for row in selection["selected_cases"]), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("run", "summary"), nargs="?", default="run")
    args = parser.parse_args()
    if args.command == "run":
        run()
    elif not SELECTION.exists():
        raise SystemExit("No completed selection")
    else:
        data = json.loads(SELECTION.read_text(encoding="utf-8"))
        print(json.dumps({
            "selected": len(data["selected_cases"]),
            "primary_eligible": len(data["primary_eligible"]),
            "exploratory_eligible": len(data["exploratory_eligible"]),
            "cases": [row["case"] for row in data["selected_cases"]],
        }, indent=2))


if __name__ == "__main__":
    main()
