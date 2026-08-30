"""Exact hard-blockade Rydberg MIS utilities used by the frozen Phase 0."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from math import sqrt

import networkx as nx
import numpy as np
from scipy.linalg import eigh
from scipy.sparse import csr_matrix, diags
from scipy.sparse.linalg import expm_multiply


@dataclass(frozen=True)
class ReducedInstance:
    graph: nx.Graph
    kept_nodes: tuple[int, ...]
    leaf: int
    neighbour: int


def relabel_graph(graph: nx.Graph) -> nx.Graph:
    return nx.convert_node_labels_to_integers(graph, ordering="sorted")


def graph6(graph: nx.Graph) -> str:
    return nx.to_graph6_bytes(relabel_graph(graph), header=False).decode().strip()


def independent_masks(graph: nx.Graph) -> tuple[int, ...]:
    graph = relabel_graph(graph)
    n = graph.number_of_nodes()
    edge_masks = tuple((1 << u) | (1 << v) for u, v in graph.edges())
    return tuple(mask for mask in range(1 << n) if all(mask & edge != edge for edge in edge_masks))


class HardBlockadeSystem:
    def __init__(self, graph: nx.Graph):
        self.graph = relabel_graph(graph)
        self.n = self.graph.number_of_nodes()
        self.masks = independent_masks(self.graph)
        self.index = {mask: i for i, mask in enumerate(self.masks)}
        self.counts = np.array([mask.bit_count() for mask in self.masks], dtype=float)
        rows: list[int] = []
        cols: list[int] = []
        for i, mask in enumerate(self.masks):
            for bit in range(self.n):
                flipped = mask ^ (1 << bit)
                j = self.index.get(flipped)
                if j is not None and i < j:
                    rows.extend((i, j))
                    cols.extend((j, i))
        data = np.ones(len(rows), dtype=float)
        self.flip = csr_matrix((data, (rows, cols)), shape=(len(self.masks), len(self.masks)))

    def hamiltonian(self, omega: float, delta: float) -> csr_matrix:
        return (-0.5 * omega) * self.flip + diags(-delta * self.counts, format="csr")

    def gap(self, omega: float, delta: float) -> float:
        dim = len(self.masks)
        if dim < 2:
            return float("inf")
        values = eigh(self.hamiltonian(omega, delta).toarray(), eigvals_only=True, subset_by_index=(0, 1))
        return float(values[1] - values[0])

    @property
    def alpha(self) -> int:
        return int(self.counts.max(initial=0))

    @property
    def optimum_masks(self) -> tuple[int, ...]:
        alpha = self.alpha
        return tuple(mask for mask in self.masks if mask.bit_count() == alpha)


def schedule(s: float, omega_scale: float = 1.0) -> tuple[float, float]:
    if s < 0.1:
        return omega_scale * s / 0.1, -2.0
    if s <= 0.9:
        return omega_scale, -2.0 + 4.0 * (s - 0.1) / 0.8
    return omega_scale * (1.0 - s) / 0.1, 2.0


def minimum_gap(system: HardBlockadeSystem, omega_scale: float = 1.0, points: int = 49) -> tuple[float, float]:
    grid = np.linspace(0.02, 0.98, points)
    gaps = []
    for s in grid:
        omega, delta = schedule(float(s), omega_scale)
        gaps.append(system.gap(omega, delta))
    index = int(np.argmin(gaps))
    return float(gaps[index]), float(grid[index])


def minimum_gap_window(
    system: HardBlockadeSystem,
    start: float,
    stop: float,
    omega_scale: float = 1.0,
    points: int = 45,
) -> tuple[float, float]:
    grid = np.linspace(start, stop, points)
    gaps = []
    for s in grid:
        omega, delta = schedule(float(s), omega_scale)
        gaps.append(system.gap(omega, delta))
    index = int(np.argmin(gaps))
    return float(gaps[index]), float(grid[index])


def evolve_success(system: HardBlockadeSystem, total_time: float, omega_scale: float = 1.0, steps: int = 400) -> float:
    state = np.zeros(len(system.masks), dtype=complex)
    state[system.index[0]] = 1.0
    dt = total_time / steps
    for step in range(steps):
        s = (step + 0.5) / steps
        omega, delta = schedule(s, omega_scale)
        state = expm_multiply((-1j * dt) * system.hamiltonian(omega, delta), state)
    optimum_indices = [system.index[mask] for mask in system.optimum_masks]
    return float(np.sum(np.abs(state[optimum_indices]) ** 2).real)


def leaf_reduction(graph: nx.Graph, leaf: int) -> ReducedInstance:
    graph = relabel_graph(graph)
    if graph.degree[leaf] != 1:
        raise ValueError("leaf_reduction requires a degree-one vertex")
    neighbour = next(iter(graph.neighbors(leaf)))
    kept = tuple(node for node in graph.nodes() if node not in (leaf, neighbour))
    reduced = nx.convert_node_labels_to_integers(graph.subgraph(kept).copy(), ordering="sorted")
    return ReducedInstance(reduced, kept, leaf, neighbour)


def lifted_optimum_count(original: nx.Graph, reduction: ReducedInstance) -> tuple[int, int]:
    original = relabel_graph(original)
    original_system = HardBlockadeSystem(original)
    reduced_system = HardBlockadeSystem(reduction.graph)
    lifted = set()
    for reduced_mask in reduced_system.optimum_masks:
        original_mask = 1 << reduction.leaf
        for reduced_bit, original_node in enumerate(reduction.kept_nodes):
            if reduced_mask & (1 << reduced_bit):
                original_mask |= 1 << original_node
        lifted.add(original_mask)
    optimum = set(original_system.optimum_masks)
    if not lifted <= optimum:
        raise AssertionError("classical leaf lift produced a non-optimal state")
    return len(lifted), len(optimum)


def driver_scales(original_n: int, reduced_n: int) -> tuple[float, ...]:
    if reduced_n <= 0:
        return (1.0,)
    return (1.0, sqrt(original_n / reduced_n), original_n / reduced_n)


def gap_distortion(first: float, second: float) -> float:
    if first <= 0.0 or second <= 0.0:
        return float("inf")
    return max(first / second, second / first)
