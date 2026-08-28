# Frozen sparse-MPS DCS-RDT constructibility protocol

Frozen before executing either stage: 2026-08-24.

## Algorithm

Aer produces a terminal MPS without a statevector. The frozen MIS scorer is
converted directly into its sparse BKS support by independent-set backtracking;
no `2^n` truth table is created. For each distinct right configuration in the
support, query the MPS amplitudes of its `2^cut` left completions and accumulate

`K_L = Tr_R((E Gamma + Gamma E)/2)`.

Only the MPS tensors, one left slice, the sparse support, and the `2^cut` square
output are resident. The rank-k spectral tail of the MPS-built operator is then
combined with the existing accumulated-angle certificate:

`ideal gap error <= epsilon_A + epsilon_B + DCS_tail + 2e-7`.

## Frozen stages

Development identity stage:

- cases `chesapeake` and `football`, both orderings;
- exact Aer MPS (`bond=128`, cutoff 0), cut 3;
- direct MPS operator must match the dense operator within `1e-10` in Frobenius
  norm, its trace within `1e-12`, and sparse support must match the scorer.

Large transfer/constructibility stage:

- cases `ibm32` and `aves-sparrow-social`, both orderings;
- pair `published_lr` versus `prior_matched_random`;
- Aer MPS `bond=128`, cutoff `1e-4`, cut 5, DCS rank 8;
- no statevector or full BKS truth table may be requested;
- direct trace must reproduce the independently archived deterministic MPS BKS
  gap within `1e-8` on all four rows;
- serialized MPS storage plus the open operator must be at least 10x smaller
  than two dense complex statevectors on every row.

Ideal-gap sign certification is secondary. Saturation of the inherited MPS
certificate is reported as abstention and does not invalidate constructibility.
No bond, cutoff, cut, or rank retuning follows either result.
