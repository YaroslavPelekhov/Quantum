# Decision-certified asymmetric resource allocation

## Object of optimization

For competing trajectories `A` and `B`, fidelity level `l` returns an estimate
`q_(s,l)`, a sound observable radius `E_(s,l)`, and cost `C_(s,l)`. We solve

`min C_(A,l_A) + C_(B,l_B)`

subject to the two intervals
`[q_(A,l_A)-E_(A,l_A), q_(A,l_A)+E_(A,l_A)]` and
`[q_(B,l_B)-E_(B,l_B), q_(B,l_B)+E_(B,l_B)]` being disjoint.

This is a decision objective. It neither asks for a uniformly accurate state nor
minimizes the error of one observable on one trajectory. The two resource levels
may differ because only separation of the competing intervals matters.

## Soundness theorem

Assume each reported interval contains its exact observable value. If the two
reported intervals are disjoint, their ordering equals the ordering of the exact
values. Therefore a policy may stop at any data-dependent time at which the
intervals become disjoint without invalidating the decision certificate.

Proof: if the upper endpoint for `A` is below the lower endpoint for `B`, every
value in `A`'s interval is below every value in `B`'s interval; the exact values
belong to those intervals by assumption. The reverse case is identical.

If a nested refinement sequence has radii converging to zero and the exact gap
is nonzero, the stopping rule eventually terminates, provided the estimates
converge to their exact values.

## Novelty boundary

The claim under test is deliberately narrower than “adaptive MPS is new.” DMRG
state targeting, adaptive bond dimensions, fidelity-controlled simulation, and
observable-specific backward propagation all have prior art. The proposed unit
of novelty is joint, asymmetric allocation across competing trajectories for a
strict comparative decision, with a stopping certificate and an explicit cost
objective. A broader priority claim requires a systematic literature review.

The current 5 x 5 experiment is a finite portfolio oracle. It establishes that
the objective is non-vacuous and measures attainable savings. It is not yet a
learned online allocator. The next methodological step is to predict transferable
allocations from design instances and test them under a frozen held-out protocol.
