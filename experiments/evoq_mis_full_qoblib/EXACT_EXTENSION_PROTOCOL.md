# Frozen 24-qubit exact-adjudication protocol

Frozen on 2026-08-09 before any result from this extension was generated.

## Question

On the real QOBLIB `aves-sparrow-social` maximum-independent-set instance,
does the schedule ranking observed with approximate MPS simulation agree with
the exact noiseless QAOA distribution?  This instance is the primary target
because the matched-random minus published-linear BKS effect decreased from
approximately +0.186 at the released MPS setting to +0.0436 at confirmation
for sorted ordering, the largest attenuation in the completed external cycle.

## Frozen instance and circuit

- Instance: `aves-sparrow-social`.
- Repository BKS: 13.
- Reduction cap: `max_degree=20`.
- Certified quantum kernel: 24 qubits and 59 reduced edges.
- QAOA depth: `p=15`.
- Constraint repair: disabled.
- Orderings: sorted and graph-spectral.

Both orderings are mandatory.  They represent the same exact circuit up to a
qubit permutation, so their metric disagreement must not exceed `1e-10`.

## Frozen schedules

No schedule is tuned in this extension:

1. published linear ramp: `(0.7, 0.4, 1.0, 1.0)`;
2. prior evolutionary schedule:
   `(0.5175030726816078, 0.7719741612274684,
   1.0773373543262421, 1.7543477389249704)`;
3. prior matched-random schedule:
   `(0.6424738670407446, 0.7593921349176262,
   1.776791693083474, 0.9917239502490107)`.

## Backend and outcomes

Qiskit `Statevector.from_instruction` in double precision produces the exact
noiseless distribution.  There are no measurement shots, seeds, truncation
cutoffs, or post-selection.  Primary outcomes are native BKS probability,
BKS-minus-one-or-better probability, and raw feasible probability.  Secondary
outcomes are quality mass and conditional mean independent-set size.

The primary estimands are each prior schedule minus the published linear ramp
for every outcome.  The exact result is compared, without refitting, against
the already frozen released MPS (`bond=64`, cutoff `1e-3`) and confirmation MPS
(`bond=128`, cutoff `1e-4`) cohorts.  MPS bias is defined as mean sampled MPS
rate minus the exact probability; finite-shot uncertainty is not conflated
with exact-backend error.

## Completion and integrity

The cohort contains exactly six jobs: three schedules by two orderings.  Each
job is checkpointed atomically.  A result is interpretable only after all six
jobs finish, the ordering-invariance audit passes, and the protocol hash
matches.  Partial rows are retained only for resume and are not analyzed.

Only one job and one BLAS/OpenMP thread may run at a time.  The protected host
runner checks resources every five seconds and terminates only the experiment
if free RAM falls below 10 GB, committed virtual memory exceeds 75%, or free
system-disk space falls below 10 GB on two consecutive checks.  No watchdog
action may reboot Windows.

The 28-qubit `johnson8-2-4` case and all 64-qubit cases are excluded from this
exact cohort: dense probability enumeration would materially increase memory
risk and was not substituted after observing results.
