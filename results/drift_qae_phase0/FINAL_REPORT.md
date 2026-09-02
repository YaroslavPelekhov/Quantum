# Drift-aware amplitude estimation Phase-0 final report

## Verdict

**KILL_BROAD_DRIFT_ASTAR**.  No QPU run is authorised from this branch.

The proposed broad claim does not survive decomposition into physically
distinct nuisance models.  This is a CPU-only structural and Monte Carlo
falsification; it contains no hardware observations.

## Decisive structural results

1. A coherent calibration offset entering the same generator as the ideal
   amplitude is exactly nonidentifiable.  The frozen pair differs in `theta` by
   0.048000, has zero nuisance
   total variation, and has maximum probability gap
   0 at every
   tested depth.
2. The bounded-variation visibility search found 35
   exact unanchored witnesses among 35 frozen rows.
   The largest tested exact theta separation was
   0.0071428571.
3. Treating visibility as a separate nuisance at every round leaves at most
   3.46e-16 of the known-nuisance
   local Fisher information.  Matched anchors restore at least
   57.684%; this is ordinary
   calibrated-nuisance information, not evidence for a new drift boundary.
4. For fixed gate-accumulating rate `gamma`,
   `I_Q <= 2 Q / (e gamma)`, hence local RMSE is
   `Omega(sqrt(gamma/Q))`.  Fixed nonzero depth noise therefore permits only
   standard-quantum-limit physical-depth scaling even when the nuisance is
   known.

## Frozen Monte Carlo screen

- Post-circuit/readout anchored median tail RMSE slope:
  -0.0201
- Strong direct `k=1` comparator median tail RMSE slope:
  -0.5051
- Gate-accumulating anchored median tail RMSE slope:
  0.0782
- Maximum readout anchored branch-failure rate:
  39.844%
- Maximum gate anchored branch-failure rate:
  25.391%

Positive readout-model scaling, if present, cannot rescue the hardware-facing
claim: depth-independent visibility was assumed, while the separate physical
model has exponential visibility loss and an analytic SQL ceiling.

## Research conclusion

The attractive phrase "QAE under drift" hides three different problems:

- generator-aligned drift requires a trusted reference or is impossible;
- post-circuit visibility drift is removable by matched calibration under the
  common-nuisance assumption;
- depth-accumulating noise destroys asymptotic quadratic scaling before drift
  becomes the novel issue.

Consequently there is no defensible A* contribution in the broad candidate as
registered.  A future branch would need a different computational object or a
restricted, independently validated anchor model with a theorem not reducible
to these three cases.  The current result must not be advertised as a positive
quantum advantage.
