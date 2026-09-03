"""Independently recompute every stored six-qubit cover inequality."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from n6_oracle import N6Oracle
from run_n6_adversarial import PauliTransform


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contexts", type=Path, required=True)
    parser.add_argument("--certificate", type=Path, required=True)
    args = parser.parse_args()
    data = np.load(args.certificate)
    state = np.asarray(data["state"], dtype=np.complex128)
    exponent = float(data["exponent"])
    recomputed = np.abs(PauliTransform.cpu_expectations(state)) ** exponent
    target_error = float(np.max(np.abs(recomputed - data["target"])))
    oracle = N6Oracle(args.contexts)
    incidence = oracle.incidence(data["contexts"])
    cover = incidence @ data["weights"]
    deficits = np.maximum(recomputed - cover, 0.0)
    raw_weight = float(np.sum(data["weights"]))
    corrected = float(raw_weight + deficits.sum())
    payload = {
        "state_norm_error": abs(float(np.vdot(state, state).real) - 1.0),
        "target_recomputation_error": target_error,
        "minimum_slack": float(np.min(cover - recomputed)),
        "total_deficit_correction": float(deficits.sum()),
        "raw_cover_weight": raw_weight,
        "corrected_cover_weight": corrected,
        "strict": corrected < 1.0,
    }
    print(json.dumps(payload, indent=2))
    if payload["state_norm_error"] > 1e-12 or target_error > 1e-12 or not payload["strict"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
