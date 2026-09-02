# Preregistration: global-likelihood alias control

Frozen after the registered Phase-0 run exposed high branch-failure rates for
the deliberately minimal sequential unwrap estimator, and before inspecting
any global-likelihood results.

## Purpose

The broad drift-QAE verdict is already supported by exact indistinguishability
and the analytic fixed-depth-noise Fisher ceiling.  This audit prevents a weak
estimator from being mistaken for the reason the candidate failed.

## Frozen change

For every target sample, form every theta candidate compatible with the
deepest observed cosine fringe.  Score all candidates using the joint binomial
likelihood of every registered depth, choose the maximum-likelihood alias, and
refine it within one-third of the deepest fringe spacing.  Visibility is
provided in three separate modes:

- exact nuisance oracle;
- matched, fully charged anchor estimates;
- nominal unanchored visibility (readout model only).

The amplitudes, depth ladders, paths, shot counts, trials, seed, direct baseline
and physical-depth accounting remain exactly those in `protocol.json`.

## Interpretation gate

If the post-circuit model recovers super-classical scaling, it is recorded as
a positive engineering control but **not** as a new drift boundary: matched
anchors have converted each round into ordinary nuisance calibration.  If the
gate-accumulating model fails, the analytic `Q^-1/2` ceiling remains decisive.
No outcome of this audit authorises hardware spending.

