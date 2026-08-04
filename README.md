# Quantum × Evolutionary Computing Research Artifact

This repository contains a complete research cycle on evolutionary transfer of
QAOA schedules and the reliability of approximate tensor-network benchmarking.
The central experiment uses the real QOBLIB Maximum Independent Set instance
`es60fst02`: 186 vertices are reduced by the released QOBLIB pipeline to a
55-qubit, depth-15 QAOA circuit.

The result is deliberately **not** presented as quantum advantage. Its main
contribution is a reproducible cross-backend demonstration that a rare-event
metric—probability of sampling a best-known solution (BKS)—can change the
ranking of QAOA schedules when MPS truncation, bond dimension, implementation,
or qubit ordering changes, even while broader feasible-mass metrics agree.

## Headline results

| Evaluation | Published linear ramp | Frozen nonlinear ramp | Interpretation |
|---|---:|---:|---|
| Aer MPS, bond 64, cutoff `1e-3`, 15,000 shots | 41 BKS (`0.273%`) | 101 BKS (`0.673%`) | nonlinear appears `2.46×` better; paired delta `+0.00400`, 95% CI `[0.00247, 0.00553]` |
| Aer MPS, bond 64, cutoff `1e-4`, 10,000 shots | 153 BKS (`1.53%`) | 109 BKS (`1.09%`) | ranking reverses |
| cuTensorNet MPS, spectral order, bond 128, cutoff `1e-3`, 5,000 shots | 6 BKS (`0.12%`) | 15 BKS (`0.30%`) | directional only, Fisher two-sided `p=0.078` |
| cuTensorNet MPS, spectral order, bond 128, cutoff `1e-4`, 5,000 shots | 12 BKS (`0.24%`) | 11 BKS (`0.22%`) | no resolved difference, `p=1.0` |

Exact state checks on the real 12- and 15-qubit donor kernels converge above
`0.99983` fidelity at cutoff `1e-6`. Independent cuTensorNet exact contractions
match the Qiskit reference states to displayed unit fidelity. The attempted
exact 55-qubit cuTensorNet sampler failed during contraction preparation after
about 293 seconds; every completed 55-qubit tensor-network result is therefore
explicitly labeled approximate.

Strong classical controls establish the correct competitive context:

| Classical method | Trials | BKS rate | Wall time |
|---|---:|---:|---:|
| SciPy/HiGHS exact MILP | 1 | optimum 88 certified, zero reported gap | `0.036 s` |
| Randomized minimum-residual-degree, full 186-vertex graph | 15,000 | `7.553%` | `19.95 s` |
| Same heuristic on released 55-variable kernel | 15,000 | `40.420%` | `2.21 s` |
| Best released-setting QAOA row | 15,000 | `0.673%` | about `183.04 s` allocated method time |

The full-graph and kernel heuristics achieve respectively `11.2×` and `60.0×`
the QAOA BKS rate while also running faster. The contribution is benchmarking
methodology and simulator auditing, not solver superiority.

## Research design

- Training: `es60fst01` and `es60fst03`.
- Validation: `es60fst04`.
- Blind test: `es60fst02`.
- Frozen candidate: a four-parameter nonlinear power ramp.
- Search controls: equal-budget evolutionary search and uniform random search.
- Promotion: validation only; blind-test outcomes never reselect a schedule.
- Scoring: unfolded samples must already be valid independent sets; repair,
  greedy fill, local search, and archived-solution fallback are disabled.
- Primary inference: 15 paired simulator jobs, 1,000 shots per method/job,
  paired bootstrap intervals, and an exact two-sided sign-flip test.

The strongest transferring schedule came from matched random search, not the
evolutionary operator. This negative optimizer result is retained rather than
hidden.

## Repository map

```text
experiments/evoq_mis_full_qoblib/
  run_cycle.py                    train/validate/blind QAOA cycle
  run_exact_mps_calibration.py    exact-vs-MPS donor calibration
  run_cutensornet_audit.py        QPY export, exact validation, MPS sampling
  run_classical_baselines.py      HiGHS and randomized greedy controls
  analyze_results.py              primary tables, figures, paired inference
  analyze_extended_results.py     cross-backend/classical comparison
  test_full_cycle.py              eight artifact-integrity tests
  results/                        raw jobs, counts, states, CSVs, figures
  paper/                          LaTeX, manuscript PDF, supplement PDF
  FROZEN_PROTOCOL.md              precommitted split and promotion gate
  PROTOCOL_DEVIATIONS.md          preserved protocol deviations
  artifact_manifest.json          SHA-256 manifest
docs/QUANTUM_EVOLUTION_RESEARCH_MAP.md
prior_work/evolutionary_computing_portfolio/
QOBLIB, metriq-gym, baselines/    pinned upstream Git submodules
```

## Start here

Clone with the exact external revisions:

```bash
git clone --recurse-submodules https://github.com/YaroslavPelekhov/Quantum.git
cd Quantum
```

Create a Python 3.13 environment and install the CPU/Aer dependencies:

```bash
python -m venv .venv
# Windows: .venv\Scripts\python -m pip install -r requirements.txt
# Linux:   .venv/bin/python -m pip install -r requirements.txt
```

Run the fast integrity suite and regenerate derived results:

```bash
cd experiments/evoq_mis_full_qoblib
python -m unittest -v test_full_cycle.py
python analyze_results.py
python analyze_extended_results.py
python build_manifest.py
```

The full Aer MPS and cuTensorNet sweeps are substantially slower. Exact commands,
environment separation, expected artifacts, and failure semantics are documented
in [REPRODUCIBILITY.md](REPRODUCIBILITY.md).

## Primary outputs

- [Main manuscript](experiments/evoq_mis_full_qoblib/paper/output/pdf/qaoa_mps_rank_reversal_manuscript.pdf)
- [Supplementary information](experiments/evoq_mis_full_qoblib/paper/output/pdf/qaoa_mps_rank_reversal_supplement.pdf)
- [Extended baseline report](experiments/evoq_mis_full_qoblib/EXTENDED_BASELINE_REPORT.md)
- [Classical raw summary](experiments/evoq_mis_full_qoblib/results/classical_baselines.json)
- [cuTensorNet sweep](experiments/evoq_mis_full_qoblib/results/cutensornet_sweep.csv)
- [Cross-backend comparison](experiments/evoq_mis_full_qoblib/results/extended_comparison.json)
- [Independent attempt log](experiments/evoq_mis_full_qoblib/results/cutensornet/ATTEMPTS.md)

## Reproducibility status

- Eight integrity tests pass.
- Raw integer counts are retained; displayed rates are reconstructible.
- Frozen schedules, seeds, simulator settings, host metadata, and wall times are
  stored in JSON artifacts.
- Small-kernel exact references and exported QPY circuits are included.
- The checksum manifest excludes only caches, temporary renders, and LaTeX build
  intermediates.
- External repositories are pinned as Git submodules; see
  [THIRD_PARTY.md](THIRD_PARTY.md).

## Limitations

This is one four-instance MIS family and one reduction policy. The 55-qubit
state is not exactly certified, both large-circuit MPS implementations are
noiseless approximations, and no quantum hardware run is claimed. The
10,000-shot Aer sensitivity points are single simulator jobs. The experiment
does not establish which tested schedule is closer to the exact 55-qubit
distribution.

## Citation

The repository includes [CITATION.cff](CITATION.cff). The manuscript is a
research draft dated 3 August 2026; author/affiliation metadata can be updated
before submission without changing the frozen experimental artifacts.

