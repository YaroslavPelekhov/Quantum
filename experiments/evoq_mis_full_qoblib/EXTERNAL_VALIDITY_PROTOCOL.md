# Frozen external-validity protocol

Frozen on 2026-08-07 before any external-cohort QAOA result was generated.

## Question

Does the resource-aware conclusion obtained on the `es60fst` family transfer
to structurally different QOBLIB maximum-independent-set families, and how
often does the apparent ranking of fixed QAOA schedules depend on the fidelity
of a matrix-product-state simulator?

No schedule, depth, ordering, reduction cap, seed, shot budget, acceptance
threshold, or cohort membership may be changed after the first QAOA result.

## Frozen methods

All schedules were selected before this external cycle and are evaluated at
the published depth `p=15` without tuning:

1. published linear ramp: `(0.7, 0.4, 1.0, 1.0)`;
2. prior evolutionary schedule:
   `(0.5175030726816078, 0.7719741612274684,
   1.0773373543262421, 1.7543477389249704)`;
3. prior matched-random schedule:
   `(0.6424738670407446, 0.7593921349176262,
   1.776791693083474, 0.9917239502490107)`.

The first method is the reference. Both `sorted` and graph-spectral qubit
orderings are tested. Constraint repair is disabled; only native feasible
samples decoded to the original graph are scored.

## External cohorts

The quantum cohort is stratified by graph source and kernel scale. Each listed
cap was fixed only after exact HiGHS certification that the reduced optimum
decodes to the repository BKS and that the quantum kernel is non-empty.

| Tier | Instance | BKS | Cap | Qubits | Reduced edges |
|---|---|---:|---:|---:|---:|
| core | aves-sparrow-social | 13 | 20 | 24 | 59 |
| core | chesapeake | 17 | 12 | 7 | 14 |
| core | football | 16 | 10 | 7 | 11 |
| core | ibm32 | 13 | 8 | 18 | 37 |
| core | johnson8-2-4 | 7 | 16 | 28 | 210 |
| core | karate | 20 | 4 | 3 | 3 |
| scale | hamming6-4 | 12 | 24 | 64 | 704 |
| scale | sloane_1dc_64 | 10 | 24 | 64 | 543 |

The boundary cohort (`C125-9`, `c-fat200-1`, `gen200_p0-9_44`,
`sloane_1dc_128`, `sloane_1zc_128`, and `brock200-2`) is audited for exact
reachability and required kernel size, but is not silently substituted into
the quantum cohort if it exceeds the frozen 64-qubit execution boundary.

## Simulator fidelities and budgets

Two Aer MPS settings are mandatory:

- released: maximum bond dimension 64, truncation cutoff `1e-3`;
- confirmation: maximum bond dimension 128, cutoff `1e-4`.

Core cohort: all three schedules, both orderings, both fidelities, five paired
seeds (`31001`--`31005`), and 500 shots per job: 360 jobs and 180,000 shots.

Scale cohort: published linear and prior matched-random schedules, both
orderings, both fidelities, three paired seeds (`32001`--`32003`), and 250
shots per job: 48 jobs and 12,000 shots.

For the four core kernels with at most 18 qubits (`chesapeake`, `football`,
`ibm32`, and `karate`), exact statevector probabilities are computed for all
three schedules. These results audit MPS bias independently of sampling noise.

## Outcomes and statistics

Primary outcomes are native BKS hit rate, BKS-minus-one rate, and feasible
rate. Secondary outcomes are feasible conditional mean size, circuit depth,
RZZ count, and wall-clock time.

Comparisons are paired by instance, seed, ordering, and simulator fidelity.
The principal estimand is matched-random minus published-linear BKS rate.
A fidelity reversal is declared when the sign of this estimand differs between
released and confirmation MPS. Exact-cohort agreement is reported separately.
Paired bootstrap confidence intervals use 50,000 resamples; two-sided exact
sign-flip tests are reported when the number of pairs permits enumeration.

The previous resource-acceptance gate is retained: lower 95% confidence bounds
must exceed `-0.005` for BKS and `-0.02` for both near-BKS and feasibility at
both fidelities, together with a real qubit/depth reduction or at least 10%
runtime reduction. Because depth and certified qubit caps are fixed here, an
external schedule can qualify only through runtime without violating quality.

## Execution integrity

- Every job is checkpointed immediately using a deterministic identity.
- Existing identities are deduplicated on resume.
- The protocol SHA-256 and software provenance are embedded in every final
  artifact.
- BLAS/OpenMP thread counts are fixed to one and only one simulator job runs at
  a time to respect the 15.8-GB host RAM limit.
- Backend failures remain in the audit log and are not converted into zeros or
  dropped observations.
- The core stage completes before the 64-qubit scale stage; partial scale
  results are labeled incomplete and never pooled as a completed cohort.
