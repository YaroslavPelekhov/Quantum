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

The independent backend audit uses cuTensorNet in the dedicated WSL
environment. Export circuits on Windows, then validate or sample in WSL:

```powershell
..\..\.venv\Scripts\python.exe run_cutensornet_audit.py export
wsl.exe -d Ubuntu -- bash -lc "cd /mnt/c/Users/psgpe/Downloads/Taiwan/experiments/evoq_mis_full_qoblib && ~/.venvs/evoq-cuquantum/bin/python run_cutensornet_audit.py validate --hyper-samples 32"
wsl.exe -d Ubuntu -- bash -lc "cd /mnt/c/Users/psgpe/Downloads/Taiwan/experiments/evoq_mis_full_qoblib && ~/.venvs/evoq-cuquantum/bin/python run_cutensornet_audit.py sample --ordering spectral --simulation-mode mps --bond 128 --cutoff 1e-4 --shots 5000"
```

The released artifacts include all raw cuTensorNet samples, exact small-kernel
cross-checks, failed-attempt audit entries, and the classical baseline trials.

The code imports the frozen QOBLIB submission utility module from the cloned
`qoblib-solutions` repository and records its Git commit in every result file.

## Strict resource-aware extension

`RESOURCE_AWARE_PROTOCOL.md` freezes an additional train/validation/blind cycle
before held-out evaluation. It jointly tests reduction caps 2--6, QAOA depths
3--15, 35 schedule genomes, sorted/spectral tensor orderings, and two MPS
fidelities. Exact HiGHS optimization first certifies whether the QOBLIB BKS is
even reachable after each reduction. Candidate acceptance then requires paired
non-inferiority for BKS, near-BKS, and feasibility at *both* simulator
fidelities, together with an actual depth or runtime reduction.

Run or resume the checkpointed stages with:

```powershell
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
$env:NUMEXPR_NUM_THREADS='1'
....\.venv\Scripts\python.exe run_resource_aware_cycle.py --stage all
....\.venv\Scripts\python.exe plot_resource_aware.py
```

The completed frozen cycle evaluated 210 exact schedule-depth configurations,
100 confirmation jobs on validation, and 60 blind jobs (60,000 blind shots).
The minimum BKS-preserving reduction cap was 4. No searched candidate satisfied
the pre-registered quality gate at both MPS fidelities, so the controller
returned `no_eligible_resource_champion` instead of making an unsafe resource
claim. On the blind instance, the prior matched schedule's paired BKS effect
against the published linear ramp reversed from +0.393 percentage points under
the released approximation to -0.420 points under tight confirmation; both
effects were statistically significant. See `RESOURCE_AWARE_REPORT.md` and
`results/figures/resource_aware_cycle.png`.
