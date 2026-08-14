# Exact and cross-backend QAOA rank stability on QOBLIB

Advisor-ready research artifact for the manuscript **When Better QAOA
Schedules Depend on the Simulator: Exact and Cross-Backend Rank Reversals on
QOBLIB**.

## Main result

Approximate MPS simulation can change which depth-15 QAOA schedule appears
better on rare best-known-solution (BKS) events. The final frozen replication
contains five real QOBLIB MIS cases, five MPS settings, three schedules, two
exact-equivalent qubit orderings, and two independent implementations (Qiskit
Aer and NVIDIA cuTensorNet): 300 dense backend rows.

- 91/100 matched-random-vs-LR cohorts preserve the exact effect sign.
- Aer and cuTensorNet agree in 45/50 matched cohorts.
- For exact distributions `p_i,p_j` and approximate distributions `q_i,q_j`,
  the event-effect error satisfies
  `|approx_effect - exact_effect| <= TVD(q_i,p_i) + TVD(q_j,p_j)`.
- All 100 measured inequalities hold.
- The exact-margin certificate covers 77 cohorts; all 77/77 preserve the exact
  sign. Outside it, 14/23 signs are correct (descriptive Fisher exact
  `p=4.30e-7`).
- All nine sign failures occur on the 24-qubit case with the smallest exact
  effect margin.

The earlier 55-qubit blind experiment provides the motivating failure: the
transferred schedule leads 101 to 41 BKS hits at the released Aer setting, but
the ranking reverses when only the truncation cutoff is tightened. Strong
classical controls dominate; this work makes no quantum-advantage claim.

## Start here

- `ADVISOR_BRIEF.md`: one-page interpretation and discussion prompts.
- `paper/output/pdf/qaoa_mps_cross_backend_rank_reversal_manuscript.pdf`:
  main paper.
- `paper/output/pdf/qaoa_mps_cross_backend_rank_reversal_supplement.pdf`:
  full tables, certificate derivation, controls, and artifact map.
- `CROSS_CASE_REPLICATION_PROTOCOL.md`: protocol frozen before the 240 new
  backend jobs.
- `results/cross_case_replication/analysis.json`: complete machine-readable
  cross-case analysis.
- `results/figures/cross_case_replication.pdf`: publication figure.

## Repository map

```text
paper/                         LaTeX sources and stable PDFs
results/cross_case_replication/
  export_manifest.json        hashes for circuits, exact states, and reused data
  aer_jobs.json               120 new deterministic Aer rows
  cutensornet_jobs.json       120 new deterministic cuTensorNet rows
  combined_jobs.json          all 300 rows
  analysis.json               100 cohort summaries and primary outcomes
  paper_statistics.json       intervals and descriptive Fisher test
results/mps_ladder/            exact 24-qubit references and Aer ladder
results/independent_ladder/    independent 24-qubit cuTensorNet ladder
run_cross_case_replication.py  export, self-test, execute, analyze, status
plot_cross_case_replication.py paper figure and compact tables
test_*.py                      integrity and numerical tests
artifact_manifest.json         SHA-256 artifact inventory
```

## Reproduce the final analysis

The completed backend checkpoints can be reanalyzed without rerunning any
simulation:

```powershell
$py = "C:\Users\psgpe\Downloads\Taiwan\.venv\Scripts\python.exe"
& $py run_cross_case_replication.py analyze
& $py plot_cross_case_replication.py
& $py -m unittest -v test_cross_case_replication.py test_independent_ladder_audit.py
& $py build_manifest.py
```

Build the paper from `paper/`:

```powershell
pdflatex -interaction=nonstopmode -halt-on-error -output-directory output/pdf main.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory output/pdf main.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory output/pdf supplement.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory output/pdf supplement.tex
```

Tested Windows analysis environment: Python 3.13.0, Qiskit 2.5.1, Aer 0.17.2,
NumPy 2.5.1, SciPy 1.18.0, and Matplotlib 3.11.1. The independent backend uses
the recorded WSL cuQuantum/cuTensorNet 26.6.0 environment.

## Full backend execution

Export and validate immutable inputs on Windows:

```powershell
& $py run_cross_case_replication.py export
& $py run_cross_case_replication.py self-test-aer
wsl.exe -d Ubuntu -- /root/.venvs/evoq-cuquantum/bin/python `
  /mnt/c/Users/psgpe/Downloads/Taiwan/experiments/evoq_mis_full_qoblib/run_cross_case_replication.py self-test-cutn
```

The protected sequential runner executes one heavy job at a time, resumes from
atomic checkpoints, and never issues reboot or shutdown commands:

```powershell
& C:\Users\psgpe\Downloads\Taiwan\run_cross_case_replication_safely.ps1
```

## GitHub note

Six exact 24-qubit `.npy` states are 256 MiB each and exceed GitHub's normal
100 MB file limit. Put `results/mps_ladder/references/*.npy` under Git LFS or
publish them as a versioned release/archive. Their identities are preserved in
`results/mps_ladder/exact_references.json` and the export manifests; the paper,
analysis JSON, circuits, compact tables, and figures remain independently
reviewable without downloading those dense arrays.

## Scope

This is an exact-calibrated simulator study, not hardware evidence. The Fisher
test treats correlated setting cohorts descriptively; the main guarantee is
the deterministic TVD inequality. The 55-qubit circuit remains approximate,
and the five-case replication is limited to one MIS reduction family, three
frozen schedules, two simulator implementations, and one GPU platform.
