# Contrast-augmented end-to-end held-out protocol

Frozen before inspecting any `karate` result: 2026-08-23.

## Construction

After every paired logical gate, form at the fixed left cut

`rho_avg = (rho_A + rho_B)/2`, `Gamma = rho_B-rho_A`,

and retain the leading eigenspace of

`H_alpha = rho_avg + alpha |Gamma|`.

Both branches are projected into this common subspace and individually
renormalized before the next gate.  `alpha=0` is conventional state averaging.

## Frozen held-out setting

- Uninspected graph: `karate`.
- Orderings: `sorted`, `spectral`.
- Cut: one high-order qubit versus the remaining two.
- Retained rank: one.
- Candidate: `alpha=0.25`, the smallest nonzero value in the exploratory 7q
  grid; baseline: `alpha=0`.
- Projection cadence: after every paired logical gate.

## Success criterion

The candidate must have the correct exact BKS ranking sign and strictly lower
absolute Delta error than state averaging on both orderings.  Otherwise the
fixed-alpha end-to-end successor is closed.  No retuning is permitted.

The earlier 7q exploration is not part of this held-out claim.
