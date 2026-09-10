# Manuscript package

Working title: **Graph-Scale Normalization Enables Zero-Shot Transfer of Evolutionary QAOA Schedules for Maximum Independent Set**.

The package is deliberately venue-neutral and anonymous. Replace `Anonymous Authors` in `main.tex`, add affiliations/funding, and apply the target venue's class file before submission.

## Build

1. Regenerate figures and machine-readable tables:

   `..\..\..\.venv\Scripts\python.exe build_paper_assets.py`

2. Compile from this directory with `latexmk -pdf main.tex`, or run `pdflatex`, `bibtex`, and `pdflatex` twice.

## Evidence boundary

The paper's primary claim is the paired normalization effect. Evolution-vs-random, robust-objective, feasible-mixer, hardware-noise and quantum-advantage claims are explicitly not promoted. `EXTERNAL_BASELINE_AUDIT.md` explains why the released GAT pipeline is cited but not assigned an invented QOBLIB score.
