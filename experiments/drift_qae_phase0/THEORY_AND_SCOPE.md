# Theory and scope: why the broad drift-QAE claim fails

## Ideal parameter

Write the prepared amplitude as `a = sin(theta)^2`.  An odd amplification
depth `k` gives an ideal binary fringe with centered expectation

```text
mu_k(theta) = cos(2 k theta).
```

Changing which binary outcome is called success only changes the sign and has
no effect on the conclusions below.  The resource `Q` is total amplified
physical depth.  When an anchor has the same depth as a target, its full `k`
cost is included.

## Proposition 1: generator-aligned drift is nonidentifiable

Suppose the realized fringe depends on `theta + delta`, where `delta` is an
unknown coherent calibration offset.  For any two distinct parameters
`theta_0` and `theta_1`, choose offsets satisfying

```text
theta_0 + delta_0 = theta_1 + delta_1.
```

Every conditional outcome probability is then equal for every possible
adaptive choice of depth and for every observation history.  The complete
adaptive experiment laws are identical.  If `Delta = |theta_1-theta_0|`, the
triangle inequality gives

```text
inf_estimator max_i E_i |theta_hat-theta_i| >= Delta / 2.
```

Both offsets can be constant, so a total-variation restriction does not repair
the ambiguity.  One must either estimate the hardware-realized parameter or
introduce a trusted reference whose coupling to this offset is independently
validated.

## Proposition 2: an unanchored visibility path can exactly confound theta

For a finite depth schedule, let

```text
p_t = [1 + v_t cos(2 k_t theta)] / 2.
```

Choose two theta values for which the relevant cosines have the same signs and
define

```text
v_t^(1) = v^(0) cos(2 k_t theta_0) / cos(2 k_t theta_1).
```

Whenever these values lie in the registered visibility interval, every target
probability is exactly equal under the two hypotheses.  The construction used
in `qae_core.py` also verifies the total-variation budget.  Thus favorable
average-case estimation cannot establish minimax identifiability for the
unanchored model.

## Proposition 3: matched anchors change the statistical object

For one round, write `c = cos(2 k theta)`, visibility `v`, and target
probability `p = (1+vc)/2`.  The derivatives are

```text
partial_theta p = -v k sin(2 k theta),
partial_v p     = c/2.
```

With only target observations and a separate unknown `v` at each round, the
two score directions are collinear.  The efficient Fisher information for
`theta` after profiling `v` is exactly zero.

An anchor with probability `(1+v)/2` adds information only to the `v,v` entry.
For positive target and anchor allocations, the Schur complement becomes
positive and remains proportional to `k^2` away from fringe degeneracies.
This can preserve local amplified scaling in a depth-independent readout
model, but it is ordinary matched nuisance calibration.  Drift no longer sets
a nontrivial phase boundary; common target/anchor coupling and a visibility
floor do.

## Proposition 4: fixed depth-accumulating noise has an SQL ceiling

For known Markovian visibility `v_k = exp(-gamma k)`, the Fisher information in
one target shot is

```text
I_k(theta)
 = 4 exp(-2 gamma k) k^2 sin(2 k theta)^2
   / [1 - exp(-2 gamma k) cos(2 k theta)^2]
 <= 4 k^2 exp(-2 gamma k).
```

For any possibly adaptive experiment with total physical depth
`sum_t k_t <= Q`,

```text
I_total
 <= 4 Q sup_k [k exp(-2 gamma k)]
 <= 2 Q / (e gamma).
```

A van Trees bound for any smooth interior prior therefore yields

```text
RMSE = Omega(sqrt(gamma / Q)).
```

For fixed nonzero `gamma`, the exponent is `Q^-1/2`, even if the complete noise
path is revealed by an oracle.  Anchors can estimate a visibility that still
exists; they cannot restore information erased by exponential depth decay.
If `gamma_Q` scales as `Q^-beta`, the information bound permits an exponent no
better than `(1+beta)/2` until `beta >= 1`.

## Scope of the negative verdict

The result closes the broad proposal registered in `PREREGISTRATION.md`.  It
does not prove that every temporally structured calibration protocol is
useless.  A narrower result would need all of the following:

- a trusted and falsifiable common-nuisance relation between target and
  references;
- at least the quadratures required to identify phase, visibility, and any
  affine SPAM offset;
- a local time-regularity assumption stronger than aggregate total variation;
- global alias control and full anchor resource accounting;
- an upper/lower minimax boundary not already implied by ordinary interpolation
  error or standard noisy quantum metrology.

That narrower problem is a new candidate and is not counted as a positive
result of this Phase 0.

