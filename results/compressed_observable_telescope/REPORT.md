# Certified Compressed Observable Telescope: ibm32 result

## Headline result

The proposed bound is mathematically valid under the stated conditions, and a
**residual-aware depth-adaptive COT preserves the `ibm32/confirm/sorted`
MR-vs-LR certificate**. At residual bond 256, the complete paired width is
`0.210617`, below the observed MPS gap `0.254904`, leaving
positive margin `0.044287`. Residual bond 128 fails, so the experiment identifies
a real compression threshold rather than reporting only a successful setting.

| Residual bond | First term | Operator correction | Full width | Margin | Certified? |
|---:|---:|---:|---:|---:|:---:|
| 128 | 0.067568 | 0.219198 | 0.286767 | -0.031862 | no |
| 256 | 0.067568 | 0.143049 | 0.210617 | 0.044287 | yes |
| 512 | 0.067568 | 0.024084 | 0.091652 | 0.163252 | yes |

The primary backward schedule is D64 on checkpoints 512-555, D128 on 448-511,
D256 on 384-447, D384 on 320-383, and the exact 18-qubit maximum central rank
D512 on 1-319. Thus the method spends full bond only after the measured
entanglement transition; the independently compressed error witness needs only
bond 256 for the positive result.

## Frozen spectral-ordering held-out test

Before inspecting residual-aware spectral results, the sorted-derived primary
schedule, residual bonds, and R256 headline endpoint were frozen in
`SPECTRAL_HELDOUT_PROTOCOL.md`. Without retuning, the prespecified R256 test
certifies with width `0.060896` against gap `0.253936`, for margin `0.193039`.
Even the lower-resource R128 control certifies.

| Residual bond | First term | Operator correction | Full width | Margin | Certified? |
|---:|---:|---:|---:|---:|:---:|
| 128 | 0.051575 | 0.017854 | 0.069429 | 0.184507 | yes |
| 256 | 0.051575 | 0.009322 | 0.060896 | 0.193039 | yes |
| 512 | 0.051575 | 0.003035 | 0.054610 | 0.199326 | yes |

This is an out-of-design qubit-ordering validation on the same QOBLIB graph,
not an independent-instance replication. It demonstrates robustness to a
major tensor-network geometry choice but does not establish cross-graph scaling.

## Bound and residual theorem

For every transition,

`|Tr(O_t Delta rho_t)| <= |Tr(O_t_tilde Delta rho_t)| + eta_t ||Delta rho_t||_1`.

Aer internal swap/SVD losses belonging to a logical gate are grouped by angle,
upper-rounded from the log, and inflated by the calibrated `1e-7` numerical
floor, giving `||Delta rho_t||_1 <= 2 sqrt(w_t_effective)`.

For an exact backward vector `v_t`, primary approximation `z_t`, and residual
`r_t=v_t-z_t`, the implementation propagates

`rhat_t = TT_R(U_t^dagger rhat_(t+1) + U_t^dagger z_(t+1) - z_t)`

and accumulates only the TT-SVD discarded-tail certificate `xi_t`. Induction
gives `||r_t|| <= ||rhat_t||+xi_t`, hence for the rank-two BKS observable

`eta_t = sum_k min(1, ||rhat_(k,t)|| + xi_(k,t))`.

This retains coherent cancellation that the rejected accumulated-angle method
throws away. The evaluated certificate is exactly the requested

`sum_t (|Tr(O_t_tilde Delta rho_t)| + 2 sqrt(w_t) eta_t)`.

## Controls and audits

- All 1112 LR/MR forward
  transitions were replayed; group-bound violations: **0**.
- Every selected residual checkpoint was compared with dense exact vectors;
  operator-bound violations: **0**.
- The compressed first terms are `0.0427720812` (LR) and `0.0247962251` (MR).
- Residual R128 is a near-boundary negative control: width `0.286767` exceeds
  the gap by `0.031862`.
- Exact-residual R512 gives width `0.091652`, separating primary-observable
  error from residual-witness compression loss.

The certified Aer radius sums are 39.9399
(LR) and 42.8717 (MR), versus
dense-oracle actual sums 15.1267
and 16.6068.
The forward certificate is therefore sound but still about 2.5x conservative.

## Fixed-bond negative control

The original fixed-bond construction remains decisively rejected:

| Backward bond | LR correction | MR correction | Paired correction | / MPS gap | Possible? |
|---:|---:|---:|---:|---:|:---:|
| 8 | 58.3644 | 48.8457 | 107.2101 | 420.6x | no |
| 16 | 53.2580 | 42.7647 | 96.0227 | 376.7x | no |
| 32 | 47.0644 | 36.9579 | 84.0223 | 329.6x | no |
| 64 | 40.3271 | 31.1760 | 71.5030 | 280.5x | no |

At fixed D64, even residual-aware accounting with R128 leaves paired correction
`65.2591`. The adaptive
success is therefore caused by allocating bond at the measured depth transition,
not merely by rewriting the same loose inequality.

## Scope

This is a complete positive 18-qubit benchmark instance, not yet a general
scaling claim. Primary D512 is exact on the early half, the forward radii depend
on parsed Aer logs, and floating point is protected by explicit empirical
allowances plus dense oracle audits rather than interval arithmetic. The next
paper-level validation should freeze the adaptive schedule before testing more
QOBLIB instances and should obtain truncation residuals directly from a
controlled MPS implementation.
