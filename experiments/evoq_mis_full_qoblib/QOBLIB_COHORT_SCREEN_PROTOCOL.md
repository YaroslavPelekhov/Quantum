# Frozen protocol: expanded QOBLIB cohort screen

## Objective

Construct a reproducible, non-cherry-picked extension cohort for the
backend-aware QAOA study.  Every MIS instance distributed in the pinned
QOBLIB checkout is screened before any new quantum result is inspected.

## Frozen inputs

- QOBLIB `07-independentset` instances and best-known-value table.
- The reduction and no-repair decoder pinned through `qoblib-solutions`.
- Reduction caps, tried from least to most aggressive:
  `32, 24, 20, 16, 12, 10, 8, 6, 4`.
- Maximum quantum kernel: 24 qubits for the initial extension.
- Per-MILP time limit: 30 seconds, one process and one case at a time.

## Eligibility rule

For each instance, select the first (largest) cap that produces a non-empty
kernel of at most 24 qubits and whose exact reduced MIS, unfolded without
repair, reaches the published QOBLIB best-known value.  A successful HiGHS
MILP solve is required.  Empty deterministic kernels, timeouts, errors, and
unreachable reductions remain in the audit but are not quantum candidates.

Only instances labelled `optimal` in the QOBLIB table enter the primary
cohort.  Best-known-only instances are retained as an explicitly exploratory
pool.  The five cases already used in the cross-backend experiment are kept
as anchors.  Remaining primary cases are selected deterministically by
round-robin over qubit-size strata and graph-family labels, with lexical
case-name tie breaking, until 15 total cases are obtained or the eligible
pool is exhausted.

## Safety and auditability

- The screen performs graph reductions and small binary MILPs only; it does
  not allocate statevectors or submit cloud jobs.
- Results are checkpointed after every attempted cap.
- Peak process RSS, wall time, input hashes, software versions, and repository
  commits are recorded.
- Candidate selection is computed only after the complete 50-instance screen.

## Next stage

The selected cohort will receive a low-cost Aer pilot with the three frozen
schedules, sorted/spectral orderings, and independent seeds.  Passing cases
then enter the two-backend accuracy ladder; QPU execution remains a separate
registered validation stage because it requires account credentials and can
consume external quota.
