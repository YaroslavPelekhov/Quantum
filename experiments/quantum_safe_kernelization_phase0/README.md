# Quantum-safe kernelization for Rydberg MIS: Phase 0

This experiment asks whether exact classical MIS preprocessing can be unsafe for
the finite-time quantum dynamics of the standard hard-blockade Rydberg
Hamiltonian.  It is an adversarial Phase-0 screen, not a positive novelty
claim.

The preregistration fixes the Hamiltonian, schedule, graph sets, controls, and
kill criteria before numerical outcomes are inspected.  The prior-art audit
records why generic gap preservation, QA Hamiltonian reduction, and the fact
that equivalent encodings can change a spectral gap cannot be claimed as new.

Run from the repository root:

```powershell
python experiments/quantum_safe_kernelization_phase0/run_phase0.py
python -m unittest experiments.quantum_safe_kernelization_phase0.test_qdk_core
```

Outputs are written to `results/quantum_safe_kernelization_phase0/`.
