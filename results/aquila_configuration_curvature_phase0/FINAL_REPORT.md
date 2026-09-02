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
