# Frozen protocol: exact sparse-event MPO contraction

Frozen on 2026-09-02 after the per-amplitude feasibility pilot failed and
before any 55-qubit event-MPO expectation value was computed.

## Motivation and target

The original exact-amplitude protocol contracts each of the 384 BKS strings
separately.  Its 55-qubit sorted-order pilot failed during cuTensorNet path
optimization with `CUTENSORNET_STATUS_ALL_HYPER_SAMPLES_FAILED`.  This protocol
tests a different exact computation:

`p_s(A) = <psi_s|P_A|psi_s>`,

where `P_A = sum_{z in A} |z><z|` is represented as one diagonal MPO.  No MPS
approximation, state truncation, sampling, or support pruning is allowed.

## Frozen inputs

- Circuits, schedules, orderings, graph reduction, decoder, and hashes are the
  immutable inputs listed in `PROTOCOL.md`.
- The event support is the hash-stable `results/exact_event_contraction/
  event_support.json`: 384 BKS strings for the 55-qubit case.
- The support indicator is compiled by exact rational row-basis elimination on
  each sparse prefix/suffix incidence matrix.  No numerical-rank threshold is
  used; the resulting TT cores are converted to complex128 only after their
  exact membership checks pass.
- The compressed MPS is converted to a diagonal MPO without changing its
  entries.  The contraction uses cuQuantum/cuTensorNet 26.6.0, complex128.

## Pre-registered validation

1. **Representation audit.** For every case and ordering, evaluate the
   compressed indicator on every included support string and on 4096
   deterministic non-support strings (or every non-support string when the
   entire Boolean domain is smaller).  The maximum absolute membership error
   must be at most `1e-10`.
2. **Dense exact self-test.** For both schedules and both orderings on both
   small kernels (eight cohorts), compare the MPO expectation with the existing
   dense exact state.  Absolute error must be at most `1e-10`.
3. **55-qubit pilot.** Run spectral LR first because the support MPO has maximum
   bond dimension 5 in that ordering.  Continue only if the exact expectation
   finishes without an internal preparation error or approximation.
4. **Primary target.** Compute spectral LR and spectral matched-random BKS
   probabilities.  Their signed difference adjudicates the frozen ideal-circuit
   ranking if it exceeds accumulated numerical tolerance.
5. **Semantic replication.** Attempt the sorted ordering for both schedules.
   Exact sorted/spectral values for each schedule must agree to absolute `1e-9`
   or relative `1e-7`.  A failed sorted contraction is recorded as a resource
   limitation, not silently replaced by an approximate result.

## Reporting rules

- Persist circuit/support hashes, full MPO bond profile, representation errors,
  wall time, GPU memory metadata, expectation value, and norm.
- A non-negligible imaginary component, norm error above `1e-10`, or small-case
  validation failure invalidates the corresponding result.
- No speedup or quantum-advantage claim is made without a matched baseline.
- Selected-amplitude and generic MPO tensor-network contraction are prior art.
  A successful computation resolves the manuscript's open exact probability;
  it is not by itself an A*-novel algorithmic claim.  Any broader claim requires
  a new general event-compilation result and cross-family scaling evidence.

## Pre-registered API fallback

If the experimental `NetworkState.compute_expectation` preparation fails, form
the same scalar network explicitly with the stable low-level API:

1. obtain the circuit density-matrix einsum network from
   `CircuitToEinsum.density_matrix()`;
2. attach the exact diagonal MPO to all ket/bra output modes and change the
   output to a scalar;
3. validate this construction on the same eight dense-reference cohorts before
   attempting 55 qubits;
4. use `Network.contract_path` and `Network.contract` without truncation.

An optimizer or resource failure is reported verbatim.  It is not grounds to
alter the circuit, event, precision, or pass criteria.
