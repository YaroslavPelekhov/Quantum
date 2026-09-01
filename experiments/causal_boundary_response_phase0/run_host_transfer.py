"""Run the frozen host-independent transfer falsification for the 4-atom surrogate."""

from __future__ import annotations

import csv
import itertools
import json
import math
from dataclasses import dataclass

import networkx as nx
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import expm_multiply

from experiments.quantum_safe_kernelization_phase0.qdk_core import independent_masks

from .run_phase0 import MEAN_DELTA, OMEGA, OUT, REGIMES, onsite_detunings


TARGET_K = 13
SURROGATE_ATOMS = 4
HORIZON = 5.0
TIME_COUNT = 41
HOST_COUNTS = {2: 1, 3: 3, 4: 8, 5: 18}
RNG_SEED = 20260903
UNIT_DISK_RADIUS = 1.0
MOTIF_SPACING = 0.9


@dataclass(frozen=True)
class Host:
    graph: nx.Graph
    positions: tuple[tuple[float, float], ...]
    code: str


def port_colored_code(graph: nx.Graph) -> str:
    n = graph.number_of_nodes()
    codes = []
    for remainder in itertools.permutations(range(1, n)):
        order = (0,) + remainder
        bits = []
        for first in range(n):
            for second in range(first + 1, n):
                bits.append("1" if graph.has_edge(order[first], order[second]) else "0")
        codes.append("".join(bits))
    return min(codes)


def graph_from_positions(positions: np.ndarray) -> nx.Graph:
    graph = nx.Graph()
    graph.add_nodes_from(range(len(positions)))
    for first in range(len(positions)):
        for second in range(first + 1, len(positions)):
            if np.linalg.norm(positions[first] - positions[second]) <= UNIT_DISK_RADIUS:
                graph.add_edge(first, second)
    return graph


def heldout_hosts() -> tuple[Host, ...]:
    rng = np.random.default_rng(RNG_SEED)
    hosts: list[Host] = []
    for n, required in HOST_COUNTS.items():
        seen: set[str] = set()
        attempts = 0
        while len(seen) < required and attempts < 300000:
            attempts += 1
            positions = np.zeros((n, 2), dtype=float)
            if n > 1:
                positions[1:, 0] = rng.uniform(0.20, 2.25, size=n - 1)
                positions[1:, 1] = rng.uniform(-1.10, 1.10, size=n - 1)
            graph = graph_from_positions(positions)
            if not nx.is_connected(graph):
                continue
            code = port_colored_code(graph)
            if code in seen:
                continue
            seen.add(code)
            hosts.append(Host(graph, tuple(map(tuple, positions.tolist())), f"n{n}_{code}"))
        if len(seen) != required:
            raise RuntimeError(f"only generated {len(seen)} of {required} distinct hosts for n={n}")
    return tuple(hosts)


def load_surrogate(regime: str) -> tuple[tuple[tuple[int, int], ...], tuple[int, ...], np.ndarray, float]:
    summary = json.loads((OUT / "capacity_audit_summary.json").read_text(encoding="utf-8"))
    decision = next(
        row for row in summary["decisions"] if int(row["atoms"]) == SURROGATE_ATOMS and row["regime"] == regime
    )
    code = decision["best_topology_code"]
    refines_path = OUT / "capacity_audit_refines.csv"
    with refines_path.open(newline="", encoding="utf-8") as handle:
        candidates = [
            row
            for row in csv.DictReader(handle)
            if row["regime"] == regime and int(row["atoms"]) == SURROGATE_ATOMS and row["topology_code"] == code
        ]
    best = min(candidates, key=lambda row: float(row["train_relative_mse"]))
    parameters = np.asarray(json.loads(best["parameters"]), dtype=float)
    internal_edges = tuple(tuple(edge) for edge in json.loads(best["internal_edges"]))
    port_blocked = tuple(json.loads(best["port_blocked"]))
    return internal_edges, port_blocked, parameters[:SURROGATE_ATOMS], float(parameters[-1])


