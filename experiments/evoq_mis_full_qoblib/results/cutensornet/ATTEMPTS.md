# cuTensorNet 55-qubit attempt log

All attempts use the frozen native depth-15 QAOA circuits. Completed numerical
results are stored as `raw_*.json`; an absent raw artifact is never interpreted
as a zero-success result.

## Exact contraction sampler

- Backend: cuQuantum/cuTensorNet 26.6.0, contraction-based `TNConfig`.
- Ordering: released sorted-node qubit order.
- Setting: 100 requested shots, 32 hyper-optimizer samples.
- Outcome: `CUTENSORNET_STATUS_INTERNAL_ERROR` during sampler preparation after
  292.7 seconds. Peak observed VRAM was approximately 3.7 GiB, so this was not
  reported as an out-of-memory result.

## Independent MPS runtime limits

- Sorted ordering, bond 64, discarded-weight cutoff `1e-3`, 1,000 shots:
  terminated after 8 minutes 19 seconds without a completed first schedule.
- Sorted ordering, bond 32, discarded-weight cutoff `1e-3`, 100 shots:
  completed in 428.3 seconds for LR and 463.3 seconds for nonlinear.
- Spectral ordering is exact-equivalent before approximation and was validated
  on the 12- and 15-qubit kernels. It lowers the 55-qubit reduced-graph edge
  bandwidth from 47 to 10 and maximum linear cut from 42 to 9.

These limits motivate reporting circuit ordering as part of approximate tensor
network benchmark provenance.
