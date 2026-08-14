"""Exact-calibrated, checkpointed MPS fidelity ladder on QOBLIB MIS."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import platform
import sys
from pathlib import Path
from time import perf_counter

import numpy as np
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator

import run_cycle as rc
import run_exact_extension as exact_extension


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results" / "mps_ladder"
REFERENCES = RESULTS / "references"
PROTOCOL = HERE / "MPS_LADDER_PROTOCOL.md"
REFERENCE_CHECKPOINT = RESULTS / "exact_references.json"
LADDER_CHECKPOINT = RESULTS / "mps_ladder.json"
ANALYSIS = RESULTS / "analysis.json"
REPORT = HERE / "MPS_LADDER_REPORT.md"
EXACT_EXTENSION = HERE / "results" / "exact_extension" / "aves_exact.json"

CASE = exact_extension.CASE
CAP = exact_extension.CAP
DEPTH = exact_extension.DEPTH
ORDERINGS = exact_extension.ORDERINGS
METHODS = exact_extension.METHODS
METRICS = exact_extension.METRICS
COMPARE_CHUNK = 1 << 18

SETTINGS = (
    {"name": "released", "family": "anchor", "bond": 64, "cutoff": 1e-3},
    {"name": "confirm", "family": "anchor", "bond": 128, "cutoff": 1e-4},
    {"name": "bond64", "family": "bond", "bond": 64, "cutoff": 1e-12},
    {"name": "bond128", "family": "bond", "bond": 128, "cutoff": 1e-12},
    {"name": "bond256", "family": "bond", "bond": 256, "cutoff": 1e-12},
    {"name": "bond512", "family": "bond", "bond": 512, "cutoff": 1e-12},
    {"name": "bond1024", "family": "bond", "bond": 1024, "cutoff": 1e-12},
    {"name": "cutoff1e-3", "family": "cutoff", "bond": 1024, "cutoff": 1e-3},
    {"name": "cutoff1e-4", "family": "cutoff", "bond": 1024, "cutoff": 1e-4},
    {"name": "cutoff1e-5", "family": "cutoff", "bond": 1024, "cutoff": 1e-5},
    {"name": "cutoff1e-6", "family": "cutoff", "bond": 1024, "cutoff": 1e-6},
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def protocol_hash() -> str:
    return sha256(PROTOCOL)


def jsonable(value):
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, Path):
        return value.as_posix()
    return value


def atomic_write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(jsonable(payload), handle, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def atomic_save_npy(path: Path, array: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as handle:
        np.save(handle, np.asarray(array, dtype=np.complex128), allow_pickle=False)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def provenance() -> dict:
    import qiskit
    import qiskit_aer
    import scipy

    return {
        "python": sys.version,
        "platform": platform.platform(),
        "qiskit": qiskit.__version__,
        "qiskit_aer": qiskit_aer.__version__,
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "protocol_sha256": protocol_hash(),
        "runner_sha256": sha256(Path(__file__)),
        "exact_runner_sha256": sha256(HERE / "run_exact_extension.py"),
        "exact_artifact_sha256": sha256(EXACT_EXTENSION),
        "qoblib_solutions_commit": rc.git_commit(rc.BASELINE_REPO),
    }


def reference_path(method: str, ordering: str) -> Path:
    return REFERENCES / f"{method}__{ordering}.npy"


def reference_identity(row: dict) -> tuple[str, str]:
    return row["method"], row["ordering"]


def job_identity(row: dict) -> tuple[str, str, str]:
    return row["method"], row["ordering"], row["setting"]


def exact_reference_rows() -> dict:
    payload = read_json(EXACT_EXTENSION)
    if not payload.get("complete", False) or len(payload.get("rows", [])) != 6:
        raise RuntimeError("Completed six-row exact extension is required")
    return {reference_identity(row): row for row in payload["rows"]}


def stage_reference() -> dict:
    exact_rows = exact_reference_rows()
    previous = read_json(REFERENCE_CHECKPOINT) if REFERENCE_CHECKPOINT.exists() else {}
    if previous and previous.get("protocol_sha256") != protocol_hash():
        raise RuntimeError("Protocol hash changed after reference checkpoint creation")
    unique = {reference_identity(row): row for row in previous.get("rows", [])}

    for method, genome in METHODS.items():
        for ordering in ORDERINGS:
            key = (method, ordering)
            path = reference_path(method, ordering)
            if key in unique and path.exists() and sha256(path) == unique[key]["state_sha256"]:
                print(f"[reference] resume skip {method}/{ordering}", flush=True)
                continue
            print(f"[reference] starting {method}/{ordering}", flush=True)
            case = exact_extension.resource.prepare_case(CASE, CAP, ordering)
            circuit = exact_extension.resource.circuit_for(case, np.asarray(genome), DEPTH)
            bare = circuit.remove_final_measurements(inplace=False)
            started = perf_counter()
            state = Statevector.from_instruction(bare)
            simulation_seconds = perf_counter() - started
            metrics, accumulator = exact_extension.streaming_probability_metrics(
                case, np.asarray(state.data)
            )
            expected_metrics = exact_rows[key]["metrics"]
            max_metric_error = max(abs(metrics[name] - expected_metrics[name]) for name in METRICS)
            if max_metric_error > 1e-10:
                raise AssertionError(
                    f"Exact reference mismatch for {method}/{ordering}: {max_metric_error}"
                )
            atomic_save_npy(path, np.asarray(state.data))
            row = {
                "case": CASE,
                "method": method,
                "ordering": ordering,
                "qubits": case.qubits,
                "depth": DEPTH,
                "state_file": path.relative_to(HERE).as_posix(),
                "state_sha256": sha256(path),
                "state_bytes": path.stat().st_size,
                "simulation_seconds": simulation_seconds,
                "max_metric_error_vs_exact_artifact": max_metric_error,
                "metrics": metrics,
                "accumulator": accumulator,
            }
            unique[key] = row
            atomic_write_json(
                REFERENCE_CHECKPOINT,
                {
                    "stage": "mps_ladder_exact_references",
                    "complete": False,
                    "protocol_sha256": protocol_hash(),
                    "rows": sorted(unique.values(), key=reference_identity),
                },
            )
            print(
                f"[reference] complete {method}/{ordering} in {simulation_seconds:.3f}s",
                flush=True,
            )
            del state, case, circuit, bare, row
            gc.collect()

    rows = sorted(unique.values(), key=reference_identity)
    if len(rows) != 6:
        raise AssertionError(f"Expected 6 exact references, found {len(rows)}")
    payload = {
        "stage": "mps_ladder_exact_references",
        "complete": True,
        "protocol_sha256": protocol_hash(),
        "provenance": provenance(),
        "rows": rows,
    }
    atomic_write_json(REFERENCE_CHECKPOINT, payload)
    return payload


def compare_states(reference: np.ndarray, approximate: np.ndarray) -> dict:
    if reference.shape != approximate.shape or reference.ndim != 1:
        raise ValueError(f"State shape mismatch: {reference.shape} versus {approximate.shape}")
    overlap = 0.0j
    reference_norm = approximate_norm = distribution_l1 = 0.0
    for start in range(0, reference.size, COMPARE_CHUNK):
        stop = min(start + COMPARE_CHUNK, reference.size)
        ref = np.asarray(reference[start:stop])
        app = np.asarray(approximate[start:stop])
        ref_prob = ref.real * ref.real + ref.imag * ref.imag
        app_prob = app.real * app.real + app.imag * app.imag
        overlap += np.vdot(ref, app)
        reference_norm += float(ref_prob.sum(dtype=np.float64))
        approximate_norm += float(app_prob.sum(dtype=np.float64))
        distribution_l1 += float(np.abs(ref_prob - app_prob).sum(dtype=np.float64))
    fidelity = abs(overlap) ** 2 / (reference_norm * approximate_norm)
    return {
        "state_fidelity": float(fidelity),
        "total_variation_distance": 0.5 * distribution_l1,
        "reference_norm": reference_norm,
        "mps_norm": approximate_norm,
    }


def normalize_state_in_place(state: np.ndarray) -> float:
    """Normalize an exported approximate state and return its raw squared norm."""

    raw_norm = 0.0
    for start in range(0, state.size, COMPARE_CHUNK):
        stop = min(start + COMPARE_CHUNK, state.size)
        block = state[start:stop]
        raw_norm += float(
            (block.real * block.real + block.imag * block.imag).sum(dtype=np.float64)
        )
    if not np.isfinite(raw_norm) or raw_norm <= 0.0:
        raise AssertionError(f"Invalid raw MPS state norm: {raw_norm}")
    state *= 1.0 / np.sqrt(raw_norm)
    return raw_norm


def mps_evaluate(case, genome: np.ndarray, setting: dict, reference: np.ndarray) -> dict:
    circuit = exact_extension.resource.circuit_for(case, genome, DEPTH)
    resources = exact_extension.resource.circuit_resources(circuit)
    bare = circuit.remove_final_measurements(inplace=False)
    bare.save_statevector()
    backend = AerSimulator(
        method="matrix_product_state",
        matrix_product_state_max_bond_dimension=setting["bond"],
        matrix_product_state_truncation_threshold=setting["cutoff"],
        max_parallel_experiments=1,
    )
    started = perf_counter()
    result = backend.run(bare).result()
    simulation_seconds = perf_counter() - started
    state = np.array(result.get_statevector(bare), dtype=np.complex128, copy=True)
    raw_mps_norm = normalize_state_in_place(state)
    metric_started = perf_counter()
    metrics, accumulator = exact_extension.streaming_probability_metrics(case, state)
    comparison = compare_states(reference, state)
    comparison["raw_mps_norm"] = raw_mps_norm
    comparison["raw_norm_drift"] = raw_mps_norm - 1.0
    metric_seconds = perf_counter() - metric_started
    del result, state, backend, bare, circuit
    gc.collect()
    return {
        "metrics": metrics,
        "comparison": comparison,
        "resources": resources,
        "simulation_seconds": simulation_seconds,
        "metric_seconds": metric_seconds,
        "elapsed_seconds": simulation_seconds + metric_seconds,
        "accumulator": accumulator,
    }


def stage_ladder() -> dict:
    references = read_json(REFERENCE_CHECKPOINT) if REFERENCE_CHECKPOINT.exists() else {}
    if not references.get("complete", False) or len(references.get("rows", [])) != 6:
        raise RuntimeError("Exact references are incomplete")
    previous = read_json(LADDER_CHECKPOINT) if LADDER_CHECKPOINT.exists() else {}
    if previous and previous.get("protocol_sha256") != protocol_hash():
        raise RuntimeError("Protocol hash changed after MPS checkpoint creation")
    unique = {job_identity(row): row for row in previous.get("rows", [])}

    for setting in SETTINGS:
        for method, genome in METHODS.items():
            for ordering in ORDERINGS:
                key = (method, ordering, setting["name"])
                if key in unique:
                    print(f"[ladder] resume skip {setting['name']}/{method}/{ordering}", flush=True)
                    continue
                path = reference_path(method, ordering)
                reference = np.load(path, mmap_mode="r", allow_pickle=False)
                case = exact_extension.resource.prepare_case(CASE, CAP, ordering)
                print(f"[ladder] starting {setting['name']}/{method}/{ordering}", flush=True)
                evaluated = mps_evaluate(case, np.asarray(genome), setting, reference)
                row = {
                    "case": CASE,
                    "method": method,
                    "ordering": ordering,
                    "setting": setting["name"],
                    "family": setting["family"],
                    "bond": setting["bond"],
                    "cutoff": setting["cutoff"],
                    "depth": DEPTH,
                    **evaluated,
                }
                unique[key] = row
                atomic_write_json(
                    LADDER_CHECKPOINT,
                    {
                        "stage": "exact_calibrated_mps_ladder",
                        "complete": False,
                        "protocol_sha256": protocol_hash(),
                        "settings": SETTINGS,
                        "rows": sorted(unique.values(), key=job_identity),
                    },
                )
                print(
                    f"[ladder] complete {setting['name']}/{method}/{ordering} "
                    f"in {evaluated['elapsed_seconds']:.3f}s",
                    flush=True,
                )
                del reference, case, evaluated, row
                gc.collect()

    rows = sorted(unique.values(), key=job_identity)
    expected = len(SETTINGS) * len(METHODS) * len(ORDERINGS)
    if len(rows) != expected:
        raise AssertionError(f"Expected {expected} MPS rows, found {len(rows)}")
    payload = {
        "stage": "exact_calibrated_mps_ladder",
        "complete": True,
        "protocol_sha256": protocol_hash(),
        "provenance": provenance(),
        "settings": SETTINGS,
        "rows": rows,
        "errors": [],
    }
    atomic_write_json(LADDER_CHECKPOINT, payload)
    return payload


def sign(value: float, tolerance: float = 1e-15) -> int:
    if value > tolerance:
        return 1
    if value < -tolerance:
        return -1
    return 0


def stage_analyze() -> dict:
    exact_rows = exact_reference_rows()
    ladder = read_json(LADDER_CHECKPOINT) if LADDER_CHECKPOINT.exists() else {}
    expected = len(SETTINGS) * len(METHODS) * len(ORDERINGS)
    if not ladder.get("complete", False) or len(ladder.get("rows", [])) != expected:
        raise RuntimeError("MPS ladder is incomplete; partial rows are not analyzed")
    rows = ladder["rows"]
    summaries = []
    for setting in SETTINGS:
        for ordering in ORDERINGS:
            cohort = [
                row
                for row in rows
                if row["setting"] == setting["name"] and row["ordering"] == ordering
            ]
            by_method = {row["method"]: row for row in cohort}
            if set(by_method) != set(METHODS):
                raise AssertionError(f"Incomplete method cohort: {setting['name']}/{ordering}")
            exact_reference = exact_rows[("published_lr", ordering)]["metrics"]
            exact_matched = exact_rows[("prior_matched_random", ordering)]["metrics"]
            exact_evolutionary = exact_rows[("prior_evolutionary", ordering)]["metrics"]
            exact_matched_effect = exact_matched["bks_rate"] - exact_reference["bks_rate"]
            matched_effect = (
                by_method["prior_matched_random"]["metrics"]["bks_rate"]
                - by_method["published_lr"]["metrics"]["bks_rate"]
            )
            evolutionary_effect = (
                by_method["prior_evolutionary"]["metrics"]["bks_rate"]
                - by_method["published_lr"]["metrics"]["bks_rate"]
            )
            exact_evolutionary_effect = (
                exact_evolutionary["bks_rate"] - exact_reference["bks_rate"]
            )
            summaries.append(
                {
                    **setting,
                    "ordering": ordering,
                    "matched_bks_effect": matched_effect,
                    "exact_matched_bks_effect": exact_matched_effect,
                    "matched_sign_correct": sign(matched_effect) == sign(exact_matched_effect),
                    "evolutionary_bks_effect": evolutionary_effect,
                    "exact_evolutionary_bks_effect": exact_evolutionary_effect,
                    "minimum_state_fidelity": min(
                        row["comparison"]["state_fidelity"] for row in cohort
                    ),
                    "maximum_tvd": max(
                        row["comparison"]["total_variation_distance"] for row in cohort
                    ),
                    "maximum_absolute_bks_error": max(
                        abs(
                            row["metrics"]["bks_rate"]
                            - exact_rows[(row["method"], ordering)]["metrics"]["bks_rate"]
                        )
                        for row in cohort
                    ),
                    "total_elapsed_seconds": sum(row["elapsed_seconds"] for row in cohort),
                }
            )

    minimum_correct_bond = {}
    for ordering in ORDERINGS:
        candidates = [
            row
            for row in summaries
            if row["family"] == "bond"
            and row["ordering"] == ordering
            and row["matched_sign_correct"]
        ]
        minimum_correct_bond[ordering] = min((row["bond"] for row in candidates), default=None)

    payload = {
        "stage": "exact_calibrated_mps_ladder_analysis",
        "complete": True,
        "protocol_sha256": protocol_hash(),
        "exact_matched_bks_effect": {
            ordering: (
                exact_rows[("prior_matched_random", ordering)]["metrics"]["bks_rate"]
                - exact_rows[("published_lr", ordering)]["metrics"]["bks_rate"]
            )
            for ordering in ORDERINGS
        },
        "minimum_correct_bond": minimum_correct_bond,
        "summaries": summaries,
    }
    atomic_write_json(ANALYSIS, payload)
    write_report(payload)
    return payload


def write_report(analysis: dict) -> None:
    lines = [
        "# Exact-calibrated MPS fidelity ladder",
        "",
        "| Setting | Ordering | Bond | Cutoff | Matched BKS effect | Correct sign | Min fidelity | Max TVD | Max BKS error | Seconds |",
        "|---|---|---:|---:|---:|---|---:|---:|---:|---:|",
    ]
    for row in analysis["summaries"]:
        lines.append(
            "| {name} | {ordering} | {bond} | {cutoff:.0e} | {matched_bks_effect:+.8f} | "
            "{matched_sign_correct} | {minimum_state_fidelity:.8f} | {maximum_tvd:.8f} | "
            "{maximum_absolute_bks_error:.8f} | {total_elapsed_seconds:.1f} |".format(**row)
        )
    lines.extend(
        [
            "",
            "Minimum tested bond with the exact matched-schedule BKS sign:",
            "",
            f"- sorted: `{analysis['minimum_correct_bond']['sorted']}`",
            f"- spectral: `{analysis['minimum_correct_bond']['spectral']}`",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stage", choices=("reference", "ladder", "analyze", "all"), default="all"
    )
    args = parser.parse_args()
    if args.stage in ("reference", "all"):
        stage_reference()
    if args.stage in ("ladder", "all"):
        stage_ladder()
    if args.stage in ("analyze", "all"):
        stage_analyze()


if __name__ == "__main__":
    main()
