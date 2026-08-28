# Frozen optimized-baseline performance falsification

Frozen 2026-08-28 before running the optimized dense baseline.

## Target

Attack the reported `23.90x` steady-state speedup, which used one timing of a
NumPy dense implementation.  Replay the same sorted 24-qubit aves QAOA state
against Qiskit Aer statevector simulation of explicit RZ/RZZ/RX layers.

## Timing design

- Same graph, normalized MIS Hamiltonian, depth 15, published schedule, initial
  `|+>^24`, local Windows CPU process.
- Transpile the Aer circuit once, outside repeated execution timings.
- Run three Aer statevector repetitions and seven twin-quotient repetitions.
- Report all raw times and medians; do not discard warm-up or slow runs.
- Validate both methods against the archived exact state on 20,000 frozen
  sample indices, modulo global phase.
- Separately measure seven executions of the three-cut quotient decision core.
- Report compile/transpile time and exact state-representation bytes.

## Decision rule

The old numeric `23.90x` claim is rejected unless it lies within 20% of the new
Aer-median / quotient-median ratio.  A weaker practical speedup survives only
if both the median steady-state ratio and the conservative fastest-Aer /
slowest-quotient ratio exceed `2x`.  Exactness requires maximum sampled
probability error below `1e-12` for both backends.

This is a single-machine falsification benchmark, not a universal performance
claim.  Qiskit/Aer versions, CPU count, raw times, and protocol hash are frozen
in the output.
