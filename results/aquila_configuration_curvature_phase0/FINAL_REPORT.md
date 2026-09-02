# Final report: Aquila configuration-space curvature Phase 0

## Verdict

**MECHANISM_PARTIAL_ASTAR_KILL**

- Frozen numerical mechanism gates passed: **False**
- A-star novelty: **KILLED by density-dependent Peierls-phase prior art**
- QPU eligible: **False**
- QPU tasks submitted: **0**

The physically defensible result is a branch-free, counts-only interaction-by-
mask directional response.  A Wilson phase extracted from a matrix logarithm
is a useful mechanistic diagnostic but is not branch independent.

## Development pulse

| quantity | adaptive-ODE result |
|---|---:|
| counts witness `chi` | 0.242291361 |
| principal-log flux | 1.570505745 rad |
| `sin(flux)` | 0.999999958 |
| edge geometric mean | 1.994567836 rad/us |
| two-bit leakage / edge | 0.312865955 |
| branch-cut margin | 0.984628852 rad |
| reverse-transpose error | 6.058e-10 |

Exact zero-interaction, equal-mask, local-envelope-off, and palindrome controls
are archived in `exact_controls.csv`.  Reversal changes the signs of both the
principal diagnostic and `chi`.

## Branch falsification

The principal branch gives flux `1.570506`, while
continuous Hamiltonian scaling gives `-1.360717`.
Across the 27 common-shift-reduced nearby logarithm branches, `sin(flux)` spans
`[-0.998809,
1.000000]`.  Therefore the
effective-flux sign/locality is branch dependent.  The native `chi` observable
does not use a logarithm and survives this falsification.

## Held-out mechanism checks

- Weak analytic formula maximum circular error:
  `1.262e-11` rad.
- Held-out distance exponent: `-6.662409`
  (prediction `-6`).
- Small interaction-times-mask-contrast fit: coefficient
  `0.03149712`, centered `R2=0.99860997`.
- Perturbation `|chi|` fifth percentile: `0.210224`;
  sign retention `100.000%`.
- Nominal ideal-model five-sigma plan: `327` shots per schedule;
  at 1,000 shots the ideal z-score is `8.747`.

The shot calculation omits the documented extra local-detuning decoherence and
device drift.  It is a planning value, not a hardware result.

The distance exponent is the sole failed numerical gate.  A clearly labelled
post-hoc analytic extension to 22--54 um gives `-6.023046`, showing that the
frozen 14--22 um window had not yet reached the small-interaction asymptote.
This diagnosis does not change the preregistered partial-pass status; see
`POSTHOC_ASYMPTOTIC_NOTE.md`.

## Why this is not A-star novelty

The mixed finite-difference mechanism is density-dependent complex hopping.
Interaction-induced plaquette flux in Fock space, Rydberg occupancy-dependent
Peierls phases, chiral Rydberg dynamics, and Peierls-phase tomography all have
direct prior art.  The exact one-mask Aquila integration appears unreported in
the targeted audit, but platform intersection alone is insufficient.

The next defensible A-star object would need a complete characterization of the
curvature tensor attainable with one rank-one spatial mask, necessary-and-
sufficient flatness and tight physical resource bounds, plus a scalable
phase-sensitive hardware capability beyond this known mechanism.

## Terminal compiler falsification

That proposed next object was tested rather than promoted.  The exact
weak-drive characterization is `image(d1 P)`, where `P` shares a spectral
phase across transition-frequency collisions and `d1` is the edge-to-square
coboundary.  Flatness is exactly `d1 P alpha = 0 mod 2 pi`.  For generic
distinct edge frequencies, one static mask already has full Bianchi-consistent
curvature rank

`(n-2) 2^(n-1) + 1`.

Exact finite-field witnesses using rational 2D inverse-sixth interactions give
ranks `5, 17, 49, 129` for `n=3,4,5,6`.
The first-order-in-interaction tangent has only ranks `2,3,4,5`, which explains
why the numerical small-signal law looked low rank without making it a global
compiler obstruction.  Polynomial spectral phases reach the full tested ranks
at degrees `6,18,50,130`.

A conditional physical bound remains: a compiler required to specify `q`
independent edge responses in bandwidth `W`, with normalized response margin
`rho` and a worst-case phase separation `Delta`, requires

`T >= 2 rho sin(Delta/2) (q-1) / W`

in the worst case.  This does **not** yet lower-bound curvature-only compilation,
because `d1 A=Phi` has vertex-gauge freedom.  There is no gauge-quotiented
lower bound, matching Aquila-constrained construction, or hardware capability
result.

**Terminal verdict: `KILL_ONE_MASK_LOW_RANK_CURVATURE_HYPOTHESIS`.**  Retain
the structural theorem and exact audit as a useful negative result, but do not
rebrand this branch as an A-star contribution.  See the
[compiler theorem](../../experiments/aquila_configuration_curvature_phase0/COMPILER_THEOREM_AND_KILL.md),
[machine-readable verdict](compiler_rank_summary.json), and
[rank diagnostic](compiler_rank_diagnostics.png).
