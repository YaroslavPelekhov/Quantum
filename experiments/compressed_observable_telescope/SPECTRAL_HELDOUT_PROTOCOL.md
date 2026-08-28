# Frozen spectral-ordering held-out protocol

Frozen before inspecting any residual-aware COT result on the spectral
ordering. The sorted-ordering design and all thresholds are carried over
without tuning.

## Frozen inputs

- QOBLIB case: `ibm32`, 18 reduced qubits, depth 15.
- Forward setting: `confirm`, Aer MPS bond 128, cutoff `1e-4`.
- Competing schedules: `published_lr` and `prior_matched_random`.
- Held-out axis: `spectral` qubit ordering.
- Checkpoints: every native two-qubit gate plus terminal tail.

## Frozen backward construction

Primary bond by checkpoint position:

- 512-555: 64
- 448-511: 128
- 384-447: 256
- 320-383: 384
- 1-319: 512

Residual witness bonds: 128, 256, and 512. No boundary or bond may be changed
after the first spectral result is observed.

## Primary endpoint

For each residual bond, compute the complete paired bound

`sum_(method,t) (|Tr(Otilde_t Delta rho_t)| + 2 sqrt(w_t) eta_t)`.

The held-out ordering is certified only if this width is strictly below the
absolute frozen MPS MR-LR gap and its sign agrees with the exact reference.
The prespecified headline test is residual bond 256. Bond 128 is the
prespecified lower-resource control; bond 512 separates residual-compression
loss from primary-observable loss.

## Scope

This is a held-out ordering test, not an independent-graph test. Success may
support robustness to tensor-network ordering, but cannot establish
cross-instance scaling.
