# Aquila gauge-resource Phase 0

This CPU-only cycle tests whether spectral compilation remains difficult after
optimizing over every vertex gauge and every circular phase lift.

Start with `PREREGISTRATION.md`, then read `THEORY_AND_SCOPE.md` and the final
report in `results/aquila_gauge_resource_phase0/FINAL_REPORT.md`.

Reproduce from the repository root:

```powershell
python -m unittest experiments.aquila_gauge_resource_phase0.test_phase0 -v
python -m unittest experiments.aquila_gauge_resource_phase0.test_full_dynamics -v
python -m experiments.aquila_gauge_resource_phase0.audit_theorem_constants
python -m experiments.aquila_gauge_resource_phase0.run_phase0
python -m experiments.aquila_gauge_resource_phase0.run_posthoc_microperturbation
python -m experiments.aquila_gauge_resource_phase0.full_dynamics_audit
python -m experiments.aquila_gauge_resource_phase0.plot_results
python -m experiments.aquila_gauge_resource_phase0.build_manifest
```

The post-hoc microperturbation is diagnostic and cannot change the frozen
verdict.  Use `--resume` on either long MILP command to reuse atomic completed
rows after interruption.  The full-dynamics audit is also post-hoc: it tests
the theorem's scope boundary and cannot upgrade the frozen A-star verdict.
Its optional, materially slower Torch search provenance is reproduced with
`python -m experiments.aquila_gauge_resource_phase0.optimize_full_dynamics`;
the archived pulse audit itself does not require Torch.
