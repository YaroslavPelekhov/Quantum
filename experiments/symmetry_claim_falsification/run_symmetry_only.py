"""Aggressively test whether the retained rank signature is symmetry-only."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULTS = REPO / "results" / "symmetry_claim_falsification"
sys.path[:0] = [
    str(REPO / "experiments" / "symmetry_quotient_decision_rank"),
    str(REPO / "experiments" / "dcsrdt_structural_audit"),
    str(REPO / "experiments" / "contrastive_tensor_simulation"),
]

from contrastive_core import atomic_json, sha256
from quotient_core import (
    QuotientState,
    TwinQuotientState,
    compile_quotient,
    compile_twin_quotient,
    evolve_quotient,
    triangle_symmetry_generators,
)
from run_symmetry_rank import (
    GENOMES,
    energy_and_event,
    order_for,
    schedule,
    triangle_graph,
)
from structural_core import deterministic_seed, low_rank_spectrum


SEEDS = 5


def random_coefficients(size: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    values = rng.normal(size=size) + 1j * rng.normal(size=size)
    return values / np.linalg.norm(values)


def ranks_at_cuts(state_a, state_b, events: np.ndarray, cuts: list[int]) -> list[int]:
    dense_a = state_a.dense()
    dense_b = state_b.dense()
    return [
        low_rank_spectrum(dense_a, dense_b, events, cut)["numerical_rank"]
        for cut in cuts
    ]


def archived_rows() -> list[dict]:
    rows = []
    for stage in ("development", "transfer"):
        payload = json.loads(
            (REPO / "results" / "symmetry_quotient_decision_rank"
             / f"{stage}.json").read_text(encoding="utf-8")
        )
        rows.extend(payload["rows"])
    return rows


def audit_row(archived: dict) -> dict:
    name = archived["case"]
    triangles = archived["qubits"] // 3
    ring = "ring" in name
    ordering = archived["ordering"]
    graph = triangle_graph(triangles, ring)
    order = order_for(graph, ordering)
    energy, events, _ = energy_and_event(graph, order)
    generators = triangle_symmetry_generators(triangles, ring, order)
    full_arch = compile_quotient(energy, generators)
    twin_arch = compile_twin_quotient(graph, order, penalty=2.0)
    cuts = list(archived["deficit_cuts"])
    archived_ranks = [
        archived["pair_rank_profiles"]["0-1"][cut - 1] for cut in cuts
    ]

    qaoa = []
    for genome in GENOMES[:2]:
        gammas, betas = schedule(genome)
        qaoa.append(evolve_quotient(full_arch, gammas, betas))
    replay_ranks = ranks_at_cuts(qaoa[0], qaoa[1], events, cuts)

    auto_haar = []
    orbit_phase = []
    twin_haar = []
    for repetition in range(SEEDS):
        seed_base = deterministic_seed(
            name, ordering, "symmetry_falsification", str(repetition)
        )
        full_a = QuotientState(
            full_arch, random_coefficients(full_arch.orbit_count, seed_base)
        )
        full_b = QuotientState(
            full_arch, random_coefficients(full_arch.orbit_count, seed_base + 1)
        )
        auto_haar.append(ranks_at_cuts(full_a, full_b, events, cuts))

        phase_a = np.exp(
            1j * np.random.default_rng(seed_base + 2).uniform(
                -np.pi, np.pi, full_arch.orbit_count
            )
        )
        phase_b = np.exp(
            1j * np.random.default_rng(seed_base + 3).uniform(
                -np.pi, np.pi, full_arch.orbit_count
            )
        )
        phased_a = QuotientState(full_arch, np.abs(qaoa[0].coefficients) * phase_a)
        phased_b = QuotientState(full_arch, np.abs(qaoa[1].coefficients) * phase_b)
        orbit_phase.append(ranks_at_cuts(phased_a, phased_b, events, cuts))

        twin_a = TwinQuotientState(
            twin_arch, random_coefficients(twin_arch.orbit_count, seed_base + 4)
        )
        twin_b = TwinQuotientState(
            twin_arch, random_coefficients(twin_arch.orbit_count, seed_base + 5)
        )
        twin_haar.append(ranks_at_cuts(twin_a, twin_b, events, cuts))

    qaoa_replayed = replay_ranks == archived_ranks
    auto_matches = all(profile == archived_ranks for profile in auto_haar)
    phase_matches = all(profile == archived_ranks for profile in orbit_phase)
    twin_exceeds = any(
        any(actual > expected for actual, expected in zip(profile, archived_ranks))
        for profile in twin_haar
    )
    seed_stable = (
        len({tuple(profile) for profile in auto_haar}) == 1
        and len({tuple(profile) for profile in orbit_phase}) == 1
        and len({tuple(profile) for profile in twin_haar}) == 1
    )
    return {
        "case": name,
        "ordering": ordering,
        "qubits": archived["qubits"],
        "cuts": cuts,
        "event_support": int(events.size),
        "full_automorphism_orbits": full_arch.orbit_count,
        "twin_orbits": twin_arch.orbit_count,
        "archived_qaoa_ranks": archived_ranks,
        "replayed_qaoa_ranks": replay_ranks,
        "full_automorphism_haar_ranks": auto_haar,
        "orbit_phase_ranks": orbit_phase,
        "twin_only_haar_ranks": twin_haar,
        "qaoa_replayed": qaoa_replayed,
        "full_automorphism_matches_qaoa": auto_matches,
        "orbit_phase_matches_qaoa": phase_matches,
        "twin_only_exceeds_qaoa": twin_exceeds,
        "seed_stable": seed_stable,
    }


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    output = RESULTS / "symmetry_only.json"
    payload = {
        "complete": False,
        "protocol_sha256": sha256(HERE / "PROTOCOL.md"),
        "seeds_per_control": SEEDS,
        "rows": [],
    }
    for archived in archived_rows():
        row = audit_row(archived)
        payload["rows"].append(row)
        atomic_json(output, payload)
        print(json.dumps({
            "case": row["case"],
            "ordering": row["ordering"],
            "cuts": row["cuts"],
            "qaoa": row["archived_qaoa_ranks"],
            "auto_haar": row["full_automorphism_haar_ranks"][0],
            "orbit_phase": row["orbit_phase_ranks"][0],
            "twin_haar": row["twin_only_haar_ranks"][0],
        }), flush=True)
    payload["qaoa_replay_success"] = all(
        row["qaoa_replayed"] for row in payload["rows"]
    )
    payload["seed_stable"] = all(row["seed_stable"] for row in payload["rows"])
    payload["ansatz_specific_claim_killed"] = all(
        row["full_automorphism_matches_qaoa"]
        and row["orbit_phase_matches_qaoa"]
        for row in payload["rows"]
    )
    payload["narrowed_to_full_graph_symmetry"] = bool(
        payload["ansatz_specific_claim_killed"]
        and any(row["twin_only_exceeds_qaoa"] for row in payload["rows"])
    )
    payload["complete"] = True
    atomic_json(output, payload)
    print(json.dumps({key: payload[key] for key in (
        "qaoa_replay_success", "seed_stable",
        "ansatz_specific_claim_killed", "narrowed_to_full_graph_symmetry"
    )}, indent=2))


if __name__ == "__main__":
    main()
