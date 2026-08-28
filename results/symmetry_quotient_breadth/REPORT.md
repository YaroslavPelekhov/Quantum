# QOBLIB quotient breadth report

## Verdict

The backend passes exact full-state and decision-core validation on **7/7**
non-aves cases from the pre-existing deterministic QOBLIB selection.  Together
with the real 24-qubit aves run, correctness is now 8/8 cases; compression is
not universal and is reported without filtering.

| case | qubits | twin classes | compression | evolution speedup | pass |
|---|---:|---|---:|---:|:---:|
| chesapeake | 7 | none | 1.00x | 0.53x | yes |
| football | 7 | none | 1.00x | 0.45x | yes |
| ibm32 | 18 | none | 1.00x | 1.33x | yes |
| karate | 3 | 3 | 2.00x | 1.00x | yes |
| es60fst03 | 12 | 3 | 2.00x | 1.14x | yes |
| mammalia-kangaroo | 15 | 4 | 3.20x | 3.08x | yes |
| es60fst01 | 15 | 2,2,2 | 2.37x | 2.12x | yes |

The maximum amplitude error is `2.24e-14`; all comparison ranks agree exactly,
and all trace/trace-norm discrepancies are below `3e-14`.

The pre-existing eight-case census finds nontrivial twin sectors in 5/8 cases,
spanning animal-network, named-network, and es60 families.  Small asymmetric
cases expose expected overhead instead of being excluded.  The large aves case
provides the main performance result (`23.90x` steady-state speedup).

