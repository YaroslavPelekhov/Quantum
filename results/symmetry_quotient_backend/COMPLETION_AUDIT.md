# Completion audit: event-certified symmetry quotient simulation

> **Historical and superseded.**  A later, stronger symmetry-preserving and
> optimized-baseline audit rejected both the ansatz-specific rank claim and the
> reported `23.90x` speedup.  Use
> `results/symmetry_claim_falsification/REPORT.md` as the current verdict.

Audit date: 2026-08-28.

## Outcome

The research cycle has reached a defensible, executable novelty claim.  The
original observation -- low decision-conditioned rank -- was not retained as
novel by itself.  It was structurally falsified, narrowed, and replaced by an
exact comparison-native simulation method with an explicit certificate and a
measured 24-qubit implementation.
Сейчас полезнее потратить следующий цикл не на генерацию десятой идеи, а на самый агрессивный falsification test именно этого последнего claim.
The supported claim is conjunctive:

> For symmetry-rich diagonal QAOA/MIS instances and structured diagonal
> decision events, compile graph-twin count sectors for exact state evolution,
> then compile the paired event-incidence graph into a capacity-two matching
> certificate and assemble only the exact small comparison core.  This gives a
> statevector-free decision-comparison backend with a cutwise rank bound and a
> parameter-generic comparison-rank signature.

No individual ingredient -- Helstrom/Jordan comparison, structural rank,
matching, orbit quotients, QAOA symmetry, or tensor-network contraction -- is
claimed as new.

## Required falsification gates

| gate | result | evidence |
|---|---:|---|
| Exact structural bound | 0 violations over 104 cuts | `results/dcsrdt_structural_audit/audit.json` |
| Haar saturates structural cap | 104/104 cuts | same audit |
| Previously highlighted generic cases survive | no | ibm32, chesapeake, and football equal Haar/structural rank |
| Independent phase scramble restores cap | all 40 eligible aves cuts | `results/coherent_frontier_rank/coherence.json` |
| Schedule pairs share rank signature | yes, all three pairs | same audit |
| Broad MaxCut-QAOA hypothesis | rejected, 0/4 | `results/ansatz_event_rank/development.json` |
| Frozen symmetry-rich development | 4/4 | `results/symmetry_quotient_decision_rank/development.json` |
| Untouched topology transfer | 2/2 | `results/symmetry_quotient_decision_rank/transfer.json` |

These controls rule out the earlier explanations based only on sparse event
support, parameter choice, common phase gauge, low Schmidt rank, or generic
QAOA structure.  The surviving effect requires the symmetry-rich ansatz/event
pairing.

## Executable algorithm gate

The twin-count quotient backend evolves the two QAOA schedules and constructs
the decision core without allocating either a full `2^24` statevector or a
dense decision operator.

| metric | measured result |
|---|---:|
| Real 24-qubit orderings passed | 2/2 |
| Quotient/full dimension | 1,658,880 / 16,777,216 |
| State representation compression | 10.11x |
| Dense trajectory | 101.96 s |
| Quotient trajectory, steady state | 4.27 s |
| Measured steady-state speedup | 23.90x |
| First-state speedup including compile | 14.88x |
| Maximum sampled probability error | 4.49e-17 |
| Decision ranks reproduced | all frozen cuts |

Exact breadth validation passed 7/7 additional pre-selected QOBLIB cases, for
8/8 total correctness cases.  The unfiltered cohort contains useful negative
controls: three cases have no nontrivial twin compression, while twins occur in
5/8 cases and give 2.0--10.11x representation compression.

## Reproducibility gate

- Protocols were frozen before their corresponding runs.
- Result manifests pin SHA-256 hashes for the structural, coherence, negative,
  development, transfer, backend, dense-comparator, and breadth artifacts.
- Full regression on 2026-08-28: 25 test modules, 149 tests, 0 failures.
- The user-owned `baselines/qoblib-solutions` submodule was not modified by
  this audit.

## Novelty boundary and remaining risk

The claim is exact and noiseless, requires a diagonal structured event, and
only accelerates instances with useful symmetry sectors.  An asymmetric graph
can reduce to the full Hilbert space.  The large-scale runtime result is one
real 24-qubit kernel in two orderings; the remaining seven cases establish
correctness and expose the failure surface, not universal speedup.

This is sufficient for a paper-level algorithmic claim and ablation package.
It is not a guarantee of venue acceptance or proof that no obscure equivalent
construction exists.  The next publication step is independent comparison
against additional symmetry-aware simulators and external peer review; it is
not needed to make the present implementation or stated claim internally
valid.
