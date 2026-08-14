"""Checkpointed exact adjudication of the 24-qubit external-validity case."""

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

import run_cycle as rc
import run_external_validity_cycle as external
import run_resource_aware_cycle as resource


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results" / "exact_extension"
PROTOCOL = HERE / "EXACT_EXTENSION_PROTOCOL.md"
CHECKPOINT = RESULTS / "aves_exact.json"
ANALYSIS = RESULTS / "analysis.json"
REPORT = HERE / "EXACT_EXTENSION_REPORT.md"
EXTERNAL_CORE = HERE / "results" / "external_validity" / "core_mps.json"

CASE = "aves-sparrow-social"
CAP = 20
DEPTH = 15
ORDERINGS = ("sorted", "spectral")
METHODS = external.METHODS
METRICS = ("bks_rate", "near_bks_rate", "feasible_rate", "quality_mass")
CHUNK_SIZE = 1 << 18


def protocol_hash() -> str:
    return hashlib.sha256(PROTOCOL.read_bytes()).hexdigest()


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
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "qoblib_solutions_commit": rc.git_commit(rc.BASELINE_REPO),
    }


def identity(row: dict) -> tuple[str, str]:
    return row["method"], row["ordering"]


def compile_decoder(case) -> dict:
    """Compile exact unfold/scoring into literals over the circuit qubits.

    Every exact MIS reduction used by the frozen baseline maps an original
    vertex to a constant, a reduced qubit, or the complement of one reduced
    qubit.  Original graph edges then become deduplicated forbidden one- or
    two-bit patterns.  This representation is equivalent to MISPostprocessor
    but does not create one Python string/object per basis state.
    """

    # Literal representation: (qubit index, xor bit).  A negative qubit index
    # denotes a constant whose value is the xor bit.
    solution = {node: (qubit, 0) for qubit, node in enumerate(case.node_order)}
    for node in case.decoder.nodes_to_remove:
        solution[node] = (-1, 0)
    for node in case.decoder.nodes_to_add:
        solution[node] = (-1, 1)
    for folded, (v, u, w) in case.decoder.unfold_steps:
        source, invert = solution[folded]
        solution[u] = (source, invert)
        solution[w] = (source, invert)
        solution[v] = (source, invert ^ 1)

    missing = [node for node in case.decoder.original_nodes if node not in solution]
    if missing:
        raise AssertionError(f"Decoder compilation missed {len(missing)} original vertices")

    constant_selected = 0
    weights = np.zeros(case.qubits, dtype=np.int16)
    for node in case.decoder.original_nodes:
        source, invert = solution[node]
        if source < 0:
            constant_selected += invert
        elif invert:
            constant_selected += 1
            weights[source] -= 1
        else:
            weights[source] += 1

    forbidden = set()
    impossible = False
    for u_index, v_index in zip(case.decoder.edge_u, case.decoder.edge_v):
        u_node = case.decoder.original_nodes[int(u_index)]
        v_node = case.decoder.original_nodes[int(v_index)]
        u_source, u_invert = solution[u_node]
        v_source, v_invert = solution[v_node]
        # An unfolded original bit is selected when q == 1 xor invert.
        u_required = 1 ^ u_invert
        v_required = 1 ^ v_invert
        if u_source < 0 and v_source < 0:
            if u_invert and v_invert:
                impossible = True
            continue
        if u_source < 0:
            if u_invert:
                mask = 1 << v_source
                pattern = v_required << v_source
                forbidden.add((mask, pattern))
            continue
        if v_source < 0:
            if v_invert:
                mask = 1 << u_source
                pattern = u_required << u_source
                forbidden.add((mask, pattern))
            continue
        if u_source == v_source:
            if u_required == v_required:
                mask = 1 << u_source
                pattern = u_required << u_source
                forbidden.add((mask, pattern))
            continue
        mask = (1 << u_source) | (1 << v_source)
        pattern = (u_required << u_source) | (v_required << v_source)
        forbidden.add((mask, pattern))

    return {
        "solution": solution,
        "constant_selected": int(constant_selected),
        "weights": weights,
        "forbidden": tuple(sorted(forbidden)),
        "impossible": impossible,
    }


