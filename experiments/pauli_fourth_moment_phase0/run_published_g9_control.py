"""Reproduce the published narrow-basin weighted beta violation on G9."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


I = np.eye(2, dtype=complex)
X = np.asarray([[0, 1], [1, 0]], dtype=complex)
Y = np.asarray([[0, -1j], [1j, 0]], dtype=complex)
Z = np.diag([1, -1]).astype(complex)
PAULI = {"I": I, "X": X, "Y": Y, "Z": Z}


def pauli_word(word: str) -> np.ndarray:
    output = np.asarray([[1.0 + 0.0j]])
    for letter in word:
        output = np.kron(output, PAULI[letter])
    return output


def objective(state: np.ndarray, operators: np.ndarray, weights: np.ndarray) -> float:
    expectations = np.real(np.einsum("i,kij,j->k", state.conj(), operators, state))
    return float(weights @ (expectations * expectations))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=80)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    words = ["XIII", "IXII", "IIXI", "ZIII", "IZII", "ZZZI", "YZYX", "YYXX", "YXZZ"]
    operators = np.stack([pauli_word(word) for word in words])
    weights = np.asarray([1, 1, 1, 1, 1, 1, 1, 2, 2], dtype=float)
    # Equation (95) prints a bra, so its entries are conjugated to form a ket.
    bra = np.asarray([
        0.065955j, -0.065955, -0.174514j, 0.174514,
        0.204966j, -0.204966, 0.028492j, -0.028492,
        0.130338, -0.130338j, -0.166030, 0.166030j,
        -0.236494, 0.236494j, 0.567352, -0.567352j,
    ], dtype=complex)
    state = bra.conj()
    state /= np.linalg.norm(state)
    initial_value = objective(state, operators, weights)
    history = [initial_value]
    root_weight = np.sqrt(weights)
    for _ in range(args.iterations):
        expectations = np.real(np.einsum("i,kij,j->k", state.conj(), operators, state))
        update = root_weight * expectations
        coefficients = update / np.linalg.norm(update)
        hamiltonian = np.einsum("i,ijk->jk", coefficients * root_weight, operators)
        eigenvalues, eigenvectors = np.linalg.eigh(hamiltonian)
        state = eigenvectors[:, int(np.argmax(np.abs(eigenvalues)))]
        history.append(objective(state, operators, weights))

    result = {
        "experiment": "published_G9_narrow_basin_positive_control",
        "source": "Wang_et_al_arXiv_2511.13531_equations_94_95",
        "weights": weights.tolist(),
        "weighted_alpha": 3.0,
        "published_beta": 3.044815,
        "initial_value": initial_value,
        "iterations": args.iterations,
        "final_value": history[-1],
        "absolute_error_to_published": abs(history[-1] - 3.044815),
        "status": "reproduced" if abs(history[-1] - 3.044815) < 2e-6 else "failed",
    }
    if result["status"] != "reproduced":
        raise AssertionError(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
