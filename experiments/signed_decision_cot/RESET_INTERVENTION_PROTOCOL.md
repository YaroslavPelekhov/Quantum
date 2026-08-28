# Frozen equal-work residual reset intervention

Locked on 2026-08-22 before the first variable-window intervention execution.

## Motivation and causal hypothesis

The completed fixed-bond ladder shows a certified residual-policy rank reversal.
On sorted ordering, full R32 first overtakes full R128 at the audited `t=192`
checkpoint; on spectral ordering the corresponding onset is `t=128`.  Both
schedules share the onset within each ordering.

The causal hypothesis is that an aggressive R32 compression window immediately
before the onset resets the represented residual trajectory and reduces the
future integrated certified remainder.  Equal-work windows away from the onset
are controls.

## Frozen policies

Keep residual bond R128 everywhere except one inclusive 64-checkpoint R32
window.  Execute all four policies for both schedules and both orderings:

- `reset_129_192`: R32 at 129-192;
- `reset_193_256`: R32 at 193-256;
- `reset_257_320`: R32 at 257-320;
- `reset_321_384`: R32 at 321-384.

All policies have identical cubic residual work.  The primary backward schedule
remains `1-319:512,320-383:384,384-447:256,448-511:128,512-555:64`.

## Prespecified predictions

1. Sorted: `reset_193_256` minimizes the LR integrated operator remainder and
   the paired signed-decision remainder among the four equal-work policies.
2. Spectral held-out: `reset_129_192` minimizes the corresponding quantities.
3. The onset-aligned policy must beat every available adjacent equal-work
   window for the mechanism prediction to pass; merely certifying the ranking
   is insufficient.
4. Every exact gap must lie inside its signed interval and all selected dense
   residual/operator enclosures must pass.

The exact BKS gap and dense exact vectors are audit-only.  All policies and
predictions are frozen before intervention execution.  A failed ordering,
schedule mismatch, or nonunique minimum is retained as a negative causal test.

## Interpretation boundary

A successful test supports a window-placement effect in this recurrence.  It
does not prove a universal reset theorem, global optimality, or total simulator
speedup.  A failed test leaves the signed decision certificate intact and
rejects the proposed mechanism.
