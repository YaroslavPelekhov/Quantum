# Decision-balanced truncation report

## Verdict

The universal end-to-end claim is **closed**. Decision-balanced
Petrov--Galerkin truncation is promising on the development schedule
pair but does not transfer uniformly to a held-out schedule pair.

## Frozen fixed-rank prospective test

- Passed rows: `3/6`.
- Wrong candidate signs: `1/6`.
- Result: fixed cut-4/rank-2 balancing is unstable and fails the
  prespecified universal criterion.

## Equal-work adaptive exploration

The smallest rank in 1..8 retaining 99% of squared Hankel singular
energy was selected at every gate. The state-averaged baseline received
the identical rank schedule.

- Lower error: `6/6`.
- Correct signs: `6/6`.
- Typical mean retained rank: 1.5--2.6.

This is a positive development-set result, not validation.

## Frozen held-out schedule-pair transfer

| case | ordering | exact Delta | DBT error | matched baseline error | factor | pass |
|---|---|---:|---:|---:|---:|:---:|
| es60fst01 | sorted | +0.266384 | 0.050863 | 0.039305 | 0.77x | no |
| es60fst01 | spectral | +0.266384 | 0.039674 | 0.005960 | 0.15x | no |
| es60fst03 | sorted | +0.235169 | 0.091666 | 0.109588 | 1.20x | yes |
| es60fst03 | spectral | +0.235169 | 0.061965 | 0.050437 | 0.81x | no |
| mammalia-kangaroo-interactions | sorted | +0.148653 | 0.086150 | 0.123363 | 1.43x | yes |
| mammalia-kangaroo-interactions | spectral | +0.148653 | 0.021357 | 0.046336 | 2.17x | yes |

The candidate preserves the correct sign on `6/6` rows,
but lowers error on only `3/6`. Observed held-out
factors range from `0.15x` to `2.17x`.
The strict 6/6 criterion fails, so no threshold retuning is allowed.

## Scientific conclusion

Backward decision environments are genuinely informative: they rescue
some wrong signs and can beat fidelity-oriented bases at identical rank
schedules. But a local Hankel-energy criterion is not sufficient to
control nonlinear error after repeated projection and renormalization.
A publishable end-to-end successor needs a propagated decision-error
certificate or a globally optimized contraction, not another local
rank threshold.

The dense backward-vector implementation is an oracle and carries no
scalability claim.
