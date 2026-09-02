# Adversarial prior-art audit

Audit date: 2026-09-02.  Scope: primary papers and official hardware
documentation.  This file records negative evidence, not a novelty claim.

## Broad one-mask controllability is not new

Let `D_h = sum_i h_i Z_i` and let the transverse control be global.  Repeated
commutators produce polynomially weighted controls such as

`ad(D_h)^(2m) X_global = (-1)^m sum_i h_i^(2m) X_i`.

For distinct labels, a Vandermonde inversion resolves individual frequency
classes.  This is finite-ensemble/frequency-selective quantum control, not a new
Aquila mechanism.  Closest primary sources include:

- Khaneja and Li, *Ensemble Control of Bloch Equations*, 2005:
  https://arxiv.org/abs/quant-ph/0510012
- Beauchard, Coron, and Rouchon, ensemble controllability limits, 2009:
  https://arxiv.org/abs/0903.2720
- Albertini and D'Alessandro, finite-dimensional quantum controllability, 2002:
  https://doi.org/10.1016/S0024-3795(02)00290-2
- Cesa and Pichler, universal computation with globally driven Rydberg arrays,
  2023: https://arxiv.org/abs/2305.19220
- Polychromatic broadband, narrowband, and passband pulse construction, 2022:
  https://arxiv.org/abs/2204.02147

Therefore full Lie rank or preparation of two small targets cannot by itself be
claimed as A-star novelty.  A remaining publishable object would need a sharp
resource theorem under Aquila's one-sign local detuning, bounded action, slew,
finite `C6/r^6`, time grid, and decoherence, ideally with matching constructive
upper bounds.

## The phase control is not a spatial gauge field

The documented global phase can be removed by the rotating frame
`R_phi = exp(-i phi N)`.  It shifts global detuning by `dot(phi)` and leaves the
static spatial mask unchanged.  On the independent-set configuration graph,
the phase on every addition/removal edge is the gradient of the excitation
number, so every Wilson loop is zero.  Hardware bounds can make two gauge-
equivalent schedules differ in admissibility, but do not create a second
spatial channel.

Likewise, transition nonreciprocity within one non-palindromic schedule is not
enough to establish chirality.  For real symmetric instantaneous Hamiltonians,
the reversed schedule obeys `U_reverse = U_forward^T`; ordinary time ordering
can make forward transition probabilities asymmetric.

## Narrow adjacent gap worth testing next

The broad statement "Floquet driving creates chiral/topological transport in
configuration space" is also occupied:

- chiral continuous-time quantum walks: https://arxiv.org/abs/1208.4049 and
  https://arxiv.org/abs/1405.6209
- Floquet topology and gauge vortices in Fock-state lattices:
  https://arxiv.org/abs/2207.00742 and https://arxiv.org/abs/2404.00533
- synthetic flux and chiral bound states in Rydberg systems:
  https://arxiv.org/abs/2203.03994
- tunable `U(1)` flux in a Rydberg synthetic dimension:
  https://arxiv.org/abs/2306.00883
- Rydberg Floquet chiral exchange: https://arxiv.org/abs/2306.07041
- global-detuning Floquet engineering in the blockade/PXP regime:
  https://arxiv.org/abs/2408.02741

The last paper is arXiv v1 from 5 August 2024; a date printed inside a later HTML
render is not an arXiv revision date.  Its discussion already points to
site-resolved detuning as a route to chiral interactions.

The audit did not find the exact intersection of all of the following:

1. current Aquila AHS constraints;
2. exactly one program-static grayscale mask;
3. global piecewise controls and one local-detuning envelope;
4. native finite `C6/r^6` tails;
5. a nonzero gauge-invariant Wilson flux on an independent-set configuration
   graph; and
6. hardware validation.

That is only an integration gap until a minimality/no-go or resource-separation
theorem is proved.  The promising mechanism is interaction-to-configuration-
curvature transduction.  If a spectral pulse gives a nonlinear transition
phase `alpha(epsilon)`, a compatible-site plaquette can acquire

`Phi_ij = alpha(e_i) + alpha(e_j+V_ij)
        - alpha(e_i+V_ij) - alpha(e_j)`.

It vanishes without interaction, with an affine spectral phase, or under the
appropriate symmetric controls.  This formula is a derived research
hypothesis, not a literature novelty claim.

## Frozen verdict for this branch

> **KILL broad one-static-mask controllability as A-star novelty.**  Continue
> the numerical run as a hardware-feasibility and enabling-lemma audit.  Move
> the novelty search to an interaction-induced, gauge-invariant configuration-
> curvature claim only if it survives Wilson-loop, reverse, palindrome,
> equal-mask, and large-spacing controls.

Official model and experimental-capability constraints:

- https://docs.aws.amazon.com/braket/latest/developerguide/braket-quera-submitting-analog-program-aquila.html
- https://docs.aws.amazon.com/braket/latest/developerguide/braket-access-local-detuning.html