def combine_target(host: Host) -> tuple[nx.Graph, np.ndarray, dict[int, tuple[float, float]]]:
    host_n = host.graph.number_of_nodes()
    graph = host.graph.copy()
    graph.add_nodes_from(range(host_n, host_n + TARGET_K))
    graph.add_edge(0, host_n)
    graph.add_edges_from((host_n + node, host_n + node + 1) for node in range(TARGET_K - 1))
    positions = {node: host.positions[node] for node in range(host_n)}
    for node in range(TARGET_K):
        positions[host_n + node] = (-MOTIF_SPACING * (node + 1), 0.0)
    return graph, np.empty(0), positions


def combine_prefix(host: Host, atoms: int = SURROGATE_ATOMS) -> tuple[nx.Graph, dict[int, tuple[float, float]]]:
    host_n = host.graph.number_of_nodes()
    graph = host.graph.copy()
    graph.add_nodes_from(range(host_n, host_n + atoms))
    graph.add_edge(0, host_n)
    graph.add_edges_from((host_n + node, host_n + node + 1) for node in range(atoms - 1))
    positions = {node: host.positions[node] for node in range(host_n)}
    for node in range(atoms):
        positions[host_n + node] = (-MOTIF_SPACING * (node + 1), 0.0)
    return graph, positions


def combine_surrogate(
    host: Host, internal_edges: tuple[tuple[int, int], ...], port_blocked: tuple[int, ...]
) -> nx.Graph:
    host_n = host.graph.number_of_nodes()
    graph = host.graph.copy()
    graph.add_nodes_from(range(host_n, host_n + SURROGATE_ATOMS))
    graph.add_edges_from((host_n + first, host_n + second) for first, second in internal_edges)
    graph.add_edges_from((0, host_n + atom) for atom in port_blocked)
    return graph


def surrogate_positions(
    host: Host, internal_edges: tuple[tuple[int, int], ...], port_blocked: tuple[int, ...]
) -> dict[int, tuple[float, float]]:
    small = nx.Graph()
    small.add_nodes_from((-1,) + tuple(range(SURROGATE_ATOMS)))
    small.add_edges_from(internal_edges)
    small.add_edges_from((-1, atom) for atom in port_blocked)
    if not nx.is_connected(small) or small.number_of_edges() != SURROGATE_ATOMS or small.degree[-1] != 1:
        raise AssertionError("the selected surrogate is not a port-ended path")
    if max(dict(small.degree()).values()) > 2:
        raise AssertionError("the selected surrogate is not a path")
    order = [-1]
    previous = None
    current = -1
    while len(order) < SURROGATE_ATOMS + 1:
        candidates = [node for node in small.neighbors(current) if node != previous]
        if len(candidates) != 1:
            raise AssertionError("ambiguous path traversal")
        following = candidates[0]
        order.append(following)
        previous, current = current, following
    host_n = host.graph.number_of_nodes()
    positions = {node: host.positions[node] for node in range(host_n)}
    for distance, atom in enumerate(order[1:], start=1):
        positions[host_n + atom] = (-MOTIF_SPACING * distance, 0.0)
    return positions


def layout_is_exact(graph: nx.Graph, positions: dict[int, tuple[float, float]]) -> bool:
    realised = set()
    nodes = list(graph.nodes())
    for index, first in enumerate(nodes):
        for second in nodes[index + 1 :]:
            if math.dist(positions[first], positions[second]) <= UNIT_DISK_RADIUS + 1e-12:
                realised.add(tuple(sorted((first, second))))
    return realised == {tuple(sorted(edge)) for edge in graph.edges()}


def arbitrary_hamiltonian(graph: nx.Graph, detunings: np.ndarray) -> tuple[tuple[int, ...], csr_matrix]:
    masks = independent_masks(graph)
    index = {mask: position for position, mask in enumerate(masks)}
    rows: list[int] = []
    cols: list[int] = []
    data: list[complex] = []
    for row, mask in enumerate(masks):
        rows.append(row)
        cols.append(row)
        data.append(complex(-sum(detunings[node] for node in range(len(detunings)) if mask & (1 << node))))
        for node in range(len(detunings)):
            col = index.get(mask ^ (1 << node))
            if col is not None and row < col:
                rows.extend((row, col))
                cols.extend((col, row))
                data.extend((-0.5 * OMEGA, -0.5 * OMEGA))
    return masks, csr_matrix((data, (rows, cols)), shape=(len(masks), len(masks)), dtype=complex)


