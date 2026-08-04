# Quantum transfer template

This package is an original adaptation skeleton derived from the transferable architectural ideas in the portfolio. It is **not** a copy of the unpublished CIPHER/RG-HLI source.

## Components

- `models.py`: candidate programs, resource contracts, proof objects, and typed residuals.
- `evaluator.py`: RAVR-S-style verifier and multi-objective fitness.
- `promotion_gate.py`: RG-HLI-style held-out operator promotion.
- `cascade.py`: CIPHER-style shared-state cheap-to-expensive evaluation.
- `example_run.py`: dependency-free smoke test.

## Integration points

Implement a `QuantumBackend` adapter that:

1. executes candidate code in an isolated process/container;
2. builds a circuit or hybrid solver;
3. runs Qiskit Aer/CUDA-Q/Metriq-Gym/QPU;
4. verifies the assignment with the QOBLIB verifier;
5. returns `RawBackendResult`.

Then wire the evaluator into OpenEvolve as the task-specific fitness function.

## Safety

Never execute LLM-mutated Python in the main process. Use a sandbox with time, memory, filesystem, and network limits.
