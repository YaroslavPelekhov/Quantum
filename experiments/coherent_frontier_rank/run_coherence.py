"""Run probability-, phase-, and schedule-pair controls for rank deficits."""

from __future__ import annotations

import gc
import json
import sys
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PROJECT = REPO / "experiments" / "evoq_mis_full_qoblib"
RESULTS = REPO / "results" / "coherent_frontier_rank"
sys.path[:0] = [
    str(REPO / "experiments" / "rankcert_mps"),
    str(REPO / "experiments" / "decision_conditioned_srdt"),
    str(REPO / "experiments" / "dcsrdt_structural_audit"),
    str(REPO / "experiments" / "contrastive_tensor_simulation"),
]

import rankcert_inputs
from contrastive_core import atomic_json, sha256
from dcsrdt_core import bks_effect_diagonal
from structural_core import (
    RANK_TOLERANCE,
    deterministic_seed,
    frontier_profile,
    low_rank_spectrum,
)


CASE = "aves-sparrow-social"
ORDERINGS = ("sorted", "spectral")
METHODS = ("published_lr", "prior_matched_random", "prior_evolutionary")


def references() -> dict[tuple[str, str], Path]:
    manifest = json.loads(
        (PROJECT / "results" / "independent_ladder" / "export_manifest.json")
        .read_text(encoding="utf-8")
    )
    result = {}
    for row in manifest["rows"]:
        if row["case"] == CASE and row["method"] in METHODS:
            result[(row["method"], row["ordering"])] = (
                rankcert_inputs.resolve_project_file(
                    row["reference_file"], row["reference_sha256"]
                )
            )
    if len(result) != len(METHODS) * len(ORDERINGS):
        raise AssertionError("missing frozen references")
    return result


def audit_pair(a: np.ndarray, b: np.ndarray, events: np.ndarray) -> list[int]:
    qubits = int(round(np.log2(a.size)))
    return [
        low_rank_spectrum(a, b, events, cut)["numerical_rank"]
        for cut in range(1, qubits)
    ]