def evolve(graph: nx.Graph, detunings: np.ndarray) -> tuple[tuple[int, ...], np.ndarray]:
    masks, matrix = arbitrary_hamiltonian(graph, detunings)
    initial = np.zeros(len(masks), dtype=complex)
    initial[masks.index(0)] = 1.0
    states = expm_multiply(-1j * matrix, initial, start=0.0, stop=HORIZON, num=TIME_COUNT, endpoint=True)
    return masks, states


def host_density(masks: tuple[int, ...], state: np.ndarray, host_n: int) -> np.ndarray:
    host_dimension = 1 << host_n
    environments = sorted({mask >> host_n for mask in masks})
    env_index = {mask: position for position, mask in enumerate(environments)}
    amplitudes = np.zeros((len(environments), host_dimension), dtype=complex)
    host_mask = host_dimension - 1
    for amplitude, mask in zip(state, masks, strict=True):
        amplitudes[env_index[mask >> host_n], mask & host_mask] = amplitude
    return amplitudes.T @ np.conjugate(amplitudes)


def trace_distance(first: np.ndarray, second: np.ndarray) -> float:
    difference = 0.5 * ((first - second) + np.conjugate(first - second).T)
    return float(0.5 * np.sum(np.abs(np.linalg.eigvalsh(difference))))


def compare_host(host: Host, regime: str) -> dict[str, object]:
    host_n = host.graph.number_of_nodes()
    target_graph, _, target_positions = combine_target(host)
    if not layout_is_exact(target_graph, target_positions):
        raise AssertionError(f"combined target layout is not exact for {host.code}")
    prefix_graph, prefix_positions = combine_prefix(host)
    if not layout_is_exact(prefix_graph, prefix_positions):
        raise AssertionError(f"combined prefix layout is not exact for {host.code}")
    internal_edges, port_blocked, surrogate_fields, port_phase_rate = load_surrogate(regime)
    surrogate_graph = combine_surrogate(host, internal_edges, port_blocked)
    selected_surrogate_positions = surrogate_positions(host, internal_edges, port_blocked)
    if not layout_is_exact(surrogate_graph, selected_surrogate_positions):
        raise AssertionError(f"combined surrogate layout is not exact for {host.code}")

    host_fields = np.full(host_n, MEAN_DELTA)
    target_fields = np.concatenate((host_fields, onsite_detunings(TARGET_K, regime)))
    prefix_fields = np.concatenate((host_fields, onsite_detunings(SURROGATE_ATOMS, regime)))
    surrogate_host_fields = host_fields.copy()
    surrogate_host_fields[0] -= port_phase_rate
    surrogate_all_fields = np.concatenate((surrogate_host_fields, surrogate_fields))

    target_masks, target_states = evolve(target_graph, target_fields)
    prefix_masks, prefix_states = evolve(prefix_graph, prefix_fields)
    surrogate_masks, surrogate_states = evolve(surrogate_graph, surrogate_all_fields)

    surrogate_trace = []
    prefix_trace = []
    surrogate_tv = []
    prefix_tv = []
    surrogate_port = []
    prefix_port = []
    port_indices = np.asarray([mask for mask in range(1 << host_n) if mask & 1], dtype=int)
    for index in range(TIME_COUNT):
        target_rho = host_density(target_masks, target_states[index], host_n)
        prefix_rho = host_density(prefix_masks, prefix_states[index], host_n)
        surrogate_rho = host_density(surrogate_masks, surrogate_states[index], host_n)
        surrogate_trace.append(trace_distance(target_rho, surrogate_rho))
        prefix_trace.append(trace_distance(target_rho, prefix_rho))
        target_diag = np.diag(target_rho).real
        prefix_diag = np.diag(prefix_rho).real
        surrogate_diag = np.diag(surrogate_rho).real
        surrogate_tv.append(float(0.5 * np.sum(np.abs(target_diag - surrogate_diag))))
        prefix_tv.append(float(0.5 * np.sum(np.abs(target_diag - prefix_diag))))
        target_port = float(np.sum(target_diag[port_indices]))
        surrogate_port.append(abs(target_port - float(np.sum(surrogate_diag[port_indices]))))
        prefix_port.append(abs(target_port - float(np.sum(prefix_diag[port_indices]))))

    max_surrogate_trace = max(surrogate_trace)
    max_prefix_trace = max(prefix_trace)
    return {
        "host_code": host.code,
        "host_n": host_n,
        "host_edges": host.graph.number_of_edges(),
        "host_port_degree": host.graph.degree[0],
        "regime": regime,
        "target_hilbert_dimension": len(target_masks),
        "surrogate_hilbert_dimension": len(surrogate_masks),
        "prefix_hilbert_dimension": len(prefix_masks),
        "surrogate_max_trace_distance": max_surrogate_trace,
        "prefix_max_trace_distance": max_prefix_trace,
        "trace_improvement_factor": max_prefix_trace / max(max_surrogate_trace, 1e-15),
        "surrogate_final_trace_distance": surrogate_trace[-1],
        "prefix_final_trace_distance": prefix_trace[-1],
        "surrogate_max_tv_distance": max(surrogate_tv),
        "prefix_max_tv_distance": max(prefix_tv),
        "surrogate_max_port_population_error": max(surrogate_port),
        "prefix_max_port_population_error": max(prefix_port),
    }


