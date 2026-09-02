# Gauge-quotiented spectral-variation theorem

## Scope

This theorem concerns the first-order weak-drive response around a fixed
time-independent diagonal Hamiltonian,

`R(omega) = integral_0^T u(t) exp(i omega t) dt`.

It holds for an arbitrary integrable complex waveform `u`, including waveforms
with zeros between sampled frequencies.  It does not constrain the complete
finite-amplitude many-body propagator, where commutators, Floquet paths, and
nonlinear optimal control can generate dynamics outside this scalar-response
description.

## Gauge-quotiented quantity

Order the `E` distinct configuration-edge frequencies as
`omega_1 < ... < omega_E` and write `W=omega_E-omega_1`.  For a circle-valued
edge phase cochain `A`, define its variation in spectral order by

`TV_omega(A) = sum_(k=1)^(E-1) dist_T(A_(e_(k+1))-A_(e_k), 0)`.

For a Bianchi-consistent curvature `Phi=d1 A0`, define

`QTV_omega(Phi) = min_(d1 A=Phi) TV_omega(A)`.

On the full configuration cube, contractibility gives
`ker(d1)=image(d0)`, hence equivalently

`QTV_omega(Phi) = min_theta TV_omega(A0+d0 theta)`.

This is genuinely gauge invariant.  It corrects the rejected argument based
only on the closest pair of frequencies.

## Arbitrary-waveform weak-drive bound

Let `A_u=integral_0^T |u(t)|dt`.  Suppose every sampled response is nonzero
with a uniform normalized margin

`|R(omega_e)| >= rho A_u`,

and its phases realize `Phi`.  For adjacent spectral samples,

`|R(omega_(k+1))-R(omega_k)| <= A_u T delta_omega_k`.

If their circular phase distance is `delta_k in [0,pi]`, the reverse triangle
geometry and `sin(delta/2)>=delta/pi` give

`|R(omega_(k+1))-R(omega_k)|
 >= 2 rho A_u sin(delta_k/2)
 >= (2 rho A_u/pi) delta_k`.

Sum over the spectral order and use `sum delta_omega_k=W`:

`T W >= (2 rho/pi) QTV_omega(Phi)`.

The registered MILP minimizes the stronger weighted `L-infinity` quantity

`L_omega(Phi) = min_theta max_k delta_k/(delta_omega_k/W)`.

Because the normalized gaps sum to one, `L_omega(Phi)>=QTV_omega(Phi)`, and
directly

`T W >= (2 rho/pi) L_omega(Phi)`.

The MILP includes one integer winding per spectral adjacency, so this is not a
fixed-branch or fixed-lift optimization.  A solver incumbent is an upper bound
on `L_omega`; only its dual bound is used as a certified numerical lower bound.

An independent finite-instance certificate follows from the same quotient.
Write the adjacent spectral phase differences as `y+M theta`, where `M=Dd0`.
For any integer vector `lambda` with `lambda^T M=0`, every circular lift obeys

`L_omega(Phi) >= dist_T(lambda^T y,0)
                  / sum_j |lambda_j| (delta_omega_j/W)`.

The integer condition makes all winding contributions multiples of `2pi`, and
the nullspace condition cancels every vertex gauge.  Sparse integer dual
circuits are therefore a route to human-checkable hard targets.  This cycle
does not prove a scalable succinct circuit family.

## Worst-case existence theorem

For the full `n`-cube, let `V=2^n`, `E=n 2^(n-1)`, and `m=E-1`.  For every
ordering of distinct edge frequencies and every `n>=7`, there exists a
Bianchi-consistent circle-valued curvature with

`QTV_omega(Phi) >= pi(E-1)/(8e)`

and therefore

`T >= rho(E-1)/(4e W)`.

Proof sketch:

1. Draw the `E` phases of `A0` independently from Haar measure on the circle.
   For any fixed vertex gauge, the `m` consecutive spectral increments are
   jointly Haar on the `m`-torus, so their absolute circular distances are
   independent uniform variables on `[0,pi]`.
2. A simplex-volume bound and `m! >= (m/e)^m` give
   `Pr[TV <= pi m/(4e)] <= 4^(-m)`.
3. Fix the root vertex phase.  A sup-norm net of the remaining vertex torus
   with radius `eta=pi/(32e)` has at most `87^(V-1)` points.
4. Moving every vertex phase by at most `eta` changes each adjacent edge-phase
   difference by at most `4 eta`, hence changes total variation by at most
   `4 eta m=pi m/(8e)`.
5. Therefore
   `Pr[min_theta TV < pi m/(8e)] <= 87^(V-1) 4^(-m) < 1` for `n>=7`.

The last inequality already has log upper bound about `-52.5` at `n=7`.
This proves existence and also shows that Haar-random edge targets are hard
with overwhelmingly high probability as `n` grows.

For two-dimensional arrays with fixed minimum spacing, bounded onsite range,
and fixed `C6`, the absolutely convergent `1/r^6` interaction sum keeps `W`
bounded independently of array area.  Pairwise-distinct generic onsite offsets
together with generic coordinates, or generic joint perturbations of both,
remove the remaining frequency collisions almost surely.  Coordinate changes
alone cannot remove collisions between coordinate-independent empty-set edges.
Thus the formal worst-case weak-drive bound can be exponential in atom count.

## Why this is not an A-star theorem

The hard target uses `Theta(E)` independent random phases.  Since
`E=n2^(n-1)`, the lower bound is only linear in the explicit target-description
length.  No succinct poly(`n`) deterministic hard target, polynomial-time
verification certificate, or matching polynomial compiler with one additional
physical control mode is established.

The response margin is also essential.  Letting `rho` shrink exponentially
removes the time bound, while fixed-area transition probabilities and shot
cost then deteriorate.  This cycle does not prove a complete time-energy-shot
tradeoff.

## Falsification of the old closest-gap argument

Any selected pair of distinct configuration edges can be assigned equal phase
by a vertex gauge, and every edge on a spanning tree can be gauged to zero.
Consequently, exponentially small minimum frequency spacing alone proves
nothing about curvature cost.

For a localized target `Phi=d1(phi 1_e)`, one representative has only one
nonzero edge; therefore `QTV<=2 dist_T(phi,0)`, independently of `E`.  Hardness
must be distributed over the gauge quotient, not attached to one crowded pair.

For one square an exact sanity check is available.  Let `s_k` be the oriented
sign of the `k`th edge in spectral order and `C_j=sum_(k<=j)s_k`.  Then

`QTV(phi) = dist_T(phi,0) / max_j |C_j|`.

At `phi=pi`, alternating signs give `QTV=pi`, while order `++--` gives
`QTV=pi/2`.

## Binding conclusion

`WEAK_DRIVE_QTV_THEOREM_VALID` and
`FULL_PROPAGATOR_RESOURCE_SEPARATION_UNPROVED`.

The theorem is retained as a precise technical result.  It must not be stated
as an Aquila full-dynamics lower bound or an A-star centerpiece.
