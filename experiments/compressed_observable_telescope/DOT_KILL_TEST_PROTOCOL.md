# Frozen DOT-MPS local kill-test protocol

Frozen before evaluating any goal-aware Schmidt subset on the primary test.

## Primary test

- Case: real QOBLIB `ibm32`, 18 qubits, `confirm/sorted`.
- Schedule: `published_lr`.
- Checkpoint position: 502 (native operation count 1010).
- Bipartition: qubits 0-10 versus 11-17 (`cut=11`).
- Primary rank: `chi=40`, matching the retained bond reported by the real Aer
  event at instruction 501 on the cut between logical qubits 10 and 11.
- Secondary rank profile: 8, 16, 32, and 64.

The input is the exact unitary image of the preceding frozen approximate MPS
checkpoint, immediately before the checkpoint truncation error. The objective
is the exact backward BKS observable at checkpoint 502.

## Compared rules

1. Standard: retain the top-`chi` Schmidt coefficients.
2. Goal-aware subset: retain exactly `chi` Schmidt pairs chosen by deterministic
   multi-start one-swap local search to minimize absolute BKS error after
   normalization.

The goal-aware search is a constructive heuristic, not a proof of global
subset optimality and not yet an arbitrary rank-`chi` subspace optimizer.

## Frozen success criterion

The primary test supports the DOT direction if, at `chi=40`, the constructed
goal-aware subset has at least 10x smaller absolute BKS error than top-Schmidt
while using the same rank. The strongest desired outcome additionally has no
better state fidelity than top-Schmidt, demonstrating that fidelity and
decision accuracy prefer different truncations.

All ranks, unsuccessful starts, mode overlap, fidelity, discarded mass, BKS
errors, and deterministic seeds must be retained. No simulator-wide claim may
be made from this single local test.
