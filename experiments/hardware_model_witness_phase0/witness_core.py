"""Exact utilities for the hardware noise-model witness Phase-0 screen."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import product
from math import cos, pi, sin
from typing import Iterable, Sequence

import numpy as np


GATE_NAMES = ("Xp", "Xm", "Yp", "Ym")
GATE_SPECS = {
    "Xp": ("x", +pi / 2),
    "Xm": ("x", -pi / 2),
    "Yp": ("y", +pi / 2),
    "Ym": ("y", -pi / 2),
}
IDENTITY = np.eye(2, dtype=np.complex128)
KET0 = np.array([1.0, 0.0], dtype=np.complex128)


@dataclass(frozen=True)
class Candidate:
    sequence: tuple[str, ...]
    counts: tuple[int, ...]
    p0: float
    declared_p0: float


@dataclass(frozen=True)
class Witness:
    high: Candidate
    low: Candidate
    gap: float


def rotation(axis: str, angle: float) -> np.ndarray:
    """Return an exact 2x2 axis rotation in SU(2)."""
    c = cos(angle / 2)
    s = -1j * sin(angle / 2)
    if axis == "x":
        pauli = np.array([[0, 1], [1, 0]], dtype=np.complex128)
    elif axis == "y":
        pauli = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
    elif axis == "z":
        pauli = np.array([[1, 0], [0, -1]], dtype=np.complex128)
    else:
        raise ValueError(f"unknown rotation axis: {axis}")
    return c * IDENTITY + s * pauli


def ideal_gate(name: str) -> np.ndarray:
    axis, angle = GATE_SPECS[name]
    return rotation(axis, angle)


def noisy_gate(name: str, epsilon: float, delta: float) -> np.ndarray:
    """Signed fractional over-rotation followed by a fixed detuning kick."""
    axis, angle = GATE_SPECS[name]
    return rotation("z", delta) @ rotation(axis, angle * (1.0 + epsilon))


def compose(sequence: Sequence[str], epsilon: float = 0.0, delta: float = 0.0) -> np.ndarray:
    """Compose gates in written execution order (left item acts first)."""
    unitary = IDENTITY.copy()
    for name in sequence:
        gate = ideal_gate(name) if epsilon == 0.0 and delta == 0.0 else noisy_gate(name, epsilon, delta)
        unitary = gate @ unitary
    return unitary


def is_identity_up_to_phase(unitary: np.ndarray, atol: float = 1e-10) -> bool:
    return bool(abs(abs(np.trace(unitary)) / 2.0 - 1.0) <= atol)


def average_gate_fidelity(actual: np.ndarray, ideal: np.ndarray) -> float:
    relative = ideal.conj().T @ actual
    value = (abs(np.trace(relative)) ** 2 + 2.0) / 6.0
    return float(np.clip(value.real, 0.0, 1.0))


def p0_for_sequence(sequence: Sequence[str], epsilon: float, delta: float) -> float:
    final = compose(sequence, epsilon=epsilon, delta=delta) @ KET0
    return float(np.clip(abs(final[0]) ** 2, 0.0, 1.0))


def gate_retentions(epsilon: float, delta: float) -> dict[str, float]:
    """Depolarizing retentions matched to each isolated gate's AGF."""
    result = {}
    for name in GATE_NAMES:
        fidelity = average_gate_fidelity(noisy_gate(name, epsilon, delta), ideal_gate(name))
        result[name] = float(np.clip(2.0 * fidelity - 1.0, -1.0 / 3.0, 1.0))
    return result


def declared_identity_p0(sequence: Sequence[str], retentions: dict[str, float]) -> float:
    retention = 1.0
    for name in sequence:
        retention *= retentions[name]
    return 0.5 * (1.0 + retention)


def count_key(sequence: Sequence[str]) -> tuple[int, ...]:
    counts = Counter(sequence)
    return tuple(counts[name] for name in GATE_NAMES)


