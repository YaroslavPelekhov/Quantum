"""Execute the frozen karate held-out end-to-end test."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from qiskit import qpy


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULTS = REPO / "results" / "signed_reduced_density_truncation"
sys.path[:0] = [
    str(HERE),
    str(REPO / "experiments" / "rankcert_mps"),
    str(REPO / "experiments" / "observable_telescope"),
]

import rankcert_inputs
from contrast_augmented import run_pair
from run_observable_telescope import bks_basis_indices
from srdt_core import atomic_json, sha256


PROTOCOL = HERE / "END_TO_END_HELDOUT_PROTOCOL.md"
OUTPUT = RESULTS / "end_to_end_heldout.json"


def load_circuit(path: str):
    with Path(path).open("rb") as handle:
        return qpy.load(handle)[0].remove_final_measurements(inplace=False)


def main() -> None:
    specs = rankcert_inputs.load_specs()
    payload = {
        "complete": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "protocol_sha256": sha256(PROTOCOL),
        "candidate_alpha": 0.25,
        "baseline_alpha": 0.0,
        "cut": 1,
        "rank": 1,
        "rows": [],
    }
    for ordering in ("sorted", "spectral"):
        spec_a = next(row for row in specs if (row["case"], row["ordering"], row["method"]) == ("karate", ordering, "published_lr"))
        spec_b = next(row for row in specs if (row["case"], row["ordering"], row["method"]) == ("karate", ordering, "prior_matched_random"))
        indices = bks_basis_indices(spec_a["scorer"])
        exact_a = np.asarray(np.load(spec_a["reference_file"], allow_pickle=False))
        exact_b = np.asarray(np.load(spec_b["reference_file"], allow_pickle=False))
        exact_delta = float((np.abs(exact_b[indices]) ** 2 - np.abs(exact_a[indices]) ** 2).sum())
        circuit_a, circuit_b = load_circuit(spec_a["circuit_file"]), load_circuit(spec_b["circuit_file"])
        methods = {}
        for name, alpha in (("state_averaged", 0.0), ("contrast_augmented", 0.25)):
            state_a, state_b, info = run_pair(circuit_a, circuit_b, cut=1, rank=1, alpha=alpha)
            delta = float((np.abs(state_b[indices]) ** 2 - np.abs(state_a[indices]) ** 2).sum())
            methods[name] = {
                "alpha": alpha,
                "delta": delta,
                "absolute_error": abs(delta - exact_delta),
                "sign_correct": bool(np.sign(delta) == np.sign(exact_delta)),
                **info,
            }
        candidate = methods["contrast_augmented"]
        baseline = methods["state_averaged"]
        row = {
            "case": "karate",
            "ordering": ordering,
            "qubits": circuit_a.num_qubits,
            "exact_delta": exact_delta,
            "methods": methods,
            "candidate_strictly_better": candidate["absolute_error"] < baseline["absolute_error"],
        }
        payload["rows"].append(row)
        atomic_json(OUTPUT, payload)
        print(json.dumps(row, indent=2), flush=True)
    payload["success"] = all(
        row["candidate_strictly_better"] and row["methods"]["contrast_augmented"]["sign_correct"]
        for row in payload["rows"]
    )
    payload["complete"] = True
    atomic_json(OUTPUT, payload)
    print(json.dumps({"output": str(OUTPUT), "success": payload["success"]}, indent=2))


if __name__ == "__main__":
    main()
