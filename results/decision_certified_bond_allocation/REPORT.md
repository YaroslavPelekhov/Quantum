# Causal asymmetric decision-certified bond allocation

## Result

The prespecified checkpoint-wise mixing proxy failed after end-to-end execution:
width `0.255099410` versus gap `0.254904437` (margin
`-0.000194973`). This retains the negative result and
demonstrates that independently mixing fixed-bond checkpoint rows is not sound
as a resource predictor because the residual tail is causal and irreversible.

The secondary causal asymmetric schedule succeeds on the difficult sorted
ordering:

| quantity | value |
|---|---:|
| compressed first-term pair | 0.067568306 |
| LR scheduled correction | 0.180029055 |
| MR fixed-R128 correction | 0.000116324 |
| total certified width | 0.247713685 |
| MPS gap | 0.254904437 |
| certificate margin | 0.007190752 |
| paired cubic work vs R256/R256 | 0.3765 |
| paired cubic work saving | 62.35% |

All selected dense-oracle inequalities pass, but dense errors are audit-only and
are excluded from selection and from the certificate construction.

## Frozen spectral transfer

The identical LR schedule plus MR/R128 remains certified: width
`0.063607243`, gap `0.253935627`, margin
`0.190328384`. Resource optimality does not transfer:
the policy uses `3.012x` the cubic
bond-work of the already sufficient spectral R128/R128 baseline. Thus the pilot
supports sound causal asymmetric allocation but not a universal allocation
policy across qubit orderings.
