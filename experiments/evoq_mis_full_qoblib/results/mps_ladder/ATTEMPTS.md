# MPS-ladder execution audit

## Attempt 1 — exact references complete, no MPS result admitted

- Exact references completed: 6 / 6.
- MPS jobs checkpointed: 0 / 66.
- The first released MPS state exported with raw squared norm
  `1.0000459850104852`.
- The exact-only accumulator correctly rejected this against its `1e-10`
  normalization assertion before any MPS row was written.
- The watchdog did not trigger and Windows remained stable.

## Corrective action before attempt 2

Approximate MPS exports are now explicitly normalized before application
probabilities, state fidelity, and total-variation distance are evaluated.
The raw squared norm and drift from one remain in every result row as simulator
diagnostics.  This is consistent with the frozen protocol, which defines
normalized pure-state fidelity, and changes no circuit, schedule, ordering,
bond dimension, cutoff, or completion rule.
