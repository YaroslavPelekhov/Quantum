# Exact-extension execution audit

## Attempt 1 — stopped before any result

- Started: 2026-08-09 07:46:59 +03:00.
- Guard stop: 2026-08-09 07:53:11 +03:00.
- Completed checkpoint rows: 0 / 6.
- Trigger: committed virtual memory reached 92.80% and 92.76% on two
  consecutive five-second polls.
- Windows remained running; only the experiment process tree was terminated.
- Root cause: the original exact metric path called `probabilities_dict()` for
  a 24-qubit statevector, attempting to materialize up to 16,777,216 Python
  string/dictionary entries.

## Corrective action before attempt 2

The circuit and exact statevector backend are unchanged.  Metric accumulation
now scans the dense amplitude array in fixed-size chunks and compiles the
baseline unfold/feasibility decoder into exact bit-literal constraints.  It
does not create per-state Python objects.

Validation completed before resume:

- exhaustive decoder equivalence on `karate`, `chesapeake`, and `football`,
  for sorted and spectral orderings;
- fixed 20,000-state equivalence samples on `ibm32` and
  `aves-sparrow-social`, for both orderings;
- all probability metrics matched the frozen `ibm32/published_lr/sorted`
  exact reference to 12 decimal places while forcing 1,024-state chunks.

No scientific parameter or acceptance rule in `EXACT_EXTENSION_PROTOCOL.md`
was changed.
