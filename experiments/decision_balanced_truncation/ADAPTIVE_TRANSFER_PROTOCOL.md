# Adaptive decision-balanced schedule-pair transfer

Frozen before evaluating the `prior_evolutionary` pair: 2026-08-23.

## Fixed policy

- Reachability/observability and oblique Petrov--Galerkin construction are
  exactly those in `PROTOCOL.md`.
- Cut: 4 high-order qubits.
- QAOA depth: 15.
- At each gate, choose the smallest integer rank in `1..8` capturing at least
  99% of squared Hankel singular-value energy.
- The state-averaged baseline receives the exact same per-gate rank schedule.
- No signed regularizer and no parameter retuning.

## Held-out dimension

The exploratory adaptive run used `published_lr` versus
`prior_matched_random`.  This transfer uses the uninspected pair
`published_lr` versus `prior_evolutionary` on the same three expanded-QOBLIB
graphs and both frozen orderings, for six rows total.

This is schedule-pair transfer, not graph-level validation.  Graph-level
validation is unavailable to the dense oracle because the untouched reachable
kernels have 45 and 55 qubits.

## Success criterion

Decision-balanced truncation must have the exact sign and strictly lower
absolute Delta error than the equal-rank-schedule state-averaged baseline on
all six rows.  Any failure closes the universal schedule-pair-transfer claim.
