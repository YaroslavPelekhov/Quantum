# Frozen DCS-RDT structural-rank falsification protocol

Frozen before executing the audit: 2026-08-28.

## Question

Test whether the reported low numerical ranks of the decision-conditioned
operator are consequences of the sparse support of the diagonal BKS event.
No DCS-RDT novelty claim survives merely because a rank equals an event-support
bound.

For event support `S` and the repository's reshape convention at cut `c`, let

- `s_L(c)` be the number of distinct left prefixes in `S`;
- `s_R(c)` be the number of distinct right suffixes in `S`.

The audit checks the exact structural bounds

`rank(K_L) <= min(2 s_L(c), 4 s_R(c), 2 mu_2(c), 2^c)`.

The `2 s_L` bound uses the common coordinate embedding of event-supported
left rows and is tighter than the initially proposed `4 |S_R|` bound.
Here `mu_2` is the maximum matching size in the cut event-incidence graph when
each right-suffix vertex is duplicated (capacity two, one coefficient channel
per compared state).  It is the term-rank bound for the stacked event-weighted
coefficient pattern; this is standard structural-matrix machinery, not claimed
as a new theorem by itself.

## Frozen cohorts and controls

- Cases: `ibm32`, `aves-sparrow-social`, `chesapeake`, `football`.
- Orderings: sorted and spectral.
- State pair: `published_lr` versus `prior_matched_random`.
- Cuts: every nontrivial cut `1..n-1`.
- Numerical rank threshold: absolute eigenvalue greater than `1e-12`.
- Haar control: one deterministic independent complex Haar pair per
  case/ordering, seed derived from the case and ordering string.
- Event-size control: `ibm32` at cut 9 with exact BKS, near-BKS (`bks-1`),
  feasible, and deterministic uniformly sampled diagonal supports of size
  10, 100, and 1000. The same QAOA and Haar state pairs are used.

## Interpretation fixed in advance

1. If QAOA and Haar ranks both saturate the same structural bound, the observed
   compression is event-support algebra, not QAOA decision structure.
2. If QAOA rank is strictly below the Haar rank by at least 25% on a cut where
   neither is limited by the Hilbert dimension, that cut is evidence of
   additional state/event structure, but not by itself a novelty claim.
3. A new hypothesis must be formulated only after this audit and must be tested
   against the structural bound, Haar states, denser events, and held-out cases.
