"""Exact cuTensorNet amplitude contractions for sparse QAOA BKS events."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import numpy as np


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SOURCE = REPO / "experiments" / "evoq_mis_full_qoblib"
RESULTS = REPO / "results" / "exact_event_contraction"
SUPPORT = RESULTS / "event_support.json"
MANIFEST = SOURCE / "results" / "cutensornet" / "export_manifest.json"
METHODS = ("published_lr", "matched_random_search")
ORDERINGS = ("sorted", "spectral")
SMALL_CASES = ("es60fst03", "es60fst01")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def jsonable(value):
    """Recursively convert common scientific-Python values to JSON types."""
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    if isinstance(value, np.ndarray):
        return jsonable(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return value.as_posix()
    return value


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(jsonable(payload), indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def provenance(hyper_samples: int) -> dict:
    import cupy
    import cuquantum
    import qiskit

    properties = cupy.cuda.runtime.getDeviceProperties(0)
    gpu = properties["name"]
    if isinstance(gpu, bytes):
        gpu = gpu.decode()
    free_bytes, total_bytes = cupy.cuda.runtime.memGetInfo()
    return {
        "created_at": utc_now(),
        "python": sys.version,
        "platform": platform.platform(),
        "qiskit": qiskit.__version__,
        "numpy": np.__version__,
        "cupy": cupy.__version__,
        "cuquantum": cuquantum.__version__,
        "gpu": gpu,
        "gpu_total_bytes": int(total_bytes),
        "gpu_free_bytes_at_start": int(free_bytes),
        "hyper_samples": hyper_samples,
        "support_sha256": sha256(SUPPORT),
        "source_manifest_sha256": sha256(MANIFEST),
    }


def source_rows() -> dict[tuple[str, str, str], dict]:
    payload = read_json(MANIFEST)
    output = {}
    for row in payload["rows"]:
        key = (row["case"], row["method"], row["ordering"])
        output[key] = row
    return output


def support_case(case_name: str) -> dict:
    payload = read_json(SUPPORT)
    if payload["source_manifest_sha256"] != sha256(MANIFEST):
        raise RuntimeError("Event support was built against a different source manifest")
    return next(row for row in payload["cases"] if row["case"] == case_name)


def load_circuit(row: dict):
    from qiskit import qpy

    path = SOURCE / row["qpy"]
    if sha256(path) != row["qpy_sha256"]:
        raise RuntimeError(f"Circuit hash mismatch: {path}")
    with path.open("rb") as handle:
        circuits = qpy.load(handle)
    if len(circuits) != 1:
        raise AssertionError(f"Expected one circuit in {path}")
    return circuits[0], path


def to_complex(value) -> complex:
    import cupy as cp

    return complex(cp.asnumpy(value).reshape(()).item())


def job_path(case_name: str, method: str, ordering: str, mode: str) -> Path:
    return RESULTS / f"{mode}_{case_name}_{method}_{ordering}.json"


def exact_reference_probability(case_name: str, method: str, ordering: str) -> float:
    rows = source_rows()
    row = rows[(case_name, method, ordering)]
    reference_value = row.get("reference")
    if not reference_value:
        raise RuntimeError(f"No dense reference for {case_name}/{method}/{ordering}")
    reference_path = SOURCE / reference_value
    if sha256(reference_path) != row["reference_sha256"]:
        raise RuntimeError(f"Reference hash mismatch: {reference_path}")
    state = np.load(reference_path, allow_pickle=False)["state"]
    bitstrings = support_case(case_name)["orderings"][ordering]["bitstrings_q0_first"]
    total = 0.0
    for bitstring in bitstrings:
        amplitude = state[tuple(int(value) for value in bitstring)]
        total += float(abs(amplitude) ** 2)
    return total


def run_job(
    case_name: str,
    method: str,
    ordering: str,
    hyper_samples: int,
    mode: str,
    limit: int | None,
) -> dict:
    import cupy as cp
    from cuquantum.tensornet import NetworkOptions
    from cuquantum.tensornet.experimental import NetworkState, TNConfig

    rows = source_rows()
    row = rows[(case_name, method, ordering)]
    circuit, circuit_path = load_circuit(row)
    support = support_case(case_name)
    bitstrings = support["orderings"][ordering]["bitstrings_q0_first"]
    if limit is not None:
        bitstrings = bitstrings[:limit]
    output = job_path(case_name, method, ordering, mode)
    prior = read_json(output) if output.exists() else {}
    completed = {item["bitstring"]: item for item in prior.get("amplitudes", [])}
    if prior and (
        prior.get("circuit_sha256") != row["qpy_sha256"]
        or prior.get("support_sha256") != sha256(SUPPORT)
        or prior.get("hyper_samples") != hyper_samples
    ):
        raise RuntimeError(f"Checkpoint identity mismatch: {output}")

    payload = prior or {
        "stage": "exact_event_amplitude_contraction",
        "mode": mode,
        "case": case_name,
        "method": method,
        "ordering": ordering,
        "qubits": int(circuit.num_qubits),
        "event_support_size": len(support["orderings"][ordering]["bitstrings_q0_first"]),
        "target_amplitudes": len(bitstrings),
        "circuit": circuit_path.relative_to(REPO).as_posix(),
        "circuit_sha256": row["qpy_sha256"],
        "support_sha256": sha256(SUPPORT),
        "hyper_samples": hyper_samples,
        "provenance": provenance(hyper_samples),
        "amplitudes": [],
        "complete": False,
    }
    if payload["target_amplitudes"] != len(bitstrings):
        raise RuntimeError(f"Checkpoint target mismatch: {output}")

    pending = [bitstring for bitstring in bitstrings if bitstring not in completed]
    if pending:
        started_job = perf_counter()
        with NetworkState.from_circuit(
            circuit,
            dtype="complex128",
            backend="cupy",
            config=TNConfig(num_hyper_samples=hyper_samples),
            options=NetworkOptions(device_id=0, memory_limit="85%"),
        ) as state:
            for position, bitstring in enumerate(pending, start=len(completed) + 1):
                started = perf_counter()
                amplitude = to_complex(state.compute_amplitude(bitstring))
                elapsed = perf_counter() - started
                item = {
                    "bitstring": bitstring,
                    "amplitude_real": amplitude.real,
                    "amplitude_imag": amplitude.imag,
                    "probability": float(abs(amplitude) ** 2),
                    "elapsed_seconds": elapsed,
                }
                completed[bitstring] = item
                payload["amplitudes"] = [completed[key] for key in bitstrings if key in completed]
                payload["probability_sum"] = float(
                    sum(value["probability"] for value in payload["amplitudes"])
                )
                payload["updated_at"] = utc_now()
                payload["last_session_seconds"] = perf_counter() - started_job
                atomic_json(output, payload)
                print(
                    f"[{case_name}/{method}/{ordering}] {position}/{len(bitstrings)} "
                    f"p={item['probability']:.12g} sec={elapsed:.3f}",
                    flush=True,
                )
        cp.get_default_memory_pool().free_all_blocks()

    payload["amplitudes"] = [completed[key] for key in bitstrings]
    payload["probability_sum"] = float(
        sum(value["probability"] for value in payload["amplitudes"])
    )
    payload["total_contraction_seconds"] = float(
        sum(value["elapsed_seconds"] for value in payload["amplitudes"])
    )
    payload["complete"] = len(payload["amplitudes"]) == len(bitstrings)
    payload["completed_at"] = utc_now()
    atomic_json(output, payload)
    return payload


def self_test(hyper_samples: int) -> None:
    rows = []
    for case_name in SMALL_CASES:
        for method in METHODS:
            for ordering in ORDERINGS:
                payload = run_job(
                    case_name,
                    method,
                    ordering,
                    hyper_samples,
                    mode="selftest",
                    limit=None,
                )
                reference = exact_reference_probability(case_name, method, ordering)
                error = abs(payload["probability_sum"] - reference)
                rows.append(
                    {
                        "case": case_name,
                        "method": method,
                        "ordering": ordering,
                        "computed_probability": payload["probability_sum"],
                        "reference_probability": reference,
                        "absolute_error": error,
                        "passed": error <= 1e-10,
                    }
                )
    result = {
        "stage": "exact_event_contraction_self_test",
        "created_at": utc_now(),
        "tolerance": 1e-10,
        "rows": rows,
        "complete": all(row["passed"] for row in rows),
    }
    atomic_json(RESULTS / "self_test_summary.json", result)
    if not result["complete"]:
        raise AssertionError(result)
    print("self-test passed", max(row["absolute_error"] for row in rows))


def optimizer_info(info) -> dict:
    """Extract stable, JSON-safe fields exposed by cuTensorNet OptimizerInfo."""
    output = {"repr": repr(info)}
    for name in (
        "largest_intermediate",
        "opt_cost",
        "path",
        "slices",
        "num_slices",
        "intermediate_modes",
    ):
        if not hasattr(info, name):
            continue
        value = getattr(info, name)
        if isinstance(value, np.ndarray):
            value = value.tolist()
        elif name in ("path", "slices", "intermediate_modes"):
            value = list(value)
        elif isinstance(value, np.generic):
            value = value.item()
        output[name] = value
    return output


def lowlevel_pilot(
    case_name: str,
    method: str,
    ordering: str,
    hyper_samples: int,
) -> dict:
    """Try the explicit einsum contraction API after NetworkState failure."""
    import cupy as cp
    from cuquantum.tensornet import (
        CircuitToEinsum,
        NetworkOptions,
        OptimizerOptions,
        contract,
        contract_path,
    )

    rows = source_rows()
    row = rows[(case_name, method, ordering)]
    circuit, circuit_path = load_circuit(row)
    support = support_case(case_name)
    bitstring = support["orderings"][ordering]["bitstrings_q0_first"][0]
    output = job_path(case_name, method, ordering, "lowlevel_pilot")
    payload = {
        "stage": "exact_event_lowlevel_pilot",
        "case": case_name,
        "method": method,
        "ordering": ordering,
        "bitstring": bitstring,
        "circuit": circuit_path.relative_to(REPO).as_posix(),
        "circuit_sha256": row["qpy_sha256"],
        "support_sha256": sha256(SUPPORT),
        "hyper_samples": hyper_samples,
        "provenance": provenance(hyper_samples),
        "complete": False,
    }
    atomic_json(output, payload)
    try:
        converter = CircuitToEinsum(circuit, dtype="complex128", backend="cupy")
        expression, operands = converter.amplitude(bitstring)
        options = NetworkOptions(device_id=0, memory_limit="85%")
        optimize = OptimizerOptions(samples=hyper_samples, seed=260902)
        started = perf_counter()
        path, path_info = contract_path(
            expression, *operands, options=options, optimize=optimize
        )
        payload["path_seconds"] = perf_counter() - started
        payload["path_info"] = optimizer_info(path_info)
        payload["operand_count"] = len(operands)
        atomic_json(output, payload)

        started = perf_counter()
        fixed_optimize = OptimizerOptions(
            path=[(int(left), int(right)) for left, right in path],
            slicing=list(path_info.slices) if path_info.num_slices > 1 else None,
        )
        amplitude, contraction_info = contract(
            expression,
            *operands,
            options=options,
            optimize=fixed_optimize,
            return_info=True,
        )
        amplitude = to_complex(amplitude)
        payload.update(
            {
                "contraction_seconds": perf_counter() - started,
                "amplitude_real": amplitude.real,
                "amplitude_imag": amplitude.imag,
                "probability": float(abs(amplitude) ** 2),
                "contraction_info": optimizer_info(contraction_info),
                "complete": True,
                "completed_at": utc_now(),
            }
        )
        cp.get_default_memory_pool().free_all_blocks()
    except Exception as error:
        payload.update(
            {
                "error_type": type(error).__name__,
                "error": str(error),
                "failed_at": utc_now(),
            }
        )
        atomic_json(output, payload)
        raise
    atomic_json(output, payload)
    print(
        f"low-level pilot p={payload['probability']:.12g} "
        f"path={payload['path_seconds']:.3f}s contract={payload['contraction_seconds']:.3f}s"
    )
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action", choices=("self-test", "pilot", "lowlevel-pilot", "run")
    )
    parser.add_argument("--case", default="es60fst02")
    parser.add_argument("--method", choices=METHODS, default="published_lr")
    parser.add_argument("--ordering", choices=ORDERINGS, default="sorted")
    parser.add_argument("--hyper-samples", type=int, default=32)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not SUPPORT.exists():
        raise RuntimeError(f"Build event support first: {SUPPORT}")
    if args.action == "self-test":
        self_test(args.hyper_samples)
    elif args.action == "pilot":
        payload = run_job(
            "es60fst02",
            "published_lr",
            "sorted",
            args.hyper_samples,
            mode="pilot",
            limit=1,
        )
        print("pilot probability", payload["probability_sum"])
    elif args.action == "lowlevel-pilot":
        lowlevel_pilot(
            args.case,
            args.method,
            args.ordering,
            args.hyper_samples,
        )
    else:
        payload = run_job(
            args.case,
            args.method,
            args.ordering,
            args.hyper_samples,
            mode="full",
            limit=None,
        )
        print("event probability", payload["probability_sum"])


if __name__ == "__main__":
    main()
