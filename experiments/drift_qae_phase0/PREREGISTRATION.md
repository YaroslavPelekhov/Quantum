# Frozen preregistration: drift-aware amplitude estimation Phase 0

Frozen on 2026-09-02 before numerical results were inspected.

## Candidate claim

For a fixed ideal amplitude `a = sin(theta)^2` observed through a
time-varying nuisance channel, there may be a nontrivial drift-rate boundary
below which amplified estimation retains super-classical physical-resource
scaling and above which it is information-theoretically impossible.

Phase 0 does **not** assert this claim.  It tries to falsify it before any QPU
use.  A successful algorithm without a lower bound, or a positive result in a
post-circuit model that fails in a depth-accumulating model, does not pass.

## Frozen observation models

At amplification depth `k`, a target bit has centered expectation

```text
E[Y | theta, k, w] = w cos(2 k theta).
```

The two meanings of `w` are kept separate throughout:

1. **A / gate-accumulating:** `w = exp(-gamma_t k)`, where `gamma_t` is a
   bounded-variation per-layer rate.
2. **B / post-circuit readout:** `w = v_t`, where `v_t` is a
   bounded-variation depth-independent visibility.

An anchor has known ideal centered expectation one and the same `w` at the
same depth.  Every anchor is charged its full depth in the physical-depth
budget.  An oracle-nuisance estimator is reported only as an unattainable upper
control.  It is never the resource-matched headline comparator.

The schedule is the fixed odd ladder `k = 1, 3, 7, ..., 2^L - 1`.  All numeric
values, amplitudes, held-out drift phases, shots, seeds, and thresholds are in
`protocol.json`.

## Structural falsification tests

1. **Coherent-offset identifiability.** If an unknown calibration offset enters
   the same generator as `theta`, construct two distinct ideal amplitudes with
   identical observation laws.  This determines whether a trusted reference
   is logically necessary.
2. **Visibility confounding without anchors.** Search for two distinct
   amplitudes and two admissible bounded-variation visibility paths giving the
   same Bernoulli probability at every scheduled depth.
3. **Nuisance Fisher audit.** Compare known nuisance, one stationary unknown
   nuisance, independent per-round nuisance without anchors, and matched
   per-round anchors.
4. **Depth attenuation.** Test the analytic fixed-rate information ceiling and
   the simulated scaling of the full geometric ladder.
5. **Estimator screen.** Compare anchored, nuisance-oracle, nominal-unanchored,
   and a stronger `k=1` direct-sampling baseline using held-out drift paths.

## Frozen decision gates

The broad A* direction is killed if the combined audit yields the structural
trichotomy below:

- without a trusted reference, coherent amplitude-direction drift is exactly
  nonidentifiable;
- without anchors, admissible visibility drift exactly confounds distinctions
  at the amplified resolution;
- with matched anchors, post-circuit drift is reduced to ordinary calibrated
  nuisance estimation rather than producing a new drift-specific boundary;
- under fixed nonzero depth-accumulating noise, the best physical-depth scaling
  is no better than the standard quantum limit.

Model A is independently killed for hardware advantage if its tail error slope
is greater than `-0.6` or its analytic information ceiling implies
`Omega(Q^-1/2)` risk.  A positive Model B result cannot rescue Model A.

Model B can survive only if all of the following occur:

- no exact admissible unanchored confounding witness is found at the tested
  amplified scales;
- the anchored estimator has less than 5% branch failures on every held-out
  path;
- its tail scaling is super-classical and beats the equal-physical-depth
  direct baseline;
- the effect cannot be explained solely by a visibility floor plus ordinary
  per-round calibration;
- a sharp lower-bound parameter depending on drift, rather than only on noise
  strength or calibration availability, remains to be proved.

Any failure forbids QPU spending and forbids reframing this Phase-0 result as a
positive A* contribution.

## Statistical scope

Monte Carlo summaries are descriptive falsification evidence, not hardware
data and not a theorem.  Seeds are deterministic.  Median absolute error,
RMSE, branch-failure frequency, local efficient Fisher information, and tail
log-log slopes are all reported.  Structural exact-equality witnesses take
precedence over favorable average-case curves.

