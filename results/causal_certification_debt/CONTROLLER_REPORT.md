# Frozen causal shadow-price controller

The controller was calibrated once on `ibm32/confirm/sorted` with `lambda=500`, then frozen for spectral ordering and a separate QOBLIB graph. Dense exact errors are audit-only.

| run | LR 128/256/512 | MR 128/256/512 | width | gap | margin | work | saving |
|---|---:|---:|---:|---:|---:|---:|---:|
| ibm32_sorted | 137/418/0 | 555/0/0 | 0.211779 | 0.254904 | 0.043125 | 0.4545 | 54.55% |
| ibm32_spectral | 338/217/0 | 555/0/0 | 0.063044 | 0.253936 | 0.190891 | 0.2961 | 70.39% |
| chesapeake_sorted | 210/0/0 | 210/0/0 | 0.015653 | 0.136037 | 0.120385 | 0.1250 | 87.50% |

## Audit

Score-argmin violations: `0`; operator violations: `0`; residual violations: `0` across `456` dense checkpoints. Maximum debt reconstruction error: `4.163e-17`.

## Claim boundary

Certified work is a feasible upper bound on decision-certification cost in this policy class, not a global minimum.
The frozen spectral policy is `0.786x` the manual transfer, but still `2.368x` an all-R128 pair that already certifies spectral. Transfer soundness is shown; global resource optimality is not.
