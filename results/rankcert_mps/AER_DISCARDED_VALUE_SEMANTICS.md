# Aer 0.17.2 `discarded_value` semantics

## Audited build and source

- Installed package: `qiskit-aer==0.17.2` in the frozen Windows environment.
- Official source tag: `0.17.2`, commit
  `51c679814c3a292d0d7c59bb39976bd6ff91f60e`.
- The installed wheel contains the compiled controller, so the matching
  official tag was checked out read-only for source inspection.

Relevant source files and SHA-256 hashes:

- `src/simulators/matrix_product_state/svd.cpp`:
  `84749b6dd9a4fa1a19fca645b81234765b9ccaee03353b9eb3a8be8b48a11ef6`
- `matrix_product_state_tensor.hpp`:
  `d0b9758df9efed3813df818e6128b4d2377bc5ae870b26dd38344b1fc936b50c`
- `matrix_product_state_internal.cpp`:
  `71f644361ccc297f122cdb213a3e566a95376b244d6206023bd448a3cea466e8`
- `matrix_product_state.hpp`:
  `5fad4c9d42c765c7adb46f0e2f4c855f52f9c326ff4da22439c0824a44efee2e`

## Computation path

`MPS::apply_2_qubit_gate` contracts the adjacent tensors, applies the gate,
and calls `MPS_Tensor::Decompose` (`matrix_product_state_internal.cpp`, around
lines 625--680). `MPS_Tensor::Decompose` performs an SVD and calls
`reduce_zeros` with both the configured maximum bond dimension and truncation
threshold (`matrix_product_state_tensor.hpp`, around lines 590--615).

`reduce_zeros` (`svd.cpp`, lines 92--141) does the following:

1. Treats singular values with squared magnitude at most the compile-time
   `CHOP_THRESHOLD=1e-16` as zero.
2. Applies the bond cap first.
3. Attempts to remove a low-singular-value tail whose cumulative squared norm
   is below `matrix_product_state_truncation_threshold`.
4. Reports `discarded_value` as the sum of `std::norm(S[i])` for every singular
   value removed by the final rank choice.
5. Renormalizes the retained singular values to squared norm one.

Thus bond-cap and cutoff losses are combined into one reported value.  The
reported quantity is computed from the pre-renormalization singular values and
is inclusive of every rank component actually removed by that decomposition.

## Normalization verdict

The function does not divide `discarded_value` by the incoming squared norm.
For this pilot's noiseless circuit path, however, the incoming state is
normalized: initialization is normalized, inter-truncation operations are
unitary, and every truncation renormalizes the retained singular values.  Under
that condition `discarded_value` is the normalized discarded Schmidt weight
required by the accumulated-angle theorem, up to floating-point drift.

The isolated analytic test with
`sqrt(1-w)|00> + sqrt(w)|11>`, `w=1e-4`, and `max_bond=1` reports exactly
`discarded_value=0.0001`; the retained state has fidelity `1-w=0.9999` and norm
one.  This empirically validates the interpretation for the installed binary.

The interpretation must not be generalized without qualification to
non-unitary/noisy paths or externally supplied unnormalized MPS states.

## Logging versus physical evolution

`MPS::apply_2_qubit_gate` appends a value only when
`discarded_value > json_chop_threshold_`. `State::set_config` assigns
`config.chop_threshold` to this JSON/log threshold; it is not passed to
`reduce_zeros`.  An isolated regression test shows that changing
`chop_threshold` from zero to `1e-3` hides a `1e-4` event while leaving the
post-truncation state bit-for-bit equal at the tested tolerance.  Therefore the
production diagnostic uses `chop_threshold=0` to expose all positive events.

The MPS logging stream and instruction counter are static. `clear_log()` is
defined but is not called in the audited execution path. Multiple simulations
in one Python process therefore accumulate log entries. Every RankCert
schedule run must execute in a fresh child process.

Aer writes `discarded_value` during the gate operation and writes the
`I<n>:... BD=[...]` record afterwards. The parser consequently assigns a
discarded value to the next operation record, not the preceding one.

### Numeric precision of the log

`MPS::print_to_log` in `matrix_product_state_internal.hpp:127-140` inserts the
`double` directly into the static `std::ostringstream`. The stream precision
is never changed on this path, so C++ `defaultfloat` uses its default precision
of six significant digits. A parsed decimal is therefore not the exact binary
`discarded_value`; using it directly could round a rigorous bound downward.

RankCert preserves each reported decimal, but evaluates the certificate using
the upper endpoint of its six-significant-digit rounding bin:

`w_upper = nextafter(w_reported + 0.5 * 10^(floor(log10(w_reported))-5), +inf)`.

The result is capped at the physical normalized-weight ceiling of one. This is
a conservative conversion. Descriptive sums of raw Aer values remain labelled
as reported values and are not substituted for the certified upper weights.

## Confirmed cutoff edge case

The cutoff loop updates `new_SV_num` only in its `else` branch. If the entire
tail from the smallest coefficient through index 1 has cumulative squared norm
below the threshold, the loop exits without setting `new_SV_num=1`. No cutoff
truncation then occurs.

This is confirmed in the installed binary:

- The published-style 4-qubit test truncates weight `0.5` at cutoff `0.5` but
  performs no truncation at cutoff `0.9`.
- The analytic state with `w=1e-4` performs no truncation at cutoff `2e-4` and
  remains fidelity one with the untruncated state.

The certificate describes the state Aer actually produced and uses only
actually logged events, so the edge case does not by itself invalidate the
certificate. It does mean that a configured cutoff is not always the nominal
discarded-tail policy. Existing paper results remain results for Aer 0.17.2's
actual evolution; interpretations that assume every eligible tail was removed
must be qualified.

## Implementation caveat

In `reduce_zeros`, `S.resize(new_SV_num)` occurs before the loop that sums
discarded `S[i]` values up to the old `SV_num`. For `std::vector` this is an
out-of-logical-range access even if the backing storage still contains the old
values. The installed binary returns the expected value in the analytic test,
but this source-level undefined behavior is an additional reason to require
empirical exact-case soundness checks before accepting any full result.

## Certificate eligibility decision

For the audited noiseless native-circuit path, isolated-process logging with
`chop_threshold=0` is provisionally usable as normalized discarded Schmidt
weight. The implementation is not labelled sound solely from source review;
it advances to exact-case testing with the mandatory BKS-error and TVD
inequalities. Any violation stops the sweep.
