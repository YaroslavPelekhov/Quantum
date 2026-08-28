# Frozen spectral transfer protocol

Locked on 2026-08-20 after the sorted causal-asymmetric result and before any
variable-residual-bond spectral execution.

## Frozen transfer

- LR residual schedule: positions 1-319 at bond 256 and 320-555 at bond 128.
- MR residual schedule: fixed bond 128, reusing its completed spectral witness.
- Primary backward schedule, forward setting `confirm`, and all numerical
  allowances are unchanged.

## Prespecified interpretation

Primary transfer success means the schedule retains a correct certificate with
no dense-oracle inequality violation. Resource transfer success is deliberately
not expected: the existing fixed spectral R128/R128 pair already certifies with
width `0.06942908595567995`. Therefore the transferred schedule will be reported
as over-allocation if it consumes more cubic bond-work than R128/R128, even if it
certifies. No spectral endpoint or bond is retuned.

This held-out run tests soundness/generalization of the construction, not a
second claim of resource optimality.
