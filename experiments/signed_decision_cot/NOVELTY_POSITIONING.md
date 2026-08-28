# Novelty boundary

The closest broad framework is goal-oriented a posteriori error estimation and
the dual-weighted residual method, where signed residual contributions provide
an output correction and a separately controlled remainder.  Relevant primary
sources include Becker and Rannacher's Acta Numerica treatment
<https://doi.org/10.1017/S0962492901000010> and later goal-oriented adaptive
methods <https://doi.org/10.1007/s00211-022-01334-8>.

In tensor networks, standard references cover MPS truncation and time evolution
<https://arxiv.org/abs/quant-ph/0503174>, TT-SVD error control
<https://doi.org/10.1137/090752286>, and observable extrapolation from MPS
variance proxies <https://arxiv.org/abs/1711.01104>.  Operator backpropagation
has also been used to trade classical observable evolution for reduced quantum
circuit depth <https://arxiv.org/abs/2502.01897>.

The safe novelty claim is not "signed error correction is new."  It is:

> a certified interval for the difference of two approximate quantum-algorithm
> outcomes, centered by paired signed observable-telescope residuals and
> enclosed by compressed backward-observable witnesses, with resource
> allocation evaluated at the level of the decision rather than either state.

The literature audit did not identify this exact combination.  That is a scoped
search result, not proof of global novelty.  A submission should use cautious
language until a systematic citation review is completed.

## Empirical algorithmic finding

The frozen low-bond ladder reveals a second, distinct result: certified
residual-policy quality is path-dependent and nonmonotone in fixed bond.  On
`ibm32/sorted`, R32 has a smaller integrated LR remainder than R64, R96, and
R128.  On spectral ordering R128 remains globally tightest, but R32 overtakes
larger intermediate bonds and becomes locally tightest in the late prefix.
Both schedules show the same ordering-specific onset depth.

This should be described as a **certified residual-policy rank reversal**, not
as evidence that lower-bond MPS states are generally more accurate.  The
result motivates state-aware control or controlled reset interventions; it
does not by itself prove the mechanism or global optimality.

## Submission-safe updated wording

“We construct a signed, recentered interval for paired algorithmic decisions
from compressed observable-telescope residuals.  The interval certifies a
frozen R32/R32 residual policy on sorted and held-out spectral orderings.  A
low-bond ladder further reveals path-dependent rank reversals among certified
residual policies, invalidating monotone bond-search assumptions in the audited
recurrence.  We claim within-policy decision feasibility and ordering transfer,
not full-simulator speedup, global resource optimality, or general scaling.”
