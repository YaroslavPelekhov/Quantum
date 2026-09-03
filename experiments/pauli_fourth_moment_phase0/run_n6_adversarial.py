"""Adversarial six-qubit tests with an exhaustive stabilizer/context oracle."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch

from n6_oracle import N6Oracle


class PauliTransform:
    def __init__(self, device: str = "cuda") -> None:
        self.device = torch.device(device)
        dimension = 64
        permutation = np.asarray(
            [[basis ^ x for basis in range(dimension)] for x in range(dimension)],
            dtype=np.int64,
        )
        hadamard = np.asarray(
            [
                [1 - 2 * ((basis & z).bit_count() & 1) for basis in range(dimension)]
                for z in range(dimension)
            ],
            dtype=np.float32,
        )
        phases = np.asarray(
            [[(1j) ** ((x & z).bit_count()) for z in range(dimension)] for x in range(dimension)],
            dtype=np.complex64,
        )
        self.permutation = torch.tensor(permutation, device=self.device)
        self.hadamard = torch.tensor(hadamard, dtype=torch.complex64, device=self.device)
        self.phases = torch.tensor(phases, dtype=torch.complex64, device=self.device)

    def expectations(self, states: torch.Tensor) -> torch.Tensor:
        correlations = torch.conj(states[:, self.permutation]) * states[:, None, :]
        values = (correlations @ self.hadamard.T) * self.phases[None, :, :]
        return values.real.permute(0, 2, 1).reshape(len(states), 4096)[:, 1:]

    @staticmethod
    def cpu_expectations(state: np.ndarray) -> np.ndarray:
        output = np.empty(4095)
        for label in range(1, 4096):
            x, z = label & 63, label >> 6
            phase = (1j) ** ((x & z).bit_count())
            output[label - 1] = sum(
                np.conj(state[basis ^ x])
                * phase
                * (-1 if (basis & z).bit_count() & 1 else 1)
                * state[basis]
                for basis in range(64)
            ).real
        return output


def apply_pauli(label: int, state: np.ndarray) -> np.ndarray:
    x, z = label & 63, label >> 6
    phase = (1j) ** ((x & z).bit_count())
    output = np.empty(64, dtype=complex)
    for basis in range(64):
        output[basis ^ x] = (
            phase * (-1 if (basis & z).bit_count() & 1 else 1) * state[basis]
        )
    return output


def stabilizer_state(oracle: N6Oracle, context: int, eigenmask: int, rng) -> np.ndarray:
    basis = np.asarray(oracle.contexts[context], dtype=int)
    state = rng.normal(size=64) + 1j * rng.normal(size=64)
    state /= np.linalg.norm(state)
    for index, label in enumerate(basis):
        eigenvalue = -1 if (eigenmask >> index) & 1 else 1
        state = state + eigenvalue * apply_pauli(int(label), state)
        state /= np.linalg.norm(state)
    return state


def separate_contexts(oracle: N6Oracle, witness, batch=240_000, topk=32):
    padded = torch.zeros(4096, dtype=torch.float64, device=oracle.device)
    padded[1:] = torch.as_tensor(np.asarray(witness, dtype=np.float64), device=oracle.device)
    best = []
    for low in range(0, len(oracle.contexts), batch):
        high = min(low + batch, len(oracle.contexts))
        bases = torch.from_numpy(
            np.asarray(oracle.contexts[low:high], dtype=np.int64)
        ).to(oracle.device)
        labels, _ = oracle.expand_contexts(bases)
        scores = padded[labels[:, 1:]].sum(1)
        count = min(topk, len(scores))
        values, indices = torch.topk(scores, count)
        best.extend(
            (float(value), low + int(index))
            for value, index in zip(values.cpu().numpy(), indices.cpu().numpy())
        )
        best = sorted(best, reverse=True)[:topk]
    return best


def optimize(mode, witness, seed_states, transform, rng, starts, steps):
    scales = (1e-4, 1e-3, 1e-2, 0.05, 0.2, 0.5)
    if mode == "triple":
        initial = []
        for state in seed_states:
            initial.append((state, state, state))
        while len(initial) < starts:
            triple = []
            for _ in range(3):
                state = rng.normal(size=64) + 1j * rng.normal(size=64)
                triple.append(state / np.linalg.norm(state))
            initial.append(tuple(triple))
        for index in range(min(72, starts - len(seed_states))):
            base = seed_states[index % len(seed_states)]
            triple = []
            for _ in range(3):
                state = base + scales[index % len(scales)] * (
                    rng.normal(size=64) + 1j * rng.normal(size=64)
                )
                triple.append(state / np.linalg.norm(state))
            initial[-1 - index] = tuple(triple)
        initial = np.asarray(initial)
    else:
        initial = list(seed_states)
        while len(initial) < starts:
            state = rng.normal(size=64) + 1j * rng.normal(size=64)
            initial.append(state / np.linalg.norm(state))
        for index in range(min(96, starts - len(seed_states))):
            base = seed_states[index % len(seed_states)]
            state = base + scales[index % len(scales)] * (
                rng.normal(size=64) + 1j * rng.normal(size=64)
            )
            initial[-1 - index] = state / np.linalg.norm(state)
        initial = np.asarray(initial)
    real = torch.nn.Parameter(torch.tensor(initial.real, dtype=torch.float32, device=transform.device))
    imag = torch.nn.Parameter(torch.tensor(initial.imag, dtype=torch.float32, device=transform.device))
    weights = torch.tensor(witness, dtype=torch.float32, device=transform.device)
    optimizer = torch.optim.Adam([real, imag], lr=0.025)
    best = (-np.inf, None)
    for step in range(steps):
        optimizer.zero_grad(set_to_none=True)
        states = torch.complex(real, imag)
        states = states / torch.linalg.vector_norm(states, dim=-1, keepdim=True)
        if mode == "triple":
            profiles = [transform.expectations(states[:, index, :]) for index in range(3)]
            values = (profiles[0] * profiles[1] * profiles[2] * weights).sum(1)
        else:
            profile = transform.expectations(states)
            if mode == "p4":
                values = (profile.pow(4) * weights).sum(1)
            else:
                squares = profile.square()
                values = squares.max(1).values * (squares * weights).sum(1)
        (-values.sum()).backward()
        optimizer.step()
        if step in (750, 1400, 1900):
            for group in optimizer.param_groups:
                group["lr"] *= 0.2
        if step % 100 == 0 or step == steps - 1:
            index = int(torch.argmax(values))
            if float(values[index]) > best[0]:
                best = (float(values[index]), states[index].detach().cpu().numpy())
    states = np.asarray(best[1], dtype=np.complex128)
    states /= np.linalg.norm(states, axis=-1, keepdims=True)
    if mode == "triple":
        profiles = [transform.cpu_expectations(state) for state in states]
        value = float(np.dot(witness, np.prod(profiles, axis=0)))
    else:
        profile = transform.cpu_expectations(states)
        value = (
            float(np.dot(witness, profile**4))
            if mode == "p4"
            else float(np.max(profile**2) * np.dot(witness, profile**2))
        )
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contexts", type=Path, required=True)
    parser.add_argument("--mode", choices=("p4", "triple", "shortcut"), required=True)
    parser.add_argument("--witnesses", type=int, default=30)
    parser.add_argument("--starts", type=int, default=160)
    parser.add_argument("--steps", type=int, default=2200)
    parser.add_argument("--seed", type=int, default=660103)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rng = np.random.default_rng(args.seed)
    oracle = N6Oracle(args.contexts)
    transform = PauliTransform()
    rows = []
    started = time.time()
    for index in range(args.witnesses):
        signed = args.mode == "triple"
        witness = np.zeros(4095)
        if index < args.witnesses // 2:
            witness[:] = rng.normal(size=4095) if signed else rng.exponential(size=4095)
        else:
            chosen = rng.choice(4095, size=int(rng.integers(20, 700)), replace=False)
            witness[chosen] = rng.normal(size=len(chosen)) if signed else rng.exponential(size=len(chosen))
        if signed:
            top = oracle.separate(witness, topk=32)
            support = max(
                float(np.dot(witness, oracle.column(context, eigenmask)))
                for _, context, eigenmask in top
            )
            seeds = [stabilizer_state(oracle, context, eigenmask, rng) for _, context, eigenmask in top[:12]]
        else:
            top = separate_contexts(oracle, witness)
            support = top[0][0]
            seeds = [stabilizer_state(oracle, context, 0, rng) for _, context in top[:16]]
        witness /= support
        value = optimize(args.mode, witness, seeds, transform, rng, args.starts, args.steps)
        row = {"index": index, "support_normalized_maximum": value, "margin": value - 1.0}
        rows.append(row)
        print(row, flush=True)
        if value > 1.00001:
            break
    payload = {
        "mode": args.mode,
        "contexts": len(oracle.contexts),
        "stabilizer_vertices": len(oracle.contexts) * 64,
        "seed": args.seed,
        "status": "counterexample" if rows[-1]["margin"] > 1e-5 else "no_violation",
        "best": max(row["support_normalized_maximum"] for row in rows),
        "seconds": time.time() - started,
        "rows": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
