# cuTensorNet truncation diagnostics

## Environment and frozen path

The existing GPU replication uses the WSL environment
`/root/.venvs/evoq-cuquantum` with cuQuantum 26.6.0 and CuPy 14.1.1 on the
RTX 4070 Ti SUPER. Its frozen simulator path is
`NetworkState.from_circuit(..., config=MPSConfig(max_extent=...,
discarded_weight_cutoff=...))`, followed by `compute_state_vector()`.

## API audit

`MPSConfig` accepts a discarded-weight cutoff, but `NetworkState` exposes no
per-gate or per-SVD truncation callback, event list, or discarded-weight
result. The public state execution methods return observables/states (and, for
some calls, a norm), not the individual MPS decomposition losses. The
underlying `StateAttribute` enum likewise has MPS configuration attributes but
no runtime per-SVD discarded-weight information attribute.

The lower-level standalone `cuquantum.tensornet.tensor.decompose(...,
return_info=True)` API does return `SVDInfo.discarded_weight`. That API is not
used by `NetworkState.from_circuit`, and instrumenting every internal
decomposition with it would require replacing the existing simulator with a
new gate-by-gate MPS implementation. This is the major low-level rewrite the
pilot explicitly excludes; it would also risk changing the frozen
decomposition/order semantics.

## Decision

The installed high-level cuTensorNet MPS interface does not expose enough
runtime information to construct the same internal certificate without a
major reimplementation. The optional 24q GPU certificate sweep was therefore
not run. Existing cuTensorNet state/TVD replication remains an immutable input,
but its exact-dependent errors cannot be relabelled as an internal runtime
certificate.
