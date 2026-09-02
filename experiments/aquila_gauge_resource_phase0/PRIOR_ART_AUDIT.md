# Adversarial prior-art audit

## Verdict

The broad weak-drive gauge-resource story is **not A-star novel**.  Its pieces
are established graph gauge theory, finite-ensemble/selective control, and
Fourier time-bandwidth conditioning.  The frequency-weighted gauge-quotient
functional appears to be a narrow intersection not found verbatim in this
search, but the current theorem has neither a succinct hard family nor a
full-propagator separation.

## Closest structural work

- Harrison, Keating, and Robbins treat graph edge potentials modulo vertex
  gauge and cycle fluxes as the complete invariants:
  https://arxiv.org/abs/1101.1535
- Schirmer, Pullen, and Solomon develop simultaneous controllability and
  selective excitation using a shared field:
  https://arxiv.org/abs/quant-ph/0503150
- Khaneja and Li use polynomial approximation and noncommuting controls for
  ensemble controllability:
  https://arxiv.org/abs/quant-ph/0510012
- Ansel, Glaser, and Sugny derive time-optimal selective control with the
  expected inverse-offset scale:
  https://arxiv.org/abs/2010.12454
- Li and Liao give sharp conditioning results for clustered Fourier/Vandermonde
  nodes in super-resolution:
  https://arxiv.org/abs/1709.03146
- Nixon, Uenal, and Schneider already use scalar onsite modulation to program
  individual Peierls links and gauge-invariant plaquette flux:
  https://arxiv.org/abs/2309.12124

## Nonperturbative bypass risk

The weak response `R(omega)` is not the full control system.  Two particularly
strong results prohibit extrapolating the QTV bound by rhetoric:

- Cesa and Pichler construct universal computation in globally driven Rydberg
  arrays with polynomial atom overhead:
  https://arxiv.org/abs/2305.19220
- Hu et al. establish broad global-control universality and demonstrate direct
  optimal-control synthesis of non-native three-body and topological dynamics
  on a Rydberg array under realistic smooth constraints:
  https://arxiv.org/abs/2508.19075

These works do not refute the scalar weak-drive theorem.  They do provide a
concrete commutator/Floquet/nonlinear path around any unsupported claim that
spectral interpolation bounds every finite-amplitude propagator.

## Hardware mismatch

Current Aquila local detuning exposes one customizable spatial pattern that is
constant throughout a program.  The accompanying temporal magnitude must
start and end at zero and remain nonpositive; access is experimental through
Braket Direct, and the documentation warns of additional decoherence.  Two
independently switchable masks within one coherent program are not the
available comparator:
https://docs.aws.amazon.com/braket/latest/developerguide/braket-access-local-detuning.html

## Remaining narrow gap

The exact missing object is an explicit same-geometry control-class separation:

1. a succinct deterministic 2D `1/r^6` family and constant measurable target;
2. a superpolynomial lower bound for every finite-amplitude admissible global
   waveform plus one fixed mask, including nonlinear and Floquet routes;
3. a polynomial constructive upper bound using exactly one additional
   physically meaningful control mode;
4. polynomial energy, leakage, robustness, and shot cost;
5. preferably a comparator executable on actual hardware.

No source found in the targeted audit supplies exactly this theorem, but the
known universality results make it high-risk and likely false.  The present
cycle therefore retains a technical weak-drive lemma and rejects an A-star
claim.
