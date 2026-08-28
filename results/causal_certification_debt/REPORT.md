# Causal Certification Debt identity audit

The implemented orientation is `j -> {t: t<=j}`. The local increment includes the TT-SVD bound and the explicit `1e-10` per-vector numerical floor.

| case | rank | direct debt | shadow-price debt | identity error | tail / correction |
|---|---:|---:|---:|---:|---:|
| sorted_rescue_lr | 2 | 0.162648290904 | 0.162648290904 | 1.665e-16 | 90.35% |
| sorted_fixed_mr_R128 | 2 | 0.000108290330423 | 0.000108290330423 | 5.421e-19 | 93.09% |
| spectral_transfer_lr | 2 | 0.00934546981636 | 0.00934546981636 | 2.949e-17 | 77.72% |
| spectral_fixed_mr_R128 | 2 | 7.14184896992e-06 | 7.14184896992e-06 | 1.779e-20 | 90.00% |

Maximum identity error: `1.665e-16`. Maximum tail-recurrence error: `0.000e+00`. Maximum reconstruction error against the production COT correction: `1.735e-18`.

No rank cap is active in these four executed witnesses, so the tail component equals the uncapped causal debt. The theorem file also proves the conservative inequality required when a cap is active.
