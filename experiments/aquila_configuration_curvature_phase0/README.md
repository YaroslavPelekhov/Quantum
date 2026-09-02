# Aquila configuration-space curvature Phase 0

This CPU-only experiment validates or falsifies an Aquila-native realization of
interaction-conditioned Wilson curvature using one static local-detuning mask.
The development pulse is explicitly disclosed; held-out solver, branch,
robustness, null-control, and distance-scaling tests are preregistered.

The broad mechanism has direct density-dependent Peierls-phase prior art.  A
positive result is therefore an integration benchmark, not an A-star novelty
claim.  No QPU task is submitted.

Run from the repository root:

```powershell
python -m unittest experiments.aquila_configuration_curvature_phase0.test_phase0 -v
python experiments/aquila_configuration_curvature_phase0/run_phase0.py
python experiments/aquila_configuration_curvature_phase0/posthoc_asymptotic.py
python experiments/aquila_configuration_curvature_phase0/plot_results.py
python experiments/aquila_configuration_curvature_phase0/build_manifest.py
```

Read `EXPLORATORY_DISCLOSURE.md` and `PREREGISTRATION.md` before interpreting
the outputs.  The post-hoc asymptotic check diagnoses one failed gate and does
not alter the frozen verdict.

