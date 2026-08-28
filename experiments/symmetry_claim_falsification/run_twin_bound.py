"""Evaluate the frozen amplitude-blind twin-quotient structural bound."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULTS = REPO / "results" / "symmetry_claim_falsification"
sys.path[:0] = [
    str(HERE),
    str(REPO / "experiments" / "symmetry_quotient_decision_rank"),
    str(REPO / "experiments" / "dcsrdt_structural_audit"),
    str(REPO / "experiments" / "contrastive_tensor_simulation"),
]

from contrastive_core import atomic_json, sha256
from quotient_core import TwinQuotientState, compile_twin_quotient
from run_symmetry_rank import energy_and_event, order_for, triangle_graph
from structural_core import deterministic_seed, low_rank_spectrum
from twin_structural import twin_frontier_profile


SEEDS = 5


def random_state(architecture, seed: int) -> TwinQuotientState:
    rng = np.random.default_rng(seed)
    coefficients = rng.normal(size=architecture.orbit_count) + 1j * rng.normal(
        size=architecture.orbit_count
    )
    coefficients /= np.linalg.norm(coefficients)
    return TwinQuotientState(architecture, coefficients)


def archived_rows() -> list[dict]:
    rows = []
    for stage in ("development", "transfer"):
        payload = json.loads(
            (REPO / "results" / "symmetry_quotient_decision_rank"
             / f"{stage}.json").read_text(encoding="utf-8")
        )
        rows.extend(payload["rows"])
    return rows


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    output = RESULTS / "twin_bound.json"
    payload = {
        "complete": False,
        "protocol_sha256": sha256(HERE / "BOUND_PROTOCOL.md"),
        "seeds_per_control": SEEDS,
        "rows": [],
    }
    for archived in archived_rows():
        name = archived["case"]
        ordering = archived["ordering"]
        qubits = archived["qubits"]
        graph = triangle_graph(qubits // 3, "ring" in name)
        order = order_for(graph, ordering)
        _, events, _ = energy_and_event(graph, order)
        architecture = compile_twin_quotient(graph, order, penalty=2.0)
        structure = twin_frontier_profile(events, qubits, architecture.groups)
        qaoa = archived["pair_rank_profiles"]["0-1"]
        twin_profiles = []
        for repetition in range(SEEDS):
            base = deterministic_seed(
                name, ordering, "twin_bound", str(repetition)
            )
            state_a = random_state(architecture, base)
            state_b = random_state(architecture, base + 1)
            dense_a, dense_b = state_a.dense(), state_b.dense()
            twin_profiles.append([
                low_rank_spectrum(dense_a, dense_b, events, cut)["numerical_rank"]
                for cut in range(1, qubits)
            ])
        bounds = [row["twin_structural_bound"] for row in structure]
        eligible = [
            index for index, row in enumerate(structure)
            if row["twin_structural_bound"] < row["dense_left_dimension"]
        ]
        row = {
            "case": name,
            "ordering": ordering,
            "qubits": qubits,
            "structure": structure,
            "qaoa_ranks": qaoa,
            "twin_haar_ranks": twin_profiles,
            "qaoa_bound_violations": sum(
                actual > bound for actual, bound in zip(qaoa, bounds)
            ),
            "generic_bound_saturation": all(
                profile[index] == bounds[index]
                for profile in twin_profiles for index in eligible
            ),
            "qaoa_residual_deficit_cuts": [
                index + 1 for index in eligible if qaoa[index] < bounds[index]
            ],
            "seed_stable": len({tuple(profile) for profile in twin_profiles}) == 1,
        }
        payload["rows"].append(row)
        atomic_json(output, payload)
        print(json.dumps({
            "case": name,
            "ordering": ordering,
            "bounds": bounds,
            "qaoa": qaoa,
            "twin_haar": twin_profiles[0],
            "residual": row["qaoa_residual_deficit_cuts"],
        }), flush=True)
    payload["bound_violations"] = sum(
        row["qaoa_bound_violations"] for row in payload["rows"]
    )
    payload["generic_saturation_all_rows"] = all(
        row["generic_bound_saturation"] for row in payload["rows"]
    )
    payload["seed_stable"] = all(row["seed_stable"] for row in payload["rows"])
    payload["ansatz_rank_residual_exists"] = any(
        row["qaoa_residual_deficit_cuts"] for row in payload["rows"]
    )
    payload["complete"] = True
    atomic_json(output, payload)
    print(json.dumps({key: payload[key] for key in (
        "bound_violations", "generic_saturation_all_rows", "seed_stable",
        "ansatz_rank_residual_exists"
    )}, indent=2))


if __name__ == "__main__":
    main()
