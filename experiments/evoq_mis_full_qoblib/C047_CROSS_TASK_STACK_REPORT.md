# C047 cross-task / cross-stack validation report

## Verdict

The observable-level TVD certificate transfers cleanly beyond the QOBLIB MIS
study. The validation changes the task to MaxCut, the benchmark generator, the
exact SDK and simulator, and the qubit placement, while reusing the frozen
schedules without retuning.

## Completed design

- 4 generated MaxCut graphs: 10, 12, 14, and 16 qubits.
- 2 frozen schedules and 2 logical-to-physical placements.
- 16 exact Qiskit rows and 16 independently constructed Amazon Braket rows.
- 5 Aer/MPS settings, producing 80 approximate states.
- 40 matched-random-minus-linear-ramp effect cohorts.

## Results

| Quantity | Result |
|---|---:|
| Maximum exact Qiskit/Braket TVD | `1.1386340642931422e-15` |
| Maximum exact placement residual | `8.326672684688674e-16` |
| TVD effect inequalities | `40/40` |
| Correct approximate signs | `40/40` |
| Certified cohorts | `16/40` |
| Correct certified signs | `16/16` |
| Rank reversals | `0` |

The absence of a MaxCut reversal is not a failure and was not used to alter the
design. These four instances have substantially larger exact margins than the
small-margin 24-qubit QOBLIB case. The result validates transport of the
sufficient certificate; it does not estimate how frequently reversals occur.

## Novelty boundary

Metamorphic and differential quantum-software testing already exist. C047 does
not claim those paradigms. Its useful design contribution is the simultaneous
task-and-stack triangulation of an application-level ranking certificate:
independently constructed exact circuits gate the experiment before the
approximation ladder is interpreted.

## Original hardware bridge

If QPU access is approved, use a two-anchor randomized-block design rather than
simply rerunning every circuit:

1. Select one C047 cohort with a large certified margin and one QOBLIB cohort
   outside the certificate near the decision boundary.
2. For each, submit two semantics-equivalent qubit placements as twins.
3. Interleave both schedules and both twins within each time block so drift
   cannot masquerade as a schedule effect.
4. Freeze a calibration snapshot and run the same verbatim circuits through a
   calibration-derived local emulator before opening QPU results.
5. Use the robust cohort as a positive control: its sign should survive across
   blocks and twins. Treat the boundary cohort as a sensitivity probe, never as
   an algorithm winner.
6. Split the shot budget into discovery and confirmatory halves. Open the
   confirmatory half only if the pre-specified control and decoder gates pass.

This produces a hardware validation of the certificate's decision semantics,
not a vague simulator-versus-hardware correlation.