def enumerate_candidates(
    lengths: Iterable[int], epsilon: float, delta: float
) -> tuple[list[Candidate], dict[tuple[int, ...], list[Candidate]], int]:
    retentions = gate_retentions(epsilon, delta)
    candidates: list[Candidate] = []
    groups: dict[tuple[int, ...], list[Candidate]] = defaultdict(list)
    enumerated = 0
    for length in lengths:
        for sequence in product(GATE_NAMES, repeat=length):
            enumerated += 1
            if not is_identity_up_to_phase(compose(sequence)):
                continue
            candidate = Candidate(
                sequence=sequence,
                counts=count_key(sequence),
                p0=p0_for_sequence(sequence, epsilon, delta),
                declared_p0=declared_identity_p0(sequence, retentions),
            )
            candidates.append(candidate)
            groups[candidate.counts].append(candidate)
    useful_groups = {key: value for key, value in groups.items() if len(value) >= 2}
    return candidates, useful_groups, enumerated


def exhaustive_witness(groups: dict[tuple[int, ...], list[Candidate]]) -> Witness:
    best: Witness | None = None
    for members in groups.values():
        low = min(members, key=lambda item: item.p0)
        high = max(members, key=lambda item: item.p0)
        witness = Witness(high=high, low=low, gap=high.p0 - low.p0)
        if best is None or witness.gap > best.gap:
            best = witness
    if best is None:
        raise RuntimeError("no matched candidate pair exists")
    return best


def matched_pair_count(groups: dict[tuple[int, ...], list[Candidate]]) -> int:
    return sum(len(items) * (len(items) - 1) // 2 for items in groups.values())


def cyclic_shift_witness(candidates: Sequence[Candidate]) -> Witness:
    lookup = {candidate.sequence: candidate for candidate in candidates}
    best: Witness | None = None
    for candidate in candidates:
        sequence = candidate.sequence
        for shift in range(1, len(sequence)):
            shifted = sequence[shift:] + sequence[:shift]
            other = lookup.get(shifted)
            if other is None:
                continue
            high, low = (candidate, other) if candidate.p0 >= other.p0 else (other, candidate)
            witness = Witness(high=high, low=low, gap=high.p0 - low.p0)
            if best is None or witness.gap > best.gap:
                best = witness
    if best is None:
        raise RuntimeError("no cyclic-shift candidate pair exists")
    return best


def process_model_residual(sequence: Sequence[str], epsilon: float, delta: float) -> float:
    actual = compose(sequence, epsilon=epsilon, delta=delta)
    ideal = compose(sequence)
    actual_fidelity = average_gate_fidelity(actual, ideal)
    retention = 1.0
    for name in sequence:
        retention *= gate_retentions(epsilon, delta)[name]
    declared_fidelity = 0.5 * (1.0 + retention)
    return abs(actual_fidelity - declared_fidelity)


def gst_like_germ_baseline(
    epsilon: float, delta: float, max_word: int = 3, max_length: int = 8
) -> dict[str, object]:
    best_sequence: tuple[str, ...] = ()
    best_germ: tuple[str, ...] = ()
    best_residual = -1.0
    circuits: set[tuple[str, ...]] = set()
    for word_length in range(1, max_word + 1):
        for germ in product(GATE_NAMES, repeat=word_length):
            for repetitions in range(1, max_length // word_length + 1):
                sequence = germ * repetitions
                circuits.add(sequence)
                residual = process_model_residual(sequence, epsilon, delta)
                if residual > best_residual:
                    best_residual = residual
                    best_sequence = sequence
                    best_germ = germ
    return {
        "circuit_count": len(circuits),
        "best_germ": list(best_germ),
        "best_sequence": list(best_sequence),
        "max_process_fidelity_residual": best_residual,
    }


def evaluate_witness(witness: Witness, epsilon: float, delta: float) -> dict[str, float | bool]:
    high = p0_for_sequence(witness.high.sequence, epsilon, delta)
    low = p0_for_sequence(witness.low.sequence, epsilon, delta)
    signed_gap = high - low
    return {
        "high_p0": high,
        "low_p0": low,
        "signed_gap": signed_gap,
        "absolute_gap": abs(signed_gap),
        "same_order": signed_gap > 0.0,
    }


def validate_matching(witness: Witness) -> dict[str, bool]:
    high = witness.high
    low = witness.low
    return {
        "same_length": len(high.sequence) == len(low.sequence),
        "same_gate_multiset": high.counts == low.counts,
        "high_ideal_identity": is_identity_up_to_phase(compose(high.sequence)),
        "low_ideal_identity": is_identity_up_to_phase(compose(low.sequence)),
        "same_declared_prediction": abs(high.declared_p0 - low.declared_p0) <= 1e-12,
        "same_width": True,
        "same_sequential_depth": True,
        "same_topology_exposure": True,
    }
