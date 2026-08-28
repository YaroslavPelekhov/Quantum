# Calibrated sparse-MPS DCS-RDT replication protocol

Frozen on 2026-08-24 after closing, and without altering, the primary 0/4
constructibility protocol. The large 18/24-qubit stage had not been executed.

## Calibration boundary

The primary small-case comparison mixed an Aer MPS trajectory with archived
dense trajectories and used `1e-10`/`1e-12` tolerances. Same-MPS reconstruction
validated the contraction at `1.67e-16`, while the independent trajectories
differed by at most `3.79e-10`. This replication uses the pre-existing RankCert
numerical simulation allowance `1e-7`; it does not relabel the primary failure.

## Untouched held-out cohort

- cases: `ibm32`, `aves-sparrow-social`;
- orderings: sorted and spectral;
- pair: `published_lr` versus `prior_matched_random`;
- Aer MPS: bond 128, cutoff `1e-4`;
- spatial cut 5, DCS rank 8;
- direct sparse support enumeration; no statevector and no `2^n` event mask.

## Criteria

Support requires all four rows to reproduce independently archived deterministic
MPS BKS gaps within `1e-7` and reduce resident representation bytes by at least
10x relative to two dense complex statevectors. The combined ideal-gap bound
`epsilon_A+epsilon_B+DCS_tail+2e-7` is reported independently. Certificate
saturation is an abstention, not a constructibility failure. No retuning follows.
