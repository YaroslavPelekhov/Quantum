"""Frozen cross-backend cuTensorNet audit of the 24-qubit MPS ladder."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import numpy as np


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results" / "independent_ladder"
CIRCUITS = RESULTS / "circuits"
PROTOCOL = HERE / "INDEPENDENT_LADDER_PROTOCOL.md"
MANIFEST = RESULTS / "export_manifest.json"
CHECKPOINT = RESULTS / "mps_jobs.json"
SELF_TEST = RESULTS / "self_test.json"
ANALYSIS = RESULTS / "analysis.json"
REPORT = HERE / "INDEPENDENT_LADDER_REPORT.md"
AER_LADDER = HERE / "results" / "mps_ladder" / "mps_ladder.json"
EXACT_REFERENCES = HERE / "results" / "mps_ladder" / "exact_references.json"

CASE = "aves-sparrow-social"
CAP = 20
DEPTH = 15
ORDERINGS = ("sorted", "spectral")
METHOD_NAMES = ("published_lr", "prior_evolutionary", "prior_matched_random")
METRICS = ("bks_rate", "near_bks_rate", "feasible_rate", "quality_mass")
CHUNK = 1 << 18
SETTINGS = (
    {"name": "released", "bond": 64, "cutoff": 1e-3},
    {"name": "confirm", "bond": 128, "cutoff": 1e-4},
    {"name": "bond128", "bond": 128, "cutoff": 1e-12},
    {"name": "cutoff1e-4", "bond": 1024, "cutoff": 1e-4},
    {"name": "cutoff1e-5", "bond": 1024, "cutoff": 1e-5},
)
EXPECTED_JOBS = len(SETTINGS) * len(METHOD_NAMES) * len(ORDERINGS)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def jsonable(value):
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating, np.bool_)):
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


def relative(path: Path) -> str:
    return path.relative_to(HERE).as_posix()


def static_scorer(compiled: dict, bks: int) -> dict:
    return {
        "constant_selected": int(compiled["constant_selected"]),
        "weights": [int(value) for value in compiled["weights"]],
        "forbidden": [[int(mask), int(pattern)] for mask, pattern in compiled["forbidden"]],
        "impossible": bool(compiled["impossible"]),
        "bks": int(bks),
    }


def qpy_dump_atomic(circuit, path: Path) -> None:
    from qiskit import qpy

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as handle:
        qpy.dump(circuit, handle)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def export_inputs() -> None:
    """Run on Windows in the original environment before target execution."""
    import qiskit
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector

    import run_exact_extension as exact

    if len(SETTINGS) != 5 or EXPECTED_JOBS != 30:
        raise AssertionError("Frozen design must contain exactly 30 jobs")
    references = read_json(EXACT_REFERENCES)
    if not references.get("complete") or len(references.get("rows", [])) != 6:
        raise RuntimeError("Six completed exact references are required")
    reference_rows = {
        (row["method"], row["ordering"]): row for row in references["rows"]
    }
    if set(reference_rows) != {
        (method, ordering) for method in METHOD_NAMES for ordering in ORDERINGS
    }:
        raise AssertionError("Exact reference cohort does not match the frozen target")

    CIRCUITS.mkdir(parents=True, exist_ok=True)
    rows = []
    for method in METHOD_NAMES:
        genome = np.asarray(exact.METHODS[method], dtype=float)
        for ordering in ORDERINGS:
            case = exact.resource.prepare_case(CASE, CAP, ordering)
            circuit = exact.resource.circuit_for(case, genome, DEPTH)
            bare = circuit.remove_final_measurements(inplace=False)
            circuit_path = CIRCUITS / f"{method}__{ordering}.qpy"
            qpy_dump_atomic(bare, circuit_path)
            ref = reference_rows[(method, ordering)]
            reference_path = HERE / ref["state_file"]
            if not reference_path.exists() or sha256(reference_path) != ref["state_sha256"]:
                raise RuntimeError(f"Exact reference hash failed: {method}/{ordering}")
            rows.append(
                {
                    "case": CASE,
                    "method": method,
                    "ordering": ordering,
                    "qubits": int(case.qubits),
                    "depth": DEPTH,
                    "circuit_file": relative(circuit_path),
                    "circuit_sha256": sha256(circuit_path),
                    "reference_file": relative(reference_path),
                    "reference_sha256": ref["state_sha256"],
                    "exact_metrics": ref["metrics"],
                    "scorer": static_scorer(exact.compile_decoder(case), case.bks),
                }
            )

    # A deliberately asymmetric four-qubit circuit catches axis-order mistakes.
    test = QuantumCircuit(4)
    test.h(0)
    test.ry(0.37, 2)
    test.cx(0, 3)
    test.rz(-0.61, 1)
    test.x(1)
    test.cx(2, 1)
    test.ry(-0.23, 3)
    test_path = CIRCUITS / "self_test.qpy"
    test_reference = CIRCUITS / "self_test_reference.npy"
    qpy_dump_atomic(test, test_path)
    atomic_save_npy(test_reference, np.asarray(Statevector.from_instruction(test).data))
    test_scorer = {
        "constant_selected": 1,
        "weights": [2, -1, 3, 1],
        "forbidden": [[3, 3], [12, 4]],
        "impossible": False,
        "bks": 5,
    }
    expected_test_metrics, _ = score_state(
        np.load(test_reference, allow_pickle=False), test_scorer
    )

    payload = {
        "stage": "independent_ladder_export",
        "complete": True,
        "created_at": utc_now(),
        "protocol_sha256": sha256(PROTOCOL),
        "runner_sha256": sha256(Path(__file__)),
        "qiskit": qiskit.__version__,
        "case": CASE,
        "cap": CAP,
        "depth": DEPTH,
        "methods": list(METHOD_NAMES),
        "orderings": list(ORDERINGS),
        "settings": SETTINGS,
        "expected_jobs": EXPECTED_JOBS,
        "state_convention": "Qiskit flat amplitudes; integer bit i is qubit i",
        "rows": sorted(rows, key=lambda row: (row["method"], row["ordering"])),
        "self_test": {
            "qubits": 4,
            "circuit_file": relative(test_path),
            "circuit_sha256": sha256(test_path),
            "reference_file": relative(test_reference),
            "reference_sha256": sha256(test_reference),
            "scorer": test_scorer,
            "exact_metrics": expected_test_metrics,
        },
        "exact_reference_manifest": relative(EXACT_REFERENCES),
        "exact_reference_manifest_sha256": sha256(EXACT_REFERENCES),
    }
    atomic_write_json(MANIFEST, payload)
    print(f"Exported and hashed {len(rows)} target circuits; manifest={sha256(MANIFEST)}")


def verify_manifest() -> dict:
    if not MANIFEST.exists():
        raise RuntimeError("Run export before the independent audit")
    manifest = read_json(MANIFEST)
    if manifest.get("protocol_sha256") != sha256(PROTOCOL):
        raise RuntimeError("Frozen protocol hash changed after export")
    if manifest.get("runner_sha256") != sha256(Path(__file__)):
        raise RuntimeError("Runner hash changed after export; re-export under a new audit")
    if manifest.get("expected_jobs") != EXPECTED_JOBS or manifest.get("settings") != list(SETTINGS):
        raise RuntimeError("Manifest design differs from the frozen 30-job design")
    for row in [*manifest["rows"], manifest["self_test"]]:
        for stem in ("circuit", "reference"):
            path = HERE / row[f"{stem}_file"]
            if not path.exists() or sha256(path) != row[f"{stem}_sha256"]:
                raise RuntimeError(f"{stem.title()} hash mismatch: {path}")
    return manifest


def load_circuit(path: Path):
    from qiskit import qpy

    with path.open("rb") as handle:
        circuits = qpy.load(handle)
    if len(circuits) != 1:
        raise AssertionError(f"Expected one circuit in {path}")
    return circuits[0]


def score_state(state: np.ndarray, scorer: dict) -> tuple[dict, dict]:
    qubits = len(scorer["weights"])
    expected = 1 << qubits
    if state.ndim != 1 or state.size != expected:
        raise ValueError(f"Expected {expected} amplitudes, got {state.shape}")
    feasible_mass = bks_mass = near_mass = quality_mass = selected_mass = total_mass = 0.0
    best = None
    for start in range(0, expected, CHUNK):
        stop = min(start + CHUNK, expected)
        indices = np.arange(start, stop, dtype=np.uint64)
        block = np.asarray(state[start:stop])
        probabilities = block.real * block.real + block.imag * block.imag
        total_mass += float(probabilities.sum(dtype=np.float64))
        selected = np.full(indices.shape, scorer["constant_selected"], dtype=np.int16)
        for qubit, weight in enumerate(scorer["weights"]):
            if weight:
                selected += np.int16(weight) * (
                    (indices >> np.uint64(qubit)) & np.uint64(1)
                ).astype(np.int16)
        feasible = np.full(indices.shape, not scorer["impossible"], dtype=np.bool_)
        for mask, pattern in scorer["forbidden"]:
            feasible &= (indices & np.uint64(mask)) != np.uint64(pattern)
        if not np.any(feasible):
            continue
        feasible_prob = probabilities[feasible]
        sizes = selected[feasible]
        bks = scorer["bks"]
        feasible_mass += float(feasible_prob.sum(dtype=np.float64))
        bks_mass += float(feasible_prob[sizes >= bks].sum(dtype=np.float64))
        near_mass += float(feasible_prob[sizes >= bks - 1].sum(dtype=np.float64))
        selected_mass += float(np.dot(feasible_prob, sizes.astype(np.float64, copy=False)))
        quality_mass += float(
            np.dot(feasible_prob, np.minimum(sizes.astype(np.float64, copy=False) / bks, 1.0))
        )
        positive = feasible & (probabilities > 0.0)
        if np.any(positive):
            chunk_best = int(selected[positive].max())
            best = chunk_best if best is None else max(best, chunk_best)
    if abs(total_mass - 1.0) > 1e-9:
        raise AssertionError(f"Normalized state has norm {total_mass}")
    metrics = {
        "feasible_rate": feasible_mass,
        "bks_rate": bks_mass,
        "near_bks_rate": near_mass,
        "quality_mass": quality_mass,
        "conditional_mean_size": selected_mass / feasible_mass if feasible_mass else None,
        "best_size_nonzero_probability": best,
    }
    return metrics, {
        "implementation": "static_chunked_literal_accumulator",
        "chunk_size": CHUNK,
        "basis_states": expected,
        "forbidden_patterns": len(scorer["forbidden"]),
        "statevector_norm": total_mass,
    }


def normalize_state(state: np.ndarray) -> float:
    raw_norm = 0.0
    for start in range(0, state.size, CHUNK):
        block = state[start : start + CHUNK]
        raw_norm += float((block.real * block.real + block.imag * block.imag).sum(dtype=np.float64))
    if not np.isfinite(raw_norm) or raw_norm <= 0:
        raise AssertionError(f"Invalid raw state norm {raw_norm}")
    state *= 1.0 / np.sqrt(raw_norm)
    return raw_norm


def compare_states(reference: np.ndarray, approximate: np.ndarray) -> dict:
    if reference.shape != approximate.shape or reference.ndim != 1:
        raise ValueError(f"State shape mismatch: {reference.shape} versus {approximate.shape}")
    overlap = 0.0j
    reference_norm = approximate_norm = distribution_l1 = 0.0
    for start in range(0, reference.size, CHUNK):
        stop = min(start + CHUNK, reference.size)
        ref = np.asarray(reference[start:stop])
        app = approximate[start:stop]
        ref_p = ref.real * ref.real + ref.imag * ref.imag
        app_p = app.real * app.real + app.imag * app.imag
        overlap += np.vdot(ref, app)
        reference_norm += float(ref_p.sum(dtype=np.float64))
        approximate_norm += float(app_p.sum(dtype=np.float64))
        distribution_l1 += float(np.abs(ref_p - app_p).sum(dtype=np.float64))
    return {
        "state_fidelity": float(abs(overlap) ** 2 / (reference_norm * approximate_norm)),
        "total_variation_distance": 0.5 * distribution_l1,
        "reference_norm": reference_norm,
        "approximate_norm": approximate_norm,
    }


def cutensornet_provenance() -> dict:
    import cupy
    import cuquantum
    import qiskit

    props = cupy.cuda.runtime.getDeviceProperties(0)
    name = props["name"].decode() if isinstance(props["name"], bytes) else props["name"]
    free_bytes, total_bytes = cupy.cuda.runtime.memGetInfo()
    return {
        "created_at": utc_now(),
        "python": sys.version,
        "platform": platform.platform(),
        "qiskit": qiskit.__version__,
        "numpy": np.__version__,
        "cupy": cupy.__version__,
        "cuquantum": cuquantum.__version__,
        "gpu": name,
        "gpu_total_bytes": int(total_bytes),
        "gpu_free_bytes_at_start": int(free_bytes),
        "network_memory_limit": "60%",
        "runner_sha256": sha256(Path(__file__)),
        "protocol_sha256": sha256(PROTOCOL),
        "manifest_sha256": sha256(MANIFEST),
    }


def simulate(circuit, bond: int, cutoff: float) -> tuple[np.ndarray, float]:
    import cupy as cp
    from cuquantum.tensornet import NetworkOptions
    from cuquantum.tensornet.experimental import MPSConfig, NetworkState

    started = perf_counter()
    with NetworkState.from_circuit(
        circuit,
        dtype="complex128",
        backend="cupy",
        config=MPSConfig(max_extent=bond, discarded_weight_cutoff=cutoff),
        options=NetworkOptions(device_id=0, memory_limit="60%"),
    ) as network:
        q0_first = network.compute_state_vector()
        axes = tuple(reversed(range(circuit.num_qubits)))
        state = cp.asnumpy(q0_first.transpose(axes).reshape(-1))
    cp.get_default_memory_pool().free_all_blocks()
    return np.ascontiguousarray(state, dtype=np.complex128), perf_counter() - started


def run_self_test() -> None:
    manifest = verify_manifest()
    spec = manifest["self_test"]
    circuit = load_circuit(HERE / spec["circuit_file"])
    approximate, simulation_seconds = simulate(circuit, 16, 1e-14)
    raw_norm = normalize_state(approximate)
    reference = np.load(HERE / spec["reference_file"], mmap_mode="r", allow_pickle=False)
    comparison = compare_states(reference, approximate)
    metrics, accumulator = score_state(approximate, spec["scorer"])
    maximum_metric_error = max(
        abs(metrics[name] - spec["exact_metrics"][name]) for name in METRICS
    )
    passed = (
        comparison["state_fidelity"] > 1.0 - 1e-10
        and comparison["total_variation_distance"] < 1e-10
        and maximum_metric_error < 1e-10
    )
    payload = {
        "stage": "independent_ladder_self_test",
        "complete": passed,
        "provenance": cutensornet_provenance(),
        "simulation_seconds": simulation_seconds,
        "raw_norm": raw_norm,
        "comparison": comparison,
        "metrics": metrics,
        "maximum_metric_error": maximum_metric_error,
        "accumulator": accumulator,
    }
    atomic_write_json(SELF_TEST, payload)
    if not passed:
        raise AssertionError(f"cuTensorNet self-test failed: {payload}")
    print(
        f"Self-test passed: fidelity={comparison['state_fidelity']:.12f}, "
        f"TVD={comparison['total_variation_distance']:.3e}"
    )


def job_identity(row: dict) -> tuple[str, str, str]:
    return row["setting"], row["method"], row["ordering"]


def run_jobs() -> None:
    manifest = verify_manifest()
    if not SELF_TEST.exists() or not read_json(SELF_TEST).get("complete"):
        raise RuntimeError("A passing independent-backend self-test is required")
    prior = read_json(CHECKPOINT) if CHECKPOINT.exists() else {}
    manifest_hash = sha256(MANIFEST)
    if prior and prior.get("manifest_sha256") != manifest_hash:
        raise RuntimeError("Manifest changed after target checkpoint creation")
    unique = {job_identity(row): row for row in prior.get("rows", [])}
    circuit_rows = {
        (row["method"], row["ordering"]): row for row in manifest["rows"]
    }
    provenance = prior.get("provenance") or cutensornet_provenance()
    for setting in SETTINGS:
        for method in METHOD_NAMES:
            for ordering in ORDERINGS:
                identity = (setting["name"], method, ordering)
                if identity in unique:
                    print(f"[resume] {setting['name']}/{method}/{ordering}", flush=True)
                    continue
                spec = circuit_rows[(method, ordering)]
                print(f"[start] {setting['name']}/{method}/{ordering}", flush=True)
                circuit = load_circuit(HERE / spec["circuit_file"])
                approximate, simulation_seconds = simulate(
                    circuit, setting["bond"], setting["cutoff"]
                )
                raw_norm = normalize_state(approximate)
                metric_started = perf_counter()
                metrics, accumulator = score_state(approximate, spec["scorer"])
                reference = np.load(
                    HERE / spec["reference_file"], mmap_mode="r", allow_pickle=False
                )
                comparison = compare_states(reference, approximate)
                comparison["raw_approximate_norm"] = raw_norm
                comparison["raw_norm_drift"] = raw_norm - 1.0
                metric_seconds = perf_counter() - metric_started
                row = {
                    "case": CASE,
                    "setting": setting["name"],
                    "bond": setting["bond"],
                    "cutoff": setting["cutoff"],
                    "method": method,
                    "ordering": ordering,
                    "qubits": spec["qubits"],
                    "depth": DEPTH,
                    "metrics": metrics,
                    "comparison": comparison,
                    "simulation_seconds": simulation_seconds,
                    "metric_seconds": metric_seconds,
                    "elapsed_seconds": simulation_seconds + metric_seconds,
                    "accumulator": accumulator,
                }
                unique[identity] = row
                rows = sorted(unique.values(), key=job_identity)
                atomic_write_json(
                    CHECKPOINT,
                    {
                        "stage": "independent_cutensornet_mps_ladder",
                        "complete": len(rows) == EXPECTED_JOBS,
                        "manifest_sha256": manifest_hash,
                        "protocol_sha256": sha256(PROTOCOL),
                        "provenance": provenance,
                        "settings": SETTINGS,
                        "expected_jobs": EXPECTED_JOBS,
                        "rows": rows,
                        "errors": [],
                    },
                )
                print(
                    f"[complete] {setting['name']}/{method}/{ordering} "
                    f"fidelity={comparison['state_fidelity']:.8f} "
                    f"BKS={metrics['bks_rate']:.8f} seconds={row['elapsed_seconds']:.1f}",
                    flush=True,
                )
                del approximate, reference, circuit, row
                gc.collect()
    if len(unique) != EXPECTED_JOBS:
        raise AssertionError(f"Expected {EXPECTED_JOBS} jobs, found {len(unique)}")


def sign(value: float, tolerance: float = 1e-15) -> int:
    return 1 if value > tolerance else (-1 if value < -tolerance else 0)


def analyze() -> None:
    manifest = verify_manifest()
    checkpoint = read_json(CHECKPOINT) if CHECKPOINT.exists() else {}
    if not checkpoint.get("complete") or len(checkpoint.get("rows", [])) != EXPECTED_JOBS:
        raise RuntimeError("All 30 independent-backend rows are required for analysis")
    if checkpoint.get("manifest_sha256") != sha256(MANIFEST):
        raise RuntimeError("Checkpoint/manifest hash mismatch")
    aer = read_json(AER_LADDER)
    if not aer.get("complete") or len(aer.get("rows", [])) != 66:
        raise RuntimeError("Completed 66-row Aer ladder is required")
    exact = {
        (row["method"], row["ordering"]): row["exact_metrics"]
        for row in manifest["rows"]
    }
    independent = {job_identity(row): row for row in checkpoint["rows"]}
    aer_rows = {
        (row["setting"], row["method"], row["ordering"]): row for row in aer["rows"]
    }
    summaries = []
    for setting in SETTINGS:
        for ordering in ORDERINGS:
            cohort = {
                method: independent[(setting["name"], method, ordering)]
                for method in METHOD_NAMES
            }
            matched_effect = (
                cohort["prior_matched_random"]["metrics"]["bks_rate"]
                - cohort["published_lr"]["metrics"]["bks_rate"]
            )
            evolutionary_effect = (
                cohort["prior_evolutionary"]["metrics"]["bks_rate"]
                - cohort["published_lr"]["metrics"]["bks_rate"]
            )
            exact_matched_effect = (
                exact[("prior_matched_random", ordering)]["bks_rate"]
                - exact[("published_lr", ordering)]["bks_rate"]
            )
            exact_evolutionary_effect = (
                exact[("prior_evolutionary", ordering)]["bks_rate"]
                - exact[("published_lr", ordering)]["bks_rate"]
            )
            aer_matched_effect = (
                aer_rows[(setting["name"], "prior_matched_random", ordering)]["metrics"]["bks_rate"]
                - aer_rows[(setting["name"], "published_lr", ordering)]["metrics"]["bks_rate"]
            )
            max_cross_backend_bks = max(
                abs(
                    cohort[method]["metrics"]["bks_rate"]
                    - aer_rows[(setting["name"], method, ordering)]["metrics"]["bks_rate"]
                )
                for method in METHOD_NAMES
            )
            summaries.append(
                {
                    **setting,
                    "ordering": ordering,
                    "matched_bks_effect": matched_effect,
                    "exact_matched_bks_effect": exact_matched_effect,
                    "aer_matched_bks_effect": aer_matched_effect,
                    "matched_sign_correct": sign(matched_effect) == sign(exact_matched_effect),
                    "same_sign_as_aer": sign(matched_effect) == sign(aer_matched_effect),
                    "evolutionary_bks_effect": evolutionary_effect,
                    "exact_evolutionary_bks_effect": exact_evolutionary_effect,
                    "minimum_state_fidelity": min(
                        row["comparison"]["state_fidelity"] for row in cohort.values()
                    ),
                    "maximum_tvd": max(
                        row["comparison"]["total_variation_distance"] for row in cohort.values()
                    ),
                    "maximum_absolute_bks_error": max(
                        abs(row["metrics"]["bks_rate"] - exact[(method, ordering)]["bks_rate"])
                        for method, row in cohort.items()
                    ),
                    "maximum_cross_backend_bks_difference": max_cross_backend_bks,
                    "total_elapsed_seconds": sum(row["elapsed_seconds"] for row in cohort.values()),
                }
            )
    payload = {
        "stage": "independent_cutensornet_mps_ladder_analysis",
        "complete": True,
        "created_at": utc_now(),
        "protocol_sha256": sha256(PROTOCOL),
        "manifest_sha256": sha256(MANIFEST),
        "checkpoint_sha256": sha256(CHECKPOINT),
        "aer_ladder_sha256": sha256(AER_LADDER),
        "summaries": summaries,
    }
    atomic_write_json(ANALYSIS, payload)
    write_report(payload)
    print(f"Independent audit analyzed: {len(summaries)} complete cohorts")


def write_report(analysis: dict) -> None:
    lines = [
        "# Independent cuTensorNet MPS audit",
        "",
        "All 30 frozen jobs completed before this report was generated.",
        "",
        "| Setting | Ordering | Matched effect | Exact effect | Aer effect | Exact sign | Aer sign | Min fidelity | Max TVD | Max BKS error | Cross-backend BKS delta |",
        "|---|---|---:|---:|---:|---|---|---:|---:|---:|---:|",
    ]
    for row in analysis["summaries"]:
        lines.append(
            "| {name} | {ordering} | {matched_bks_effect:+.8f} | {exact_matched_bks_effect:+.8f} | "
            "{aer_matched_bks_effect:+.8f} | {matched_sign_correct} | {same_sign_as_aer} | "
            "{minimum_state_fidelity:.8f} | {maximum_tvd:.8f} | {maximum_absolute_bks_error:.8f} | "
            "{maximum_cross_backend_bks_difference:.8f} |".format(**row)
        )
    lines.extend(
        [
            "",
            "Primary interpretation is the exact-sign column. Cross-backend differences are",
            "reported as diagnostics and do not replace exact adjudication.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("export", "self-test", "run", "analyze"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "export":
        export_inputs()
    elif args.command == "self-test":
        run_self_test()
    elif args.command == "run":
        run_jobs()
    else:
        analyze()


if __name__ == "__main__":
    main()
