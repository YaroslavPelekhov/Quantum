# Dynamical kernel geometry: Phase 0

This phase tests a connected endpoint-bijective leaf-reduction family designed
to separate minimum-gap preservation from finite-time annealing performance.
See `PREREGISTRATION.md` for the frozen success gates and
`PRIOR_ART_BOUNDARY.md` for the narrow claim boundary.

Run:

```powershell
python experiments/dynamical_kernel_geometry_phase0/run_family.py
python -m unittest experiments.dynamical_kernel_geometry_phase0.test_family
```

Results are written to `results/dynamical_kernel_geometry_phase0/`.
