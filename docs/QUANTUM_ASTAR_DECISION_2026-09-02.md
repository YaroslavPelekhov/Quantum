# Quantum A-star research decision, 2026-09-02

## Executive verdict

There is **no defensible A-star claim yet and no justified QPU spend**.  This is
not a stalled result: several tempting mechanisms have now been closed by exact
counterarguments or aggressive controls before hardware selection could turn
them into expensive false positives.

The strongest surviving experimental object is an Aquila-compatible,
branch-free counts witness of an interaction-by-static-mask directional
response.  It is numerically strong and has clean causal nulls, but the
underlying density-dependent Peierls mechanism has direct prior art.  The last
attempt to obtain a stronger theorem from it also fails: one mask does not
impose a generic low-rank configuration-space curvature tensor.

## Decision ledger

| branch | strongest result | decisive falsifier | status |
|---|---|---|---|
| QAOA/MPS symmetry | exact quotient and useful memory compression | ordinary twin symmetry plus event incidence explains all audited rank rows; honest Aer speedup is modest | closed as A-star |
| drift-aware QAE | exact confounding and drift/noise information bounds | generator-aligned drift is nonidentifiable; fixed gate noise restores SQL scaling | closed as A-star |
| one-mask Aquila control | full small-system Lie rank | adaptive ODE reduces coarse-grid near-unit fidelities to `0.787188` and `0.683809`; ensemble-control prior art covers the algebraic mechanism | closed as A-star |
| configuration curvature | counts witness `chi=0.242291`, exact nulls, 100% sign retention in 256 perturbations | logarithmic flux is branch dependent and the branch-free mechanism is known density-dependent Peierls hopping | closed as A-star |
| one-mask curvature compiler | exact attainable space `image(d1 P)` and a conditional edge-response bound | generic one-mask rank is already full; the observed low rank is only a perturbative tangent | closed as A-star centerpiece |

## What the last theorem establishes

For weak-drive edge response `R(omega)`, let `P` copy the phase at each distinct
transition frequency onto the corresponding configuration edges and let `d1`
be the edge-to-plaquette coboundary.  The complete local unwrapped flux space is

`image(d1 P)`.

Flatness is necessary and sufficient exactly when `d1 P alpha=0 mod 2 pi`.
When the edge frequencies are distinct, `P=I`, and a full `n`-cube has rank

`(n-2) 2^(n-1) + 1`.

Exact prime-field calculations on rational 2D inverse-sixth geometries confirm
ranks `5,17,49,129` for `n=3,4,5,6`.
The first-order interaction tangent has ranks only `2,3,4,5`, explaining the
apparently simple numerical law without supporting a finite-control low-rank
theorem.

The remaining rigorous inequality is conditional.  If a compiler must specify
`q` independent edge responses in width `W`, those responses retain normalized
magnitude at least `rho`, and a closest spectral pair is assigned phase
separation `Delta`, then a worst case obeys

`T >= 2 rho sin(Delta/2) (q-1) / W`.

This is not yet a lower bound for curvature-only compilation: the equation
`d1 A=Phi` has vertex-gauge freedom, which may change the phases assigned to
the closest frequency pair.  There is no gauge-quotiented lower bound, matching
construction under actual hardware constraints, proven end-to-end separation,
or new scalable measurement capability.

## Hardware decision

No real-server task was submitted.  The current hardware-facing curvature
packet would be suitable only as an engineering replication of known physics,
not as validation of a new A-star mechanism.  Any later execution must use
interleaved forward, reverse, zero-interaction/large-distance, equal-mask, and
palindromic schedules; preserve the counts-only estimator; and revalidate the
live device constraints immediately before submission.  Ideal shot estimates
do not include the extra decoherence documented for local detuning or device
drift.

## The only adjacent branch worth one more bounded screen

The next hypothesis should concern **resource-bounded robust compilability**,
not the existence of curvature:

> There is an explicit family of Rydberg configuration graphs and fixed-margin
> branch-free circulation targets for which every single-mask, bounded-amplitude,
> bounded-slew compiler requires superpolynomial physical time or shots, while
> a precisely specified stronger control resource has a polynomial constructive
> compiler.

This becomes potentially A-star only if one frozen cycle passes all of the
following gates:

1. A gauge-quotiented lower bound applies to arbitrary admissible waveforms,
   not just polynomial spectral ansatzes, fixed edge representatives, or one
   optimizer.
2. A matching polynomial upper construction exists for a physically meaningful
   comparator resource.
3. The separation retains nonvanishing response margin, bounded leakage, and
   polynomial measurement cost.
4. The family embeds in a realistic Rydberg geometry rather than freely chosen
   independent edge frequencies.
5. An adversarial primary-source review separates the result from classical
   time-bandwidth bounds, ensemble controllability, graph gauge theory, and
   known Peierls engineering.
6. Small exact instances and held-out geometries confirm the theorem without
   retuning.

Failure of any one gate closes this adjacent line.  Passing all six would
justify a hardware packet; until then, spending QPU budget would add evidence
for a known mechanism rather than test the new claim.

## Repository entry points

- Curvature result: `results/aquila_configuration_curvature_phase0/FINAL_REPORT.md`
- Exact compiler theorem: `experiments/aquila_configuration_curvature_phase0/COMPILER_THEOREM_AND_KILL.md`
- Machine-readable rank result: `results/aquila_configuration_curvature_phase0/compiler_rank_summary.json`
- One-mask control falsification: `results/aquila_one_mask_phase0/FINAL_REPORT.md`
- Drift-QAE falsification: `results/drift_qae_phase0/FINAL_REPORT.md`
- Sequential drift boundary: `results/interleaved_drift_boundary_phase0/FINAL_REPORT.md`

The binding research policy is simple: preserve the useful engineering
artifacts, state every negative result, and do not rename a falsified mechanism
into novelty.
