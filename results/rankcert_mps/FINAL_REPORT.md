# RankCert-MPS final report

## Result

**Outcome 2 - Sound but too conservative.** The accumulated-angle truncation certificate passed every empirical exact-case soundness check, but useful coverage did not survive problem scaling. It certified 14 / 50 LR-vs-MR cohorts (28.0%) and certified no wrong sign. However, only 2 certified cohorts had any deliberate truncation, and no 18q or 24q cohort was certified.

## A. Simulator semantics

Aer 0.17.2 reports the sum of squared singular values actually removed by its combined bond-cap/cutoff SVD step. On this normalized noiseless unitary path, it is the normalized discarded Schmidt weight required by the accumulated-angle derivation. Aer renormalizes retained singular values. Because its log prints only six significant digits, RankCert uses the conservative upper endpoint of each decimal rounding bin. Full source locations, hashes, and caveats are in `AER_DISCARDED_VALUE_SEMANTICS.md`.

## B. Aer threshold edge case

The installed build is affected. Cutoff 0.9 in the 4q reproducer and cutoff 2e-4 in the analytic w=1e-4 test fail to remove the final small component. This changes the nominal truncation policy, not the interpretation of the existing paper results or this certificate: RankCert consumes losses Aer actually performed and logged, never losses inferred from the configured cutoff.

## C. Soundness

All 100 schedule runs satisfied both `BKS_error <= epsilon_MPS + numerical_floor` and `TVD <= epsilon_MPS + numerical_floor`. BKS violations: 0; TVD violations: 0. The separately reported numerical floor is 1e-07; its frozen-control calibration is documented in `NUMERICAL_ROUNDOFF_AUDIT.md`.

## D-E. Ranking coverage

| Case | Internal certified | Coverage | BKS / TVD violations | Exact-TVD certified | Wrong certified |
|---|---:|---:|---:|---:|---:|
| karate | 10 / 10 | 100.0% | 0 / 0 | 10 | 0 |
| chesapeake | 2 / 10 | 20.0% | 0 / 0 | 10 | 0 |
| football | 2 / 10 | 20.0% | 0 / 0 | 8 | 0 |
| ibm32 | 0 / 10 | 0.0% | 0 / 0 | 8 | 0 |
| aves-sparrow-social | 0 / 10 | 0.0% | 0 / 0 | 1 | 0 |

Globally, correct certified / certified = 14 / 14; wrong-sign certified = 0. Six known wrong-sign cohorts occurred, all on aves, and all six were rejected by the internal certificate.

| Setting | Internal certified | Exact-TVD certified |
|---|---:|---:|
| released | 2 / 10 | 4 / 10 |
| confirm | 2 / 10 | 8 / 10 |
| bond128 | 6 / 10 | 9 / 10 |
| cutoff1e-4 | 2 / 10 | 8 / 10 |
| cutoff1e-5 | 2 / 10 | 8 / 10 |

## F. Conservativeness

Among the 74 runs with positive truncation epsilon, `epsilon_MPS / TVD` has median 37.25 (range 1.91-305.35); `epsilon_MPS / BKS_error` has median 236.84 (range 3.67-4940.49). TVD itself is a median 4.29 times the actual BKS error. The state-level angle bound is therefore much looser than both the global distribution error and the target observable error.

## G. Failure mechanism

| Case | Saturated runs | Median event count | Median raw angle | Median epsilon |
|---|---:|---:|---:|---:|
| karate | 0 / 20 | 0.0 | 0 | 0 |
| chesapeake | 4 / 20 | 96.5 | 0.48014 | 0.461848 |
| football | 4 / 20 | 85.0 | 0.442934 | 0.428518 |
| ibm32 | 19 / 20 | 2023.5 | 14.8842 | 1 |
| aves-sparrow-social | 17 / 20 | 2269.0 | 13.8581 | 1 |

The bound saturated at epsilon=1 in 44 / 100 runs. The mechanism is accumulation of hundreds or thousands of individually small losses, not a single catastrophic event. The largest reported single event was 0.00270828 in `aves-sparrow-social/bond128/MR/sorted` at `internal_swap` on qubits [12, 11]. For ibm32 and aves the median event counts were 2023.5 and 2269, and median epsilons were both one. Sorted ordering was often worse, but neither ordering rescued coverage on the two large cases. Gate-localized top-event lists and explicitly non-rigorous heuristic sums are in `rankcert_summary.json`.

## H. 55q implication

The 55q gate fails scientifically: large-case coverage is 0 cohorts, while ibm32 and aves already accumulate epsilon near or at one. A new 55q run would almost certainly add another vacuous epsilon=1 result. No 55q job was run and no finite-shot claim was made.

## I. Research verdict

**Outcome 2 - Sound but too conservative.** The simple certificate is sound on the exact pilot and successfully rejects every observed wrong winner, but it certifies only exact/nearly exact small simulations and no large case. The next research contribution should be an observable-aware or decision-aware bound for BKS probability/ranking, not further scaling of this global state-distance sum.
