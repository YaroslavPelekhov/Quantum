# Frozen independent-backend MPS audit protocol

Frozen on 2026-08-11 before any target cuTensorNet audit result was generated.

## Research question

Does the conclusion of the exact-calibrated Aer MPS ladder survive an
independent tensor-network implementation?  In particular, can an apparently
high-fidelity approximation reverse the sign of the small BKS-rate effect of
the matched random schedule relative to the published LR schedule?

## Fixed target

- QOBLIB MIS instance: `aves-sparrow-social`.
- Reduced problem size: 24 qubits, maximum reduction degree 20.
- QAOA depth: 15.
- Methods: `published_lr`, `prior_evolutionary`, and
  `prior_matched_random`; their already-frozen schedules are imported without
  optimization or retuning.
- Qubit orderings: `sorted` and `spectral`.
- No repair and no sampling: metrics are accumulated deterministically from
  the exported dense approximate state.
- Exact adjudication: the six completed local exact-state references from the
  Aer ladder, verified by SHA-256 before use.

## Fixed approximation settings

Exactly five settings are tested:

| Name | Maximum bond | Discarded-weight cutoff |
|---|---:|---:|
| `released` | 64 | 1e-3 |
| `confirm` | 128 | 1e-4 |
| `bond128` | 128 | 1e-12 |
| `cutoff1e-4` | 1024 | 1e-4 |
| `cutoff1e-5` | 1024 | 1e-5 |

The target audit therefore contains exactly 5 settings x 3 methods x 2
orderings = 30 jobs.  Partial cohorts are checkpointed but are not interpreted.

## Independent backend and estimands

- Backend: NVIDIA cuQuantum/cuTensorNet 26.6.0 through
  `NetworkState.from_circuit` with `MPSConfig` on the local RTX 4070 Ti SUPER.
- Each returned state is transferred to CPU, converted explicitly from
  cuTensorNet's q0-first tensor axes to Qiskit's flat little-endian amplitude
  order, and normalized.  Its raw squared norm is retained as an audit field.
- Primary estimand: sign and magnitude of
  `BKS(prior_matched_random) - BKS(published_lr)` within every setting and
  ordering, compared with the exact sign.
- Secondary estimands: the evolutionary-vs-LR BKS effect, state fidelity,
  total-variation distance, absolute BKS error, raw norm drift, runtime, and
  agreement with the corresponding Aer MPS row.
- No target result is accepted until all circuit, reference, runner, and
  protocol hashes pass and all 30 unique jobs are complete.

## Reproducibility and safety

- Circuit QPY files, decoder literals, hashes, software versions, GPU
  provenance, and atomic per-job checkpoints are retained.
- A separate four-qubit exact self-test must pass before target execution; it
  checks QPY transport, axis conversion, normalization, fidelity, TVD, and the
  static metric accumulator.
- Only one GPU job runs at a time.  cuTensorNet may use at most 60% of GPU
  memory.  CPU BLAS thread counts are fixed to one.
- A five-second Windows watchdog stops only the experiment process after two
  consecutive breaches of any bound: free RAM below 12 GiB, committed virtual
  memory above 70%, free C: space below 100 GiB, free GPU memory below 2 GiB,
  or GPU temperature above 82 C.  The watchdog never reboots or shuts down the
  machine; completed atomic checkpoints remain resumable.
- Exact dense references remain local and are excluded from publication due
  to their size.  Their hashes and generation provenance are sufficient to
  identify them.

Any change to the target, settings, methods, orderings, primary estimand, or
stopping rule requires a new protocol file and a new results directory.
