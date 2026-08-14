# Frozen exact-calibrated MPS fidelity-ladder protocol

Frozen on 2026-08-10 before any MPS result in this cycle was generated.

## Question

For the real QOBLIB `aves-sparrow-social` maximum-independent-set instance,
how much MPS fidelity is required to recover the exact ranking of three fixed
QAOA schedules, and which simulator control (bond dimension or truncation
cutoff) is responsible for a wrong application-level conclusion?

The preceding exact cycle established, before this protocol was written, that
matched-random minus published-linear BKS probability is `-0.01213885`, while
the released and confirmation sampled MPS settings reported positive effects.
This cycle measures convergence; it does not select or tune a schedule.

## Frozen problem and schedules

- Instance: `aves-sparrow-social` (QOBLIB MIS).
- BKS: 13.
- Reduction cap: `max_degree=20`.
- Kernel: 24 qubits, 59 reduced edges.
- QAOA depth: `p=15`.
- Native decoding only; constraint repair remains disabled.
- Orderings: sorted and graph-spectral.

The three schedules are unchanged:

1. published LR: `(0.7, 0.4, 1.0, 1.0)`;
2. prior evolutionary:
   `(0.5175030726816078, 0.7719741612274684,
   1.0773373543262421, 1.7543477389249704)`;
3. prior matched-random:
   `(0.6424738670407446, 0.7593921349176262,
   1.776791693083474, 0.9917239502490107)`.

## Exact references

Six double-precision exact statevectors (three schedules by two orderings) are
generated once with `Statevector.from_instruction` and stored locally as
atomic `.npy` checkpoints.  Their application metrics must agree with the
completed exact-extension artifact within `1e-10`, and the statevector norm
must agree with one within `1e-10`.

## Frozen MPS settings

Each setting is evaluated for all three schedules and both orderings, with no
measurement shots.  Aer MPS evolves the circuit and exports its approximate
dense final statevector; metrics are accumulated in bounded chunks.

Anchors:

- `released`: bond 64, cutoff `1e-3`;
- `confirm`: bond 128, cutoff `1e-4`.

Bond-isolation sweep (cutoff fixed at `1e-12`):

- bond 64, 128, 256, 512, and 1024.

Cutoff-isolation sweep (bond fixed at 1024):

- cutoff `1e-3`, `1e-4`, `1e-5`, and `1e-6`.

The frozen cohort therefore contains 11 settings and 66 MPS jobs.  No setting
may be added, removed, or promoted after observing a result in this cycle.

## Outcomes

Primary outcome: matched-random minus published-LR native BKS probability.
The primary correctness event is agreement of its sign with the exact effect.

Secondary outcomes:

- evolutionary minus published-LR BKS probability;
- BKS-minus-one, feasible, and quality-mass errors versus exact;
- pure-state fidelity `|<exact|MPS>|^2` after normalization;
- total-variation distance between computational-basis distributions;
- runtime and circuit resources.

The minimum tested bond with correct primary sign is reported separately for
each ordering.  Cutoff results are interpreted only at fixed bond 1024.  A
metric is never promoted based on feasibility alone.

## Completion and execution integrity

- Every exact reference and every MPS job is checkpointed atomically.
- Existing deterministic identities are deduplicated on resume.
- Partial cohorts are retained for resume but never interpreted as complete.
- Protocol, runner, exact-reference, QOBLIB, Python, NumPy, Qiskit, and Aer
  provenance are recorded.
- Only one job and one BLAS/OpenMP thread run at a time.
- The host guard polls every five seconds and terminates only the experiment
  after two consecutive unsafe readings: free RAM below 12 GB, committed
  virtual memory above 70%, or free C: space below 100 GB.
- The guard cannot reboot Windows.

The exact vectors are local transient research checkpoints and are excluded
from publication artifacts; derived hashes, metrics, and comparisons remain.
