# Preregistration: gauge-quotiented curvature-resource Phase 0

Frozen on 2026-09-02 before reading any outcomes for the validation tags in
`protocol.json`.

## Question

The parent cycle proved that one static mask has generically full weak-drive
curvature rank.  Its nearest-frequency time-bandwidth inequality applied only
to independently fixed edge responses, not to a curvature class: every
solution of `d1 A=Phi` may be changed by a vertex gauge `A -> A+d0 theta`.

This cycle asks whether minimization over that complete gauge freedom still
leaves a scalable physical resource obstruction.

## Frozen mathematical observable

For the full configuration cube, let `A0` be the deterministically hashed edge
phase vector and `G=d0` the oriented vertex-to-edge incidence matrix.  Sort all
distinct transition frequencies.  The exact circular quotient cost is

`L_circ(Phi) = min_theta max_j dist_2pi((D(A0+G theta))_j,0) / delta_omega_j`,

where `D` differences adjacent entries in spectral order and frequencies are
normalized to unit width.  Since `ker(d1)=image(d0)` on the cube, this searches
all edge-phase representatives with the same curvature `Phi=d1 A0`.

It will be solved as a mixed-integer linear program with one winding integer
per adjacent spectral pair.  Bounding vertex phases by `[-pi,pi]` is complete
modulo vertex gauge.  The registered winding range `[-3,3]` covers every
difference of two bounded edge gradients plus the hashed phase range.

If all response magnitudes satisfy `|R(omega)| >= rho int|u|dt`, the Fourier
Lipschitz inequality and `sin(x/2)>=x/pi` for `x in [0,pi]` imply the certified
conditional bound

`T * physical_frequency_width >= (2 rho/pi) L_circ(Phi)`.

Unlike the parent bound, this quantity is explicitly gauge quotiented.

## Frozen instances and targets

The two coordinate/mask families, particle counts, SHA-256 target tags, four
target identifiers per size, physical `C6`, and frequency normalization are
fixed verbatim in `protocol.json`.  Geometry A is development; geometry B is
held out.  No target is selected or normalized after hashing.

The full cube is intentional: it is the hardest algebraic case and makes the
gauge equality exact.  It is not a claim that all `2^n` configurations remain
equally measurable under blockade and decoherence.

## Numerical gates

All registered gates in `protocol.json` must pass.  Scaling is fitted by OLS to
`log2(median L_circ)` against `n`, using `n=4..7` for development and `n=5..8`
for heldout.  Solver timeouts, nonzero MILP gaps above threshold, frequency
collisions, or a nontrivial-flux failure count against the claim.

The unquotiented `theta=0` value and a continuous unwrapped LP are controls,
not substitutes for the circular MILP.

## A-star and hardware kill rules

Passing numerical exponential scaling is insufficient.  An A-star candidate
exists only if **all six** qualitative gates in `protocol.json` pass, including
a theorem for arbitrary admissible waveforms and a matching polynomial
construction for a physically meaningful stronger resource.  Random hashed
targets alone are not an explicit scalable theorem family.

Any reduction to ordinary spectral interpolation, graph gauge theory,
ensemble controllability, or known Peierls engineering kills novelty.  Any
lower bound obtained only by fixing an edge representative repeats the parent
error and is rejected.

This Phase 0 authorizes zero QPU tasks.  Hardware becomes eligible only after
the theorem, construction, signal/shot, prior-art, and heldout gates all pass.

## Exploratory disclosure

The algebraic rank theorem, the missing gauge quotient, and the parent
conditional bound were known before this freeze.  Parallel exploratory agents
were asked to attack the general theorem and numerical formulation, but their
outcomes had not been read when the validation tags and gates above were
written.  Any subsequent change is post-hoc and must be labelled as such.
