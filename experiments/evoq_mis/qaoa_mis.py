from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error


@dataclass(frozen=True)
class GraphInstance:
    name: str
    n: int
    edges: tuple[tuple[int, int], ...]
    source: str

    @property
    def degrees(self) -> np.ndarray:
        result = np.zeros(self.n, dtype=np.int16)
        for u, v in self.edges:
            result[u] += 1
            result[v] += 1
        return result


@dataclass(frozen=True)
class ExactSpace:
    masks: np.ndarray
    sizes: np.ndarray
    feasible: np.ndarray
    optimum: int
    optimal: np.ndarray


def load_dimacs_graph(path: Path) -> GraphInstance:
    n = None
    expected_edges = None
    edges: list[tuple[int, int]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("c"):
            continue
        parts = line.split()
        if parts[0] == "p":
            n, expected_edges = int(parts[2]), int(parts[3])
        elif parts[0] == "e":
            edges.append((int(parts[1]) - 1, int(parts[2]) - 1))
    if n is None:
        raise ValueError(f"Missing problem line in {path}")
    if expected_edges != len(edges):
        raise ValueError(f"Expected {expected_edges} edges, parsed {len(edges)}")
    if any(u == v or min(u, v) < 0 or max(u, v) >= n for u, v in edges):
        raise ValueError(f"Invalid edge in {path}")
    normalized = tuple(sorted({(min(u, v), max(u, v)) for u, v in edges}))
    if len(normalized) != expected_edges:
        raise ValueError(f"Duplicate edges in {path}")
    return GraphInstance(path.stem, n, normalized, str(path.resolve()))


def induced_subgraph(graph: GraphInstance, vertices: Iterable[int], name: str) -> GraphInstance:
    selected = tuple(sorted({int(vertex) for vertex in vertices}))
    if not selected or min(selected) < 0 or max(selected) >= graph.n:
        raise ValueError("Induced-subgraph vertices are outside the source graph")
    remap = {old: new for new, old in enumerate(selected)}
    edges = tuple(
        (remap[u], remap[v])
        for u, v in graph.edges
        if u in remap and v in remap
    )
    source = f"induced:{graph.source};vertices_1_based={','.join(str(v + 1) for v in selected)}"
    return GraphInstance(name=name, n=len(selected), edges=edges, source=source)


def enumerate_exact_space(graph: GraphInstance) -> ExactSpace:
    if graph.n > 24:
        raise ValueError("Exact enumeration is intentionally limited to 24 vertices")
    masks = np.arange(1 << graph.n, dtype=np.uint32)
    sizes = np.fromiter((int(x).bit_count() for x in masks), dtype=np.int16, count=len(masks))
    feasible = np.ones(len(masks), dtype=bool)
    for u, v in graph.edges:
        feasible &= ~((((masks >> u) & 1) != 0) & (((masks >> v) & 1) != 0))
    optimum = int(sizes[feasible].max())
    optimal = feasible & (sizes == optimum)
    return ExactSpace(masks, sizes, feasible, optimum, optimal)


def qaoa_circuit(
    graph: GraphInstance,
    params: np.ndarray,
    p: int,
    measure: bool = False,
    cost_scale: str = "none",
) -> QuantumCircuit:
    params = np.asarray(params, dtype=float)
    if len(params) != 1 + 2 * p:
        raise ValueError(f"Expected {1 + 2 * p} parameters, got {len(params)}")
    penalty = float(params[0])
    betas = params[1 : 1 + p]
    gammas = params[1 + p :]
    degrees = graph.degrees
    h_coefficients = 0.5 - penalty * degrees.astype(float) / 4.0
    j_coefficient = penalty / 4.0
    if cost_scale == "none":
        scale = 1.0
    elif cost_scale == "max_coefficient":
        scale = max(1e-12, float(np.max(np.abs(h_coefficients))), abs(j_coefficient))
    else:
        raise ValueError(f"Unknown cost scale: {cost_scale}")
    h_coefficients = h_coefficients / scale
    j_coefficient /= scale

    qc = QuantumCircuit(graph.n)
    qc.h(range(graph.n))
    for layer in range(p):
        gamma = float(gammas[layer])
        # C(x) = -sum_i x_i + penalty * sum_(i,j) x_i*x_j, x_i=(1-Z_i)/2.
        for i in range(graph.n):
            qc.rz(2.0 * gamma * float(h_coefficients[i]), i)
        for u, v in graph.edges:
            qc.rzz(2.0 * gamma * j_coefficient, u, v)
        for i in range(graph.n):
            qc.rx(2.0 * float(betas[layer]), i)
    if measure:
        qc.measure_all()
    else:
        qc.save_statevector()
    return qc


def statevector_probabilities(
    graph: GraphInstance,
    params: np.ndarray,
    p: int,
    cost_scale: str = "none",
) -> np.ndarray:
    backend = AerSimulator(method="statevector")
    circuit = qaoa_circuit(graph, params, p, measure=False, cost_scale=cost_scale)
    result = backend.run(circuit).result()
    return np.asarray(result.get_statevector(circuit).probabilities(), dtype=float)


def distribution_metrics(probs: np.ndarray, exact: ExactSpace) -> dict[str, float]:
    probs = np.asarray(probs, dtype=float)
    if len(probs) != len(exact.masks):
        raise ValueError("Probability vector and exact state space differ")
    feasible_probability = float(probs[exact.feasible].sum())
    expected_feasible_size = float(np.dot(probs[exact.feasible], exact.sizes[exact.feasible]))
    optimal_probability = float(probs[exact.optimal].sum())
    conditional_size = expected_feasible_size / feasible_probability if feasible_probability > 0 else 0.0
    score = expected_feasible_size / exact.optimum + 0.25 * optimal_probability + 0.10 * feasible_probability
    return {
        "score": score,
        "feasible_probability": feasible_probability,
        "optimal_probability": optimal_probability,
        "expected_feasible_size_unconditional": expected_feasible_size,
        "expected_size_given_feasible": conditional_size,
        "approximation_ratio_unconditional": expected_feasible_size / exact.optimum,
    }


def repair_mask(mask: int, graph: GraphInstance) -> int:
    selected = {i for i in range(graph.n) if (mask >> i) & 1}
    graph_degrees = graph.degrees
    while True:
        conflict_degree = {i: 0 for i in selected}
        for u, v in graph.edges:
            if u in selected and v in selected:
                conflict_degree[u] += 1
                conflict_degree[v] += 1
        max_conflicts = max(conflict_degree.values(), default=0)
        if max_conflicts == 0:
            break
        victim = max(
            (i for i, count in conflict_degree.items() if count == max_conflicts),
            key=lambda i: (int(graph_degrees[i]), i),
        )
        selected.remove(victim)
    for i in sorted(set(range(graph.n)) - selected, key=lambda j: (int(graph_degrees[j]), j)):
        if all(not ({u, v} <= selected | {i}) for u, v in graph.edges if i in (u, v)):
            selected.add(i)
    repaired = 0
    for i in selected:
        repaired |= 1 << i
    return repaired


def sample_counts(
    graph: GraphInstance,
    params: np.ndarray,
    p: int,
    shots: int,
    seed: int,
    noise: bool,
    cost_scale: str = "none",
) -> tuple[dict[int, int], dict[str, object]]:
    noise_model = None
    if noise:
        noise_model = NoiseModel()
        noise_model.add_all_qubit_quantum_error(depolarizing_error(0.001, 1), ["rz", "rx", "h"])
        noise_model.add_all_qubit_quantum_error(depolarizing_error(0.01, 2), ["rzz"])
    backend = AerSimulator(method="statevector", noise_model=noise_model)
    original = qaoa_circuit(graph, params, p, measure=True, cost_scale=cost_scale)
    compiled = transpile(original, backend, optimization_level=1, seed_transpiler=seed)
    raw_counts = backend.run(compiled, shots=shots, seed_simulator=seed).result().get_counts()
    counts = {int(bits.replace(" ", ""), 2): int(count) for bits, count in raw_counts.items()}
    circuit_stats = {
        "depth": int(compiled.depth()),
        "size": int(compiled.size()),
        "operations": {str(k): int(v) for k, v in compiled.count_ops().items()},
    }
    return counts, circuit_stats


def multinomial_counts(probs: np.ndarray, shots: int, seed: int) -> dict[int, int]:
    """Draw ideal finite-shot counts without rerunning an identical statevector circuit."""
    rng = np.random.default_rng(seed)
    sampled = rng.multinomial(shots, np.asarray(probs, dtype=float) / float(np.sum(probs)))
    return {int(mask): int(count) for mask, count in enumerate(sampled) if count}


def counts_metrics(counts: dict[int, int], graph: GraphInstance, exact: ExactSpace) -> dict[str, float | int]:
    shots = sum(counts.values())
    feasible_shots = 0
    optimal_shots = 0
    feasible_size_sum = 0
    repaired_size_sum = 0
    repaired_optimal_shots = 0
    best_repaired_mask = 0
    best_repaired_size = -1
    for mask, count in counts.items():
        if exact.feasible[mask]:
            feasible_shots += count
            size = int(exact.sizes[mask])
            feasible_size_sum += count * size
            if exact.optimal[mask]:
                optimal_shots += count
        repaired = repair_mask(mask, graph)
        repaired_size = int(exact.sizes[repaired])
        repaired_size_sum += count * repaired_size
        if repaired_size == exact.optimum:
            repaired_optimal_shots += count
        if repaired_size > best_repaired_size:
            best_repaired_size = repaired_size
            best_repaired_mask = repaired
    return {
        "shots": shots,
        "raw_feasible_rate": feasible_shots / shots,
        "raw_optimal_rate": optimal_shots / shots,
        "raw_expected_feasible_size_unconditional": feasible_size_sum / shots,
        "repaired_expected_size": repaired_size_sum / shots,
        "repaired_optimal_rate": repaired_optimal_shots / shots,
        "best_repaired_size": best_repaired_size,
        "best_repaired_mask": best_repaired_mask,
    }


def differential_evolution_fixed_budget(
    objective: Callable[[np.ndarray], float],
    bounds: list[tuple[float, float]],
    budget: int,
    seed: int,
    population_size: int = 10,
) -> tuple[np.ndarray, float, list[dict[str, float | int | list[float]]]]:
    if budget < population_size:
        raise ValueError("Budget must cover the initial population")
    rng = np.random.default_rng(seed)
    low = np.array([b[0] for b in bounds], dtype=float)
    high = np.array([b[1] for b in bounds], dtype=float)
    population = rng.uniform(low, high, size=(population_size, len(bounds)))
    scores = np.empty(population_size, dtype=float)
    history: list[dict[str, float | int | list[float]]] = []
    evaluations = 0

    def record() -> None:
        best = int(np.argmax(scores[: min(evaluations, population_size)]))
        history.append({
            "evaluation": evaluations,
            "best_score": float(scores[best]),
            "best_params": population[best].tolist(),
        })

    for i in range(population_size):
        scores[i] = objective(population[i])
        evaluations += 1
        record()

    while evaluations < budget:
        for i in range(population_size):
            if evaluations >= budget:
                break
            pool = [j for j in range(population_size) if j != i]
            a, b, c = rng.choice(pool, size=3, replace=False)
            mutant = np.clip(population[a] + 0.8 * (population[b] - population[c]), low, high)
            crossover = rng.random(len(bounds)) < 0.9
            crossover[rng.integers(len(bounds))] = True
            trial = np.where(crossover, mutant, population[i])
            trial_score = objective(trial)
            evaluations += 1
            if trial_score >= scores[i]:
                population[i] = trial
                scores[i] = trial_score
            record()
    best = int(np.argmax(scores))
    return population[best].copy(), float(scores[best]), history


def random_search_fixed_budget(
    objective: Callable[[np.ndarray], float],
    bounds: list[tuple[float, float]],
    budget: int,
    seed: int,
) -> tuple[np.ndarray, float, list[dict[str, float | int | list[float]]]]:
    rng = np.random.default_rng(seed)
    low = np.array([b[0] for b in bounds], dtype=float)
    high = np.array([b[1] for b in bounds], dtype=float)
    best_params = None
    best_score = -np.inf
    history: list[dict[str, float | int | list[float]]] = []
    for evaluation in range(1, budget + 1):
        params = rng.uniform(low, high)
        score = objective(params)
        if score > best_score:
            best_score = score
            best_params = params.copy()
        history.append({
            "evaluation": evaluation,
            "best_score": float(best_score),
            "best_params": best_params.tolist(),
        })
    assert best_params is not None
    return best_params, float(best_score), history


def mask_to_vertices(mask: int, n: int) -> list[int]:
    return [i + 1 for i in range(n) if (mask >> i) & 1]
