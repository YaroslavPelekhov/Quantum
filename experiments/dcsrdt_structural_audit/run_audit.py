"""Execute the frozen DCS-RDT structural-rank falsification audit."""

from __future__ import annotations

import copy
import gc
import json
import sys
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULTS = REPO / "results" / "dcsrdt_structural_audit"
sys.path[:0] = [
    str(HERE),
    str(REPO / "experiments" / "rankcert_mps"),
    str(REPO / "experiments" / "decision_conditioned_srdt"),
    str(REPO / "experiments" / "contrastive_tensor_simulation"),
]

import rankcert_inputs
from contrastive_core import atomic_json, sha256
from dcsrdt_core import bks_effect_diagonal
from structural_core import (
    RANK_TOLERANCE,
    deterministic_seed,
    frontier_profile,
    haar_pair,
    low_rank_spectrum,
)


CASES = ("ibm32", "aves-sparrow-social", "chesapeake", "football")
ORDERINGS = ("sorted", "spectral")
METHOD_A = "published_lr"
METHOD_B = "prior_matched_random"


def specs_by_key() -> dict:
    return {
        (row["case"], row["ordering"], row["method"]): row
        for row in rankcert_inputs.load_specs()
    }


def event_indices(scorer: dict) -> np.ndarray:
    return np.flatnonzero(bks_effect_diagonal(scorer)).astype(np.int64)


def audit_pair(
    state_a: np.ndarray,
    state_b: np.ndarray,
    events: np.ndarray,
    qubits: int,
) -> list[dict]:
    rows = []
    for profile in frontier_profile(events, qubits):
        spectrum = low_rank_spectrum(
            state_a, state_b, events, profile["cut"]
        )
        if spectrum["numerical_rank"] > profile["structural_bound"]:
            raise AssertionError("structural rank bound violated")
        rows.append({**profile, **spectrum})
    return rows


def controlled_events(
    scorer: dict, qubits: int, case: str, ordering: str
) -> list[tuple[str, np.ndarray]]:
    controls = [("exact_bks", event_indices(scorer))]
    near = copy.deepcopy(scorer)
    near["bks"] = int(near["bks"]) - 1
    controls.append(("near_bks", event_indices(near)))
    feasible = copy.deepcopy(scorer)
    feasible["bks"] = -32768
    controls.append(("feasible", event_indices(feasible)))
    rng = np.random.default_rng(deterministic_seed(case, ordering, "events"))
    dimension = 1 << qubits
    for support in (10, 100, 1000):
        sampled = np.sort(rng.choice(dimension, size=support, replace=False))
        controls.append((f"random_{support}", sampled.astype(np.int64)))
    return controls


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    output = RESULTS / "audit.json"
    indexed = specs_by_key()
    payload = {
        "complete": False,
        "protocol_sha256": sha256(HERE / "PROTOCOL.md"),
        "rank_tolerance": RANK_TOLERANCE,
        "rows": [],
        "event_controls": [],
    }
    for case in CASES:
        for ordering in ORDERINGS:
            spec_a = indexed[(case, ordering, METHOD_A)]
            spec_b = indexed[(case, ordering, METHOD_B)]
            qubits = int(spec_a["qubits"])
            state_a = np.asarray(
                np.load(spec_a["reference_file"], mmap_mode="r", allow_pickle=False)
            )
            state_b = np.asarray(
                np.load(spec_b["reference_file"], mmap_mode="r", allow_pickle=False)
            )
            events = event_indices(spec_a["scorer"])
            seed = deterministic_seed(case, ordering, "haar")
            haar_a, haar_b = haar_pair(state_a.size, seed)
            qaoa_rows = audit_pair(state_a, state_b, events, qubits)
            haar_rows = audit_pair(haar_a, haar_b, events, qubits)
            cuts = []
            for qaoa, haar in zip(qaoa_rows, haar_rows, strict=True):
                if qaoa["cut"] != haar["cut"]:
                    raise AssertionError("cut mismatch")
                evidence = bool(
                    qaoa["numerical_rank"] <= 0.75 * haar["numerical_rank"]
                    and haar["numerical_rank"] < qaoa["left_dimension"]
                )
                cuts.append({
                    **qaoa,
                    "haar_numerical_rank": haar["numerical_rank"],
                    "haar_spectral_norm": haar["spectral_norm"],
                    "qaoa_to_haar_rank_ratio": (
                        qaoa["numerical_rank"] / haar["numerical_rank"]
                        if haar["numerical_rank"] else None
                    ),
                    "additional_structure_evidence": evidence,
                })
            row = {
                "case": case,
                "ordering": ordering,
                "qubits": qubits,
                "event_support": int(events.size),
                "haar_seed": seed,
                "cuts": cuts,
                "evidence_cuts": [
                    item["cut"] for item in cuts
                    if item["additional_structure_evidence"]
                ],
            }
            payload["rows"].append(row)
            print(json.dumps({
                "case": case,
                "ordering": ordering,
                "event_support": int(events.size),
                "qaoa_ranks": [item["numerical_rank"] for item in cuts],
                "haar_ranks": [item["haar_numerical_rank"] for item in cuts],
                "evidence_cuts": row["evidence_cuts"],
            }), flush=True)
            if case == "ibm32":
                for name, controlled in controlled_events(
                    spec_a["scorer"], qubits, case, ordering
                ):
                    profile = frontier_profile(controlled, qubits)[8]
                    qaoa = low_rank_spectrum(
                        state_a, state_b, controlled, cut=9
                    )
                    haar = low_rank_spectrum(
                        haar_a, haar_b, controlled, cut=9
                    )
                    payload["event_controls"].append({
                        "case": case,
                        "ordering": ordering,
                        "event": name,
                        "event_support": int(controlled.size),
                        **profile,
                        "qaoa_rank": qaoa["numerical_rank"],
                        "haar_rank": haar["numerical_rank"],
                        "qaoa_trace_norm": qaoa["trace_norm"],
                        "haar_trace_norm": haar["trace_norm"],
                    })
            atomic_json(output, payload)
            del haar_a, haar_b
            gc.collect()
    payload["summary"] = {
        "rows": len(payload["rows"]),
        "cuts": sum(len(row["cuts"]) for row in payload["rows"]),
        "bound_violations": sum(
            item["numerical_rank"] > item["structural_bound"]
            for row in payload["rows"] for item in row["cuts"]
        ),
        "additional_structure_evidence_cuts": sum(
            len(row["evidence_cuts"]) for row in payload["rows"]
        ),
    }
    payload["complete"] = True
    atomic_json(output, payload)
    print(json.dumps(payload["summary"], indent=2))


if __name__ == "__main__":
    main()

