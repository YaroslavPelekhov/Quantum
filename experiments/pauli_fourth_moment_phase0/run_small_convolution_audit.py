"""Exact stabilizer-polytope tests for triple quantum convolution."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from stabilizer_core import (
    pauli_expectations,
    random_state,
    stabilizer_gauge,
    stabilizer_matrix,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-qubits", type=int, default=4)
    parser.add_argument("--seed", type=int, default=660100)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, default=Path(".cache"))
    args = parser.parse_args()
    trial_counts = {1: 5000, 2: 5000, 3: 2000, 4: 100}
    rng = np.random.default_rng(args.seed)
    rows = []
    violation = None
    for qubits in range(1, args.max_qubits + 1):
        matrix, contexts = stabilizer_matrix(qubits, args.cache_dir)
        best = -np.inf
        for trial in range(trial_counts[qubits]):
            states = [random_state(1 << qubits, rng) for _ in range(3)]
            coefficients = np.prod(
                [pauli_expectations(state, qubits) for state in states], axis=0
            )
            result = stabilizer_gauge(matrix, coefficients)
            gauge = float(result.fun) if result.success else float("inf")
            best = max(best, gauge)
            if gauge > 1.0 + 1e-8:
                violation = {
                    "qubits": qubits,
                    "trial": trial,
                    "gauge": gauge,
                }
                break
        rows.append(
            {
                "qubits": qubits,
                "contexts": len(contexts),
                "stabilizer_vertices": matrix.shape[1],
                "trials": trial_counts[qubits],
                "maximum_gauge": best,
            }
        )
        if violation:
            break
    payload = {
        "claim": "triple convolution of arbitrary inputs is stabilizer",
        "status": "counterexample" if violation else "no_violation",
        "seed": args.seed,
        "tolerance": 1e-8,
        "rows": rows,
        "violation": violation,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