def compiled_outcomes(compiled: dict, indices: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    indices = np.asarray(indices, dtype=np.uint64)
    selected = np.full(indices.shape, compiled["constant_selected"], dtype=np.int16)
    for qubit, weight in enumerate(compiled["weights"]):
        if weight:
            selected += np.int16(weight) * ((indices >> np.uint64(qubit)) & np.uint64(1)).astype(
                np.int16
            )
    feasible = np.full(indices.shape, not compiled["impossible"], dtype=np.bool_)
    for mask, pattern in compiled["forbidden"]:
        feasible &= (indices & np.uint64(mask)) != np.uint64(pattern)
    return selected, feasible


def streaming_probability_metrics(case, amplitudes: np.ndarray) -> tuple[dict, dict]:
    expected = 1 << case.qubits
    if amplitudes.ndim != 1 or amplitudes.size != expected:
        raise ValueError(f"Expected {expected} amplitudes, got shape {amplitudes.shape}")
    compiled = compile_decoder(case)
    feasible_mass = bks_mass = near_mass = quality_mass = selected_mass = total_mass = 0.0
    best = None

    for start in range(0, expected, CHUNK_SIZE):
        stop = min(start + CHUNK_SIZE, expected)
        indices = np.arange(start, stop, dtype=np.uint64)
        block = amplitudes[start:stop]
        probabilities = block.real * block.real + block.imag * block.imag
        total_mass += float(probabilities.sum(dtype=np.float64))
        selected, feasible = compiled_outcomes(compiled, indices)
        if not np.any(feasible):
            continue
        feasible_probabilities = probabilities[feasible]
        feasible_sizes = selected[feasible]
        feasible_mass += float(feasible_probabilities.sum(dtype=np.float64))
        bks_mass += float(feasible_probabilities[feasible_sizes >= case.bks].sum(dtype=np.float64))
        near_mass += float(
            feasible_probabilities[feasible_sizes >= case.bks - 1].sum(dtype=np.float64)
        )
        selected_mass += float(
            np.dot(feasible_probabilities, feasible_sizes.astype(np.float64, copy=False))
        )
        quality_mass += float(
            np.dot(
                feasible_probabilities,
                np.minimum(feasible_sizes.astype(np.float64, copy=False) / case.bks, 1.0),
            )
        )
        positive = feasible & (probabilities > 0.0)
        if np.any(positive):
            chunk_best = int(selected[positive].max())
            best = chunk_best if best is None else max(best, chunk_best)

    if abs(total_mass - 1.0) > 1e-10:
        raise AssertionError(f"Statevector norm drift: {total_mass}")
    metrics = {
        "feasible_rate": feasible_mass,
        "bks_rate": bks_mass,
        "near_bks_rate": near_mass,
        "quality_mass": quality_mass,
        "conditional_mean_size": selected_mass / feasible_mass if feasible_mass else None,
        "best_size_nonzero_probability": best,
    }
    audit = {
        "implementation": "chunked_statevector_literal_accumulator",
        "chunk_size": CHUNK_SIZE,
        "basis_states": expected,
        "forbidden_patterns": len(compiled["forbidden"]),
        "statevector_norm": total_mass,
    }
    return metrics, audit


def streaming_exact_evaluate(case, genome: np.ndarray, depth: int) -> dict:
    circuit = resource.circuit_for(case, genome, depth)
    resources = resource.circuit_resources(circuit)
    bare = circuit.remove_final_measurements(inplace=False)
    simulation_start = perf_counter()
    state = Statevector.from_instruction(bare)
    simulation_seconds = perf_counter() - simulation_start
    metric_start = perf_counter()
    metrics, accumulator = streaming_probability_metrics(case, np.asarray(state.data))
    metric_seconds = perf_counter() - metric_start
    del state
    gc.collect()
    return {
        "metrics": metrics,
        "resources": resources,
        "elapsed_seconds": simulation_seconds + metric_seconds,
        "simulation_seconds": simulation_seconds,
        "metric_seconds": metric_seconds,
        "accumulator": accumulator,
    }


def exact_stage() -> dict:
    previous = read_json(CHECKPOINT) if CHECKPOINT.exists() else {}
    if previous and previous.get("protocol_sha256") != protocol_hash():
        raise RuntimeError("Protocol hash changed after the exact checkpoint was created")
    rows = previous.get("rows", [])
    unique = {identity(row): row for row in rows}

    for method, genome in METHODS.items():
        for ordering in ORDERINGS:
            key = (method, ordering)
            if key in unique:
                print(f"[exact] resume skip {method}/{ordering}", flush=True)
                continue
            print(f"[exact] starting {method}/{ordering}", flush=True)
            case = resource.prepare_case(CASE, CAP, ordering)
            if case.qubits != 24:
                raise AssertionError(f"Frozen kernel changed: expected 24 qubits, got {case.qubits}")
            result = streaming_exact_evaluate(case, np.asarray(genome), DEPTH)
            row = {
                "case": CASE,
                "bks": int(case.bks),
                "max_degree": CAP,
                "qubits": int(case.qubits),
                "method": method,
                "genome": genome,
                "depth": DEPTH,
                "ordering": ordering,
                **result,
            }
            unique[key] = row
            atomic_write_json(
                CHECKPOINT,
                {
                    "stage": "aves_24q_exact_statevector",
                    "complete": False,
                    "protocol_sha256": protocol_hash(),
                    "rows": sorted(unique.values(), key=identity),
                },
            )
            print(
                f"[exact] complete {method}/{ordering} in {result['elapsed_seconds']:.3f}s",
                flush=True,
            )
            del case, result, row
            gc.collect()

    rows = sorted(unique.values(), key=identity)
    expected = len(METHODS) * len(ORDERINGS)
    if len(rows) != expected:
        raise AssertionError(f"Expected {expected} exact rows, found {len(rows)}")

    max_ordering_error = 0.0
    for method in METHODS:
        pair = {row["ordering"]: row for row in rows if row["method"] == method}
        if set(pair) != set(ORDERINGS):
            raise AssertionError(f"Missing ordering for {method}")
        for metric in METRICS:
            error = abs(
                pair["sorted"]["metrics"][metric]
                - pair["spectral"]["metrics"][metric]
            )
            max_ordering_error = max(max_ordering_error, error)
    if max_ordering_error > 1e-10:
        raise AssertionError(f"Exact ordering remap error: {max_ordering_error}")

    payload = {
        "stage": "aves_24q_exact_statevector",
        "complete": True,
        "protocol_sha256": protocol_hash(),
        "provenance": provenance(),
        "max_ordering_error": max_ordering_error,
        "rows": rows,
    }
    atomic_write_json(CHECKPOINT, payload)
    return payload


def mean(values) -> float:
    values = list(values)
    if not values:
        raise ValueError("Cannot average an empty collection")
    return float(sum(values) / len(values))


def analyze_stage() -> dict:
    if not CHECKPOINT.exists():
        raise RuntimeError("Exact checkpoint does not exist")
    exact = read_json(CHECKPOINT)
    if not exact.get("complete", False) or len(exact.get("rows", [])) != 6:
        raise RuntimeError("Exact cohort is incomplete; partial results will not be analyzed")
    if exact.get("protocol_sha256") != protocol_hash():
        raise RuntimeError("Protocol hash mismatch")
    external_core = read_json(EXTERNAL_CORE)
    if not external_core.get("complete", False):
        raise RuntimeError("Frozen external MPS cohort is incomplete")
    mps_rows = [row for row in external_core["rows"] if row["case"] == CASE]

    exact_by_key = {identity(row): row for row in exact["rows"]}
    bias_rows = []
    for method in METHODS:
        for ordering in ORDERINGS:
            exact_row = exact_by_key[(method, ordering)]
            for setting in ("released", "confirm"):
                cohort = [
                    row
                    for row in mps_rows
                    if row["method"] == method
                    and row["ordering"] == ordering
                    and row["setting"] == setting
                ]
                if len(cohort) != 5:
                    raise AssertionError(
                        f"Expected 5 MPS seeds for {method}/{ordering}/{setting}, got {len(cohort)}"
                    )
                metrics = {}
                for metric in METRICS:
                    sampled = mean(row["metrics"][metric] for row in cohort)
                    exact_value = float(exact_row["metrics"][metric])
                    metrics[metric] = {
                        "exact": exact_value,
                        "mps_mean": sampled,
                        "mps_minus_exact": sampled - exact_value,
                    }
                bias_rows.append(
                    {
                        "method": method,
                        "ordering": ordering,
                        "setting": setting,
                        "paired_seeds": 5,
                        "metrics": metrics,
                    }
                )

    effects = []
    for candidate in ("prior_evolutionary", "prior_matched_random"):
        for ordering in ORDERINGS:
            reference = exact_by_key[("published_lr", ordering)]["metrics"]
            candidate_metrics = exact_by_key[(candidate, ordering)]["metrics"]
            effects.append(
                {
                    "candidate": candidate,
                    "ordering": ordering,
                    "metrics": {
                        metric: float(candidate_metrics[metric] - reference[metric])
                        for metric in METRICS
                    },
                }
            )

    payload = {
        "stage": "aves_24q_exact_analysis",
        "complete": True,
        "protocol_sha256": protocol_hash(),
        "exact_checkpoint": CHECKPOINT.relative_to(HERE).as_posix(),
        "external_checkpoint": EXTERNAL_CORE.relative_to(HERE).as_posix(),
        "exact_effects": effects,
        "mps_bias": bias_rows,
    }
    atomic_write_json(ANALYSIS, payload)
    write_report(payload)
    return payload


def write_report(analysis: dict) -> None:
    lines = [
        "# Exact 24-qubit external adjudication",
        "",
        "The frozen six-job exact cohort completed without measurement noise.",
        "",
        "## Exact schedule effects versus published LR",
        "",
        "| Candidate | Ordering | BKS | Near-BKS | Feasible | Quality mass |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in analysis["exact_effects"]:
        metrics = row["metrics"]
        lines.append(
            "| {candidate} | {ordering} | {bks_rate:+.8f} | "
            "{near_bks_rate:+.8f} | {feasible_rate:+.8f} | {quality_mass:+.8f} |".format(
                candidate=row["candidate"], ordering=row["ordering"], **metrics
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation rule",
            "",
            "The exact probabilities adjudicate the sign and magnitude of schedule effects. "
            "Approximate MPS differences are reported as diagnostic bias and are not used "
            "to retune any schedule.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("exact", "analyze", "all"), default="all")
    args = parser.parse_args()
    if args.stage in ("exact", "all"):
        exact_stage()
    if args.stage in ("analyze", "all"):
        analyze_stage()


if __name__ == "__main__":
    main()
