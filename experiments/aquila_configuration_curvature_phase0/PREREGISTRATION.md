# Preregistration: Aquila configuration-space curvature validation

Frozen on 2026-09-02 after the explicitly disclosed development preflight and
before the held-out validation outputs were computed.

## Scientific object

For two compatible atoms, the computational/configuration states form a square

`00 -> 01 -> 11 -> 10 -> 00`.

Native finite interaction changes an addition energy when the other site is
occupied.  A time-asymmetric global spectral response can therefore give the
four effective edges a nonzero Wilson product even though the only spatial
control is one program-static detuning mask.

For a weak two-kick response with spectral phase `alpha`, the predicted flux is

`Phi = alpha(e1) + alpha(e2+V) - alpha(e1+V) - alpha(e2)`.

This is a mixed finite difference.  It must vanish without `V`, with equal
site arguments, with affine spectral phase, and for the frozen palindrome
control.  Schedule reversal must reverse its sign.

## Primary definitions

The one-cycle unitary is integrated with adaptive DOP853.  The principal
effective Hamiltonian is `H_F = i log(U)/T`, hermitized after logging.  With
matrix convention `H[destination, source]`, the oriented Wilson product is

`H[1,0] H[3,1] H[2,3] H[0,2]`.

Its argument is `Phi`; `sin(Phi)` is the chirality witness because flux zero or
pi is time-reversal invariant.  Every edge magnitude and the eigenphase
branch-cut margin are reported.

The native counts-only witness from initial `00` is, in integer-mask notation,

`chi = (p_F(mask 1)-p_R(mask 1)) - (p_F(mask 2)-p_R(mask 2))`,

where `R` is the exactly time-reversed waveform.  This is a proposed hardware
observable, not phase tomography.

## Frozen validation

1. Recompute the disclosed development pulse with DOP853 and midpoint grids of
   1, 2, 4, 8, 16, 32, and 64 substeps per knot interval.
2. Verify pulse ranges, endpoints, time grid, and slew against the provisional
   Aquila limits; live properties remain mandatory before any hardware use.
3. Test zero interaction, equal mask, palindromized pulse, and reversal.  Use
   `sin(Phi)` for nulls.  Verify invariance under 64 frozen random diagonal
   basis rephasings.
4. Enumerate logarithm branches with one common integer shift removed and each
   remaining eigenphase shift in `{-1,0,1}`.  This is an adversarial diagnostic:
   a principal/continued flux is not called branch-independent if the spread is
   material.
5. Run 256 frozen perturbations of distance, mask, and field calibrations.
6. Compute the multinomial shot variance of `chi` and shots required for a
   nominal five-sigma separation.
7. Independently validate the two-kick weak-drive formula by a continuous log
   tracked from zero drive at the three frozen scales.
8. Run the frozen held-out distance scan and fit the small-interaction log slope
   against the predicted `r^-6` law.
9. Without reoptimization, test the frozen small `V * mask-contrast` rectangle
   and require the through-origin mixed-term model to reach `R^2 >= 0.98`.
10. Apply the identical development waveform without reoptimization to the
    frozen three- and four-atom geometries.  Report all vacuum pair witnesses
    and their zero-interaction and palindrome controls.

## Interpretation and terminal decisions

Passing every numerical gate validates the mechanism and a possible counts-only
Aquila integration benchmark.  It does not establish topology, scalable chiral
transport, quantum advantage, or A-star novelty.

The A-star gate is frozen negative regardless of outcome.  Density-dependent
Peierls phases, interaction-induced Fock-space plaquette flux, Rydberg chiral
hopping, and phase tomography all have direct prior art.  An exact platform
intersection not found in search is integration novelty only.

No QPU task is submitted.  A later hardware benchmark would additionally need
live device properties, SDK validation, confirmed Braket Direct local-detuning
access, an empirical local-detuning decoherence measurement, and a scientific
question stronger than reproducing the known mechanism.
