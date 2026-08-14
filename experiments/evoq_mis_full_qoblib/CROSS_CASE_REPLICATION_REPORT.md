# Cross-case exact MPS replication

All 300 frozen backend rows completed before analysis: 240 newly executed rows and 60 hash-validated 24-qubit rows.

## Primary outcomes

- Matched-vs-LR exact-sign correctness: 91/100 backend cohorts.
- Cross-backend sign agreement: 45/50 cohorts.
- Exact-margin TVD certificates: 77/100 cohorts.
- Approximate-margin TVD certificates: 76/100 cohorts.
- Fidelity-only certificates: 58/100 cohorts.
- Verified TVD inequalities: 100/100 cohorts.
- When normalized TVD/margin < 1: 77/77 signs correct; at >= 1: 14/23.

## Per-case replication

| Case | Correct signs | TVD-certified | Cross-backend signs | First universally certified setting | Max TVD/margin |
|---|---:|---:|---:|---|---:|
| karate | 20/20 | 20/20 | 10/10 | released | 0.136 |
| chesapeake | 20/20 | 20/20 | 10/10 | released | 0.755 |
| football | 20/20 | 18/20 | 10/10 | confirm | 4.106 |
| ibm32 | 20/20 | 14/20 | 10/10 | cutoff1e-4 | 3.196 |
| aves-sparrow-social | 11/20 | 5/20 | 5/10 | none | 57.571 |

A setting is called universally certified only when the exact-margin TVD certificate holds for both backends and both orderings. The first setting is taken in the protocol-frozen ladder order, not selected post hoc by runtime.
