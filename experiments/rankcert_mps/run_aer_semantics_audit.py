"""Isolated-process audits of Aer MPS truncation and logging semantics."""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from parse_aer_mps_log import parse_mps_log


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULTS = REPO / "results" / "rankcert_mps"
OUTPUT = RESULTS / "aer_semantics_audit.json"
W = 1e-4


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def encode_state(state) -> list[list[float]]:
    return [[float(value.real), float(value.imag)] for value in np.asarray(state)]


def decode_state(state) -> np.ndarray:
    return np.asarray([complex(real, imag) for real, imag in state])


def circuit_for(name: str):
    from qiskit import QuantumCircuit

    if name == "published_4q":
        circuit = QuantumCircuit(4)
        circuit.h(1)
        circuit.cx(1, 2)
        circuit.swap(0, 1)
        circuit.swap(2, 3)
        circuit.h(1)
        circuit.cx(1, 2)
    elif name == "analytic_2q":
        circuit = QuantumCircuit(2)
        circuit.ry(2 * np.arcsin(np.sqrt(W)), 0)
        circuit.cx(0, 1)
    else:
        raise ValueError(name)
    circuit.save_statevector()
    return circuit


def child_run(args) -> None:
    import qiskit_aer
    from qiskit_aer import AerSimulator

    options = {
        "method": "matrix_product_state",
        "mps_log_data": True,
        "chop_threshold": args.chop,
        "matrix_product_state_truncation_threshold": args.cutoff,
        "max_parallel_threads": 1,
        "max_parallel_experiments": 1,
        "mps_omp_threads": 1,
        "fusion_enable": False,
    }
    if args.bond is not None:
        options["matrix_product_state_max_bond_dimension"] = args.bond
    circuit = circuit_for(args.circuit)
    result = AerSimulator(**options).run(circuit).result()
    experiment = result.results[0]
    payload = {
        "circuit": args.circuit,
        "bond": args.bond,
        "cutoff": args.cutoff,
        "chop_threshold": args.chop,
        "qiskit_aer": qiskit_aer.__version__,
        "success": bool(result.success),
        "statevector": encode_state(result.get_statevector()),
        "metadata": experiment.metadata,
        "raw_mps_log": experiment.metadata.get("MPS_log_data", ""),
    }
    print(json.dumps(payload))


def isolated(circuit: str, bond: int | None, cutoff: float, chop: float) -> dict:
    command = [sys.executable, str(Path(__file__).resolve()), "child", circuit,
               "--cutoff", repr(cutoff), "--chop", repr(chop)]
    if bond is not None:
        command.extend(("--bond", str(bond)))
    completed = subprocess.run(command, capture_output=True, text=True, check=True)
    payload = json.loads(completed.stdout)
    payload["parsed_log"] = parse_mps_log(payload["raw_mps_log"])
    return payload


def fidelity(left: np.ndarray, right: np.ndarray) -> float:
    return float(abs(np.vdot(left, right)) ** 2 / (np.vdot(left, left).real * np.vdot(right, right).real))


def main_audit() -> None:
    tests_a = {
        str(threshold): isolated("published_4q", None, threshold, 0.0)
        for threshold in (0.0, 0.5, 0.9)
    }
    b1 = isolated("analytic_2q", None, 0.0, 0.0)
    b2 = isolated("analytic_2q", 1, 0.0, 0.0)
    b3 = isolated("analytic_2q", None, 2e-4, 0.0)
    b2_hidden = isolated("analytic_2q", 1, 0.0, 1e-3)
    exact = decode_state(b1["statevector"])
    for row in (b1, b2, b3, b2_hidden):
        state = decode_state(row["statevector"])
        row["fidelity_to_untruncated"] = fidelity(exact, state)
        row["state_norm"] = float(np.vdot(state, state).real)
    b2_weight = b2["parsed_log"]["discarded_weights"]
    payload = {
        "stage": "aer_semantics_audit",
        "complete": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "process_isolation": True,
        "analytic_weight": W,
        "test_a": tests_a,
        "test_b": {"B1": b1, "B2": b2, "B3": b3},
        "chop_threshold_regression": {
            "visible": b2,
            "hidden": b2_hidden,
            "states_equal": bool(np.allclose(decode_state(b2["statevector"]), decode_state(b2_hidden["statevector"]), atol=1e-14, rtol=0)),
            "visible_event_count": b2["parsed_log"]["number_of_truncations"],
            "hidden_event_count": b2_hidden["parsed_log"]["number_of_truncations"],
        },
        "checks": {
            "B1_no_approximation": b1["parsed_log"]["number_of_truncations"] == 0 and math.isclose(b1["fidelity_to_untruncated"], 1.0, abs_tol=1e-14),
            "B2_one_event": len(b2_weight) == 1,
            "B2_discarded_value_matches_w": len(b2_weight) == 1 and math.isclose(b2_weight[0], W, rel_tol=1e-8, abs_tol=1e-12),
            "B2_fidelity_matches_one_minus_w": math.isclose(b2["fidelity_to_untruncated"], 1-W, rel_tol=1e-10, abs_tol=1e-12),
            "B3_threshold_edge_case_present": b3["parsed_log"]["number_of_truncations"] == 0 and math.isclose(b3["fidelity_to_untruncated"], 1.0, abs_tol=1e-14),
            "chop_only_changes_logging": bool(np.allclose(decode_state(b2["statevector"]), decode_state(b2_hidden["statevector"]), atol=1e-14, rtol=0)) and b2_hidden["parsed_log"]["number_of_truncations"] == 0,
        },
    }
    atomic_json(OUTPUT, payload)
    print(json.dumps({"output": str(OUTPUT), "checks": payload["checks"],
                      "test_a_events": {k:v['parsed_log']['number_of_truncations'] for k,v in tests_a.items()}}, indent=2))


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    sub = result.add_subparsers(dest="command", required=True)
    sub.add_parser("audit")
    child = sub.add_parser("child")
    child.add_argument("circuit", choices=("published_4q", "analytic_2q"))
    child.add_argument("--bond", type=int)
    child.add_argument("--cutoff", type=float, required=True)
    child.add_argument("--chop", type=float, required=True)
    return result


if __name__ == "__main__":
    arguments = parser().parse_args()
    if arguments.command == "child":
        child_run(arguments)
    else:
        main_audit()
