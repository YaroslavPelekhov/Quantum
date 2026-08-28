# DOT-MPS local kill-test

## Verdict

The prespecified decision-optimal Schmidt-subset test **failed**. On the real
`ibm32/confirm/sorted` LR checkpoint 502, cut 11, and rank 40, top-Schmidt has
BKS error `9.959530e-05` and the best constructed
goal-aware subset has `9.776575e-05`: only
`1.019x` improvement, far below the frozen
10x success threshold.

The goal-aware subset has slightly worse fidelity
(`0.999753940` versus
`0.999758764`), but the decision gain is only
about 1.9%. This is not the proposed killer result.

## Why the negative result is informative

The Spearman correlation between Schmidt mass and leave-one-mode BKS importance
is `0.999437`. Standard state-mass and
decision-importance rankings are therefore almost identical at this diagnosed
checkpoint. The selected subsets overlap in 39 of 40 modes.

The actual frozen Aer checkpoint BKS change is
`4.479428e-04`, larger than either isolated
single-cut approximation error because the logical Aer transition contains
multiple internal swap/SVD truncations. The local test does not reproduce the
entire multi-truncation update.

## Exploratory neighboring-cut sensitivity

This sweep was performed only after the frozen cut-11 endpoint failed and is
labelled exploratory.

| Cut | Top-Schmidt error | Goal-aware error | Improvement | Spearman | Mode overlap |
|---:|---:|---:|---:|---:|---:|
| 6 | 3.758e-05 | 3.758e-05 | 1.000x | 0.99831 | 40/40 |
| 7 | 4.798e-04 | 4.785e-04 | 1.003x | 0.99793 | 39/40 |
| 8 | 3.992e-04 | 3.806e-04 | 1.049x | 0.99853 | 39/40 |
| 9 | 4.131e-04 | 3.944e-04 | 1.047x | 0.99892 | 39/40 |
| 10 | 1.270e-04 | 1.234e-04 | 1.029x | 0.99809 | 39/40 |
| 11 | 9.960e-05 | 9.777e-05 | 1.019x | 0.99944 | 39/40 |
| 12 | 1.457e-05 | 1.457e-05 | 1.000x | 0.99800 | 40/40 |

No cut reaches the 10x criterion. The largest improvement is
`1.049x`; all mass versus
decision-importance correlations exceed
`0.99793`.

## Conceptual issue with the unconstrained DOT objective

Minimizing only

`|<psi|O|psi> - <phi|O|phi>|`

over low-Schmidt-rank `phi` does not require `phi` to remain a useful
approximation to `psi`. A low-rank state can match one scalar while destroying
other observables, phases needed by later gates, or the next truncation step.
Consequently the unconstrained arbitrary-subspace objective can be degenerate.

A defensible successor would instead solve a constrained or regularized
problem, for example:

`maximize fidelity(psi,phi) subject to |J(psi)-J(phi)| <= epsilon`,

or

`minimize ||psi-phi||^2 + lambda |J(psi)-J(phi)|^2`,

using multiple future observables or a residual subspace rather than one scalar.
Such a formulation requires a new theorem and a new frozen test; it is not
supported by the present subset result.

## Decision

Do not build a custom DOT-MPS simulator yet. Retain COT as a diagnostic, report
this negative result, and only revisit goal-aware truncation after formulating a
non-degenerate constrained primitive or finding a checkpoint where Schmidt mass
and decision importance demonstrably separate.
