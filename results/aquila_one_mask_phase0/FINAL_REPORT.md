# Final report: Aquila one-static-mask Phase 0

## Verdict

**KILL_ONE_MASK_PHASE0**

- CPU numerical gates passed: **False**
- Broad A-star novelty: **KILLED by prior art**
- QPU eligible under the preregistration: **False**
- QPU tasks submitted: **0**

The one-mask gradient is a real spatial symmetry-breaking resource, but the
underlying frequency-selective/Vandermonde controllability mechanism is known.
The run is retained as a hardware-feasibility audit and an enabling lemma, not
rebranded as a primary novelty claim.

## Primary target results

The optimizer appeared to reach `0.9995` and `0.9998` on its frozen two-
substep internal grid.  That was a numerical false positive.  The midpoint
sequence converged monotonically under 2, 4, 8, 16, 32, and 64 substeps, and an
adaptive DOP853 reference (`rtol=2e-10`, `atol=2e-12`) gave the definitive
hardware-facing values below.

| target mask | adaptive-ODE full-C6 fidelity | quantized adaptive-ODE fidelity | frozen perturbation p05 |
|---:|---:|---:|---:|---:|---:|
| `0101` | 0.787188 | 0.787195 | 0.105305 |
| `1010` | 0.683809 | 0.683802 | 0.126006 |

The robustness values use the frozen eight-substep screen and are already far
below the `0.80` gate; refining them cannot reverse the decision.  Full
per-seed convergence is in `reference_convergence.csv` and the independent
diagnosis is in `REFERENCE_AUDIT.md`.

Global-only and uniform-mask dynamics obey an exact per-target fidelity ceiling
of 0.5 by reflection symmetry; this does not depend on optimizer performance.

## Structural falsification

- Rotating-frame phase-gauge error: `5.721e-12`.
- Global-only reflection commutator norm: `0.000e+00`.
- Gradient-mask full Lie rank stable across frozen tolerances:
  `True`.
- Ramp-limited local-detuning action in the provisional 4 us window:
  `487.559713 rad`.
- Necessary perfect two-frequency X/I addressability capacity from this action:
  at most `173` labels.
- At 256 packed labels the unavoidable operator-norm error from this necessary
  bound is at least `0.229107`.

The action result is an ensemble/twin-site bound, not a universal limit for
arbitrary geometries whose interactions already distinguish sites.

## Hardware decision

No hardware job was submitted.  Local detuning is an experimental Braket Direct
capability, its use carries an extra decoherence warning, this environment has
neither a live device snapshot nor confirmed access, and the adversarial
prior-art gate is negative.  The saved pulses are simulation artifacts, not
claimed hardware programs.

## Research continuation

The next hypothesis changes the scientific object: use finite native `C6/r^6`
tails plus a nonlinear, time-asymmetric spectral response to generate a
gauge-invariant Wilson-loop phase on an independent-set configuration
plaquette.  It must vanish for zero interaction, equal masks, palindromic
drives, and large spacing, reverse sign under schedule reversal, and survive a
matrix-log branch audit before it can become a hardware candidate.
