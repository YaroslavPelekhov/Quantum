# Causal boundary-response Phase 0

This experiment asks whether a classically removable pendant Rydberg motif has
a finite-time boundary response that can be represented by substantially fewer
physical atoms.  It starts with an information-theoretic rank gate and a
same-budget locality baseline, before any expensive surrogate fitting.

Run from the repository root:

```powershell
python -m experiments.causal_boundary_response_phase0.run_phase0
python -m unittest experiments.causal_boundary_response_phase0.test_phase0
```

The frozen design is in `PREREGISTRATION.md`.  Generated artifacts are written
to `results/causal_boundary_response_phase0/`.

