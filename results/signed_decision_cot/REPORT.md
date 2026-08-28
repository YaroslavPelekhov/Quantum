# Signed Decision-Gap COT

The interval is centered at the MPS gap corrected by the signed compressed
observable-telescope residual. Exact gaps are audit-only.

## ibm32/confirm/sorted

MPS gap: `-0.254904437`; paired signed error center: `-0.008781498`; recentered gap: `-0.246122939`.  The legacy absolute first term is `0.067568306`, a `7.694x` inflation over the magnitude of the signed pair center.

| R | signed interval | signed | margin | legacy width | legacy | saving |
|---:|---:|:---:|---:|---:|:---:|---:|
| 32 | [-0.453426, -0.038820] | yes | 0.038820 | 0.274872 | no | 99.80% |
| 64 | [-0.478230, -0.014016] | yes | 0.014016 | 0.299676 | no | 98.44% |
| 96 | [-0.480397, -0.011849] | yes | 0.011849 | 0.301843 | no | 94.73% |
| 128 | [-0.465322, -0.026924] | yes | 0.026924 | 0.286767 | no | 87.50% |
| 256 | [-0.389172, -0.103074] | yes | 0.103074 | 0.210617 | yes | 0.00% |
| 512 | [-0.270207, -0.222039] | yes | 0.222039 | 0.091652 | yes | -700.00% |

Audit-only exact gap: `-0.246123001`; recentered error: `6.239e-08`.

### Path-dependence audit

- `published_lr` lower-bond-tighter checkpoints: R32<R64: 329/556, R64<R96: 236/556, R96<R128: 0/556; dense violations 0/36.
- `prior_matched_random` lower-bond-tighter checkpoints: R32<R64: 301/556, R64<R96: 234/556, R96<R128: 95/556; dense violations 0/36.

### Repeated-bond regression

- `published_lr` R128: absolute difference `5.926e-07`; frozen `1e-10` criterion fails.
- `prior_matched_random` R128: absolute difference `1.650e-09`; frozen `1e-10` criterion fails.

## ibm32/confirm/spectral

MPS gap: `-0.253935627`; paired signed error center: `-0.007812623`; recentered gap: `-0.246123004`.  The legacy absolute first term is `0.051574685`, a `6.601x` inflation over the magnitude of the signed pair center.

| R | signed interval | signed | margin | legacy width | legacy | saving |
|---:|---:|:---:|---:|---:|:---:|---:|
| 32 | [-0.265197, -0.227049] | yes | 0.227049 | 0.070648 | yes | 99.80% |
| 64 | [-0.267413, -0.224833] | yes | 0.224833 | 0.072865 | yes | 98.44% |
| 96 | [-0.266567, -0.225679] | yes | 0.225679 | 0.072018 | yes | 94.73% |
| 128 | [-0.263977, -0.228269] | yes | 0.228269 | 0.069429 | yes | 87.50% |
| 256 | [-0.255445, -0.236801] | yes | 0.236801 | 0.060896 | yes | 0.00% |
| 512 | [-0.249158, -0.243088] | yes | 0.243088 | 0.054610 | yes | -700.00% |

Audit-only exact gap: `-0.246123001`; recentered error: `-2.743e-09`.

### Path-dependence audit

- `published_lr` lower-bond-tighter checkpoints: R32<R64: 286/556, R64<R96: 123/556, R96<R128: 0/556; dense violations 0/36.
- `prior_matched_random` lower-bond-tighter checkpoints: R32<R64: 270/556, R64<R96: 136/556, R96<R128: 0/556; dense violations 0/36.

### Repeated-bond regression

- `published_lr` R128: absolute difference `2.238e-10`; frozen `1e-10` criterion fails.
- `prior_matched_random` R128: absolute difference `4.168e-11`; frozen `1e-10` criterion passes.

## Minimum-work asymmetric policy

Sorted selects LR R32 / MR R32 at 99.80% saving.

Frozen spectral transfer is certified with interval [-0.265197, -0.227049].

## Claim boundary

This is a center-plus-certified-remainder interval. It retains signed
cancellation only in the computable center and keeps the unknown remainder
fully adversarial. It proves feasibility for the evaluated policy points,
not global resource optimality or general scaling.
