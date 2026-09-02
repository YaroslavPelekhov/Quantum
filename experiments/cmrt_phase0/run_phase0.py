"""Run the frozen offline falsification of Conformal Metamorphic Rank Transfer."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import statistics
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable

import networkx as nx
import numpy as np
from scipy.stats import spearmanr

from experiments.cmrt_phase0.cmrt_core import (
    finite_sample_quantile,
    selective_metrics,
    sign_or_abstain,
    wilson_difference_interval,
)
from experiments.cmrt_phase0.synthetic_qaoa import (
    event_probability,
    hardware_surrogate_distribution,
    qaoa_mis_statevector,
)


REPO = Path(__file__).resolve().parents[2]
PROTOCOL_PATH = Path(__file__).with_name("protocol.json")
DEFAULT_OUTPUT = REPO / "results" / "cmrt_phase0" / "phase0_results.json"
PENALTY = 2.0


def _stable_int(*parts: object) -> int:
    digest = hashlib.sha256(":".join(map(str, parts)).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def _canonical_edges(edges: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return tuple(sorted((min(int(u), int(v)), max(int(u), int(v))) for u, v in edges))


def _generate_graphs(protocol: dict[str, Any]) -> list[dict[str, Any]]:
    config = protocol["graphs"]
    master_seed = int(protocol["seed"])
    generated: list[dict[str, Any]] = []
    by_size: dict[int, list[nx.Graph]] = {}
    for n in map(int, config["sizes"]):
        accepted: list[nx.Graph] = []
        attempt = 0
        while len(accepted) < int(config["per_size"]):
            if attempt >= 20_000:
                raise RuntimeError(f"could not generate enough non-isomorphic n={n} graphs")
            rng = np.random.default_rng(master_seed + 10_000 * n + attempt)
            permutation = list(map(int, rng.permutation(n)))
            edges = {
                (min(permutation[index], permutation[index + 1]), max(permutation[index], permutation[index + 1]))
                for index in range(n - 1)
            }
            degrees = [0] * n
            for u, v in edges:
                degrees[u] += 1
                degrees[v] += 1
            candidates = [(u, v) for u in range(n) for v in range(u + 1, n) if (u, v) not in edges]
            rng.shuffle(candidates)
            target_chords = 1 + attempt % max(2, n // 3)
            for u, v in candidates:
                if target_chords == 0:
                    break
                if degrees[u] >= int(config["maximum_degree"]) or degrees[v] >= int(config["maximum_degree"]):
                    continue
                edges.add((u, v))
                degrees[u] += 1
                degrees[v] += 1
                target_chords -= 1
            graph = nx.Graph()
            graph.add_nodes_from(range(n))
            graph.add_edges_from(sorted(edges))
            attempt += 1
            if max(dict(graph.degree()).values()) > int(config["maximum_degree"]):
                continue
            if any(nx.is_isomorphic(graph, previous) for previous in accepted):
                continue
            accepted.append(graph)
        by_size[n] = accepted

    for n in sorted(by_size):
        for local_index, graph in enumerate(by_size[n]):
            edges = _canonical_edges(graph.edges())
            edge_digest = hashlib.sha256(json.dumps(edges).encode("utf-8")).hexdigest()[:12]
            graph_id = f"n{n:02d}_g{local_index:02d}_{edge_digest}"
            generated.append(
                {
                    "graph_id": graph_id,
                    "n_qubits": n,
                    "edges": [list(edge) for edge in edges],
                    "edge_count": len(edges),
                    "maximum_degree": max(dict(graph.degree()).values()),
                    "wl_hash": nx.weisfeiler_lehman_graph_hash(graph),
                }
            )

    expected = int(config["count"])
    if len(generated) != expected:
        raise AssertionError(f"generated {len(generated)} graphs, expected {expected}")
    ranked = sorted(
        generated,
        key=lambda row: hashlib.sha256(
            (config["split_hash_prefix"] + row["graph_id"]).encode("utf-8")
        ).hexdigest(),
    )
    calibration_ids = {
        row["graph_id"] for row in ranked[: int(config["calibration_count"])]
    }
    for row in generated:
        row["split"] = "calibration" if row["graph_id"] in calibration_ids else "test"
    counts = {split: sum(row["split"] == split for row in generated) for split in ("calibration", "test")}
    if counts != {
        "calibration": int(config["calibration_count"]),
        "test": int(config["test_count"]),
    }:
        raise AssertionError(f"invalid graph split: {counts}")
    return generated


def _degree_bfs_order(n: int, edges: tuple[tuple[int, int], ...]) -> tuple[int, ...]:
    graph = nx.Graph()
    graph.add_nodes_from(range(n))
    graph.add_edges_from(edges)
    start = min(graph.nodes(), key=lambda node: (-graph.degree[node], node))
    seen = {start}
    queue = [start]
    order: list[int] = []
    while queue:
        node = queue.pop(0)
        order.append(node)
        neighbours = sorted(graph.neighbors(node), key=lambda item: (-graph.degree[item], item))
        for neighbour in neighbours:
            if neighbour not in seen:
                seen.add(neighbour)
                queue.append(neighbour)
    order.extend(node for node in range(n) if node not in seen)
    return tuple(order)


def _event_mask_and_alpha(n: int, edges: tuple[tuple[int, int], ...]) -> tuple[np.ndarray, int, int]:
    dimension = 1 << n
    mask = np.zeros(dimension, dtype=bool)
    feasible: list[tuple[int, int]] = []
    alpha = 0
    for index in range(dimension):
        if any(((index >> u) & 1) and ((index >> v) & 1) for u, v in edges):
            continue
        size = int(index.bit_count())
        feasible.append((index, size))
        alpha = max(alpha, size)
    threshold = max(0, alpha - 1)
    for index, size in feasible:
        if size >= threshold:
            mask[index] = True
    return mask, alpha, threshold


def _schedule_angles(spec: dict[str, Any], depth: int) -> tuple[np.ndarray, np.ndarray]:
    if spec["kind"] != "power":
        raise ValueError(f"unsupported schedule kind {spec['kind']!r}")
    t = (np.arange(depth, dtype=np.float64) + 0.5) / depth
    betas = float(spec["beta_scale"]) * np.power(1.0 - t, float(spec["beta_power"]))
    gammas = float(spec["gamma_scale"]) * np.power(t, float(spec["gamma_power"]))
    return gammas, betas


def _exact_event_probability(
    n: int,
    edges: tuple[tuple[int, int], ...],
    event_mask: np.ndarray,
    gammas: np.ndarray,
    betas: np.ndarray,
) -> float:
    state = qaoa_mis_statevector(n, edges, gammas, betas, penalty=PENALTY)
    return event_probability(state, event_mask)


def _choose_schedules(
    protocol: dict[str, Any],
    n: int,
    edges: tuple[tuple[int, int], ...],
    event_mask: np.ndarray,
    depth: int,
) -> tuple[dict[str, Any], dict[str, tuple[np.ndarray, np.ndarray, float]]]:
    library = {row["id"]: row for row in protocol["schedule_library"]}
    exact: dict[str, tuple[np.ndarray, np.ndarray, float]] = {}
    for schedule_id, spec in library.items():
        gammas, betas = _schedule_angles(spec, depth)
        exact[schedule_id] = (
            gammas,
            betas,
            _exact_event_probability(n, edges, event_mask, gammas, betas),
        )
    selection = protocol["schedule_selection"]
    candidates: list[dict[str, Any]] = []
    for pair_index, (left, right) in enumerate(protocol["schedule_pairs_in_order"]):
        p_left = exact[left][2]
        p_right = exact[right][2]
        gap = p_left - p_right
        eligible = (
            float(selection["probability_min"]) <= p_left <= float(selection["probability_max"])
            and float(selection["probability_min"]) <= p_right <= float(selection["probability_max"])
            and float(selection["absolute_gap_min"]) <= abs(gap) <= float(selection["absolute_gap_max"])
        )
        row = {
            "pair_index": pair_index,
            "schedule_a": left,
            "schedule_b": right,
            "p_a_exact": p_left,
            "p_b_exact": p_right,
            "exact_gap": gap,
            "eligible": eligible,
        }
        candidates.append(row)
        if eligible:
            row["fallback"] = False
            return row, exact
    chosen = min(
        candidates,
        key=lambda row: (abs(abs(row["exact_gap"]) - float(selection["fallback_target_gap"])), row["pair_index"]),
    )
    chosen["fallback"] = True
    return chosen, exact


def _variant_probability(
    n: int,
    edges: tuple[tuple[int, int], ...],
    event_mask: np.ndarray,
    gammas: np.ndarray,
    betas: np.ndarray,
    *,
    bond: int,
    order: tuple[int, ...],
) -> tuple[float, dict[str, Any]]:
    state, diagnostics = qaoa_mis_statevector(
        n,
        edges,
        gammas,
        betas,
        penalty=PENALTY,
        max_bond=bond,
        qubit_order=order,
        truncate_after=("cost_layer", "mixer_layer"),
        return_diagnostics=True,
    )
    return event_probability(state, event_mask), diagnostics


def _surrogate_probability(
    n: int,
    edges: tuple[tuple[int, int], ...],
    event_mask: np.ndarray,
    gammas: np.ndarray,
    betas: np.ndarray,
    snapshot: dict[str, Any],
    *,
    row_seed: int,
) -> float:
    distribution = hardware_surrogate_distribution(
        n_qubits=n,
        edges=edges,
        gammas=np.asarray(gammas) * float(snapshot["gamma_scale"]),
        betas=np.asarray(betas) * float(snapshot["beta_scale"]),
        penalty=PENALTY,
        edge_sigma=float(snapshot["edge_phase_std"]),
        readout_flip=float(snapshot["readout_flip"]),
        depolarizing=float(snapshot["depolarizing_mix"]),
        seed=int(snapshot["seed"]) ^ int(row_seed),
    )
    return event_probability(distribution, event_mask, probabilities=True)


def _run_cohort(protocol: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    graphs = _generate_graphs(protocol)
    rows: list[dict[str, Any]] = []
    equivalence_errors: list[float] = []
    start = time.perf_counter()
    for graph_number, graph_row in enumerate(graphs, start=1):
        n = int(graph_row["n_qubits"])
        edges = _canonical_edges(tuple(map(tuple, graph_row["edges"])))
        event_mask, independence_number, event_threshold = _event_mask_and_alpha(n, edges)
        natural = tuple(range(n))
        degree_bfs = _degree_bfs_order(n, edges)
        for depth in map(int, protocol["depths"]):
            chosen, exact_library = _choose_schedules(protocol, n, edges, event_mask, depth)
            schedule_ids = (chosen["schedule_a"], chosen["schedule_b"])
            variant_gaps: list[dict[str, Any]] = []
            variant_lookup: dict[tuple[int, str], float] = {}
            for bond in map(int, protocol["metamorphic_variants"]["bond_caps"]):
                for order_name, order in (("natural", natural), ("degree_bfs", degree_bfs)):
                    probabilities: list[float] = []
                    maximum_kept_bond = 0
                    discarded_weight = 0.0
                    for schedule_id in schedule_ids:
                        gammas, betas, _ = exact_library[schedule_id]
                        probability, diagnostics = _variant_probability(
                            n,
                            edges,
                            event_mask,
                            gammas,
                            betas,
                            bond=bond,
                            order=order,
                        )
                        probabilities.append(probability)
                        for truncation in diagnostics["truncations"]:
                            maximum_kept_bond = max(maximum_kept_bond, int(truncation["max_kept_rank"]))
                            discarded_weight += float(truncation["discarded_weight_sum"])
                    gap = probabilities[0] - probabilities[1]
                    variant_lookup[(bond, order_name)] = gap
                    variant_gaps.append(
                        {
                            "bond": bond,
                            "order": order_name,
                            "gap": gap,
                            "p_a": probabilities[0],
                            "p_b": probabilities[1],
                            "maximum_kept_bond": maximum_kept_bond,
                            "discarded_weight_sum_both_schedules": discarded_weight,
                        }
                    )

            values = [item["gap"] for item in variant_gaps]
            center = float(np.median(values))
            spread = float(max(values) - min(values))
            exact_gap = float(chosen["exact_gap"])
            high_bond_gap = variant_lookup[(max(protocol["metamorphic_variants"]["bond_caps"]), "degree_bfs")]

            # One full-rank reconstruction per size audits that representation
            # order alone does not alter an exact state.
            if depth == min(protocol["depths"]) and graph_row["graph_id"].split("_g")[1].startswith("00"):
                for order in (natural, degree_bfs):
                    probabilities = []
                    for schedule_id in schedule_ids:
                        gammas, betas, _ = exact_library[schedule_id]
                        full_state = qaoa_mis_statevector(
                            n,
                            edges,
                            gammas,
                            betas,
                            penalty=PENALTY,
                            max_bond=1 << (n // 2),
                            qubit_order=order,
                            truncate_after=("cost_layer", "mixer_layer"),
                        )
                        probabilities.append(event_probability(full_state, event_mask))
                    equivalence_errors.append(abs((probabilities[0] - probabilities[1]) - exact_gap))

            row_seed = _stable_int(protocol["seed"], graph_row["graph_id"], depth) & 0x7FFF_FFFF
            primary: list[dict[str, Any]] = []
            for snapshot in protocol["primary_noise_snapshots"]:
                hardware_probabilities = []
                for schedule_id in schedule_ids:
                    gammas, betas, _ = exact_library[schedule_id]
                    hardware_probabilities.append(
                        _surrogate_probability(
                            n,
                            edges,
                            event_mask,
                            gammas,
                            betas,
                            snapshot,
                            row_seed=row_seed,
                        )
                    )
                primary.append(
                    {
                        "snapshot": snapshot["id"],
                        "p_a": hardware_probabilities[0],
                        "p_b": hardware_probabilities[1],
                        "gap": hardware_probabilities[0] - hardware_probabilities[1],
                    }
                )

            def noise_gap(snapshot: dict[str, Any]) -> tuple[float, float, float]:
                probabilities = []
                for schedule_id in schedule_ids:
                    gammas, betas, _ = exact_library[schedule_id]
                    probabilities.append(
                        _surrogate_probability(
                            n,
                            edges,
                            event_mask,
                            gammas,
                            betas,
                            snapshot,
                            row_seed=row_seed,
                        )
                    )
                return probabilities[0], probabilities[1], probabilities[0] - probabilities[1]

            nominal_a, nominal_b, nominal_gap = noise_gap(protocol["nominal_noise_snapshot"])
            shift_a, shift_b, shift_gap = noise_gap(protocol["shift_noise_snapshot"])
            rows.append(
                {
                    "graph_id": graph_row["graph_id"],
                    "split": graph_row["split"],
                    "n_qubits": n,
                    "edge_count": len(edges),
                    "depth": depth,
                    "independence_number": independence_number,
                    "event_threshold": event_threshold,
                    "event_basis_count": int(event_mask.sum()),
                    "schedule_selection": chosen,
                    "metamorphic_center": center,
                    "metamorphic_spread": spread,
                    "exact_noiseless_gap": exact_gap,
                    "single_high_bond_gap": high_bond_gap,
                    "gate_proxy": float(depth * (n + len(edges))),
                    "variant_gaps": variant_gaps,
                    "primary_hardware_surrogates": primary,
                    "nominal_noise": {"p_a": nominal_a, "p_b": nominal_b, "gap": nominal_gap},
                    "shift_noise": {"p_a": shift_a, "p_b": shift_b, "gap": shift_gap},
                }
            )
        elapsed = time.perf_counter() - start
        print(f"[{graph_number:02d}/{len(graphs)}] {graph_row['graph_id']} complete in {elapsed:.1f}s", flush=True)
    audit = {
        "maximum_exact_equivalence_gap_error": max(equivalence_errors, default=0.0),
        "equivalence_checks": len(equivalence_errors),
        "runtime_seconds": time.perf_counter() - start,
    }
    return graphs, rows, audit


def _method_spec(row: dict[str, Any], method: str, epsilon: float) -> tuple[float, float]:
    if method == "cmrt":
        return float(row["metamorphic_center"]), float(row["metamorphic_spread"]) + epsilon
    if method == "unscaled_ensemble":
        return float(row["metamorphic_center"]), 1.0
    if method == "gate_proxy":
        return float(row["metamorphic_center"]), float(row["gate_proxy"])
    if method == "single_high_bond":
        return float(row["single_high_bond_gap"]), 1.0
    if method == "exact_noiseless":
        return float(row["exact_noiseless_gap"]), 1.0
    if method == "nominal_noise":
        return float(row["nominal_noise"]["gap"]), 1.0
    raise KeyError(method)


def _block_scores(
    rows: list[dict[str, Any]], method: str, epsilon: float
) -> dict[str, float]:
    result: dict[str, float] = {}
    for row in rows:
        if row["split"] != "calibration":
            continue
        center, scale = _method_spec(row, method, epsilon)
        residuals = [
            abs(float(item["gap"]) - center) / scale
            for item in row["primary_hardware_surrogates"]
        ]
        result[row["graph_id"]] = max(result.get(row["graph_id"], 0.0), *residuals)
    return result


def _evaluate_method(
    rows: list[dict[str, Any]], method: str, protocol: dict[str, Any]
) -> dict[str, Any]:
    epsilon = float(protocol["epsilon_scale"])
    block_scores = _block_scores(rows, method, epsilon)
    qhat = finite_sample_quantile(list(block_scores.values()), float(protocol["alpha"]))
    test_records: list[dict[str, Any]] = []
    for row in rows:
        if row["split"] != "test":
            continue
        center, scale = _method_spec(row, method, epsilon)
        radius = qhat * scale
        lower, upper = center - radius, center + radius
        decision = sign_or_abstain(lower, upper)
        for hardware in row["primary_hardware_surrogates"]:
            truth_gap = float(hardware["gap"])
            if abs(truth_gap) <= 1e-15:
                raise AssertionError("registered sign estimand encountered an exact tie")
            test_records.append(
                {
                    "graph_id": row["graph_id"],
                    "depth": row["depth"],
                    "snapshot": hardware["snapshot"],
                    "truth_gap": truth_gap,
                    "truth_sign": 1 if truth_gap > 0.0 else -1,
                    "center": center,
                    "scale": scale,
                    "radius": radius,
                    "lower": lower,
                    "upper": upper,
                    "decision": decision,
                    "covered": lower <= truth_gap <= upper,
                    "strength": max(0.0, abs(center) - radius) / max(radius, epsilon),
                }
            )
    truth = [record["truth_sign"] for record in test_records]
    decisions = [record["decision"] for record in test_records]
    metrics = selective_metrics(decisions, truth)
    graph_coverage = {
        graph_id: all(record["covered"] for record in test_records if record["graph_id"] == graph_id)
        for graph_id in sorted({record["graph_id"] for record in test_records})
    }
    by_snapshot: dict[str, Any] = {}
    for snapshot in [row["id"] for row in protocol["primary_noise_snapshots"]]:
        selected = [record for record in test_records if record["snapshot"] == snapshot]
        snapshot_metrics = selective_metrics(
            [record["decision"] for record in selected],
            [record["truth_sign"] for record in selected],
        )
        by_snapshot[snapshot] = asdict(snapshot_metrics)
    widths = [2.0 * record["radius"] for record in test_records]
    return {
        "method": method,
        "qhat": qhat,
        "calibration_block_scores": block_scores,
        "metrics": asdict(metrics),
        "row_coverage": sum(record["covered"] for record in test_records) / len(test_records),
        "covered_blocks": sum(graph_coverage.values()),
        "total_test_blocks": len(graph_coverage),
        "block_coverage": graph_coverage,
        "median_interval_width": statistics.median(widths),
        "by_snapshot": by_snapshot,
        "test_records": test_records,
    }


def _matched_error_reductions(evaluations: dict[str, dict[str, Any]]) -> dict[str, Any]:
    cmrt = evaluations["cmrt"]
    target = int(cmrt["metrics"]["n_certified"])
    output: dict[str, Any] = {}
    for baseline in (
        "unscaled_ensemble",
        "gate_proxy",
        "single_high_bond",
        "exact_noiseless",
        "nominal_noise",
    ):
        other = evaluations[baseline]
        if int(other["metrics"]["n_certified"]) < target:
            output[baseline] = {
                "comparable_at_cmrt_count": False,
                "baseline_certified": int(other["metrics"]["n_certified"]),
                "cmrt_target_count": target,
            }
            continue
        cmrt_records = cmrt["test_records"]
        other_records = other["test_records"]
        if len(cmrt_records) != len(other_records):
            raise AssertionError("methods produced different test cohorts")
        cmrt_selected = sorted(
            (index for index, record in enumerate(cmrt_records) if record["decision"] != 0),
            key=lambda index: (-cmrt_records[index]["strength"], index),
        )[:target]
        other_selected = sorted(
            (index for index, record in enumerate(other_records) if record["decision"] != 0),
            key=lambda index: (-other_records[index]["strength"], index),
        )[:target]
        cmrt_correct = sum(
            cmrt_records[index]["decision"] == cmrt_records[index]["truth_sign"]
            for index in cmrt_selected
        )
        other_correct = sum(
            other_records[index]["decision"] == other_records[index]["truth_sign"]
            for index in other_selected
        )
        cmrt_error = 1.0 - cmrt_correct / target if target else 1.0
        other_error = 1.0 - other_correct / target if target else 1.0
        if other_error == 0.0:
            # Keep the machine-readable artifact valid JSON.  A negative unit
            # value is already a decisive failure of the +25% gate.
            reduction = 0.0 if cmrt_error == 0.0 else -1.0
        else:
            reduction = (other_error - cmrt_error) / other_error
        output[baseline] = {
            "comparable_at_cmrt_count": True,
            "target_count": target,
            "cmrt_correct": cmrt_correct,
            "baseline_correct": other_correct,
            "cmrt_error_rate": cmrt_error,
            "baseline_error_rate": other_error,
            "relative_error_reduction": reduction,
            "independent_newcombe_accuracy_difference_interval": asdict(
                wilson_difference_interval(cmrt_correct, target, other_correct, target, confidence=0.95)
            ) if target else None,
            "warning": "interval is descriptive; method cohorts are selected separately and are not paired-inference units",
        }
    return output


def _shift_evaluation(
    rows: list[dict[str, Any]], evaluation: dict[str, Any]
) -> dict[str, Any]:
    record_by_key = {
        (record["graph_id"], int(record["depth"])): record
        for record in evaluation["test_records"]
    }
    decisions: list[int] = []
    truth: list[int] = []
    covered: list[bool] = []
    for row in rows:
        if row["split"] != "test":
            continue
        template = record_by_key[(row["graph_id"], int(row["depth"]))]
        gap = float(row["shift_noise"]["gap"])
        if abs(gap) <= 1e-15:
            raise AssertionError("shifted sign estimand encountered an exact tie")
        decisions.append(int(template["decision"]))
        truth.append(1 if gap > 0 else -1)
        covered.append(float(template["lower"]) <= gap <= float(template["upper"]))
    metrics = selective_metrics(decisions, truth)
    return {"metrics": asdict(metrics), "row_coverage": sum(covered) / len(covered)}


def _shot_audit(rows: list[dict[str, Any]], protocol: dict[str, Any]) -> dict[str, Any]:
    test_rows = [row for row in rows if row["split"] == "test"]
    total_contrasts = len(test_rows) * len(protocol["primary_noise_snapshots"])
    confidence = 1.0 - float(protocol["shot_audit"]["familywise_alpha"]) / total_contrasts
    shots = int(protocol["shot_audit"]["shots_per_circuit"])
    rng = np.random.default_rng(int(protocol["seed"]) ^ 0x5A07)
    resolved = 0
    correct = 0
    contains_truth = 0
    rows_out: list[dict[str, Any]] = []
    for row in test_rows:
        for hardware in row["primary_hardware_surrogates"]:
            count_a = int(rng.binomial(shots, float(hardware["p_a"])))
            count_b = int(rng.binomial(shots, float(hardware["p_b"])))
            interval = wilson_difference_interval(
                count_a,
                shots,
                count_b,
                shots,
                confidence=confidence,
            )
            decision = sign_or_abstain(interval.lower, interval.upper)
            truth_gap = float(hardware["gap"])
            if abs(truth_gap) <= 1e-15:
                raise AssertionError("shot-audit sign estimand encountered an exact tie")
            if decision:
                resolved += 1
                correct += decision == (1 if truth_gap > 0 else -1)
            contains_truth += interval.lower <= truth_gap <= interval.upper
            rows_out.append(
                {
                    "graph_id": row["graph_id"],
                    "depth": row["depth"],
                    "snapshot": hardware["snapshot"],
                    "count_a": count_a,
                    "count_b": count_b,
                    "lower": interval.lower,
                    "upper": interval.upper,
                    "decision": decision,
                }
            )
    return {
        "shots_per_circuit": shots,
        "per_contrast_confidence": confidence,
        "total_contrasts": total_contrasts,
        "resolved_contrasts": resolved,
        "resolved_fraction": resolved / total_contrasts,
        "resolved_sign_accuracy": correct / resolved if resolved else None,
        "truth_containment_fraction": contains_truth / total_contrasts,
        "rows": rows_out,
        "binding": False,
        "interval_scope": (
            "descriptive Bonferroni-adjusted Newcombe-Wilson intervals; "
            "not an exact finite-sample familywise guarantee"
        ),
    }


def _snapshot_matched_advantage(
    evaluations: dict[str, dict[str, Any]],
    protocol: dict[str, Any],
) -> dict[str, Any]:
    """Conservatively compare CMRT with every baseline inside each snapshot."""

    threshold = float(protocol["kill_gates"]["minimum_relative_error_reduction"])
    output: dict[str, Any] = {}
    cmrt_all = evaluations["cmrt"]["test_records"]
    baseline_names = [name for name in evaluations if name != "cmrt"]
    for snapshot in [row["id"] for row in protocol["primary_noise_snapshots"]]:
        cmrt = [row for row in cmrt_all if row["snapshot"] == snapshot]
        cmrt_available = [index for index, row in enumerate(cmrt) if row["decision"] != 0]
        comparisons: dict[str, Any] = {}
        snapshot_pass = bool(cmrt_available)
        for baseline_name in baseline_names:
            baseline = [
                row
                for row in evaluations[baseline_name]["test_records"]
                if row["snapshot"] == snapshot
            ]
            if len(baseline) != len(cmrt):
                raise AssertionError("snapshot cohorts differ across methods")
            baseline_available = [index for index, row in enumerate(baseline) if row["decision"] != 0]
            target = min(len(cmrt_available), len(baseline_available))
            if target == 0:
                comparisons[baseline_name] = {
                    "comparable": False,
                    "target_count": 0,
                    "pass": False,
                }
                snapshot_pass = False
                continue
            selected_cmrt = sorted(
                cmrt_available, key=lambda index: (-cmrt[index]["strength"], index)
            )[:target]
            selected_baseline = sorted(
                baseline_available,
                key=lambda index: (-baseline[index]["strength"], index),
            )[:target]
            cmrt_error = 1.0 - sum(
                cmrt[index]["decision"] == cmrt[index]["truth_sign"] for index in selected_cmrt
            ) / target
            baseline_error = 1.0 - sum(
                baseline[index]["decision"] == baseline[index]["truth_sign"]
                for index in selected_baseline
            ) / target
            if baseline_error == 0.0:
                reduction = 0.0 if cmrt_error == 0.0 else -1.0
            else:
                reduction = (baseline_error - cmrt_error) / baseline_error
            comparison_pass = reduction >= threshold
            comparisons[baseline_name] = {
                "comparable": True,
                "target_count": target,
                "cmrt_error_rate": cmrt_error,
                "baseline_error_rate": baseline_error,
                "relative_error_reduction": reduction,
                "pass": comparison_pass,
            }
            snapshot_pass = snapshot_pass and comparison_pass
        output[snapshot] = {"pass": snapshot_pass, "comparisons": comparisons}
    return output


def _decision(
    graphs: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    audit: dict[str, Any],
    evaluations: dict[str, dict[str, Any]],
    matched: dict[str, Any],
    shift: dict[str, Any],
    protocol: dict[str, Any],
) -> dict[str, Any]:
    gates = protocol["kill_gates"]
    test_rows = [row for row in rows if row["split"] == "test"]
    spread_values: list[float] = []
    residual_values: list[float] = []
    for row in test_rows:
        for hardware in row["primary_hardware_surrogates"]:
            spread_values.append(float(row["metamorphic_spread"]))
            residual_values.append(abs(float(hardware["gap"]) - float(row["metamorphic_center"])))
    correlation_result = spearmanr(spread_values, residual_values)
    correlation = float(correlation_result.statistic) if math.isfinite(float(correlation_result.statistic)) else 0.0
    cmrt = evaluations["cmrt"]
    cmrt_metrics = cmrt["metrics"]
    fallback_fraction = (
        sum(row["schedule_selection"]["fallback"] for row in test_rows) / len(test_rows)
    )

    comparable_reductions = [
        float(value["relative_error_reduction"])
        for value in matched.values()
        if value["comparable_at_cmrt_count"]
    ]
    gate_4_pass = bool(comparable_reductions) and all(
        value >= float(gates["minimum_relative_error_reduction"])
        for value in comparable_reductions
    )

    dominance: dict[str, bool] = {}
    for method in ("exact_noiseless", "nominal_noise"):
        contender = evaluations[method]
        contender_accuracy = contender["metrics"]["selective_accuracy"]
        cmrt_accuracy = cmrt_metrics["selective_accuracy"]
        dominance[method] = bool(
            contender_accuracy is not None
            and cmrt_accuracy is not None
            and float(contender_accuracy) >= float(cmrt_accuracy)
            and float(contender["metrics"]["coverage"]) >= float(cmrt_metrics["coverage"])
            and float(contender["median_interval_width"]) <= float(cmrt["median_interval_width"])
        )

    snapshot_absolute_pass = all(
        value["selective_accuracy"] is not None
        and float(value["selective_accuracy"]) >= float(gates["minimum_selective_accuracy"])
        and float(value["coverage"]) >= float(gates["minimum_accepted_fraction"])
        for value in cmrt["by_snapshot"].values()
    )
    snapshot_advantage = _snapshot_matched_advantage(evaluations, protocol)
    snapshot_pass = snapshot_absolute_pass and all(
        value["pass"] for value in snapshot_advantage.values()
    )
    checks = {
        "G1_spread_predicts_residual": {
            "pass": correlation >= float(gates["minimum_spread_residual_spearman"]),
            "value": correlation,
            "threshold": float(gates["minimum_spread_residual_spearman"]),
        },
        "G2_simultaneous_block_coverage": {
            "pass": int(cmrt["covered_blocks"]) >= int(gates["minimum_covered_test_blocks"]),
            "value": int(cmrt["covered_blocks"]),
            "threshold": int(gates["minimum_covered_test_blocks"]),
        },
        "G3_selective_accuracy_and_coverage": {
            "pass": cmrt_metrics["selective_accuracy"] is not None
            and float(cmrt_metrics["selective_accuracy"]) >= float(gates["minimum_selective_accuracy"])
            and float(cmrt_metrics["coverage"]) >= float(gates["minimum_accepted_fraction"]),
            "accuracy": cmrt_metrics["selective_accuracy"],
            "coverage": cmrt_metrics["coverage"],
        },
        "G4_matched_error_reduction": {
            "pass": gate_4_pass,
            "minimum_observed_reduction": min(comparable_reductions) if comparable_reductions else None,
            "threshold": float(gates["minimum_relative_error_reduction"]),
            "comparable_baselines": len(comparable_reductions),
        },
        "G5_not_dominated_by_strong_simulator": {
            "pass": not any(dominance.values()),
            "dominance": dominance,
        },
        "G6_each_primary_snapshot": {
            "pass": snapshot_pass,
            "absolute_metrics_pass": snapshot_absolute_pass,
            "by_snapshot": cmrt["by_snapshot"],
            "matched_advantage": snapshot_advantage,
        },
        "G7_shift_stress": {
            "pass": shift["metrics"]["selective_accuracy"] is not None
            and float(shift["metrics"]["selective_accuracy"]) >= float(gates["minimum_shift_accuracy"])
            and float(shift["metrics"]["coverage"]) >= float(gates["minimum_shift_accepted_fraction"]),
            "accuracy": shift["metrics"]["selective_accuracy"],
            "coverage": shift["metrics"]["coverage"],
        },
        "G8_schedule_selection_not_fallback_driven": {
            "pass": fallback_fraction <= float(gates["maximum_fallback_fraction"]),
            "value": fallback_fraction,
            "threshold": float(gates["maximum_fallback_fraction"]),
        },
        "G9_integrity": {
            "pass": float(audit["maximum_exact_equivalence_gap_error"]) <= 1e-10
            and len({row["graph_id"] for row in test_rows}) == int(protocol["graphs"]["test_count"])
            and len(graphs) == int(protocol["graphs"]["count"]),
            "maximum_exact_equivalence_gap_error": audit["maximum_exact_equivalence_gap_error"],
        },
        "G10_prior_art_boundary": {
            "pass": True,
            "value": "no direct pre-freeze collision located; conjunction remains narrow and provisional",
        },
    }
    passed = all(check["pass"] for check in checks.values())
    return {
        "terminal_label": "AUTHORIZE_HELDOUT_QPU_PHASE" if passed else "KILL_CMRT_AS_ASTAR_SOURCE",
        "all_gates_passed": passed,
        "passed_gate_count": sum(bool(check["pass"]) for check in checks.values()),
        "total_gate_count": len(checks),
        "failed_gates": [name for name, check in checks.items() if not check["pass"]],
        "checks": checks,
        "fallback_fraction": fallback_fraction,
        "spread_residual_spearman": correlation,
        "scope": "offline synthetic falsification only; never a hardware or A-star result",
    }


def run(output: Path) -> dict[str, Any]:
    protocol_bytes = PROTOCOL_PATH.read_bytes()
    protocol = json.loads(protocol_bytes)
    graphs, rows, audit = _run_cohort(protocol)
    methods = (
        "cmrt",
        "unscaled_ensemble",
        "gate_proxy",
        "single_high_bond",
        "exact_noiseless",
        "nominal_noise",
    )
    evaluations = {method: _evaluate_method(rows, method, protocol) for method in methods}
    matched = _matched_error_reductions(evaluations)
    shift = _shift_evaluation(rows, evaluations["cmrt"])
    shot_audit = _shot_audit(rows, protocol)
    decision = _decision(graphs, rows, audit, evaluations, matched, shift, protocol)
    payload = {
        "experiment": protocol["name"],
        "protocol_sha256": hashlib.sha256(protocol_bytes).hexdigest(),
        "protocol_status_before_run": protocol["status_before_run"],
        "decision": decision,
        "audit": audit,
        "cohort": {
            "graphs": graphs,
            "graph_count": len(graphs),
            "base_rows": len(rows),
            "primary_rows": len(rows) * len(protocol["primary_noise_snapshots"]),
            "calibration_graphs": sum(row["split"] == "calibration" for row in graphs),
            "test_graphs": sum(row["split"] == "test" for row in graphs),
        },
        "evaluations": evaluations,
        "matched_error_reductions": matched,
        "shift_evaluation": shift,
        "shot_audit": shot_audit,
        "rows": rows,
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "numpy": np.__version__,
            "networkx": nx.__version__,
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False), encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = run(args.output)
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
