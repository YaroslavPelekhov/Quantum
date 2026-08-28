# Frozen causal asymmetric residual protocol

Locked after the prespecified 1-303 variable-bond schedule failed and before
executing the schedule below. This is a secondary design result, not a
replacement for the retained primary negative result.

## Evidence available at lock time

The primary variable schedule produced LR correction `0.18744487867179097`
and MR correction `0.00008622517049305588`. Its total certificate missed by
approximately `1.95e-4`. Fixed R128 diagnostics showed that LR dominates the
residual correction while MR contributes only `0.00011632382016721521`.

The residual scalar tail obeys `xi_t = xi_(t+1) + delta_t + floor`. Increasing
the bond later in the backward sweep cannot remove an already accumulated
tail. The rescue schedule therefore moves the R128-to-R256 transition to the
existing primary-schedule boundary rather than selecting new checkpoints by
exact error.

## Frozen asymmetric schedules

- LR: residual bond 256 at positions 1-319 and bond 128 at 320-555.
- MR: fixed residual bond 128 at all positions, reusing the already completed
  certified fixed-R128 witness.
- Primary backward schedule and forward `confirm` trajectories remain frozen.

No exact dense projector error enters the selection or stopping rule.

## Criteria

Primary success requires

`first_term_pair + LR_variable_correction + MR_R128_correction < |Delta_MPS|`

and all selected dense-oracle inequalities must pass. With cubic bond-work as
the implementation-independent tensor contraction proxy, the paired ratio to
fixed R256/R256 is

`0.5 * ((319*256^3 + 236*128^3)/(555*256^3) + (128/256)^3)`

`= 0.37646396396396396`.

Thus resource success requires certification with at least 60% paired cubic
bond-work reduction. Failure is retained and no endpoint is changed.
