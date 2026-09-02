# Reproducing the QOBLIB QAOA/MPS audit

All commands below are run from the repository root unless stated otherwise.
The archived results were produced on Windows with CPU Qiskit Aer and in WSL2
Ubuntu with an NVIDIA RTX 4070 Ti SUPER (16 GB) for cuTensorNet. The host exposed
48 GB system RAM with XMP disabled; the cross-case runs used a protected
single-job watchdog and a separate WSL cuTensorNet environment.

## 0. Reproduce the latest Aquila falsification cycles

These exact CPU cycles submit zero QPU tasks.  Reproduce the latest
gauge-resource cycle first:

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

The registered MILPs can be resumed after interruption.  The held-out
microperturbation is explicitly post-hoc and cannot reverse the frozen failed
verdict.  The full-dynamics audit is also post-hoc; it demonstrates why the
theorem applies only to scalar weak-drive response and cannot be extrapolated
to the complete finite-amplitude propagator.
The optional Torch discovery run is documented in
`experiments/aquila_gauge_resource_phase0/EXPLORATORY_OPTIMIZATION.md`; it is
not required to validate the frozen pulse.

The two preceding Aquila cycles are:

```powershell
python -m unittest experiments.aquila_one_mask_phase0.test_phase0 -v
python experiments/aquila_one_mask_phase0/run_phase0.py
python experiments/aquila_one_mask_phase0/audit_reference.py
python experiments/aquila_one_mask_phase0/plot_results.py
python experiments/aquila_one_mask_phase0/build_manifest.py

python -m unittest experiments.aquila_configuration_curvature_phase0.test_phase0 -v
python experiments/aquila_configuration_curvature_phase0/run_phase0.py
python experiments/aquila_configuration_curvature_phase0/posthoc_asymptotic.py
python experiments/aquila_configuration_curvature_phase0/compiler_rank_audit.py
python experiments/aquila_configuration_curvature_phase0/plot_results.py
python experiments/aquila_configuration_curvature_phase0/build_manifest.py
```

Read each preregistration and the curvature cycle's exploratory disclosure
before interpreting outputs.  The one-mask adaptive-ODE audit is mandatory: it
is what detects the coarse-grid pulse-optimization false positive.  The
curvature post-hoc distance extension diagnoses one failed finite-range gate
and does not change the frozen verdict.  The compiler audit is an exact
finite-field falsifier of the post-validation low-rank conjecture for
`n=3,4,5,6`; its polynomial rank profile is a tested-size witness, not an
all-size proof.

## 0. Reproduce the causal boundary-response closure

This CPU-only exact cycle has no cloud credentials or QPU dependency:

```powershell
python -m experiments.causal_boundary_response_phase0.run_phase0
python -m experiments.causal_boundary_response_phase0.run_rank_audit
python -m experiments.causal_boundary_response_phase0.run_physical_surrogate
python -m experiments.causal_boundary_response_phase0.run_capacity_audit
python -m experiments.causal_boundary_response_phase0.run_host_transfer
python -m experiments.causal_boundary_response_phase0.run_process_gram
python -m unittest experiments.causal_boundary_response_phase0.test_phase0 -v
python -m experiments.causal_boundary_response_phase0.build_manifest
```

Read each preregistration before interpreting a rerun.  The capacity audit is
the slowest step.  The final A-star verdict is determined by the frozen
process-Gram gate, not by the positive isolated-response fit.

## 0a. Reproduce the hardware-witness Phase-0 closure

This small exact falsification screen is independent of Qiskit and does not use
hardware credentials.  With the pinned NumPy/SciPy environment installed:

```powershell
python -m unittest experiments.hardware_model_witness_phase0.test_witness_core
python experiments/hardware_model_witness_phase0/run_phase0.py
```

The run deterministically enumerates 87,296 sequences, executes 128 fixed-seed
random-search trials at four budgets, and rewrites
`results/hardware_model_witness_phase0/`.  Its 10,000-shot calculation uses
expected binomial counts and exact intervals; it does not claim sampled or QPU
observations.  Read the frozen protocol before interpreting or changing the
search space.

## 1. Obtain pinned benchmark code

```bash
git submodule update --init --recursive
git submodule status
```

