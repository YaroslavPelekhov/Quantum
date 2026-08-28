# Global decision-balanced contraction protocol

Frozen before executing either schedule pair: 2026-08-23.

## Construction

At gate `t`, exact forward paired states define the reduced reachability
Gramian `R_t`; exact backward BKS basis vectors define observability `Q_t`.
From the SVD of `Q_t^(1/2) R_t^(1/2)`, construct biorthogonal trial/test
factors `V_t,W_t` with `W_t^dagger V_t=I`.

The circuit is then contracted as a single linear reduced model:

`x_t = (W_t^dagger tensor I) U_t (V_(t-1) tensor I) x_(t-1)`.

There is no intermediate state normalization and no feedback from approximate
states into later bases.  The final state is reconstructed once with `V_T` and
contracted with the BKS support.

At each gate, use the smallest rank in `1..8` capturing at least 99% of squared
Hankel singular-value energy.  The baseline receives the identical rank
schedule and uses the leading orthogonal eigenbasis of `R_t`.

## Cohorts

- Cases: `es60fst01`, `es60fst03`, `mammalia-kangaroo-interactions`.
- Orderings: sorted and spectral.
- Cut: 4 high-order qubits.
- QAOA depth: 15.
- Reference: `published_lr`.
- Development pair: `prior_matched_random`.
- Held-out schedule-pair transfer: `prior_evolutionary`.

No policy parameter may change between pairs.

## Criteria

Development support requires correct sign and strictly lower absolute Delta
error than the equal-rank-schedule orthogonal baseline on all six rows.
Only if development passes is the held-out pair promoted to confirmation.

Transfer support requires the same 6/6 criterion.  Any transfer failure closes
the universal schedule-pair claim; no threshold or rank-cap retuning follows.

The dense exact-Gramian implementation is a feasibility oracle.  It does not
establish scalable construction cost.
