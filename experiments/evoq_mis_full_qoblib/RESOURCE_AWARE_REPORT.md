# Resource-aware QAOA cycle

- Minimum BKS-preserving reduction cap: `4`.
- Exact schedule-depth configurations evaluated: 210.
- Exact training-eligible configurations: 53.
- Champion status: `no_eligible_resource_champion`.

## Blind summary

| Configuration | Setting | Depth | BKS | Near-BKS | Feasible | Median s/job | RZZ |
|---|---:|---:|---:|---:|---:|---:|---:|
| prior_matched_random_p15__sorted | confirm | 15 | 197/15000 (0.01313) | 0.18153 | 0.68640 | 370.233 | 1365 |
| prior_matched_random_p15__sorted | released | 15 | 108/15000 (0.00720) | 0.15793 | 0.90087 | 12.009 | 1365 |
| published_lr_p15__sorted | confirm | 15 | 260/15000 (0.01733) | 0.18540 | 0.49367 | 236.960 | 1365 |
| published_lr_p15__sorted | released | 15 | 49/15000 (0.00327) | 0.11507 | 0.50933 | 7.909 | 1365 |

## Paired blind comparison against published LR

| Setting | Metric | Mean difference | Paired-bootstrap 95% CI | Sign-flip p |
|---|---|---:|---:|---:|
| released | bks_rate | +0.00393 | [+0.00267, +0.00513] | 0.000244141 |
| released | near_bks_rate | +0.04287 | [+0.03673, +0.04900] | 6.10352e-05 |
| released | feasible_rate | +0.39153 | [+0.38380, +0.39887] | 6.10352e-05 |
| confirm | bks_rate | -0.00420 | [-0.00580, -0.00253] | 0.000732422 |
| confirm | near_bks_rate | -0.00387 | [-0.00780, +0.00020] | 0.0979004 |
| confirm | feasible_rate | +0.19273 | [+0.18347, +0.20220] | 6.10352e-05 |

## Strict conclusion

No newly searched configuration satisfied the pre-registered non-inferiority gate at both MPS fidelities, so the controller correctly returned no resource champion. The smallest reduction cap preserving the known best solution on all four instances was 4; lower depths did not preserve blind-relevant validation performance.

The held-out comparison shows a statistically significant fidelity reversal. The prior matched schedule improves BKS under the released approximation but degrades BKS under the tighter confirmation setting. Feasibility improves under both, demonstrating that feasibility alone is not a sufficient proxy for the upper tail of solution quality.

The defensible application result is therefore a certified abstention: under the frozen quality tolerances, this search found no safe reduction in qubits, QAOA depth, or end-to-end runtime. The methodological result is that multi-fidelity confirmation prevents a cheap tensor-network approximation from producing a false resource-efficiency claim.

## Scope

These conclusions apply to the frozen four-instance es60fst split, noiseless MPS simulation, native unrepaired samples, and the tested schedule family. Hardware latency/noise and broader QOBLIB families remain external-validation targets.
