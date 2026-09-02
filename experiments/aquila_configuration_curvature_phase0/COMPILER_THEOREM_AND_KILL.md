# One-mask weak-curvature compiler theorem and terminal novelty verdict

This note is a post-validation structural result.  It applies to first-order
weak-drive links, or to a fixed continuously continued Floquet branch with all
response divisors nonzero.  It does **not** turn the branch-dependent finite-
drive principal logarithm into a physical invariant.

## Setup

Let `F` be a downward-closed family of feasible bit configurations.  Its
oriented addition edges are `e=(S,i)` with `S` and `S union {i}` in `F`.  For a
diagonal Rydberg Hamiltonian,

`omega_(S,i) = epsilon_i + sum_(k in S) V_ik`,

where `epsilon_i=a+b h_i` for one static grayscale mask.  In first order in a
complex global drive `u(t)=Omega(t) exp(-i phi(t))`, every edge samples the same
temporal response

`R(omega) = integral_0^T u(t) exp(i omega t) dt`

(for an analytic-log response, absorb its known nonzero divisor into `R`).
Write `alpha(omega)=arg R(omega)`.

For a square `(S;i,j)`, the exact unwrapped curvature is

`Phi_(S;ij) = alpha(x_i) + alpha(x_j+V_ij)
            - alpha(x_i+V_ij) - alpha(x_j)`,

with `x_l=epsilon_l+sum_(k in S) V_lk`.  This is a discrete mixed derivative,
not a new gauge mechanism.

## Exact attainable-space theorem

Let `P` replicate one spectral phase variable onto all configuration edges with
the same transition frequency, and let `d1` be the oriented edge-to-square
coboundary matrix.  Then the locally attainable unwrapped flux space is exactly

`image(d1 P)`, with dimension `rank(d1 P)`.

Flatness is necessary and sufficient:

`d1 P alpha = 0 mod 2 pi`

if and only if there is a vertex phase `theta_S` satisfying

`alpha(omega_(S,i)) = theta_(S union {i}) - theta_S mod 2 pi`.

Proof: edge phases are the cochain `P alpha`; Wilson phases are its coboundary.
The downward-closed cubical complex is star-shaped under coordinate contraction
and hence contractible.  Its first cohomology vanishes, so every closed edge
cochain is a vertex coboundary.

If all edge transition frequencies are distinct, `P=I`.  Contractibility gives

`rank(d1) = N1 - N0 + 1`,

where `N0` and `N1` are the numbers of configurations and addition edges.  For
the full `n`-cube,

`rank(d1) = (n-2) 2^(n-1) + 1`.

Every Bianchi-consistent plaquette tensor is then attainable in the ideal
finite-sample weak-drive model.  To see existence constructively, solve
`d1 A=Phi`, choose nonzero complex target responses `y_e=r_e exp(i A_e)`, and
interpolate them at the distinct frequencies.  The finite Fourier Gram matrix

`G_ef = integral_0^T exp(i(omega_e-omega_f)t) dt`

is positive definite, so a finite complex waveform exists.  Scaling all `y_e`
can meet an amplitude ceiling, but also scales the measurable signal to zero.

This theorem falsifies the proposed exact "one mask implies low-rank
curvature" claim.  A second mask may split collisions and improve conditioning,
but cannot increase the already-full generic algebraic rank.

## Why the small-signal result looked rank one

Under `V -> lambda V`, Taylor expansion gives

`Phi_(S;ij) = lambda V_ij [alpha'(epsilon_j)-alpha'(epsilon_i)]
              + O(lambda^2)`.

It is independent of the base configuration at first order and has dimension
at most `n-1`.  Equality holds for the full cube when the nonzero interaction
graph is connected.  If also
`epsilon_i=a+mu h_i`, then

`Phi_(S;ij) = lambda mu alpha''(a) V_ij (h_j-h_i)
              + O(lambda mu^2 + lambda^2)`.

For one fixed mask this joint tangent is a one-dimensional line.  The measured
`chi proportional to V delta_h` collapse is therefore a perturbative tangent,
not a finite-control expressivity theorem.

