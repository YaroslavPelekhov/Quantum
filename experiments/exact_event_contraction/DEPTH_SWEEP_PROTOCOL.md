# Frozen protocol: exact 55-qubit event-probability depth boundary

Frozen on 2026-09-02 after the full-depth (`p=15`) amplitude and MPO path
searches failed, and before any truncated-depth 55-qubit result was computed.

## Question

The exact rank-5 spectral event projector is validated, but the doubled
full-depth circuit network exceeds the tested cuTensorNet pathfinder regime.
This experiment locates the depth boundary at which the same fixed 55-qubit
BKS probability remains exactly contractible on one 16 GB GPU.

This is a resource/feasibility map, not a claim that a truncated circuit
answers the original depth-15 ranking question.

## Immutable construction

- Start only from the four hash-pinned 55-qubit QPY circuits.
- A gate's QAOA layer is determined by the number of preceding `rx` gates on
  its participating qubit(s).  For every `rzz`, both endpoint counts must be
  equal.  Retain all initial `h` gates and exactly the first `p` complete
  `rz`/`rzz`/`rx` layers.
- For a graph with `n=55`, `m=91`, the retained circuit at depth `p` must have
  exactly `n + p(2n+m) = 55 + 201p` operations: 55 `h`, `55p` `rz`, `91p`
  `rzz`, and `55p` `rx`.
- The event remains all 384 decoded BKS solutions.  The event-MPO, precision,
  circuit parameters, and cuTensorNet implementation are unchanged.

## Sweep and escalation

1. Validate layer extraction and exact low-level MPO probabilities against
   dense statevectors on both small graphs at depths `p=1,2,4,8,15` (or all
   available depths up to 15), both schedules and both orderings.
2. On 55 qubits run spectral LR at `p=1,2,4,8`; bisect any success/failure
   interval to locate the largest completed integer depth.
3. Run matched-random at every spectral depth completed by LR.
4. At the largest depth completed by both schedules, attempt sorted-order
   semantic replication.  Exact probabilities must agree to absolute `1e-9`
   or relative `1e-7`.

## Decision rules

- A depth succeeds only when path search and scalar contraction both finish
  without approximation, the imaginary magnitude is at most `1e-10`, and the
  finite output lies in `[0,1]` up to that tolerance.
- Optimizer failures and resource exhaustion are recorded, not imputed.
- Report path-search and contraction times separately.  Do not compare
  schedules at unequal depths.
- The depth-15 ranking remains unresolved unless both depth-15 schedules finish
  and an ordering replication passes.
- A shallow-depth success demonstrates only an exact capability boundary.  It
  does not establish A*-level novelty or quantum advantage.

## Resource-guard amendment (before the `p=3` run)

The first `p=4` path exposed `2^32` slices and an optimizer cost of
`5.80e20`; execution was stopped rather than spending an unbounded amount of
GPU time.  The completed `p=2` reference used optimizer cost `1.33e10` and
0.94 seconds of contraction.  Before bisecting at `p=3`, the following
non-statistical execution guard was fixed: record but do not execute a path
with more than 65,536 slices or optimizer cost above `1e13`.  This allows a
generous order-of-magnitude wall-time margin over `p=2` while rejecting plans
that are plainly outside a single-workstation research cycle.  Rejection is a
resource-bound result, not an algorithmic or numerical failure.
