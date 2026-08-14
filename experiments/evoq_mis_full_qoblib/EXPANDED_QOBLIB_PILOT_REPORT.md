# Expanded QOBLIB Aer pilot report

The frozen pilot completed all 18 exact statevector references and all 108
seeded Aer MPS jobs on the three new screen-selected cases.  It contains
54,000 shots and no failed or dropped jobs.  All 32 project tests pass after
adding the pilot integrity tests.

## Primary result

All 24/24 MPS candidate-vs-`published_lr` cohorts preserved the exact BKS-rate
effect sign across two candidates, two orderings, and two MPS settings.  The
largest absolute effect error was 0.08199.

| Case | Candidate | Exact BKS effect | Sign-correct MPS cohorts |
|---|---|---:|---:|
| es60fst01 | prior evolutionary | +0.26638 | 4/4 |
| es60fst01 | prior matched random | +0.24288 | 4/4 |
| es60fst03 | prior evolutionary | +0.23517 | 4/4 |
| es60fst03 | prior matched random | +0.21947 | 4/4 |
| mammalia-kangaroo-interactions | prior evolutionary | +0.14865 | 4/4 |
| mammalia-kangaroo-interactions | prior matched random | -0.26949 | 4/4 |

The exact effects are ordering-invariant, as required by relabeling
equivalence.  The negative matched-random effect on the mammalia case is a
useful nontrivial control: sign preservation is not caused by all transferred
schedules uniformly beating the published schedule.

## Safety observation

The minimum recorded available physical memory before an MPS job was 11.55
GiB; maximum runner RSS was 0.147 GiB.  Simulations were sequential with
one-thread BLAS/OpenMP limits and an 8-GiB safety stop.

## Interpretation

This pilot strengthens cross-instance validity from five to eight rigorously
eligible QOBLIB cases, but it does not add a third independent simulator or
real-QPU evidence.  The next registered stage should export the 18 new
circuits to cuTensorNet and, separately, prepare a small hardware/noise-aware
subset once QPU credentials and quota are available.
