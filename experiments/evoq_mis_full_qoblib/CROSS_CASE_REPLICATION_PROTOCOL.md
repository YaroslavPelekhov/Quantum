# Frozen cross-case exact MPS replication protocol

Frozen on 2026-08-11 before generating any new cross-case ladder state. The
completed `aves-sparrow-social` artifacts predate this protocol and are reused
only through their recorded SHA-256 hashes; no setting is selected from a new
case after viewing its ladder outcome.

## Objective and hypothesis

The objective is to determine whether backend- and ordering-dependent schedule
rank instability is confined to one 24-qubit graph or follows a predictable
effect-margin pattern across real QOBLIB MIS instances.

Primary hypothesis: sign instability is governed by the application-level
effect margin relative to accumulated distribution error, rather than by qubit
count or global state fidelity alone. For BKS event `A`, schedules `i,j`, exact
distributions `p`, and approximate distributions `q`, the pre-specified
certificate is

`|(q_i(A)-q_j(A))-(p_i(A)-p_j(A))| <= TVD(q_i,p_i)+TVD(q_j,p_j)`.

A cohort is certified when the exact effect magnitude exceeds the right-hand
side. The operational approximate-margin version is also reported.

## Fixed cases and circuits

All cases use the existing QOBLIB reduction implementation, depth 15, no repair,
and the three frozen schedules `published_lr`, `prior_evolutionary`, and
`prior_matched_random` under sorted and spectral qubit orderings.

| Case | Reduction cap | Exact qubits | Exact matched-vs-LR BKS effect |
|---|---:|---:|---:|
| `karate` | 4 | 3 | +0.08641201 |
| `chesapeake` | 12 | 7 | -0.13421359 |
| `football` | 10 | 7 | +0.01926887 |
| `ibm32` | 8 | 18 | -0.24612300 |
| `aves-sparrow-social` | 20 | 24 | -0.01213885 |

The first four exact effects come from the completed external-validity exact
artifact; the fifth comes from the completed exact-extension artifact. Exact
states are regenerated and hashed before approximate execution so fidelity and
TVD can be computed without sampling.

## Fixed backends and ladder

- Qiskit Aer 0.17.2 matrix-product-state simulation on CPU.
- NVIDIA cuQuantum/cuTensorNet 26.6.0 `MPSConfig` on the RTX 4070 Ti SUPER.
- Fixed settings: `(bond, cutoff)` = `(64,1e-3)`, `(128,1e-4)`,
  `(128,1e-12)`, `(1024,1e-4)`, and `(1024,1e-5)`.
- Dense deterministic output states; no shots.
- Five cases x five settings x three schedules x two orderings x two backends =
  300 backend rows. The already completed 60 `aves-sparrow-social` rows are
  reused after hash validation, leaving 240 new backend jobs.

## Outcomes and analysis

Primary outcomes, evaluated only after all case/backend/setting method cohorts
are complete:

1. matched-random-vs-LR sign correctness;
2. cross-backend sign agreement;
3. TVD exact-margin and approximate-margin certification;
4. smallest tested setting certified across both backends and orderings for
   each case; and
5. association of sign failure with normalized margin
   `(TVD_i+TVD_j)/|exact effect|`.

Secondary outcomes are evolutionary-vs-LR effects, fidelity-only certificates,
maximum application-metric errors, raw norm drift, runtime, qubit count, gate
count, interaction bandwidth, and maximum linear cut. No schedule optimization,
case removal, setting insertion, or primary-outcome change is allowed after a
new target row is generated. Positive and negative exact-effect cases are both
retained.

## Completeness, provenance, and safety

- Export manifests hash every QPY circuit, exact state, protocol, runner, and
  reused completed artifact.
- Atomic checkpoints are written after every job; partial cohorts are not used
  for conclusions.
- A small exact cuTensorNet axis/scoring self-test is mandatory before target
  execution.
- One simulator job runs at a time. CPU thread counts are one and cuTensorNet is
  limited to 60% GPU memory.
- The Windows watchdog stops only the experiment after two consecutive samples
  with free RAM below 12 GiB, commit above 70%, free C: below 100 GiB, free GPU
  memory below 2 GiB, or GPU temperature above 82 C. It contains no reboot or
  shutdown action.

The exact dense states remain local; manifests and hashes identify them in the
publishable artifact.
