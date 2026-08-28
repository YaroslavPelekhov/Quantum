# Contrastive tensor simulation kill-test report

## Verdict

The general full-density M/D simulator claim is **closed** by the frozen
criteria. The narrower signed diagonal contrast tensor is **supported**
for the frozen diagonal BKS observable.

## Equal-budget aves result

| ordering | state bond | contrast bond | separate Delta | contrast Delta | separate error | contrast error | factor | separate certified | contrast certified |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|:---:|
| sorted | 4 | 5 | +0.119859827 | -0.003412765 | 1.320e-01 | 8.726e-03 | 15.1x | no | no |
| sorted | 8 | 11 | +0.019466883 | -0.012780250 | 3.161e-02 | 6.414e-04 | 49.3x | no | no |
| sorted | 16 | 23 | -0.000516766 | -0.012154914 | 1.162e-02 | 1.606e-05 | 723.6x | no | yes |
| sorted | 32 | 47 | -0.009345761 | -0.012138410 | 2.793e-03 | 4.415e-07 | 6326.4x | no | yes |
| sorted | 64 | 95 | -0.011718102 | -0.012138879 | 4.207e-04 | 2.705e-08 | 15555.9x | no | yes |
| spectral | 4 | 5 | +0.036055540 | -0.010704770 | 4.819e-02 | 1.434e-03 | 33.6x | no | no |
| spectral | 8 | 11 | +0.008830254 | -0.012139464 | 2.097e-02 | 6.125e-07 | 34234.1x | no | no |
| spectral | 16 | 23 | -0.004239735 | -0.012140818 | 7.899e-03 | 1.966e-06 | 4017.9x | no | yes |
| spectral | 32 | 47 | -0.009761178 | -0.012138578 | 2.378e-03 | 2.735e-07 | 8693.1x | no | yes |
| spectral | 64 | 95 | -0.011801280 | -0.012138855 | 3.376e-04 | 3.461e-09 | 97532.1x | no | yes |

Exact aves Delta is `-0.012138852` (audit only). Separate MPS gives the
wrong sign at R4 and R8 on both orderings. The signed diagonal contrast
has the correct sign at every budget and obtains a strict Frobenius-tail
certificate at R16/R32/R64 on both orderings. Separate MPS obtains no
strict sign certificate at any frozen aves budget.

## Full M/D prototype

- `sorted`: exact recurrence error `2.591e-15`; exact Delta `-0.134213591`; certified policies `0/4`; largest radius `1.521e+38`.
- `spectral`: exact recurrence error `2.248e-15`; exact Delta `-0.134213591`; certified policies `0/4`; largest radius `1.426e+38`.

The M/D algebra is exact, but the gatewise trace-norm recurrence is
catastrophically vacuous (`~1e38` radii). Full D is lower-rank than both
individual projectors at `0/12` frozen cuts,
so the structural full-operator criterion also fails.

## Claim boundary

The positive result is comparison-native compression of the signed
diagonal observable tensor `q(z)=p_B(z)-p_A(z)`. It is not evidence that
a general density-MPO trajectory is cheaper than two state-MPS
trajectories. Construction of q currently uses exact terminal
probabilities; an end-to-end contrastive dynamics algorithm remains open.

The contrast certificate uses only the TT discarded Frobenius norm and
`||O||_F=sqrt(rank O)`. Exact Delta is excluded from interval construction.

## Sparse point-query construction

| case | ordering | rank | train fraction | train rel RMSE | holdout rel RMSE | estimated Delta | relative Delta error | sign |
|---|---|---:|---:|---:|---:|---:|---:|:---:|
| ibm32 | sorted | 8 | 15.601% | 0.135 | 1.070 | -0.00910457 | 0.963 | correct |
| ibm32 | sorted | 12 | 31.421% | 0.044 | 1.195 | -0.00456406 | 0.981 | correct |
| ibm32 | spectral | 8 | 15.601% | 0.065 | 1.891 | -0.01055281 | 0.957 | correct |
| ibm32 | spectral | 12 | 31.421% | 0.041 | 0.984 | +0.01018424 | 1.041 | wrong |
| aves-sparrow-social | sorted | 8 | 0.354% | 0.033 | 1.200 | +0.00715698 | 1.590 | wrong |
| aves-sparrow-social | sorted | 12 | 0.738% | 0.038 | 1.771 | -0.00128813 | 0.894 | correct |
| aves-sparrow-social | spectral | 8 | 0.354% | 0.068 | 1.115 | -0.00036813 | 0.970 | correct |
| aves-sparrow-social | spectral | 12 | 0.738% | 0.051 | 1.159 | +0.00108049 | 1.089 | wrong |

Generic uniform-query TT completion fails the frozen construction
criteria. Low terminal TT rank therefore demonstrates compressibility
with global access, not sample-efficient recoverability. Training errors
can be small while holdout relative RMSE remains near or above one. No
BKS-support point was used for training or holdout.