def percentile(values: list[float], quantile: float) -> float:
    return float(np.quantile(np.asarray(values), quantile))


def main() -> None:
    hosts = heldout_hosts()
    rows: list[dict[str, object]] = []
    for regime in REGIMES:
        for index, host in enumerate(hosts):
            row = compare_host(host, regime)
            rows.append(row)
            print(f"{regime} {index + 1}/{len(hosts)} {host.code} trace={row['surrogate_max_trace_distance']:.6g}", flush=True)

    decisions = []
    for regime in REGIMES:
        subset = [row for row in rows if row["regime"] == regime]
        trace_values = [float(row["surrogate_max_trace_distance"]) for row in subset]
        improvements = [float(row["trace_improvement_factor"]) for row in subset]
        port_errors = [float(row["surrogate_max_port_population_error"]) for row in subset]
        win_rate = float(np.mean([value > 1.0 for value in improvements]))
        decision = {
            "regime": regime,
            "host_count": len(subset),
            "median_max_trace_distance": percentile(trace_values, 0.5),
            "p90_max_trace_distance": percentile(trace_values, 0.9),
            "worst_max_trace_distance": max(trace_values),
            "median_prefix_improvement": percentile(improvements, 0.5),
            "prefix_win_rate": win_rate,
            "p90_max_port_population_error": percentile(port_errors, 0.9),
        }
        decision["case_passes"] = (
            decision["median_max_trace_distance"] <= 0.02
            and decision["p90_max_trace_distance"] <= 0.05
            and decision["worst_max_trace_distance"] <= 0.10
            and decision["median_prefix_improvement"] >= 5.0
            and decision["prefix_win_rate"] >= 0.90
            and decision["p90_max_port_population_error"] <= 0.02
        )
        decisions.append(decision)

    survives = all(bool(row["case_passes"]) for row in decisions)
    summary = {
        "host_counts": HOST_COUNTS,
        "rng_seed": RNG_SEED,
        "decisions": decisions,
        "host_transfer_survives": survives,
        "verdict": "ADVANCE_TO_HARDWARE_ALGEBRA" if survives else "FALSIFIED_NONTRANSFERABLE_RESPONSE_SLICE",
    }
    with (OUT / "host_transfer.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (OUT / "host_transfer_hosts.json").write_text(
        json.dumps(
            [
                {"code": host.code, "positions": host.positions, "edges": list(host.graph.edges())}
                for host in hosts
            ],
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (OUT / "host_transfer_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