## Conditional resource bounds

Let `A=int |u(t)|dt`.  Since

`|R(omega)-R(nu)| <= A T |omega-nu|`,

two target responses of magnitude at least `r` and phase separation `Delta`
must satisfy

`A T |delta_omega| >= 2 r sin(Delta/2)`.

With normalized response margin `rho=r/A`,

`T |delta_omega| >= 2 rho sin(Delta/2)`.

If a compiler must independently specify `q` edge responses whose frequencies
occupy width `W`, pigeonhole gives `delta_min <= W/(q-1)`.  An arbitrary
edge-response compiler therefore has worst cases requiring

`T >= 2 rho sin(Delta/2) (q-1)/W`.

For the full configuration cube `q` can be `n 2^(n-1)`.  If `W=O(n)`, this is
an exponential time-bandwidth obstruction for arbitrary edge-response
compilation despite full algebraic rank.  It is **not yet a lower bound for a
curvature-only compiler**: the solutions of `d1 A=Phi` have vertex-gauge
freedom `A -> A+d0 theta`, and no proof yet forces every representative to
separate the closest spectral pair.

Where `|R|>=rho A` over the relevant energy rectangle,

`|alpha''| <= T^2 (rho^-1 + rho^-2)`,

and hence

`|Phi_ij| <= |V_ij| |x_i-x_j| T^2 (rho^-1 + rho^-2)`.

The local curvature-amplitude inequality is gauge independent.  The
frequency-packing inequality is conditional on independently targeted edge
responses.  Neither supplies a matching efficient construction under Aquila
slew, one-sign detuning, finite lifetime, leakage, and noise.

## Exact computational audit

`compiler_rank_audit.py` constructs the cubical coboundary matrix and checks
ranks over the prime field `p=2^31-1`.  For `n=3,4,5,6` it confirms full ranks
`5,17,49,129` and first-interaction-order ranks `2,3,4,5`.

The archived witnesses use exact rational two-dimensional geometries with
`V_ij=1/||r_i-r_j||^6`, represented in the prime field, and onsite energies
realisable as `epsilon_i=a+b h_i` with one mask `h_i in [0,1]`.  For polynomial
spectral phases
`alpha(x)=sum_(q=0)^d c_q x^q`, the exact finite-field profile is

`rank = min(max(0,d-1), full_flux_rank)`

through `n=6`.  Thus full rank first appears at degrees `6,18,50,130`.  This is
an exact witness for the tested sizes, not a general proof of that polynomial
rank formula.  A nonzero minor modulo `p` (all rational denominators are
invertible) implies that the corresponding rational, and therefore real, minor
is nonzero.  The witness establishes geometric algebraic rank, not compliance
with every live-device numerical constraint.  Coordinates and exact affine-mask
representations are archived in the
[geometry witnesses](../../results/aquila_configuration_curvature_phase0/compiler_geometry_witnesses.json).

## Prior-art and terminal A-star verdict

The ingredients are standard finite-ensemble/Fourier interpolation, graph
gauge cohomology, and density-dependent Peierls hopping.  Closest structural
sources include:

- Altafini, Vandermonde transition separation and connected-graph quantum
  controllability: https://arxiv.org/abs/quant-ph/0110147
- Schirmer, Pullen, and Solomon, simultaneous/selective controllability:
  https://arxiv.org/abs/quant-ph/0503150
- Harrison, Keating, and Robbins, graph gauge potentials and fundamental-cycle
  flux: https://arxiv.org/abs/1101.1535
- Nixon, Uenal, and Schneider, scalar modulation to programmable Peierls links
  and plaquette flux: https://arxiv.org/abs/2309.12124

> **KILL the one-mask curvature-compiler branch as an A-star centerpiece.**
> Generic one-mask algebraic rank is already full; the apparent rank-one law is
> perturbative; and the remaining conditional edge-response bound is not a
> curvature-only lower bound, let alone a tight Aquila-constrained lower/upper
> separation or scalable hardware capability.  Retain this theorem as a
> technical negative result and do not rebrand it.
