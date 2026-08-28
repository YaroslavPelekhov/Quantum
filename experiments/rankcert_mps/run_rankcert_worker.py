"""One isolated Aer MPS schedule run; invoked only by the checkpointing driver."""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import numpy as np

from certificate import NUMERICAL_SIMULATION_TOLERANCE, accumulated_angle_certificate
from parse_aer_mps_log import parse_mps_log
from rankcert_inputs import PROJECT, atomic_json, lookup_spec, sha256

sys.path.insert(0, str(PROJECT))
import run_independent_ladder_audit as frozen_audit


def peak_memory_bytes() -> int | None:
    try:
        import psutil
        info = psutil.Process().memory_info()
        return int(getattr(info, "peak_wset", info.rss))
    except Exception:
        return None


def main(args) -> None:
    import qiskit
    import qiskit_aer
    from qiskit_aer import AerSimulator

    spec = lookup_spec(args.case, args.method, args.ordering)
    circuit_path = Path(spec["circuit_file"])
    if sha256(circuit_path) != spec["circuit_sha256"]:
        raise RuntimeError(f"Circuit hash mismatch: {circuit_path}")
    circuit = frozen_audit.load_circuit(circuit_path)
    executable = circuit.copy()
    executable.save_statevector()
    backend = AerSimulator(
        method="matrix_product_state",
        matrix_product_state_max_bond_dimension=args.bond,
        matrix_product_state_truncation_threshold=args.cutoff,
        max_parallel_experiments=1,
        max_parallel_threads=1,
        mps_omp_threads=1,
        mps_log_data=True,
        chop_threshold=0.0,
    )
    started = perf_counter()
    result = backend.run(executable).result()
    simulation_seconds = perf_counter() - started
    if not result.success:
        raise RuntimeError(str(result.status))
    raw_log = result.results[0].metadata.get("MPS_log_data", "")
    parsed = parse_mps_log(raw_log, include_segments=False)
    if len(parsed["discarded_weights"]) != len(parsed["events"]):
        raise AssertionError("Parser lost truncation events")
    raw_path = Path(args.raw_log)
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_log = raw_path.with_suffix(raw_path.suffix + ".tmp")
    temporary_log.write_text(raw_log, encoding="utf-8")
    os.replace(temporary_log, raw_path)

    state = np.array(result.get_statevector(executable), dtype=np.complex128, copy=True)
    raw_norm = frozen_audit.normalize_state(state)
    metric_started = perf_counter()
    metrics, accumulator = frozen_audit.score_state(state, spec["scorer"])
    reference_path = Path(spec["reference_file"])
    reference = np.load(reference_path, mmap_mode="r", allow_pickle=False)
    comparison = frozen_audit.compare_states(reference, state)
    metric_seconds = perf_counter() - metric_started
    certificate = accumulated_angle_certificate(parsed["certificate_weight_upper_bounds"])
    exact_bks = float(spec["exact_metrics"]["bks_rate"])
    mps_bks = float(metrics["bks_rate"])
    bks_error = abs(mps_bks - exact_bks)
    tvd = float(comparison["total_variation_distance"])
    tolerance = NUMERICAL_SIMULATION_TOLERANCE
    events_path = Path(args.events)
    atomic_json(events_path, {
        "raw_log_sha256": sha256(raw_path),
        "number_of_truncations": parsed["number_of_truncations"],
        "events": parsed["events"],
    })
    top_events = sorted(parsed["events"], key=lambda row: row["discarded_weight"], reverse=True)[:20]
    row = {
        "stage": "rankcert_aer_schedule_run",
        "complete": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "git_sha": args.git_sha,
        "python": sys.version,
        "platform": platform.platform(),
        "qiskit": qiskit.__version__,
        "qiskit_aer": qiskit_aer.__version__,
        "numpy": np.__version__,
        "case": spec["case"],
        "backend": "AerSimulator/matrix_product_state",
        "ordering": spec["ordering"],
        "bond": args.bond,
        "cutoff": args.cutoff,
        "setting": args.setting,
        "schedule": spec["schedule"],
        "method": spec["method"],
        "schedule_parameters": spec["schedule_parameters"],
        "qubits": spec["qubits"],
        "depth": spec["depth"],
        "circuit_file": str(circuit_path),
        "circuit_sha256": spec["circuit_sha256"],
        "reference_file": str(reference_path),
        "reference_sha256": spec["reference_sha256"],
        "seed": None,
        "shots": None,
        "deterministic_statevector_readout": True,
        "raw_log_path": str(raw_path),
        "raw_log_sha256": sha256(raw_path),
        "events_path": str(events_path),
        "number_of_truncations": parsed["number_of_truncations"],
        "discarded_weights": parsed["discarded_weights"],
        "discarded_weights_semantics": "Aer-reported values rounded to six significant digits",
        "certificate_discarded_weight_upper_bounds": parsed["certificate_weight_upper_bounds"],
        "certificate_rounding_policy": "upper endpoint of each six-significant-digit decimal rounding bin",
        "max_discarded_weight": parsed["max_discarded_weight"],
        "sum_discarded_weight": parsed["sum_discarded_weight"],
        "sum_sqrt_discarded_weight_heuristic": float(sum(np.sqrt(parsed["discarded_weights"]))),
        "sqrt_sum_discarded_weight_heuristic": float(np.sqrt(sum(parsed["discarded_weights"]))),
        "product_survival_loss_heuristic": float(1.0 - np.prod([1.0 - value for value in parsed["discarded_weights"]], dtype=np.float64)),
        "max_bond_seen": parsed["max_bond_seen"],
        "top_truncation_events": top_events,
        "raw_angle_sum": certificate.raw_angle_sum,
        "accumulated_angle": certificate.accumulated_angle,
        "epsilon_mps": certificate.epsilon,
        "epsilon_with_numerical_floor": min(1.0, certificate.epsilon + tolerance),
        "certificate_saturated": certificate.saturated,
        "p_bks_exact": exact_bks,
        "p_bks_mps": mps_bks,
        "actual_bks_error": bks_error,
        "certificate_slack_bks": certificate.epsilon - bks_error,
        "true_tvd": tvd,
        "certificate_slack_tvd": certificate.epsilon - tvd,
        "bks_bound_holds": bks_error <= certificate.epsilon + tolerance,
        "tvd_bound_holds": tvd <= certificate.epsilon + tolerance,
        "soundness_tolerance": tolerance,
        "metrics": metrics,
        "comparison": {**comparison, "raw_mps_norm": raw_norm, "raw_norm_drift": raw_norm - 1.0},
        "accumulator": accumulator,
        "simulation_seconds": simulation_seconds,
        "metric_seconds": metric_seconds,
        "runtime_seconds": simulation_seconds + metric_seconds,
        "peak_memory_bytes": peak_memory_bytes(),
        "aer_options": {
            "method": "matrix_product_state", "mps_log_data": True, "chop_threshold": 0.0,
            "matrix_product_state_max_bond_dimension": args.bond,
            "matrix_product_state_truncation_threshold": args.cutoff,
            "max_parallel_experiments": 1, "max_parallel_threads": 1, "mps_omp_threads": 1,
        },
    }
    atomic_json(Path(args.output), row)
    print(json.dumps({
        "output": args.output, "events": row["number_of_truncations"],
        "epsilon": row["epsilon_mps"], "tvd": tvd, "bks_error": bks_error,
        "runtime_seconds": row["runtime_seconds"],
    }))


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--case", required=True)
    result.add_argument("--method", required=True)
    result.add_argument("--ordering", required=True)
    result.add_argument("--setting", required=True)
    result.add_argument("--bond", type=int, required=True)
    result.add_argument("--cutoff", type=float, required=True)
    result.add_argument("--git-sha", required=True)
    result.add_argument("--output", required=True)
    result.add_argument("--raw-log", required=True)
    result.add_argument("--events", required=True)
    return result


if __name__ == "__main__":
    main(parser().parse_args())
