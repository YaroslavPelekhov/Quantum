# Aquila one-static-mask Phase 0

This falsification-first experiment tests whether a single spatial local-
detuning mask, fixed for an entire Aquila program, can be temporally
reprogrammed to prepare either member of a reflected pair of Rydberg-blockade
states within documented hardware constraints.

The preregistration is the authoritative scope.  The exact full-`C6` model is
the hardware-facing truth; the hard-blockade model is only a surrogate.  No QPU
submission is made by this experiment.

Run from the repository root after installing the repository dependencies:

```powershell
python experiments/aquila_one_mask_phase0/run_phase0.py
python experiments/aquila_one_mask_phase0/audit_reference.py
python experiments/aquila_one_mask_phase0/plot_results.py
python -m unittest experiments.aquila_one_mask_phase0.test_phase0
```

Outputs are written to `results/aquila_one_mask_phase0/`.

The adaptive-ODE audit is required: it is the step that detects the frozen
optimizer's coarse-mesh false positive.  Do not interpret the optimization-grid
fidelity as a hardware-facing result.
