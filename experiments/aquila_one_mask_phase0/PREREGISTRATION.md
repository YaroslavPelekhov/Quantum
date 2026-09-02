# Preregistration: one-static-mask temporal reprogramming on Aquila

Frozen before any pulse-optimization output was inspected on 2026-09-02.

## Question

Can one program-static local-detuning pattern on QuEra Aquila act as a reusable
spatial control resource?  The same mask must prepare either of two reflected
hard-blockade target states; only the temporal global controls may change.
This is deliberately stronger than using a different static mask to encode each
target and narrower than an abstract Lie-controllability claim.

The primary geometry is a four-atom path at 5.5 micrometre spacing.  Starting
from `0000`, the targets are the two reflected maximum independent sets `0101`
and `1010` (little-endian bit ordering).  The frozen mask is

`h = (0, 1/3, 2/3, 1)`.

## Hamiltonian and truth model

We use the documented Aquila Hamiltonian

`H(t) = sum(i<j) C6/r_ij^6 n_i n_j
       + ux(t)/2 sum_i X_i + uy(t)/2 sum_i Y_i
       - Delta_g(t) sum_i n_i - Delta_l(t) sum_i h_i n_i`,

where `sqrt(ux^2+uy^2) <= Omega_max` and `Delta_l <= 0`.  Exact full-Hilbert
`C6/r^6` evolution is the hardware-facing truth.  A projected hard-blockade
model is only a surrogate and any pulse found there is reevaluated in the full
model.

All numerical limits in `AQUILA_CONSTRAINTS_PROVISIONAL.json` are a frozen
documentation snapshot, not a claim about live device properties.  A fresh
`GetDevice` capture and SDK validation are mandatory before hardware.

## Exact negative control

With global controls only, reflection of the path commutes with the Hamiltonian
at every time.  The initial state is reflection-even, while the two target
amplitudes are exchanged.  Their probabilities are therefore equal and the
fidelity to either selected target is at most `1/2`.  A uniform mask is also a
global-detuning term and obeys the same ceiling.

## Frozen numerical screen

1. Compute dynamical Lie ranks for global-only, uniform-mask, and gradient-mask
   controls in projected hard-blockade and exact full-`C6` models.  Repeat the
   rank calculation across numerical tolerances.
2. Verify the global-phase rotating-frame identity numerically.  Phase is a
   global quadrature/detuning gauge resource, not a second spatial pattern.
3. Optimize hardware-bounded, piecewise-linear pulses at `T=4 us`, 17 knots,
   for each target separately but with the identical gradient mask.  Use the
   exact seeds and budgets in `protocol.json`.
4. Run the identical optimizer budget for global-only and uniform-mask
   ablations.  The exact `1/2` ceiling remains the decisive baseline; optimizer
   failure is not evidence.
5. Reevaluate every best pulse with twice the propagation resolution and after
   device-grid quantization.
6. Perturb coordinates, Rabi calibration, both detuning calibrations, and mask
   coefficients using the frozen distributions.  Report median and fifth
   percentile, never only the best seed.
7. Evaluate Markovian local-dephasing brackets.  These are sensitivity curves,
   not a substitute for the unpublished local-detuning coherence measurement.
8. Compute the pulse-shape-independent mask-action addressability bound from
   Duhamel continuity and the pigeonhole spacing of `h in [0,1]^n`.

## Pass, kill, and QPU gates

The capability passes CPU Phase 0 only if both reflected targets reach at least
0.95 fidelity in discretized full-`C6` evolution, hard-blockade transfer loses
at most 0.05, device-grid quantization loses at most 0.02, the robustness fifth
percentile is at least 0.80, and the full Lie-rank signal is tolerance-stable.

Passing those numerical gates is not an A-star novelty verdict.  It additionally
requires an adversarial primary-literature audit to show that the result is not
ordinary symmetry breaking, frequency-selective control, or a standard
controllability construction.

No QPU task is authorized in Phase 0.  Hardware becomes a candidate only after
all CPU and prior-art gates pass, live capabilities are archived, the program
passes the current SDK validator, and Braket Direct local-detuning access is
confirmed.  Failure of either target, robustness, prior art, or the live access
checks kills hardware escalation.

## Interpretation discipline

- Full Lie rank alone is not a practical capability.
- A good result for only the mask-favoured target is not reprogrammability.
- Beating an unoptimized anneal is not sufficient.
- A hardware-sized claim cannot be extrapolated from P4 without a separate
  scaling phase.
- A useful engineering primitive is not automatically A-star research novelty.

