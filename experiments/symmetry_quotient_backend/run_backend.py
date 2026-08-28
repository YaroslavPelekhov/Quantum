"""Validate the twin-orbit quotient backend on the real 24-qubit cohort."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import networkx as nx
import numpy as np


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULTS = REPO / "results" / "symmetry_quotient_backend"
sys.path[:0] = [
    str(REPO / "experiments" / "rankcert_mps"),
    str(REPO / "experiments" / "sparse_mps_dcsrdt"),
    str(REPO / "experiments" / "dcsrdt_structural_audit"),
    str(REPO / "experiments" / "symmetry_quotient_decision_rank"),
    str(REPO / "experiments" / "contrastive_tensor_simulation"),
]

import rankcert_inputs
from contrastive_core import atomic_json, sha256
from quotient_core import (
    compile_twin_quotient,
    evolve_twin_quotient,
    quotient_decision_spectrum,
)
from sparse_mps_core import enumerate_bks_support


CASE = "aves-sparrow-social"
CUTS = (5, 9, 12)
DEPTH = 15


def graph_from_scorer(scorer: dict) -> nx.Graph:
    graph = nx.Graph()
    graph.add_nodes_from(range(len(scorer["weights"])))
    for mask, pattern in scorer["forbidden"]:
        bits = [q for q in range(len(scorer["weights"])) if (mask >> q) & 1]
        if mask != pattern or len(bits) != 2:
            raise ValueError("expected pairwise MIS exclusions")
        graph.add_edge(*bits)
    return graph


def schedule(genome):
    delta_beta, delta_gamma, beta_power, gamma_power = map(float, genome)
    layer = np.arange(1, DEPTH + 1, dtype=float)
    betas = delta_beta * ((DEPTH - layer + 1) / DEPTH) ** beta_power
    gammas = delta_gamma * (layer / DEPTH) ** gamma_power
    return gammas, -betas  # archived RX(-2 beta) convention


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    output = RESULTS / "backend.json"
    specs = {
        (row["case"], row["ordering"], row["method"]): row
        for row in rankcert_inputs.load_specs()
    }
    structural = json.loads(
        (REPO / "results" / "dcsrdt_structural_audit" / "audit.json")
        .read_text(encoding="utf-8")
    )
    exact_ranks = {
        (row["ordering"], cut["cut"]): cut["numerical_rank"]
        for row in structural["rows"] if row["case"] == CASE
        for cut in row["cuts"]
    }
    payload = {
        "complete": False,
        "protocol_sha256": sha256(HERE / "PROTOCOL.md"),
        "primary_path_loads_dense_state": False,
        "primary_path_constructs_dense_operator": False,
        "rows": [],
    }
    for ordering in ("sorted", "spectral"):
        spec_a = specs[(CASE, ordering, "published_lr")]
        spec_b = specs[(CASE, ordering, "prior_matched_random")]
        graph = graph_from_scorer(spec_a["scorer"])
        start = time.perf_counter()
        architecture = compile_twin_quotient(
            graph, list(range(24)), penalty=1.5, normalized_ising=True
        )
        compile_seconds = time.perf_counter() - start
        start = time.perf_counter()
        state_a = evolve_twin_quotient(
            architecture, *schedule(spec_a["schedule_parameters"])
        )
        state_b = evolve_twin_quotient(
            architecture, *schedule(spec_b["schedule_parameters"])
        )
        evolve_seconds = time.perf_counter() - start
        events = np.asarray(enumerate_bks_support(spec_a["scorer"]), dtype=np.int64)
        exact_gap = float(
            spec_b["exact_metrics"]["bks_rate"]
            - spec_a["exact_metrics"]["bks_rate"]
        )
        cut_rows = []
        start = time.perf_counter()
        for cut in CUTS:
            spectrum = quotient_decision_spectrum(state_a, state_b, events, cut)
            cut_rows.append({
                "cut": cut,
                **spectrum,
                "expected_rank": exact_ranks[(ordering, cut)],
                "rank_matches": spectrum["numerical_rank"]
                == exact_ranks[(ordering, cut)],
                "exact_gap": exact_gap,
                "trace_error": abs(spectrum["trace"] - exact_gap),
            })
        decision_seconds = time.perf_counter() - start

        # Validation-only path begins here; it is not used to build either
        # quotient state or any decision core.
        dense_a = np.load(spec_a["reference_file"], mmap_mode="r", allow_pickle=False)
        dense_b = np.load(spec_b["reference_file"], mmap_mode="r", allow_pickle=False)
        rng = np.random.default_rng(20260828 + (ordering == "spectral"))
        sample = rng.choice(dense_a.size, size=20_000, replace=False)
        probability_errors = []
        amplitude_errors = []
        for quotient, dense in ((state_a, dense_a), (state_b, dense_b)):
            q_values = quotient.amplitudes(sample)
            d_values = np.asarray(dense[sample])
            phase = np.vdot(q_values, d_values)
            phase /= abs(phase)
            amplitude_errors.append(float(np.max(np.abs(phase * q_values - d_values))))
            probability_errors.append(float(np.max(
                np.abs(np.abs(q_values) ** 2 - np.abs(d_values) ** 2)
            )))
        row = {
            "case": CASE,
            "ordering": ordering,
            "qubits": 24,
            "twin_groups": [list(group) for group in architecture.groups],
            "quotient_dimension": architecture.orbit_count,
            "full_dimension": 1 << 24,
            "dimension_compression": (1 << 24) / architecture.orbit_count,
            "coefficient_bytes_per_state": int(state_a.coefficients.nbytes),
            "dense_bytes_per_state": int(dense_a.nbytes),
            "compile_seconds": compile_seconds,
            "two_state_evolve_seconds": evolve_seconds,
            "three_cut_decision_seconds": decision_seconds,
            "state_norm_errors": [
                abs(float(np.linalg.norm(state.coefficients)) - 1.0)
                for state in (state_a, state_b)
            ],
            "sample_amplitude_errors": amplitude_errors,
            "sample_probability_errors": probability_errors,
            "cuts": cut_rows,
        }
        row["pass"] = bool(
            row["quotient_dimension"] <= 0.1 * row["full_dimension"]
            and max(probability_errors) < 1e-12
            and max(row["state_norm_errors"]) < 1e-10
            and all(cut["rank_matches"] for cut in cut_rows)
            and max(cut["trace_error"] for cut in cut_rows) <= 1e-10
        )
        payload["rows"].append(row)
        atomic_json(output, payload)
        print(json.dumps({key: row[key] for key in (
            "ordering", "quotient_dimension", "dimension_compression",
            "compile_seconds", "two_state_evolve_seconds",
            "three_cut_decision_seconds", "sample_probability_errors", "pass"
        )}, indent=2), flush=True)
    payload["passed_rows"] = sum(row["pass"] for row in payload["rows"])
    payload["success"] = payload["passed_rows"] == len(payload["rows"])
    payload["complete"] = True
    atomic_json(output, payload)
    print(json.dumps({"passed_rows": payload["passed_rows"],
        "success": payload["success"]}, indent=2))


if __name__ == "__main__":
    main()

