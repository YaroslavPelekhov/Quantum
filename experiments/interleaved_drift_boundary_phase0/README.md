# Sequential-reference curvature boundary Phase 0

This CPU-only cycle tests a theorem mechanism at the boundary between
wall-clock calibration and coherent quantum depth.  It is separate from the
closed broad drift-QAE claim.

Run from the repository root:

```powershell
python -m unittest experiments.interleaved_drift_boundary_phase0.test_phase0 -v
python -m experiments.interleaved_drift_boundary_phase0.run_phase0
python -m experiments.interleaved_drift_boundary_phase0.plot_results
python -m experiments.interleaved_drift_boundary_phase0.build_manifest
```

Read `PREREGISTRATION.md` before interpreting generated results.

