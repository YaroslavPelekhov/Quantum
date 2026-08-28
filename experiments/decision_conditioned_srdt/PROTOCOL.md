# Frozen decision-conditioned SRDT protocol

Frozen before executing the new operator benchmark: 2026-08-24.

## Construction

For a paired pure-state contrast
`Gamma = |B><B| - |A><A|`, a Hermitian decision effect `0 <= E <= I`,
and a spatial split `L|R`, define

`K_L(E,Gamma) = Tr_R((E Gamma + Gamma E) / 2)`.

The construction must satisfy:

1. `K_L` is Hermitian and `Tr(K_L) = Tr(E Gamma)`;
2. for `E = I`, `K_L` reduces exactly to the original SRDT operator
   `rho_L^B - rho_L^A`;
3. retaining the `k` eigenmodes of `K_L` with largest absolute eigenvalues
   minimizes every Schatten-norm residual, and the discarded absolute sum is
   an a posteriori bound on the global decision-gap error.

The equal-rank controls project `K_L` into either the original SRDT basis
(absolute eigenmodes of `rho_L^B-rho_L^A`) or the state-averaged basis
(leading eigenmodes of `(rho_L^A+rho_L^B)/2`).

## Frozen cohorts

- Pair: `published_lr` versus `prior_matched_random`.
- Decision effect: the exact frozen BKS projector encoded by each scorer.
- Orderings: sorted and spectral.
- Development cases: `ibm32`, `aves-sparrow-social`, cut 5, ranks 1,2,4,8,16.
- Held-out cases: `chesapeake`, `football`, cut 3, ranks 1,2,4.
- Fixed comparison rank: 8 for development and 4 for held-out.

## Go/no-go

Development promotion requires all algebraic identities to pass, strictly
smaller rank-8 trace-norm residual than both equal-rank controls on all four
rows, and a geometric-mean improvement of at least 2x against each control.

Only if development passes is the held-out cohort executed. Transfer support
requires a strictly smaller rank-4 residual than both controls on all four
held-out rows. Sign-certification ranks and actual gap errors are secondary
descriptive outcomes and are never used for retuning.

The dense exact-state and exact-projector implementation is a feasibility
oracle. It carries no scalable-construction claim.
