# Signed Decision-Gap Certified Observable Telescope

## Setup

For trajectory `s` and checkpoint `t`, the exact observable telescope gives

`E_s = p_s^MPS - p_s^exact = sum_t c_(s,t)`.

The compressed backward observable produces a signed computable center

`C_s = sum_t ctilde_(s,t)`

and the residual-aware COT construction certifies

`|E_s - C_s| <= R_s`,

where `R_s = sum_t a_(s,t) eta_(s,t) + tau_s`.  The trace-norm radii `a`,
operator enclosures `eta`, and numerical allowance `tau` are exactly those of
the existing COT proof.  No dense exact state or exact BKS value enters `C_s`
or `R_s`.

## Theorem: signed decision-gap interval

Let trajectories `A` and `B` be compared through

`Delta_MPS = p_B^MPS - p_A^MPS`

and define the signed error center `D = C_B - C_A`.  Then the exact decision
gap satisfies

`Delta_exact in [Delta_MPS - D - (R_A+R_B),
                 Delta_MPS - D + (R_A+R_B)]`.

Proof.  Since `Delta_MPS-Delta_exact = E_B-E_A`,

`|(Delta_MPS-Delta_exact) - (C_B-C_A)|`

`<= |E_B-C_B| + |E_A-C_A| <= R_A+R_B`.

Rearranging gives the interval.  A ranking is strictly certified when both
endpoints have the same nonzero sign.

### Asymmetric-bond corollary

The two trajectory enclosures may be constructed with unrelated residual
policies `pi_A` and `pi_B`.  The same proof gives radius

`R_A(pi_A) + R_B(pi_B)`.

Thus an exhaustive grid or any oracle-free policy search can minimize paired
work subject to strict exclusion of zero without requiring symmetric bonds.

## Relation to the previous certificate

The previous COT width uses

`sum_(s,t) |ctilde_(s,t)| + R_A + R_B`

around the uncorrected MPS gap.  The signed interval instead retains temporal
cancellation inside each trajectory, cancellation between trajectories, and
recenters the decision by the computable approximation `D` to the MPS gap
error.  It does not assume cancellation in the unknown remainder: the full
`R_A+R_B` remains adversarial.

The new interval is therefore not obtained by dropping absolute values from an
upper bound.  It is a center-plus-certified-remainder statement.  Its soundness
depends on the already audited COT enclosure `|E_s-C_s|<=R_s`.

## Why bond quality need not be monotone

For a fixed checkpoint input, increasing TT-SVD bond weakly reduces the local
discarded tail.  This does not order complete recursive policies.  Different
bonds produce different represented residual states, which are propagated and
recompressed at every later backward checkpoint.  The maps are state-dependent
and the resulting trajectories are not nested.  Consequently neither
`eta_t(pi)` nor the integrated remainder `R(pi)` is guaranteed to be monotone
in a bond used throughout the trajectory.

The frozen low-bond experiment observes this effect and audits every selected
operator enclosure.  It is empirical evidence for the current recurrence, not
a general theorem that smaller bonds must improve a certificate.

## Claim boundary

Signed residual correction is related to classical dual-weighted-residual and
goal-oriented a posteriori error estimation.  The elementary recentering
identity is not claimed as a new general theorem.  The research claim to test
is the narrower combination of a signed paired decision interval, compressed
backward quantum observables, and bond allocation for certifying an algorithmic
ranking rather than a full-state approximation.
