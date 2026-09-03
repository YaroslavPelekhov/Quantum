"""Construct explicit six-qubit commuting-context covers of Pauli profiles."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch
from scipy.optimize import linprog
from scipy.sparse import hstack

from n6_oracle import N6Oracle
from run_n6_adversarial import PauliTransform


def separate_contexts(oracle: N6Oracle, witness, batch=240_000, topk=256):
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contexts", type=Path, required=True)
    parser.add_argument("--exponent", type=float, default=3.0)
    parser.add_argument("--near-angle", type=float)
    parser.add_argument("--seed", type=int, default=660080)
    parser.add_argument("--certificate", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    rng = np.random.default_rng(args.seed)
    if args.near_angle is None:
        state = rng.normal(size=64) + 1j * rng.normal(size=64)
    else:
        origin = np.zeros(64, dtype=np.complex128)
        origin[0] = 1.0
        direction = rng.normal(size=64) + 1j * rng.normal(size=64)
        direction -= origin * np.vdot(origin, direction)
        direction /= np.linalg.norm(direction)
        state = np.cos(args.near_angle) * origin + np.sin(args.near_angle) * direction
    state /= np.linalg.norm(state)
    target = np.abs(PauliTransform.cpu_expectations(state)) ** args.exponent
    oracle = N6Oracle(args.contexts)
    contexts = [1]
    contexts.extend(map(int, rng.choice(len(oracle.contexts), size=127, replace=False)))
    seen = set(contexts)
    matrix = oracle.incidence(contexts)
    bound = 10.0
    started = time.time()
    rounds = []
    for round_index in range(160):
        dual = linprog(
            -target,
            A_ub=matrix.T,
            b_ub=np.ones(matrix.shape[1]),
            bounds=[(0.0, bound)] * len(target),
            method="highs-ipm",
            options={"dual_feasibility_tolerance": 1e-9},
        )
        if not dual.success:
            raise RuntimeError(dual.message)
        witness = dual.x
        top = separate_contexts(oracle, witness)
        objective = float(np.dot(witness, target))
        support = top[0][0]
        rounds.append(
            {
                "round": round_index,
                "constraints": matrix.shape[1],
                "restricted_dual": objective,
                "global_support": support,
            }
        )
        if objective < 0.999:
            if np.max(witness) >= 0.999999 * bound:
                bound *= 10.0
                continue
            break
        new_contexts = []
        for _, context in top:
            if context not in seen:
                seen.add(context)
                new_contexts.append(context)
        if not new_contexts:
            raise RuntimeError("separator returned no new context")
        contexts.extend(new_contexts)
        matrix = hstack([matrix, oracle.incidence(new_contexts)], format="csc")
    else:
        raise RuntimeError("round limit reached")

    primal = linprog(
        np.ones(matrix.shape[1]),
        A_ub=-matrix,
        b_ub=-target,
        bounds=(0, None),
        method="highs",
        options={
            "dual_feasibility_tolerance": 1e-9,
            "primal_feasibility_tolerance": 1e-9,
        },
    )
    if not primal.success:
        raise RuntimeError(primal.message)
    cover = matrix @ primal.x
    deficits = np.maximum(target - cover, 0.0)
    # Each Pauli extends to a maximal commuting context.  Adding one such
    # context with the corresponding deficit proves this conservative strict
    # upper bound even when the floating LP has tiny negative slacks.
    corrected_weight = float(primal.fun + deficits.sum())
    nonzero = np.flatnonzero(primal.x > 1e-11)
    args.certificate.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        args.certificate,
        state=state,
        target=target,
        contexts=np.asarray([contexts[index] for index in nonzero]),
        weights=primal.x[nonzero],
        exponent=args.exponent,
    )
    payload = {
        "status": "strict_cover" if corrected_weight < 1.0 else "not_certified",
        "qubits": 6,
        "exponent": args.exponent,
        "near_angle": args.near_angle,
        "seed": args.seed,
        "raw_cover_weight": float(primal.fun),
        "minimum_slack": float(np.min(cover - target)),
        "total_deficit_correction": float(deficits.sum()),
        "corrected_cover_weight": corrected_weight,
        "nonzero_contexts": len(nonzero),
        "seconds": time.time() - started,
        "rounds": rounds,
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
