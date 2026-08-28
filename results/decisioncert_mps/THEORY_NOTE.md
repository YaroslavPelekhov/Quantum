# Why discarded weights alone cannot give a universally sharper bound

For truncation event t, the logged normalized discarded weight determines one
local geometric fact: the pre/post-truncation pure states have fidelity
`1-w_t` and Fubini-Study angle

`alpha_t = asin(sqrt(w_t))`.

If no other information is retained, the only universal composition rule is
the triangle inequality. It gives

`A <= min(pi/2, sum_t alpha_t)` and `trace_distance <= sin(A)`.

This use of the triangle inequality is information-theoretically sharp. In a
two-dimensional projective Hilbert subspace, points can be placed successively
on one geodesic with separations `alpha_t`. Their endpoint separation is then
the sum of the local angles until pi/2, and a binary Helstrom projector attains
the corresponding trace distance. The list `{w_t}` does not encode whether
real truncation perturbations align coherently in this worst-case direction,
cancel, or point mostly outside the final BKS observable.

Consequently, a universally smaller formula based only on unordered or ordered
discarded weights requires an additional assumption such as incoherent/random
error orientation. Quantities like `sqrt(sum w_t)`, root-sum-square angles, or
`sqrt(1-product_t(1-w_t))` express such an assumption and must remain
heuristics unless that structure is proved for the simulator/circuit family.

A rigorous improvement must add information absent from the weight list. The
most relevant options are:

1. backward propagation of the BKS projector or a tractable relaxation of it;
2. validated upper/lower tensor-network contractions for BKS probability;
3. per-truncation overlaps between discarded Schmidt subspaces and the
   backward observable environment;
4. a formal stochastic/incoherence theorem with auditable assumptions.

The empirical stability envelope studied in this follow-up adds independent
multi-fidelity simulations rather than claiming a tighter theorem. It is an
abstention rule, not a proof of the accepted sign.

## A rigorous probability-aware refinement that is still insufficient

The global angle can be converted to a tighter interval for a known projector
probability q. A two-outcome measurement maps a pure state to the unit vector
`(sqrt(q), sqrt(1-q))`; fidelity monotonicity implies that its classical angle
cannot exceed the state angle A. Therefore

`|asin(sqrt(p_exact)) - asin(sqrt(q_MPS))| <= A`.

Inverting this relation gives the event-angle interval used in the follow-up
report. This refinement is rigorous and probability-aware, but it cannot help
once A is near pi/2. Empirically it retained the same 14 / 50 coverage. Thus
the missing ingredient is not merely a sharper final conversion from state
distance to event probability; it is per-truncation information about the BKS
observable direction.
