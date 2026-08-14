"""Frozen 300-row cross-case Aer/cuTensorNet MPS replication.

The runner exports immutable QPY circuits and exact reference states on Windows,
then executes the same deterministic ladder on Aer and cuTensorNet.  The already
completed 24-qubit aves cohort is reused only after hash validation.
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import numpy as np

import run_independent_ladder_audit as audit


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results" / "cross_case_replication"
CIRCUITS = RESULTS / "circuits"
REFERENCES = RESULTS / "references"
PROTOCOL = HERE / "CROSS_CASE_REPLICATION_PROTOCOL.md"
MANIFEST = RESULTS / "export_manifest.json"
SELF_TEST_AER = RESULTS / "self_test_aer.json"
SELF_TEST_CUTN = RESULTS / "self_test_cutensornet.json"
AER_CHECKPOINT = RESULTS / "aer_jobs.json"
CUTN_CHECKPOINT = RESULTS / "cutensornet_jobs.json"
COMBINED = RESULTS / "combined_jobs.json"
ANALYSIS = RESULTS / "analysis.json"
REPORT = HERE / "CROSS_CASE_REPLICATION_REPORT.md"

EXTERNAL_EXACT = HERE / "results" / "external_validity" / "exact_statevector.json"
PRIOR_AER = HERE / "results" / "mps_ladder" / "mps_ladder.json"
PRIOR_CUTN = HERE / "results" / "independent_ladder" / "mps_jobs.json"
PRIOR_MANIFEST = HERE / "results" / "independent_ladder" / "export_manifest.json"

CASES = (
    {"name": "karate", "cap": 4, "qubits": 3, "expected_effect": 0.08641201},
    {"name": "chesapeake", "cap": 12, "qubits": 7, "expected_effect": -0.13421359},
    {"name": "football", "cap": 10, "qubits": 7, "expected_effect": 0.01926887},
    {"name": "ibm32", "cap": 8, "qubits": 18, "expected_effect": -0.24612300},
)
REUSED_CASE = "aves-sparrow-social"
ALL_CASES = tuple(case["name"] for case in CASES) + (REUSED_CASE,)
DEPTH = 15
ORDERINGS = ("sorted", "spectral")
METHOD_NAMES = ("published_lr", "prior_evolutionary", "prior_matched_random")
METRICS = ("bks_rate", "near_bks_rate", "feasible_rate", "quality_mass")
SETTINGS = (
    {"name": "released", "bond": 64, "cutoff": 1e-3},
    {"name": "confirm", "bond": 128, "cutoff": 1e-4},
    {"name": "bond128", "bond": 128, "cutoff": 1e-12},
    {"name": "cutoff1e-4", "bond": 1024, "cutoff": 1e-4},
    {"name": "cutoff1e-5", "bond": 1024, "cutoff": 1e-5},
)
EXPECTED_NEW_PER_BACKEND = len(CASES) * len(SETTINGS) * len(METHOD_NAMES) * len(ORDERINGS)
EXPECTED_REUSED_PER_BACKEND = len(SETTINGS) * len(METHOD_NAMES) * len(ORDERINGS)
EXPECTED_TOTAL = 2 * (EXPECTED_NEW_PER_BACKEND + EXPECTED_REUSED_PER_BACKEND)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def relative(path: Path) -> str:
    return path.relative_to(HERE).as_posix()


def sha256(path: Path) -> str:
    return audit.sha256(path)


def read_json(path: Path):
    return audit.read_json(path)


def write_json(path: Path, payload) -> None:
    audit.atomic_write_json(path, payload)


def exact_identity(row: dict) -> tuple[str, str, str]:
    return row["case"], row["method"], row["ordering"]


def job_identity(row: dict) -> tuple[str, str, str, str]:
    return row["case"], row["setting"], row["method"], row["ordering"]


def sign(value: float, tolerance: float = 1e-15) -> int:
    return 1 if value > tolerance else (-1 if value < -tolerance else 0)


def export_inputs() -> None:
    """Generate exact references and immutable circuits in the Windows environment."""
    import qiskit
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector

    import run_exact_extension as exact

    if EXPECTED_NEW_PER_BACKEND != 120 or EXPECTED_TOTAL != 300:
        raise AssertionError("Frozen design must contain 240 new and 300 total rows")
    external = read_json(EXTERNAL_EXACT)
    if not external.get("complete") or len(external.get("rows", [])) != 24:
        raise RuntimeError("Completed 24-row external exact artifact is required")
    external_rows = {exact_identity(row): row for row in external["rows"]}

    CIRCUITS.mkdir(parents=True, exist_ok=True)
    REFERENCES.mkdir(parents=True, exist_ok=True)
    rows = []
    max_exact_metric_error = 0.0
    for case_spec in CASES:
        for method in METHOD_NAMES:
            genome = np.asarray(exact.METHODS[method], dtype=float)
            for ordering in ORDERINGS:
                case = exact.resource.prepare_case(case_spec["name"], case_spec["cap"], ordering)
                if case.qubits != case_spec["qubits"]:
                    raise AssertionError(
                        f"Frozen kernel changed for {case_spec['name']}: "
                        f"expected {case_spec['qubits']} qubits, got {case.qubits}"
                    )
                measured = exact.resource.circuit_for(case, genome, DEPTH)
                resources = exact.resource.circuit_resources(measured)
                circuit = measured.remove_final_measurements(inplace=False)
                stem = f"{case_spec['name']}__{method}__{ordering}"
                circuit_path = CIRCUITS / f"{stem}.qpy"
                reference_path = REFERENCES / f"{stem}.npy"
                audit.qpy_dump_atomic(circuit, circuit_path)
                state = np.asarray(Statevector.from_instruction(circuit).data, dtype=np.complex128)
                audit.atomic_save_npy(reference_path, state)
                scorer = audit.static_scorer(exact.compile_decoder(case), case.bks)
                metrics, accumulator = audit.score_state(state, scorer)
                source = external_rows[(case_spec["name"], method, ordering)]
                errors = [abs(float(metrics[key]) - float(source["metrics"][key])) for key in METRICS]
                max_exact_metric_error = max(max_exact_metric_error, *errors)
                if max(errors) > 1e-10:
                    raise AssertionError(f"Exact metric mismatch for {stem}: {max(errors)}")
                rows.append(
                    {
                        "case": case_spec["name"],
                        "cap": case_spec["cap"],
                        "method": method,
                        "ordering": ordering,
                        "qubits": int(case.qubits),
                        "depth": DEPTH,
                        "circuit_file": relative(circuit_path),
                        "circuit_sha256": sha256(circuit_path),
                        "reference_file": relative(reference_path),
                        "reference_sha256": sha256(reference_path),
                        "exact_metrics": metrics,
                        "scorer": scorer,
                        "resources": resources,
                        "accumulator": accumulator,
                    }
                )
                del state, circuit, measured, case
                gc.collect()

    test = QuantumCircuit(4)
    test.h(0)
    test.ry(0.37, 2)
    test.cx(0, 3)
    test.rz(-0.61, 1)
    test.x(1)
    test.cx(2, 1)
    test.ry(-0.23, 3)
    test_path = CIRCUITS / "self_test.qpy"
    test_reference = REFERENCES / "self_test_reference.npy"
    audit.qpy_dump_atomic(test, test_path)
    audit.atomic_save_npy(test_reference, np.asarray(Statevector.from_instruction(test).data))
    test_scorer = {
        "constant_selected": 1,
        "weights": [2, -1, 3, 1],
        "forbidden": [[3, 3], [12, 4]],
        "impossible": False,
        "bks": 5,
    }
    test_metrics, _ = audit.score_state(
        np.load(test_reference, allow_pickle=False), test_scorer
    )
    reused = []
    for path in (EXTERNAL_EXACT, PRIOR_AER, PRIOR_CUTN, PRIOR_MANIFEST):
        if not path.exists():
            raise RuntimeError(f"Required prior artifact missing: {path}")
        reused.append({"file": relative(path), "sha256": sha256(path)})
    payload = {
        "stage": "cross_case_replication_export",
        "complete": True,
        "created_at": utc_now(),
        "protocol_sha256": sha256(PROTOCOL),
        "runner_sha256": sha256(Path(__file__)),
        "qiskit": qiskit.__version__,
        "cases": CASES,
        "reused_case": REUSED_CASE,
        "depth": DEPTH,
        "methods": METHOD_NAMES,
        "orderings": ORDERINGS,
        "settings": SETTINGS,
        "expected_new_per_backend": EXPECTED_NEW_PER_BACKEND,
        "expected_total": EXPECTED_TOTAL,
        "max_exact_metric_error": max_exact_metric_error,
        "state_convention": "Qiskit flat amplitudes; integer bit i is qubit i",
        "rows": sorted(rows, key=exact_identity),
        "self_test": {
            "qubits": 4,
            "circuit_file": relative(test_path),
            "circuit_sha256": sha256(test_path),
            "reference_file": relative(test_reference),
            "reference_sha256": sha256(test_reference),
            "scorer": test_scorer,
            "exact_metrics": test_metrics,
        },
        "reused_artifacts": reused,
    }
    write_json(MANIFEST, payload)
    print(
        f"Exported 24 circuits/references; exact check={max_exact_metric_error:.3e}; "
        f"manifest={sha256(MANIFEST)}",
        flush=True,
    )


def verify_manifest() -> dict:
    if not MANIFEST.exists():
        raise RuntimeError("Run export before simulation")
    manifest = read_json(MANIFEST)
    if manifest.get("protocol_sha256") != sha256(PROTOCOL):
        raise RuntimeError("Frozen protocol changed after export")
    if manifest.get("runner_sha256") != sha256(Path(__file__)):
        raise RuntimeError("Runner changed after export; re-export before target execution")
    if (
        manifest.get("settings") != list(SETTINGS)
        or manifest.get("expected_new_per_backend") != EXPECTED_NEW_PER_BACKEND
        or len(manifest.get("rows", [])) != 24
    ):
        raise RuntimeError("Manifest differs from the frozen design")
    for row in [*manifest["rows"], manifest["self_test"]]:
        for stem in ("circuit", "reference"):
            path = HERE / row[f"{stem}_file"]
            if not path.exists() or sha256(path) != row[f"{stem}_sha256"]:
                raise RuntimeError(f"{stem} hash mismatch: {path}")
    for item in manifest["reused_artifacts"]:
        path = HERE / item["file"]
        if not path.exists() or sha256(path) != item["sha256"]:
            raise RuntimeError(f"Reused artifact hash mismatch: {path}")
    return manifest


def aer_provenance() -> dict:
    import qiskit
    import qiskit_aer

    return {
        "created_at": utc_now(),
        "python": sys.version,
        "platform": platform.platform(),
        "qiskit": qiskit.__version__,
        "qiskit_aer": qiskit_aer.__version__,
        "numpy": np.__version__,
        "max_parallel_experiments": 1,
        "runner_sha256": sha256(Path(__file__)),
        "protocol_sha256": sha256(PROTOCOL),
        "manifest_sha256": sha256(MANIFEST),
    }


def simulate_aer(circuit, bond: int, cutoff: float) -> tuple[np.ndarray, float]:
    from qiskit_aer import AerSimulator

    executable = circuit.copy()
    executable.save_statevector()
    backend = AerSimulator(
        method="matrix_product_state",
        matrix_product_state_max_bond_dimension=bond,
        matrix_product_state_truncation_threshold=cutoff,
        max_parallel_experiments=1,
    )
    started = perf_counter()
    result = backend.run(executable).result()
    elapsed = perf_counter() - started
    state = np.array(result.get_statevector(executable), dtype=np.complex128, copy=True)
    del result, backend, executable
    return state, elapsed


def run_self_test(backend_name: str) -> None:
    manifest = verify_manifest()
    spec = manifest["self_test"]
    circuit = audit.load_circuit(HERE / spec["circuit_file"])
    if backend_name == "aer":
        approximate, seconds = simulate_aer(circuit, 16, 1e-14)
        output = SELF_TEST_AER
        provenance = aer_provenance()
    else:
        approximate, seconds = audit.simulate(circuit, 16, 1e-14)
        output = SELF_TEST_CUTN
        provenance = audit.cutensornet_provenance()
        provenance["manifest_sha256"] = sha256(MANIFEST)
        provenance["runner_sha256"] = sha256(Path(__file__))
        provenance["protocol_sha256"] = sha256(PROTOCOL)
    raw_norm = audit.normalize_state(approximate)
    reference = np.load(HERE / spec["reference_file"], mmap_mode="r", allow_pickle=False)
    comparison = audit.compare_states(reference, approximate)
    metrics, accumulator = audit.score_state(approximate, spec["scorer"])
    max_error = max(abs(metrics[name] - spec["exact_metrics"][name]) for name in METRICS)
    passed = (
        comparison["state_fidelity"] > 1.0 - 1e-10
        and comparison["total_variation_distance"] < 1e-10
        and max_error < 1e-10
    )
    write_json(
        output,
        {
            "stage": f"cross_case_{backend_name}_self_test",
            "complete": passed,
            "manifest_sha256": sha256(MANIFEST),
            "provenance": provenance,
            "simulation_seconds": seconds,
            "raw_norm": raw_norm,
            "comparison": comparison,
            "metrics": metrics,
            "maximum_metric_error": max_error,
            "accumulator": accumulator,
        },
    )
    if not passed:
        raise AssertionError(f"{backend_name} self-test failed")
    print(
        f"{backend_name} self-test passed: fidelity={comparison['state_fidelity']:.12f}, "
        f"TVD={comparison['total_variation_distance']:.3e}",
        flush=True,
    )


def run_jobs(backend_name: str) -> None:
    manifest = verify_manifest()
    self_test_path = SELF_TEST_AER if backend_name == "aer" else SELF_TEST_CUTN
    if not self_test_path.exists() or not read_json(self_test_path).get("complete"):
        raise RuntimeError(f"Passing {backend_name} self-test required")
    checkpoint_path = AER_CHECKPOINT if backend_name == "aer" else CUTN_CHECKPOINT
    prior = read_json(checkpoint_path) if checkpoint_path.exists() else {}
    manifest_hash = sha256(MANIFEST)
    if prior and prior.get("manifest_sha256") != manifest_hash:
        raise RuntimeError("Manifest changed after checkpoint creation")
    unique = {job_identity(row): row for row in prior.get("rows", [])}
    specs = {exact_identity(row): row for row in manifest["rows"]}
    provenance = prior.get("provenance") or (
        aer_provenance() if backend_name == "aer" else audit.cutensornet_provenance()
    )
    provenance["manifest_sha256"] = manifest_hash
    provenance["runner_sha256"] = sha256(Path(__file__))
    provenance["protocol_sha256"] = sha256(PROTOCOL)
    for case_spec in CASES:
        case_name = case_spec["name"]
        for setting in SETTINGS:
            for method in METHOD_NAMES:
                for ordering in ORDERINGS:
                    identity = (case_name, setting["name"], method, ordering)
                    if identity in unique:
                        print(f"[resume] {backend_name}/" + "/".join(identity), flush=True)
                        continue
                    spec = specs[(case_name, method, ordering)]
                    print(f"[start] {backend_name}/" + "/".join(identity), flush=True)
                    circuit = audit.load_circuit(HERE / spec["circuit_file"])
                    if backend_name == "aer":
                        state, simulation_seconds = simulate_aer(
                            circuit, setting["bond"], setting["cutoff"]
                        )
                    else:
                        state, simulation_seconds = audit.simulate(
                            circuit, setting["bond"], setting["cutoff"]
                        )
                    raw_norm = audit.normalize_state(state)
                    metric_started = perf_counter()
                    metrics, accumulator = audit.score_state(state, spec["scorer"])
                    reference = np.load(
                        HERE / spec["reference_file"], mmap_mode="r", allow_pickle=False
                    )
                    comparison = audit.compare_states(reference, state)
                    comparison["raw_approximate_norm"] = raw_norm
                    comparison["raw_norm_drift"] = raw_norm - 1.0
                    metric_seconds = perf_counter() - metric_started
                    row = {
                        "case": case_name,
                        "backend": backend_name,
                        "setting": setting["name"],
                        "bond": setting["bond"],
                        "cutoff": setting["cutoff"],
                        "method": method,
                        "ordering": ordering,
                        "qubits": spec["qubits"],
                        "depth": DEPTH,
                        "metrics": metrics,
                        "comparison": comparison,
                        "resources": spec["resources"],
                        "simulation_seconds": simulation_seconds,
                        "metric_seconds": metric_seconds,
                        "elapsed_seconds": simulation_seconds + metric_seconds,
                        "accumulator": accumulator,
                    }
                    unique[identity] = row
                    rows = sorted(unique.values(), key=job_identity)
                    write_json(
                        checkpoint_path,
                        {
                            "stage": f"cross_case_{backend_name}_mps_ladder",
                            "complete": len(rows) == EXPECTED_NEW_PER_BACKEND,
                            "manifest_sha256": manifest_hash,
                            "protocol_sha256": sha256(PROTOCOL),
                            "provenance": provenance,
                            "settings": SETTINGS,
                            "expected_jobs": EXPECTED_NEW_PER_BACKEND,
                            "rows": rows,
                            "errors": [],
                        },
                    )
                    print(
                        f"[complete] {backend_name}/" + "/".join(identity)
                        + f" fidelity={comparison['state_fidelity']:.8f} "
                        + f"TVD={comparison['total_variation_distance']:.3e} "
                        + f"seconds={row['elapsed_seconds']:.2f}",
                        flush=True,
                    )
                    del state, reference, circuit, row
                    gc.collect()
    if len(unique) != EXPECTED_NEW_PER_BACKEND:
        raise AssertionError(f"Expected {EXPECTED_NEW_PER_BACKEND} {backend_name} jobs")


def selected_reused_rows(path: Path, backend_name: str) -> list[dict]:
    artifact = read_json(path)
    if not artifact.get("complete"):
        raise RuntimeError(f"Incomplete reused artifact: {path}")
    setting_names = {setting["name"] for setting in SETTINGS}
    rows = [
        {**row, "backend": backend_name}
        for row in artifact["rows"]
        if row["case"] == REUSED_CASE and row["setting"] in setting_names
    ]
    if len(rows) != EXPECTED_REUSED_PER_BACKEND or len({job_identity(row) for row in rows}) != len(rows):
        raise AssertionError(f"Expected {EXPECTED_REUSED_PER_BACKEND} unique reused {backend_name} rows")
    return rows


def exact_rows(manifest: dict) -> dict:
    result = {exact_identity(row): row["exact_metrics"] for row in manifest["rows"]}
    prior_manifest = read_json(PRIOR_MANIFEST)
    if not prior_manifest.get("complete") or len(prior_manifest.get("rows", [])) != 6:
        raise RuntimeError("Prior exact reference manifest is incomplete")
    for row in prior_manifest["rows"]:
        result[(REUSED_CASE, row["method"], row["ordering"])] = row["exact_metrics"]
    if len(result) != len(ALL_CASES) * len(METHOD_NAMES) * len(ORDERINGS):
        raise AssertionError("Exact metric design is incomplete")
    return result


def analyze() -> None:
    manifest = verify_manifest()
    aer = read_json(AER_CHECKPOINT) if AER_CHECKPOINT.exists() else {}
    cutn = read_json(CUTN_CHECKPOINT) if CUTN_CHECKPOINT.exists() else {}
    for name, artifact in (("aer", aer), ("cutensornet", cutn)):
        if not artifact.get("complete") or len(artifact.get("rows", [])) != EXPECTED_NEW_PER_BACKEND:
            raise RuntimeError(f"All {EXPECTED_NEW_PER_BACKEND} new {name} rows are required")
        if artifact.get("manifest_sha256") != sha256(MANIFEST):
            raise RuntimeError(f"{name} checkpoint/manifest mismatch")
    rows = [
        *aer["rows"],
        *cutn["rows"],
        *selected_reused_rows(PRIOR_AER, "aer"),
        *selected_reused_rows(PRIOR_CUTN, "cutensornet"),
    ]
    if len(rows) != EXPECTED_TOTAL:
        raise AssertionError(f"Expected {EXPECTED_TOTAL} combined rows, got {len(rows)}")
    lookup = {
        (row["case"], row["backend"], row["setting"], row["method"], row["ordering"]): row
        for row in rows
    }
    if len(lookup) != EXPECTED_TOTAL:
        raise AssertionError("Duplicate combined rows")
    exact = exact_rows(manifest)
    summaries = []
    cross_backend = []
    for case_name in ALL_CASES:
        for setting in SETTINGS:
            for ordering in ORDERINGS:
                effects = {}
                for backend_name in ("aer", "cutensornet"):
                    cohort = {
                        method: lookup[(case_name, backend_name, setting["name"], method, ordering)]
                        for method in METHOD_NAMES
                    }
                    exact_effect = (
                        exact[(case_name, "prior_matched_random", ordering)]["bks_rate"]
                        - exact[(case_name, "published_lr", ordering)]["bks_rate"]
                    )
                    approximate_effect = (
                        cohort["prior_matched_random"]["metrics"]["bks_rate"]
                        - cohort["published_lr"]["metrics"]["bks_rate"]
                    )
                    evolutionary_effect = (
                        cohort["prior_evolutionary"]["metrics"]["bks_rate"]
                        - cohort["published_lr"]["metrics"]["bks_rate"]
                    )
                    tvd_bound = sum(
                        cohort[method]["comparison"]["total_variation_distance"]
                        for method in ("published_lr", "prior_matched_random")
                    )
                    fidelity_bound = sum(
                        np.sqrt(max(0.0, 1.0 - cohort[method]["comparison"]["state_fidelity"]))
                        for method in ("published_lr", "prior_matched_random")
                    )
                    actual_effect_error = abs(approximate_effect - exact_effect)
                    row = {
                        "case": case_name,
                        "backend": backend_name,
                        **setting,
                        "ordering": ordering,
                        "exact_matched_bks_effect": exact_effect,
                        "matched_bks_effect": approximate_effect,
                        "evolutionary_bks_effect": evolutionary_effect,
                        "matched_sign_correct": sign(approximate_effect) == sign(exact_effect),
                        "tvd_effect_bound": tvd_bound,
                        "actual_effect_error": actual_effect_error,
                        "tvd_bound_valid": actual_effect_error <= tvd_bound + 1e-12,
                        "exact_margin_tvd_certified": abs(exact_effect) > tvd_bound,
                        "approximate_margin_tvd_certified": abs(approximate_effect) > tvd_bound,
                        "fidelity_effect_bound": fidelity_bound,
                        "fidelity_certified": abs(exact_effect) > fidelity_bound,
                        "normalized_margin_ratio": tvd_bound / abs(exact_effect),
                        "minimum_state_fidelity": min(
                            item["comparison"]["state_fidelity"] for item in cohort.values()
                        ),
                        "maximum_tvd": max(
                            item["comparison"]["total_variation_distance"] for item in cohort.values()
                        ),
                        "maximum_absolute_bks_error": max(
                            abs(item["metrics"]["bks_rate"] - exact[(case_name, method, ordering)]["bks_rate"])
                            for method, item in cohort.items()
                        ),
                        "total_elapsed_seconds": sum(item["elapsed_seconds"] for item in cohort.values()),
                    }
                    if not row["tvd_bound_valid"]:
                        raise AssertionError(f"TVD theorem violation: {row}")
                    summaries.append(row)
                    effects[backend_name] = approximate_effect
                cross_backend.append(
                    {
                        "case": case_name,
                        "setting": setting["name"],
                        "ordering": ordering,
                        "aer_effect": effects["aer"],
                        "cutensornet_effect": effects["cutensornet"],
                        "same_sign": sign(effects["aer"]) == sign(effects["cutensornet"]),
                        "absolute_effect_difference": abs(effects["aer"] - effects["cutensornet"]),
                    }
                )

    case_summaries = []
    for case_name in ALL_CASES:
        case_rows = [row for row in summaries if row["case"] == case_name]
        cross_rows = [row for row in cross_backend if row["case"] == case_name]
        first_universal = None
        for setting in SETTINGS:
            cohort = [row for row in case_rows if row["name"] == setting["name"]]
            if len(cohort) == 4 and all(row["exact_margin_tvd_certified"] for row in cohort):
                first_universal = setting["name"]
                break
        case_summaries.append(
            {
                "case": case_name,
                "sign_correct": sum(row["matched_sign_correct"] for row in case_rows),
                "sign_total": len(case_rows),
                "exact_margin_certified": sum(row["exact_margin_tvd_certified"] for row in case_rows),
                "approximate_margin_certified": sum(
                    row["approximate_margin_tvd_certified"] for row in case_rows
                ),
                "cross_backend_same_sign": sum(row["same_sign"] for row in cross_rows),
                "cross_backend_total": len(cross_rows),
                "first_universal_certified_setting": first_universal,
                "maximum_normalized_margin_ratio": max(
                    row["normalized_margin_ratio"] for row in case_rows
                ),
            }
        )
    certified = [row for row in summaries if row["normalized_margin_ratio"] < 1.0]
    uncertified = [row for row in summaries if row["normalized_margin_ratio"] >= 1.0]
    global_summary = {
        "backend_cohorts": len(summaries),
        "cross_backend_cohorts": len(cross_backend),
        "sign_correct": sum(row["matched_sign_correct"] for row in summaries),
        "sign_total": len(summaries),
        "exact_margin_certified": sum(row["exact_margin_tvd_certified"] for row in summaries),
        "approximate_margin_certified": sum(
            row["approximate_margin_tvd_certified"] for row in summaries
        ),
        "fidelity_certified": sum(row["fidelity_certified"] for row in summaries),
        "tvd_bounds_valid": sum(row["tvd_bound_valid"] for row in summaries),
        "cross_backend_same_sign": sum(row["same_sign"] for row in cross_backend),
        "cross_backend_total": len(cross_backend),
        "ratio_below_one_sign_correct": sum(row["matched_sign_correct"] for row in certified),
        "ratio_below_one_total": len(certified),
        "ratio_at_least_one_sign_correct": sum(row["matched_sign_correct"] for row in uncertified),
        "ratio_at_least_one_total": len(uncertified),
        "new_job_seconds": sum(row["elapsed_seconds"] for row in aer["rows"] + cutn["rows"]),
    }
    write_json(
        COMBINED,
        {
            "stage": "cross_case_combined_jobs",
            "complete": True,
            "created_at": utc_now(),
            "manifest_sha256": sha256(MANIFEST),
            "expected_rows": EXPECTED_TOTAL,
            "rows": rows,
        },
    )
    payload = {
        "stage": "cross_case_replication_analysis",
        "complete": True,
        "created_at": utc_now(),
        "protocol_sha256": sha256(PROTOCOL),
        "manifest_sha256": sha256(MANIFEST),
        "aer_checkpoint_sha256": sha256(AER_CHECKPOINT),
        "cutensornet_checkpoint_sha256": sha256(CUTN_CHECKPOINT),
        "combined_sha256": sha256(COMBINED),
        "global": global_summary,
        "cases": case_summaries,
        "summaries": summaries,
        "cross_backend": cross_backend,
    }
    write_json(ANALYSIS, payload)
    write_report(payload)
    print(
        f"Analyzed all {EXPECTED_TOTAL} rows: sign={global_summary['sign_correct']}/"
        f"{global_summary['sign_total']}, certified={global_summary['exact_margin_certified']}/"
        f"{global_summary['backend_cohorts']}",
        flush=True,
    )


def write_report(analysis: dict) -> None:
    g = analysis["global"]
    lines = [
        "# Cross-case exact MPS replication",
        "",
        "All 300 frozen backend rows completed before analysis: 240 newly executed rows "
        "and 60 hash-validated 24-qubit rows.",
        "",
        "## Primary outcomes",
        "",
        f"- Matched-vs-LR exact-sign correctness: {g['sign_correct']}/{g['sign_total']} backend cohorts.",
        f"- Cross-backend sign agreement: {g['cross_backend_same_sign']}/{g['cross_backend_total']} cohorts.",
        f"- Exact-margin TVD certificates: {g['exact_margin_certified']}/{g['backend_cohorts']} cohorts.",
        f"- Approximate-margin TVD certificates: {g['approximate_margin_certified']}/{g['backend_cohorts']} cohorts.",
        f"- Fidelity-only certificates: {g['fidelity_certified']}/{g['backend_cohorts']} cohorts.",
        f"- Verified TVD inequalities: {g['tvd_bounds_valid']}/{g['backend_cohorts']} cohorts.",
        f"- When normalized TVD/margin < 1: {g['ratio_below_one_sign_correct']}/"
        f"{g['ratio_below_one_total']} signs correct; at >= 1: "
        f"{g['ratio_at_least_one_sign_correct']}/{g['ratio_at_least_one_total']}.",
        "",
        "## Per-case replication",
        "",
        "| Case | Correct signs | TVD-certified | Cross-backend signs | First universally certified setting | Max TVD/margin |",
        "|---|---:|---:|---:|---|---:|",
    ]
    for row in analysis["cases"]:
        first = row["first_universal_certified_setting"] or "none"
        lines.append(
            f"| {row['case']} | {row['sign_correct']}/{row['sign_total']} | "
            f"{row['exact_margin_certified']}/{row['sign_total']} | "
            f"{row['cross_backend_same_sign']}/{row['cross_backend_total']} | {first} | "
            f"{row['maximum_normalized_margin_ratio']:.3f} |"
        )
    lines.extend(
        [
            "",
            "A setting is called universally certified only when the exact-margin TVD "
            "certificate holds for both backends and both orderings. The first setting is "
            "taken in the protocol-frozen ladder order, not selected post hoc by runtime.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def status() -> None:
    for name, path, expected in (
        ("aer", AER_CHECKPOINT, EXPECTED_NEW_PER_BACKEND),
        ("cutensornet", CUTN_CHECKPOINT, EXPECTED_NEW_PER_BACKEND),
    ):
        artifact = read_json(path) if path.exists() else {}
        rows = artifact.get("rows", [])
        seconds = sum(float(row.get("elapsed_seconds", 0.0)) for row in rows)
        print(f"{name}: {len(rows)}/{expected}, complete={artifact.get('complete', False)}, job_hours={seconds/3600:.3f}")
    print(f"analysis: complete={ANALYSIS.exists() and read_json(ANALYSIS).get('complete', False)}")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=(
            "export",
            "self-test-aer",
            "self-test-cutn",
            "run-aer",
            "run-cutn",
            "analyze",
            "status",
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    RESULTS.mkdir(parents=True, exist_ok=True)
    actions = {
        "export": export_inputs,
        "self-test-aer": lambda: run_self_test("aer"),
        "self-test-cutn": lambda: run_self_test("cutensornet"),
        "run-aer": lambda: run_jobs("aer"),
        "run-cutn": lambda: run_jobs("cutensornet"),
        "analyze": analyze,
        "status": status,
    }
    actions[args.command]()


if __name__ == "__main__":
    main()
