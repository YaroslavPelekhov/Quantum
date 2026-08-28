# Decision-certified asymmetric allocation pilot

## Frozen design result

The complete 5 x 5 sorted grid contains 20 certified pairs out of 25. No certified pair has the wrong exact direction in the audit.

| policy | LR setting | matched-random setting | simulation s | pair width | margin |
|---|---:|---:|---:|---:|---:|
| joint minimum | released | confirm | 20.024430 | 0.302265 | 0.109762 |
| best symmetric | confirm | confirm | 22.451397 | 0.067568 | 0.187336 |

Measured forward-simulation saving: 10.81%.

The selection objective uses only approximate values, certified telescope radii, and costs. Exact values are excluded from selection and retained only for the post-selection soundness audit.

## Frozen spectral held-out result

| policy | LR setting | matched-random setting | simulation s | certified | margin | correct |
|---|---:|---:|---:|---:|---:|---:|
| transferred joint | released | confirm | 12.741818 | True | 0.128818 | True |
| symmetric baseline | confirm | confirm | 13.758669 | True | 0.202361 | True |

Frozen-transfer measured saving: 7.39%.