def random_phase(size: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return np.exp(1j * rng.uniform(-np.pi, np.pi, size=size))


def local_product_phase(qubits: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    phase = np.ones(1, dtype=np.complex128)
    for theta in rng.uniform(-np.pi, np.pi, size=qubits):
        phase = np.kron(phase, np.asarray([1.0, np.exp(1j * theta)]))
    return phase


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    output = RESULTS / "coherence.json"
    refs = references()
    specs = {
        (row["case"], row["ordering"], row["method"]): row
        for row in rankcert_inputs.load_specs()
    }
    payload = {
        "complete": False,
        "protocol_sha256": sha256(HERE / "PROTOCOL.md"),
        "rank_tolerance": RANK_TOLERANCE,
        "rows": [],
    }
    for ordering in ORDERINGS:
        states = {
            method: np.asarray(
                np.load(refs[(method, ordering)], mmap_mode="r", allow_pickle=False)
            )
            for method in METHODS
        }
        primary_a = states["published_lr"]
        primary_b = states["prior_matched_random"]
        qubits = int(round(np.log2(primary_a.size)))
        scorer = specs[(CASE, ordering, "published_lr")]["scorer"]
        events = np.flatnonzero(bks_effect_diagonal(scorer)).astype(np.int64)
        profile = frontier_profile(events, qubits)
        transformations: dict[str, list[int]] = {}
        transformations["original"] = audit_pair(primary_a, primary_b, events)

        magnitude_a = np.asarray(np.abs(primary_a), dtype=np.complex128)
        magnitude_b = np.asarray(np.abs(primary_b), dtype=np.complex128)
        transformations["magnitude_only"] = audit_pair(
            magnitude_a, magnitude_b, events
        )
        del magnitude_a, magnitude_b
        gc.collect()

        phase_a = random_phase(
            primary_a.size,
            deterministic_seed(CASE, ordering, "independent_phase_a"),
        )
        phase_b = random_phase(
            primary_b.size,
            deterministic_seed(CASE, ordering, "independent_phase_b"),
        )
        transformations["independent_phase"] = audit_pair(
            np.abs(primary_a) * phase_a,
            np.abs(primary_b) * phase_b,
            events,
        )
        del phase_a, phase_b
        gc.collect()

        common = random_phase(
            primary_a.size,
            deterministic_seed(CASE, ordering, "common_diagonal_phase"),
        )
        transformations["common_diagonal_phase"] = audit_pair(
            primary_a * common, primary_b * common, events
        )
        del common
        gc.collect()

        local = local_product_phase(
            qubits, deterministic_seed(CASE, ordering, "local_product_phase")
        )
        transformations["local_product_phase"] = audit_pair(
            primary_a * local, primary_b * local, events
        )
        del local
        gc.collect()

        pair_ranks = {}
        for method_a, method_b in (
            ("published_lr", "prior_matched_random"),
            ("published_lr", "prior_evolutionary"),
            ("prior_matched_random", "prior_evolutionary"),
        ):
            name = f"{method_a}__vs__{method_b}"
            pair_ranks[name] = audit_pair(
                states[method_a], states[method_b], events
            )

        cuts = []
        for index, structure in enumerate(profile):
            cap = structure["structural_bound"]
            transformed = {
                name: ranks[index] for name, ranks in transformations.items()
            }
            pairs = {name: ranks[index] for name, ranks in pair_ranks.items()}
            cuts.append({
                **structure,
                "transformation_ranks": transformed,
                "pair_ranks": pairs,
                "original_deficit": 1.0 - transformed["original"] / cap,
            })
        payload["rows"].append({
            "case": CASE,
            "ordering": ordering,
            "qubits": qubits,
            "event_support": int(events.size),
            "cuts": cuts,
        })
        atomic_json(output, payload)
        print(json.dumps({
            "ordering": ordering,
            "original": transformations["original"],
            "magnitude_only": transformations["magnitude_only"],
            "independent_phase": transformations["independent_phase"],
            "common_diagonal_phase": transformations["common_diagonal_phase"],
            "local_product_phase": transformations["local_product_phase"],
            "pair_ranks": pair_ranks,
        }), flush=True)

    eligible = [
        cut for row in payload["rows"] for cut in row["cuts"]
        if cut["structural_bound"] < cut["left_dimension"]
    ]
    independent_saturation = sum(
        cut["transformation_ranks"]["independent_phase"]
        == cut["structural_bound"]
        for cut in eligible
    ) / len(eligible)
    local_invariance = all(
        cut["transformation_ranks"]["local_product_phase"]
        == cut["transformation_ranks"]["original"]
        for row in payload["rows"] for cut in row["cuts"]
    )
    pair_names = next(iter(payload["rows"]))["cuts"][0]["pair_ranks"].keys()
    qualifying_by_pair = {
        name: {
            (row["ordering"], cut["cut"])
            for row in payload["rows"] for cut in row["cuts"]
            if cut["pair_ranks"][name] <= 0.75 * cut["structural_bound"]
            and cut["structural_bound"] < cut["left_dimension"]
        }
        for name in pair_names
    }
    common_qualifying = set.intersection(*qualifying_by_pair.values())
    pairs_with_five = sum(len(cuts) >= 5 for cuts in qualifying_by_pair.values())
    payload["summary"] = {
        "eligible_cuts": len(eligible),
        "independent_phase_saturation_fraction": independent_saturation,
        "local_product_rank_invariance": local_invariance,
        "qualifying_cuts_by_pair": {
            name: sorted([list(item) for item in cuts])
            for name, cuts in qualifying_by_pair.items()
        },
        "common_qualifying_cuts": sorted([list(item) for item in common_qualifying]),
        "pairs_with_at_least_five_qualifying_cuts": pairs_with_five,
    }
    payload["success"] = bool(
        local_invariance
        and independent_saturation >= 0.9
        and pairs_with_five >= 2
        and len(common_qualifying) >= 5
    )
    payload["complete"] = True
    atomic_json(output, payload)
    print(json.dumps({**payload["summary"], "success": payload["success"]}, indent=2))


if __name__ == "__main__":
    main()

