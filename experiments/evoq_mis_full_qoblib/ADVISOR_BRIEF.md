# Advisor brief: exact and cross-backend QAOA rank stability

## One-sentence contribution

We show that the reliability of an approximate-simulator QAOA ranking is
controlled by the application-level effect margin relative to the schedules'
total-variation error, and validate a sufficient sign certificate in a frozen
300-row Aer/cuTensorNet experiment on five real QOBLIB MIS cases.

## What is new

1. **Application-facing resource validation.** Instead of comparing only raw
   simulator fidelity at fixed scale, the study asks whether a cheaper MPS
   setting preserves the benchmark decision: which schedule has higher BKS
   probability.
2. **Observable-level certificate.** For a BKS event and schedules `i,j`,
   `|approx_effect - exact_effect| <= TVD_i + TVD_j`. If the exact margin is
   larger than this budget, the approximate ranking is guaranteed correct.
3. **Frozen cross-case evidence.** Five QOBLIB cases, five settings, three
   schedules, two orderings, and two backends yield 300 dense rows and 100
   primary cohorts. All 77 certified cohorts have the exact sign; all nine
   failures are outside the certified region.
4. **Backend portability failure.** Aer and cuTensorNet agree in sign only
   45/50 matched cohorts. A nominal bond/cutoff pair is therefore not a
   backend-independent accuracy contract.
5. **Conservative negative results.** Evolutionary search does not beat its
   matched random-search control, and simple classical MIS controls dominate
   the QAOA results. The claimed novelty is validation methodology, not quantum
   or evolutionary advantage.

## Key numbers

| Result | Value |
|---|---:|
| Dense backend rows | 300/300 |
| New frozen executions | 240 |
| Correct matched-effect signs | 91/100 |
| Cross-backend sign agreement | 45/50 |
| Exact-margin TVD certificates | 77/100 |
| Correct signs inside certificate | 77/77 |
| Correct signs outside certificate | 14/23 |
| Verified TVD inequalities | 100/100 |
| Fidelity-only certificates | 58/100 |

The exact matched-random-minus-LR BKS effects are `+0.086412` (karate),
`-0.134214` (chesapeake), `+0.019269` (football), `-0.246123` (ibm32), and
`-0.012139` (aves-sparrow-social). The smallest-margin case contains all nine
wrong signs and all five cross-backend disagreements.

## Recommended paper framing

Primary framing: **decision-preserving approximate simulation for quantum
optimization benchmarks**. The 55-qubit reversal is the motivating example;
the five-case exact replication and TVD certificate are the main evidence.

Avoid framing this as a new optimizer, a quantum advantage result, or a claim
that one MPS implementation is globally more accurate. The certificate is
sufficient, not necessary, and the 100 cohorts share circuits/settings, so the
Fisher result is descriptive rather than the foundation of the claim.

## Questions for advisor discussion

- Target venue and expected paper length: quantum benchmarking, quantum
  software/simulation, or evolutionary computation application track?
- Should the 55-qubit schedule-search history remain in the main paper or move
  mostly to the supplement, leaving the certificate as the central narrative?
- Is the exact-margin certificate acceptable as an offline validation rule, or
  should the next phase target computable upper bounds that do not require an
  exact target state?
- Which additional problem families or hardware/noise backends would provide
  the strongest external validation?

## Honest next experiment

The strongest extension is to replace exact-state TVD with a computable or
empirical upper confidence bound (for example, contraction residual bounds,
cross-backend discrepancy plus exact small-instance calibration, or
distribution-testing bounds) and test whether it safely drives adaptive
resource allocation without knowing the exact target distribution.
