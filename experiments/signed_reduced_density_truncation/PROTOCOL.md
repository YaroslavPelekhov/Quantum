# Frozen SRDT protocol

Date frozen: 2026-08-22.

## Claims tested

1. The synthetic pure-state family has constant signed rank two while the
   Schmidt rank required for 0.99 fidelity grows exponentially in half-system
   qubits.
2. On the frozen `ibm32` and `aves-sparrow-social` exact terminal states,
   absolute-eigenvalue truncation is compared with the conventional
   state-averaged subspace at exactly the same retained dimension.

## Frozen data and grid

- Methods: `published_lr` versus `prior_matched_random`.
- Orderings: `sorted`, `spectral`.
- Cuts: 3, 5, 7, and `min(9,n/2)`.
- Retained dimensions: 2, 4, 8, 16, 32, 64 where feasible.
- Synthetic: half-system sizes 2 through 8 qubits, `epsilon=0.1`, fidelity
  target 0.99.

## Go/no-go

- The theorem/separation survives only if all numerical identities pass and
  the exact signed rank remains two throughout the synthetic ladder.
- A real-data efficiency claim requires SRDT trace-norm error to be at least
  2x smaller than the state-averaged-basis contrast error at one fixed rank on
  both orderings of a case.
- Failure of that empirical criterion is reported as a failed transfer, not
  hidden by the synthetic theorem.
