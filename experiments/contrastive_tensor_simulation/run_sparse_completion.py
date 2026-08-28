"""Run the frozen point-query construction test for signed diagonal contrast."""

from __future__ import annotations

import gc
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import numpy as np


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULTS = REPO / "results" / "contrastive_tensor_simulation"
OUTPUT = RESULTS / "sparse_completion.json"
PROTOCOL = HERE / "SPARSE_CONSTRUCTION_PROTOCOL.md"
sys.path[:0] = [
    str(HERE),
    str(REPO / "experiments" / "rankcert_mps"),
    str(REPO / "experiments" / "observable_telescope"),
]

import rankcert_inputs
from contrastive_core import atomic_json, canonical_parameter_count, sha256
from run_observable_telescope import bks_basis_indices
from sparse_tt_completion import (
    fit_tt_als,
    predict_indices,
    sample_distinct_indices,
)


CASES = ("ibm32", "aves-sparrow-social")
ORDERINGS = ("sorted", "spectral")
RANKS = (8, 12)
QUERY_MULTIPLIER = 24
HOLDOUT_COUNT = 65_536
SWEEPS = 12
RELATIVE_RIDGE = 1e-10
BASE_SEED = 20_260_822


def spec(case: str, method: str, ordering: str) -> dict:
    return next(
        row for row in rankcert_inputs.load_specs()
        if (row["case"], row["method"], row["ordering"])
        == (case, method, ordering)
    )


def oracle(state_a: np.ndarray, state_b: np.ndarray, indices: np.ndarray) -> np.ndarray:
    amplitude_a = np.asarray(state_a[indices])
    amplitude_b = np.asarray(state_b[indices])
    return np.square(np.abs(amplitude_b)) - np.square(np.abs(amplitude_a))


def run_row(case: str, ordering: str, rank: int) -> dict:
    spec_a = spec(case, "published_lr", ordering)
    spec_b = spec(case, "prior_matched_random", ordering)
    sites = int(spec_a["qubits"])
    total = 2**sites
    state_a = np.load(spec_a["reference_file"], mmap_mode="r", allow_pickle=False)
    state_b = np.load(spec_b["reference_file"], mmap_mode="r", allow_pickle=False)
    bks = bks_basis_indices(spec_a["scorer"])
    forbidden = set(int(value) for value in bks)
    parameters = canonical_parameter_count(sites, 2, rank)
    training_count = QUERY_MULTIPLIER * parameters
    seed = BASE_SEED + 10_000 * CASES.index(case) + 1_000 * ORDERINGS.index(ordering) + rank
    training = sample_distinct_indices(total, training_count, forbidden, seed)
    holdout = sample_distinct_indices(
        total,
        HOLDOUT_COUNT,
        forbidden | set(int(value) for value in training),
        seed + 101,
    )
    training_targets = oracle(state_a, state_b, training)
    holdout_targets = oracle(state_a, state_b, holdout)
    started = perf_counter()
    cores, fit = fit_tt_als(
        training,
        training_targets,
        sites=sites,
        max_rank=rank,
        sweeps=SWEEPS,
        relative_ridge=RELATIVE_RIDGE,
        seed=seed + 202,
    )
    holdout_prediction = predict_indices(cores, holdout, sites)
    holdout_error = holdout_prediction - holdout_targets
    holdout_rmse = float(np.sqrt(np.mean(np.square(holdout_error))))
    holdout_scale = float(np.sqrt(np.mean(np.square(holdout_targets))))
    bks_array = np.asarray(bks, dtype=np.int64)
    exact_delta = float(oracle(state_a, state_b, bks_array).sum(dtype=np.float64))
    estimated_delta = float(predict_indices(cores, bks_array, sites).sum(dtype=np.float64))
    result = {
        "case": case,
        "ordering": ordering,
        "qubits": sites,
        "rank": rank,
        "parameter_count": fit["parameter_count"],
        "training_query_count": training_count,
        "holdout_query_count": HOLDOUT_COUNT,
        "training_query_fraction": training_count / total,
        "bks_support_count": len(bks),
        "bks_training_overlap": int(np.isin(bks_array, training).sum()),
        "bks_holdout_overlap": int(np.isin(bks_array, holdout).sum()),
        "seed": seed,
        "sweeps": SWEEPS,
        "relative_ridge": RELATIVE_RIDGE,
        "fit_history": fit["history"],
        "holdout_rmse": holdout_rmse,
        "holdout_relative_rmse": holdout_rmse / max(holdout_scale, np.finfo(float).tiny),
        "exact_delta_audit_only": exact_delta,
        "estimated_delta": estimated_delta,
        "absolute_delta_error": abs(estimated_delta - exact_delta),
        "relative_delta_error": abs(estimated_delta - exact_delta) / abs(exact_delta),
        "sign_correct_audit": np.sign(estimated_delta) == np.sign(exact_delta),
        "runtime_seconds": perf_counter() - started,
    }
    del state_a, state_b, training_targets, holdout_targets, cores
    gc.collect()
    return result


def main() -> None:
    payload = {
        "stage": "sparse_point_query_contrast_completion",
        "complete": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "protocol_sha256": sha256(PROTOCOL),
        "runner_sha256": sha256(Path(__file__)),
        "ranks": RANKS,
        "query_multiplier": QUERY_MULTIPLIER,
        "holdout_count": HOLDOUT_COUNT,
        "sweeps": SWEEPS,
        "relative_ridge": RELATIVE_RIDGE,
        "rows": [],
    }
    for case in CASES:
        for ordering in ORDERINGS:
            for rank in RANKS:
                print(f"[sparse contrast] {case}/{ordering}/R{rank}", flush=True)
                row = run_row(case, ordering, rank)
                payload["rows"].append(row)
                atomic_json(OUTPUT, payload)
                print(
                    f"  train_rel={row['fit_history'][-1]['training_relative_rmse']:.4g} "
                    f"holdout_rel={row['holdout_relative_rmse']:.4g} "
                    f"delta={row['estimated_delta']:+.8g}",
                    flush=True,
                )
    payload["complete"] = True
    atomic_json(OUTPUT, payload)


if __name__ == "__main__":
    main()
