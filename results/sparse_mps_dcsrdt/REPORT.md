# Sparse-MPS DCS-RDT constructibility report

## Verdict

The frozen promotion protocol is **closed (0/4)**, so the 18/24-qubit
large transfer stage was not run. The failure is caused by an over-tight
cross-backend identity tolerance, not by the sparse-MPS contraction algebra.
This distinction is diagnostic only and does not retroactively change the
prespecified verdict.

## Frozen development rows

| case | ordering | direct gap | trace difference | operator difference | same-MPS identity | pass |
|---|---|---:|---:|---:|---:|:---:|
| chesapeake | sorted | -0.134213592 | 1.88e-10 | 3.33e-10 | 1.13e-16 | no |
| chesapeake | spectral | -0.134213592 | 2.84e-10 | 3.08e-10 | 2.00e-17 | no |
| football | sorted | +0.019268875 | 8.09e-11 | 1.76e-10 | 5.65e-17 | no |
| football | spectral | +0.019268875 | 8.73e-11 | 3.79e-10 | 1.67e-16 | no |

The protocol required `<1e-12` trace difference and `<1e-10` operator
difference against the archived dense trajectory. Observed cross-backend
differences were `8.09e-11`--`2.84e-10`
and `1.76e-10`--`3.79e-10`.
All runs had zero truncations, unit norm, and zero accumulated-angle error.

When the dense operator is reconstructed from the *same returned MPS*,
the direct sparse contraction agrees within `2.00e-17`--
`1.67e-16`. This validates the implementation identity
and locates the larger discrepancy in independent simulator trajectories.
The repository's previously calibrated numerical simulation allowance is
`1e-7`, but substituting it after observing this result would be retuning.

## Algorithm retained from the kill test

The implementation never requests a full statevector or `2^n` BKS mask.
For the frozen unit-weight MIS scorers it enumerates the BKS support through
independent-set backtracking, groups support strings by their right half,
queries only the required MPS left slices, and accumulates the open
decision-conditioned operator. The local spectral tail composes with
RankCert as `epsilon_A+epsilon_B+tail+2e-7`.

These properties are theorem/unit-test results, not evidence that the large
benchmark passed. A future replication may freeze a same-trajectory identity
test plus a separately calibrated backend-equivalence tolerance, but must be
reported as a new protocol rather than a repair of this one.

## Separately frozen calibrated replication

After closing the primary result, a new protocol used the pre-existing
RankCert `1e-7` numerical allowance and then opened the untouched 18/24-qubit
cohort. It also failed `0/4`.

| case | ordering | archive gap error | storage reduction | combined bound | pass |
|---|---|---:|---:|---:|:---:|
| ibm32 | sorted | 1.30e-03 | 6.83x | 2.000 | no |
| ibm32 | spectral | 7.23e-04 | 9.61x | 2.000 | no |
| aves-sparrow-social | sorted | 4.35e-04 | 1581.67x | 2.000 | no |
| aves-sparrow-social | spectral | 5.26e-04 | 2067.62x | 2.000 | no |

All archived-gap discrepancies (`4.35e-4`--`1.30e-3`) exceed the calibrated
tolerance. The inherited accumulated-angle bound saturates at `2.0` on every
row, so no ideal-gap sign is certified. The 18-qubit rows save only
6.83x--9.61x and miss the frozen 10x storage criterion; the 24-qubit rows
save over 1500x but still fail reproducibility and certification.

## Snapshot-semantics diagnosis

On `ibm32/sorted`, a fresh `save_statevector` run reproduces the archived
probabilities within `1.1e-15`, while `save_matrix_product_state` changes the
two schedule probabilities by `8.01e-4` and `2.10e-3`. The resulting gap
changes by `0.001301`. Thus the large mismatch is
specific to the terminal MPS snapshot/export path under truncation, not the
sparse support contraction. Exported MPS tensors cannot be treated as
semantically interchangeable with statevector readout from the same Aer MPS
configuration without a separate calibration.
