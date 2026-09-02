# Drift-aware amplitude estimation Phase 0

This CPU-only experiment tests whether nonstationary visibility creates a new
amplitude-estimation regime, rather than assuming that it does.  Read the
frozen `PREREGISTRATION.md` before interpreting results.

Run from the repository root:

```powershell
python -m unittest experiments.drift_qae_phase0.test_phase0 -v
python -m experiments.drift_qae_phase0.run_phase0
python -m experiments.drift_qae_phase0.build_manifest
```

Artifacts are written to `results/drift_qae_phase0/`.  No cloud credentials,
sampled QPU observations, or closed-branch QAOA/MPS claims are used.

