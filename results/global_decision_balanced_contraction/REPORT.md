# Global decision-balanced contraction report

## Verdict

The prespecified development claim is **closed**. A single linear
two-pass Petrov--Galerkin contraction does not reliably preserve the
paired BKS decision, even when its bases use exact forward and backward
dense Gramians. The held-out schedule pair was not run.

## Frozen equal-rank development test

| case | ordering | exact Delta | GDBC error | orthogonal error | factor | sign | pass |
|---|---|---:|---:|---:|---:|:---:|:---:|
| es60fst01 | sorted | +0.242884 | 0.389937 | 0.317144 | 0.81x | no | no |
| es60fst01 | spectral | +0.242884 | 0.214712 | 0.151904 | 0.71x | yes | no |
| es60fst03 | sorted | +0.219474 | 0.345898 | 0.388002 | 1.12x | no | no |
| es60fst03 | spectral | +0.219474 | 0.276172 | 0.303401 | 1.10x | no | no |
| mammalia-kangaroo-interactions | sorted | -0.269489 | 0.138539 | 0.233324 | 1.68x | yes | yes |
| mammalia-kangaroo-interactions | spectral | -0.269489 | 0.109008 | 0.173290 | 1.59x | yes | yes |

- Strict passes: `2/6` (required `6/6`).
- Lower absolute error: `4/6`.
- Correct candidate signs: `3/6`; equal-rank orthogonal control: `3/6`.
- Error factors: `0.71x` to `1.68x`.
- Candidate final-state norms: `0.269` to `0.765`.
- Maximum biorthogonality error: `3.14e-14`; fallbacks: `0`.

The last diagnostic rules out numerical loss of biorthogonality as the
explanation. Instead, many individually aggressive low-rank maps compose
into severe loss of state mass. Using a globally linear recurrence removes
the earlier normalization feedback, but it does not remove accumulated
projection bias or guarantee the sign of a small probability difference.

## Claim boundary

This experiment supports a negative result only: exact local forward/backward
Gramians plus a 99% local Hankel-energy rule are insufficient for a universal
end-to-end paired-decision advantage. Because development failed, running the
frozen `prior_evolutionary` held-out pair would not be confirmatory and was
forbidden by the protocol.

The implementation is an exact dense feasibility oracle, not a scalable
algorithm. The remaining positive result in this research line is the local
signed reduced-density truncation primitive and its trace-norm certificate;
no end-to-end universal superiority claim survives.
