# Frozen protocol: expanded QOBLIB Aer pilot

## Scope

The pilot covers the three primary-eligible cases added by the complete
50-instance cohort screen: `es60fst01`, `es60fst03`, and
`mammalia-kangaroo-interactions`.  Their reduction caps are read from the
hash-bound screen artifact and may not be changed after observing QAOA output.

## Fixed design

- QAOA depth: 15.
- Schedules: `published_lr`, `prior_evolutionary`, `prior_matched_random`.
- Qubit orderings: sorted and spectral.
- Exact statevector reference for every case/schedule/ordering combination.
- Aer MPS settings: bond 64/cutoff 1e-3 and bond 128/cutoff 1e-4.
- Seeds: 41001, 41002, 41003; 500 shots per job.
- Total: 18 exact references and 108 independently seeded MPS jobs.
- No post-sampling repair.

The primary pilot outcome is the sign of the BKS-rate difference between each
candidate schedule and `published_lr`, compared with its exact-statevector
sign.  BKS rate, near-BKS rate, feasibility, runtime, and circuit resources are
reported for all methods; no case or seed is dropped.

## Safety

Jobs run sequentially.  BLAS/OpenMP thread counts are fixed to one by the
launch command.  Before every simulation the runner stops cleanly if available
physical memory is below 8 GiB or its own RSS exceeds 8 GiB.  Every exact row
and MPS job is atomically checkpointed.
