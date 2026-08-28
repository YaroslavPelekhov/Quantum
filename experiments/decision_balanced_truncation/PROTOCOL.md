# Decision-balanced truncation prospective protocol

Frozen before running the expanded-QOBLIB cohort: 2026-08-23.

## Algorithm

At every paired logical gate and a fixed spatial cut, construct:

- the forward reachability Gramian `R_t=(rho_A,t+rho_B,t)/2`;
- the backward decision observability Gramian `Q_t`, obtained from the exact
  backward images of every BKS-support basis vector for both circuit suffixes.

Let `X=R_t^(1/2)`, `Y=Q_t^(1/2)` and
`Y^dagger X = U Sigma V^dagger`.  The retained Petrov--Galerkin factors are

`V_r = X V_k Sigma_k^(-1/2)`,
`W_r = Y U_k Sigma_k^(-1/2)`,

so `W_r^dagger V_r=I`.  The forward states are reduced by the oblique projector
`P_t=V_r W_r^dagger` and normalized before the next gate.

## Frozen comparison

- Cases: `es60fst01`, `es60fst03`, `mammalia-kangaroo-interactions`.
- Orderings: `sorted`, `spectral`.
- Schedule pair: `published_lr` versus `prior_matched_random`.
- QAOA depth: 15.
- Cut: 4 high-order qubits versus the remainder.
- Retained rank: 2.
- Baseline: rank-2 orthogonal projection onto the leading eigenvectors of `R_t`.
- Candidate has no tuned signed regularizer (`alpha=0`).

The cohort was not used by the preceding 7q exploration.

## Success criterion

On all six case/order rows, decision-balanced truncation must:

1. reproduce the exact sign of the BKS probability difference; and
2. have strictly smaller absolute Delta error than state averaging.

Any failure closes the universal fixed-policy claim.  Partial coverage remains
descriptive and cannot be promoted to the primary result.

Dense state and backward-vector batches are an oracle implementation for this
kill test, not a scalable MPS implementation.
