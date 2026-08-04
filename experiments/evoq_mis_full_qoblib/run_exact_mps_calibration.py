"""Calibrate Aer MPS approximation against exact states on real QOBLIB kernels."""

from __future__ import annotations

import json
from time import perf_counter

import numpy as np
from qiskit_aer import AerSimulator

import run_cycle as rc


CASES = ("es60fst01", "es60fst03")
METHODS = ("published_lr", "matched_random_search")
SETTINGS = (
    (16, 1e-3),
    (16, 3e-4),
    (16, 1e-4),
    (32, 1e-3),
    (32, 3e-4),
    (32, 1e-4),
    (64, 1e-3),
    (64, 3e-4),
    (64, 1e-4),
    (128, 1e-3),
    (128, 3e-4),
    (128, 1e-4),
    (128, 1e-5),
    (128, 1e-6),
)


def probability_metrics(case, probabilities):
    feasible = bks = near = quality = conditional_size = 0.0
    best = None
    distribution = {}
    width = case.reduced_vertices
    for index, probability in enumerate(probabilities):
        probability = float(probability)
        if probability < 1e-16:
            continue
        # Qiskit statevector indexing is q[n-1]...q[0]; the released decoder
        # expects q[0]...q[n-1] because the circuit reverses classical bits.
        bitstring = format(index, f"0{width}b")[::-1]
        decoded = case.decoder.decode(bitstring)
        if not decoded.raw_feasible:
            continue
        size = int(decoded.raw_selected)
        feasible += probability
        bks += probability if size >= case.bks else 0.0
        near += probability if size >= case.bks - 1 else 0.0
        quality += probability * min(size / case.bks, 1.0)
        conditional_size += probability * size
        best = size if best is None else max(best, size)
        distribution[str(size)] = distribution.get(str(size), 0.0) + probability
    return {
        "feasible_rate": feasible,
        "bks_rate": bks,
        "near_bks_rate": near,
        "quality_mass": quality,
        "conditional_mean_size": conditional_size / feasible if feasible else None,
        "best_size_with_nonzero_probability": best,
        "size_distribution": dict(sorted(distribution.items(), key=lambda item: int(item[0]))),
    }


def simulate_state(case, genome, mode, bond=None, threshold=None):
    circuit = rc.bind_case(case, np.asarray(genome, dtype=float)).remove_final_measurements(
        inplace=False
    )
    circuit.save_statevector()
    if mode == "statevector":
        backend = AerSimulator(method="statevector", max_parallel_experiments=1)
    else:
        backend = AerSimulator(
            method="matrix_product_state",
            matrix_product_state_max_bond_dimension=bond,
            matrix_product_state_truncation_threshold=threshold,
            max_parallel_experiments=1,
        )
    start = perf_counter()
    result = backend.run(circuit).result()
    elapsed = perf_counter() - start
    vector = np.asarray(result.get_statevector(circuit), dtype=np.complex128)
    vector /= np.linalg.norm(vector)
    metadata = result.results[0].metadata
    return vector, elapsed, metadata


def distribution_errors(exact, approximate):
    p = np.abs(exact) ** 2
    q = np.abs(approximate) ** 2
    midpoint = 0.5 * (p + q)

    def kl(a, b):
        mask = a > 0
        return float(np.sum(a[mask] * np.log(a[mask] / np.maximum(b[mask], 1e-300))))

    return {
        "state_fidelity": float(abs(np.vdot(exact, approximate)) ** 2),
        "total_variation": float(0.5 * np.abs(p - q).sum()),
        "hellinger": float(np.sqrt(0.5 * ((np.sqrt(p) - np.sqrt(q)) ** 2).sum())),
        "jensen_shannon": float(0.5 * kl(p, midpoint) + 0.5 * kl(q, midpoint)),
        "max_probability_error": float(np.max(np.abs(p - q))),
    }


def main():
    validation = json.loads((rc.RESULTS / "validation.json").read_text(encoding="utf-8"))
    champions = validation["frozen_champions"]
    payload = {
        "stage": "exact_mps_calibration",
        "provenance": rc.provenance(),
        "cases": [],
        "methods": list(METHODS),
        "settings": [{"bond": b, "threshold": t} for b, t in SETTINGS],
        "rows": [],
    }
    for case_name in CASES:
        case = rc.prepare_case(case_name)
        payload["cases"].append(rc.case_metadata(case))
        for method in METHODS:
            genome = champions[method]["genome"]
            print(f"EXACT {case_name} {method}", flush=True)
            exact, exact_elapsed, exact_metadata = simulate_state(
                case, genome, mode="statevector"
            )
            exact_probabilities = np.abs(exact) ** 2
            exact_metrics = probability_metrics(case, exact_probabilities)
            for bond, threshold in SETTINGS:
                print(
                    f"MPS {case_name} {method} bond={bond} threshold={threshold:g}",
                    flush=True,
                )
                approximate, elapsed, metadata = simulate_state(
                    case, genome, mode="mps", bond=bond, threshold=threshold
                )
                approximate_probabilities = np.abs(approximate) ** 2
                approximate_metrics = probability_metrics(case, approximate_probabilities)
                metric_errors = {
                    key: float(approximate_metrics[key] - exact_metrics[key])
                    for key in ("bks_rate", "near_bks_rate", "feasible_rate", "quality_mass")
                }
                payload["rows"].append(
                    {
                        "case": case_name,
                        "method": method,
                        "genome": genome,
                        "bond": bond,
                        "threshold": threshold,
                        "exact_runtime_seconds": exact_elapsed,
                        "mps_runtime_seconds": elapsed,
                        "exact_metrics": exact_metrics,
                        "mps_metrics": approximate_metrics,
                        "metric_errors": metric_errors,
                        "distribution_errors": distribution_errors(exact, approximate),
                        "exact_metadata": exact_metadata,
                        "mps_metadata": metadata,
                    }
                )
                rc.write_json(rc.RESULTS / "exact_mps_calibration_checkpoint.json", payload)
    rc.write_json(rc.RESULTS / "exact_mps_calibration.json", payload)


if __name__ == "__main__":
    main()
