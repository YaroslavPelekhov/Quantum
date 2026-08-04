# Full-instance QOBLIB research cycle

This experiment tests transfer of low-dimensional nonlinear-ramp QAOA
schedules on the four real `es60fst` Maximum Independent Set instances in
QOBLIB. The split is frozen before held-out evaluation:

- train: `es60fst01` (123 vertices, BKS 60) and `es60fst03` (113, BKS 55);
- validation: `es60fst04` (162, BKS 78);
- blind test: `es60fst02` (186, BKS 88).

All instances use the published degree-reduction/folding/pruning pipeline with
`max_degree=4`. Samples are unfolded to the original graph and only raw valid
independent sets are scored. Constraint repair is disabled.

The candidate schedule has four parameters:

`beta_k = delta_beta * ((p-k+1)/p)^beta_power`

`gamma_k = delta_gamma * (k/p)^gamma_power`

The benchmark compares the published linear ramp `(0.7, 0.4, 1, 1)`, a
matched-budget uniform random search, and a robust evolutionary search. Search
fitness is based on Wilson lower bounds for feasible, BKS-1, and BKS hit rates
plus feasible quality mass. Search cost and deployment shots are reported
separately.

Run with the workspace Python environment:

```powershell
..\..\.venv\Scripts\python.exe run_cycle.py --stage all
```

Regenerate the exact-state calibration, derived tables/figures, tests, and
manifest with:

```powershell
..\..\.venv\Scripts\python.exe run_exact_mps_calibration.py
..\..\.venv\Scripts\python.exe run_classical_baselines.py
..\..\.venv\Scripts\python.exe analyze_results.py
..\..\.venv\Scripts\python.exe analyze_extended_results.py
..\..\.venv\Scripts\python.exe -m unittest -v test_full_cycle.py
..\..\.venv\Scripts\python.exe build_manifest.py
```

The independent backend audit uses cuTensorNet in a dedicated WSL/Linux
environment. Export circuits on Windows, then enter this same directory from
WSL and validate or sample:

```powershell
..\..\.venv\Scripts\python.exe run_cutensornet_audit.py export
# In WSL, after `cd` to this directory:
~/.venvs/evoq-cuquantum/bin/python run_cutensornet_audit.py validate --hyper-samples 32
~/.venvs/evoq-cuquantum/bin/python run_cutensornet_audit.py sample --ordering spectral --simulation-mode mps --bond 128 --cutoff 1e-4 --shots 5000
```

The released artifacts include all raw cuTensorNet samples, exact small-kernel
cross-checks, failed-attempt audit entries, and the classical baseline trials.

The code imports the frozen QOBLIB submission utility module from the cloned
`qoblib-solutions` repository and records its Git commit in every result file.