The experiment imports the released QOBLIB MIS reduction and decoder from
`baselines/qoblib-solutions` and graph data from `QOBLIB`. Do not silently swap
these revisions: reduction and gate representation affect the benchmark.

## 2. CPU/Aer environment

Python 3.13 was used for the archived Windows runs.

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
cd experiments\evoq_mis_full_qoblib
```

Fast verification:

```powershell
..\..\.venv\Scripts\python.exe -m unittest -v test_full_cycle.py
..\..\.venv\Scripts\python.exe analyze_results.py
..\..\.venv\Scripts\python.exe analyze_extended_results.py
..\..\.venv\Scripts\python.exe build_manifest.py
```

Final cross-case verification from the experiment directory:

```powershell
..\..\.venv\Scripts\python.exe -m unittest discover -v -p "test_*.py"
..\..\.venv\Scripts\python.exe run_cross_case_replication.py analyze
..\..\.venv\Scripts\python.exe plot_cross_case_replication.py
```

The completed public checkpoints contain all 300 compact backend rows. Six
256-MiB dense 24-qubit `.npy` references are omitted from ordinary Git history;
their SHA-256 identities are recorded in the manifests and they can be supplied
through Git LFS or a release archive.

Run the research cycle or individual audits:

```powershell
..\..\.venv\Scripts\python.exe run_cycle.py --stage all
..\..\.venv\Scripts\python.exe run_exact_mps_calibration.py
..\..\.venv\Scripts\python.exe run_classical_baselines.py
```

`run_cycle.py --stage all` rewrites primary artifacts and can take a long time.
Checkpoints are written after long jobs. The frozen protocol and deviations must
be read before interpreting a rerun.

## 3. Independent cuTensorNet environment

The archived independent backend used:

- Qiskit `2.5.1`
- cuQuantum Python for CUDA 12 `26.6.0`
- CuPy CUDA 12 `14.1.1`
- NumPy `2.5.1`
- SciPy `1.18.0`

Create a separate Linux/WSL environment with a working NVIDIA CUDA driver:

```bash
python3 -m venv ~/.venvs/evoq-cuquantum
~/.venvs/evoq-cuquantum/bin/python -m pip install -r requirements-cutensornet.txt
nvidia-smi
```

First export QPY circuits and exact small-kernel references in the CPU/Aer
environment:

```powershell
cd experiments\evoq_mis_full_qoblib
..\..\.venv\Scripts\python.exe run_cutensornet_audit.py export
```

Then enter the same project directory from WSL and run:

```bash
~/.venvs/evoq-cuquantum/bin/python run_cutensornet_audit.py validate --hyper-samples 32
~/.venvs/evoq-cuquantum/bin/python run_cutensornet_audit.py sample \
  --ordering spectral --simulation-mode mps --bond 128 --cutoff 1e-3 --shots 5000
~/.venvs/evoq-cuquantum/bin/python run_cutensornet_audit.py sample \
  --ordering spectral --simulation-mode mps --bond 128 --cutoff 1e-4 --shots 5000
```

Decode and aggregate in the CPU environment:

```powershell
..\..\.venv\Scripts\python.exe run_cutensornet_audit.py decode
..\..\.venv\Scripts\python.exe analyze_extended_results.py
```

The exact 55-qubit sampler attempt is expected to be difficult and is not a
required success criterion. In the archived run it returned
`CUTENSORNET_STATUS_INTERNAL_ERROR` during sampler preparation. Failed and
terminated attempts belong in `results/cutensornet/ATTEMPTS.md`; they must not
be represented as completed data points.

## 4. Paper build

From `experiments/evoq_mis_full_qoblib/paper`:

```bash
pdflatex -interaction=nonstopmode -halt-on-error -output-directory output/pdf main.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory output/pdf main.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory output/pdf supplement.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory output/pdf supplement.tex
```

The public deliverables use stable filenames beginning
`qaoa_mps_cross_backend_rank_reversal_`; LaTeX intermediates and duplicate
default filenames are intentionally not tracked.

## 5. Artifact integrity

Run `build_manifest.py` only after all intended artifact changes. It records
relative paths, byte counts, and SHA-256 values while excluding caches,
temporary renders, and LaTeX intermediates. A clean verification run should
also report 29 passing integrity and numerical tests in the archived
environment.

