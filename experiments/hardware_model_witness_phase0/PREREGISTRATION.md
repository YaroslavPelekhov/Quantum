# Frozen Phase-0 protocol

Frozen before inspecting numerical search results on 2026-08-28.

## Claim under test

A search over pairs of logically and structurally matched circuits might expose
ordering information omitted by an isolated-gate calibration model, and might
constitute a new hardware model-falsification primitive rather than a renamed
coherent-error amplification experiment.

## Exact search space

- Gate alphabet: `Xp=Rx(pi/2)`, `Xm=Rx(-pi/2)`, `Yp=Ry(pi/2)`, and
  `Ym=Ry(-pi/2)`.
- Sequence lengths: 4 through 8 inclusive.
- A candidate sequence must implement identity up to global phase.
- A candidate pair must have identical counts of every native gate.
- Composition order, floating-point tolerances, and random seeds are fixed in
  `witness_core.py` and `run_phase0.py`.

## Declared and hidden models

The hidden search oracle applies a signed fractional pulse over-rotation
`epsilon=0.02`, followed after every pulse by a fixed `Rz(delta)` detuning with
`delta=0.01` radians.  The declared model replaces each isolated native-gate
error by a depolarizing retention having the same isolated average gate
fidelity.  Thus two matched circuits receive exactly the same declared
prediction, while the hidden oracle retains ordering and phase.

A gate-local depolarizing oracle is the negative control.  A deterministic grid
of held-out coherent/detuning parameters is used for transfer testing; it is
not used to select the pair.

## Baselines and budgets

1. Exhaustive enumeration is the reference optimum.
2. Uniform random matched-pair sampling is evaluated at 16, 64, 256, and 1024
   pair queries over 128 fixed seeds.
3. A no-optimization cyclic-shift baseline compares rotations of the same
   identity sequence.
4. A GST-like baseline repeats every word of length 1--3 to total length at
   most 8 and reports the largest discrepancy between hidden process fidelity
   and the declared isolated-gate prediction.

## Shot analysis

The best pair is converted to two binomial `P(0)` experiments with 10,000 shots
per circuit.  Clopper--Pearson intervals use family-wise alpha 0.05 with a
Bonferroni correction over every matched pair considered by exhaustive search.
Expected integer counts are used only to test whether the effect size could in
principle survive the frozen shot budget; no simulated count is represented as
hardware data.

## Frozen kill criteria

The A* direction is closed if any one condition is met:

1. Prior art already contains the core capability: designed/repeated circuits
   that amplify coherent or context-dependent errors and reject an inadequate
   gate/noise model.
2. A simple cyclic or GST-like construction exposes at least 90% of the
   exhaustive effect scale, so no new search primitive is demonstrated.
3. Uniform random matched-pair search reaches at least 90% of the exhaustive
   optimum in a majority of trials at 1024 pair queries.
4. Bonferroni-corrected exact intervals overlap at 10,000 shots per circuit.
5. The pair differs in any frozen matched feature.
6. Fewer than 75% of held-out coherent/detuning draws preserve the training
   ordering, or fewer than 50% retain at least half of the training gap.

Passing the simulator screen would only authorize a separate, preregistered
hardware validation.  Failing any criterion forbids QPU spending and forbids
rebranding the result as A* novelty.
