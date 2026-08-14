# Quantum x Evolutionary Computing Research Artifact

Reproducible research repository on evolutionary QAOA schedule transfer and
the reliability of approximate tensor-network benchmarking on real QOBLIB
Maximum Independent Set instances.

The final contribution is not a quantum-advantage claim. It is an
application-facing validation rule for approximate simulation: before declaring
one QAOA schedule better than another, the simulator error must be small relative
to the observed performance margin.

## Final headline result

The frozen exact replication contains:

- five real QOBLIB MIS cases reduced to 3, 7, 7, 18, and 24 qubits;
- five MPS bond/cutoff settings;
- the published linear ramp, a prior evolutionary schedule, and an
  equal-budget matched-random schedule;
- sorted and spectral qubit orderings; and
- Qiskit Aer MPS and NVIDIA cuTensorNet MPS.

This gives 300 dense backend rows: 240 newly executed after protocol freeze and
60 reused only after SHA-256 validation.

| Primary outcome | Result |
|---|---:|
| Correct matched-random-vs-LR effect signs | **91/100** |
| Aer/cuTensorNet sign agreement | **45/50** |
| Verified event-effect TVD inequalities | **100/100** |
| Exact-margin TVD certificates | **77/100** |
| Correct signs inside certificate | **77/77** |
| Correct signs outside certificate | **14/23** |
| Fidelity-only certificates | **58/100** |

For BKS event `A`, schedules `i,j`, exact distributions `p`, and approximate
distributions `q`,

```text
|(q_i(A)-q_j(A)) - (p_i(A)-p_j(A))|
    <= TVD(q_i,p_i) + TVD(q_j,p_j).
```

Therefore the approximate sign is certified whenever the exact effect magnitude
exceeds the summed TVD budget. Every certified cohort preserves the exact sign.
All nine observed failures occur on the 24-qubit case with the smallest exact
effect margin. The descriptive Fisher comparison across the certificate
threshold is `p=4.30e-7`; the guarantee itself is deterministic and does not
depend on that statistical test.

## Motivating 55-qubit result

On `es60fst02` (186 original vertices, 55-qubit depth-15 circuit), the released
Aer MPS setting gives 101 BKS hits for the transferred nonlinear schedule and
41 for the published ramp in 15,000 shots each. Tightening only the truncation
cutoff reverses the ranking. Independent cuTensorNet sampling also loses the
nonlinear advantage as accuracy is tightened.

Strong classical controls dominate both QAOA schedules. Evolutionary search
also fails to beat its matched random-search control. These negative results
are retained: the contribution is benchmark validity and resource-aware
simulation, not optimizer or solver superiority.

## Start here

- [Main manuscript](experiments/evoq_mis_full_qoblib/paper/output/pdf/qaoa_mps_cross_backend_rank_reversal_manuscript.pdf)
- [Supplementary information](experiments/evoq_mis_full_qoblib/paper/output/pdf/qaoa_mps_cross_backend_rank_reversal_supplement.pdf)
- [One-page advisor brief](experiments/evoq_mis_full_qoblib/ADVISOR_BRIEF.md)
- [Frozen cross-case protocol](experiments/evoq_mis_full_qoblib/CROSS_CASE_REPLICATION_PROTOCOL.md)
- [Complete cross-case analysis](experiments/evoq_mis_full_qoblib/results/cross_case_replication/analysis.json)
- [Publication figure](experiments/evoq_mis_full_qoblib/results/figures/cross_case_replication.pdf)
- [Detailed reproduction guide](REPRODUCIBILITY.md)

## Repository map

```text
experiments/evoq_mis_full_qoblib/
  run_cross_case_replication.py   export, self-tests, Aer/cuTN execution, analysis
  plot_cross_case_replication.py  paper statistics and final figure
  results/cross_case_replication/ 300 rows, 100 cohorts, hashes and summaries
  paper/                          LaTeX manuscript, supplement and stable PDFs
  test_*.py                       29 integrity/numerical tests
  *_PROTOCOL.md                   frozen decisions before target execution
  artifact_manifest.json         SHA-256 inventory of public artifacts
docs/QUANTUM_EVOLUTION_RESEARCH_MAP.md
prior_work/evolutionary_computing_portfolio/
QOBLIB, metriq-gym, baselines/    pinned upstream Git submodules
```

## Quick verification

```bash
git clone --recurse-submodules https://github.com/YaroslavPelekhov/Quantum.git
cd Quantum
python -m venv .venv
# Windows: .venv\Scripts\python -m pip install -r requirements.txt
# Linux:   .venv/bin/python -m pip install -r requirements.txt
cd experiments/evoq_mis_full_qoblib
python -m unittest discover -v -p "test_*.py"
python run_cross_case_replication.py analyze
python plot_cross_case_replication.py
```

The completed JSON checkpoints allow the final analysis and paper figure to be
regenerated without rerunning expensive backend simulations. Full Windows/WSL
commands and safety assumptions are in [REPRODUCIBILITY.md](REPRODUCIBILITY.md).

## Large exact states

Six dense 24-qubit reference states are 256 MiB each and exceed GitHub's normal
100 MB object limit. They are intentionally omitted from ordinary Git history.
Their filenames, byte sizes, and SHA-256 identities remain recorded in
`results/mps_ladder/exact_references.json` and the export manifests. Publish
them through Git LFS or a versioned release/archive when independent
state-by-state recomputation is required. The paper, compact results, circuits,
metrics, and certificate analysis are reviewable without them.

## Reproducibility status

- 300/300 dense backend rows complete.
- 29/29 integrity and numerical tests pass in the archived environment.
- Both backend axis-convention self-tests pass at near-machine precision.
- All long jobs use atomic checkpoints and hash-bound frozen manifests.
- Manuscript and supplement were rendered and visually checked page by page.
- Raw counts, errors, runtimes, software versions, and failed attempts are
  retained rather than silently removed.

## Scope and limitations

This is an exact-calibrated noiseless simulator study, not quantum hardware
evidence. The 55-qubit target remains approximate. The five-case replication
uses one MIS reduction family, three frozen schedules, two simulator
implementations, and one GPU platform. Setting cohorts share circuits and are
not independent population samples, so the Fisher test is descriptive. The TVD
certificate is sufficient rather than necessary and currently requires an
exact reference distribution.

## Citation

Citation metadata are provided in [CITATION.cff](CITATION.cff). Author,
affiliation, venue, and DOI fields can be updated before submission without
changing the frozen experimental artifacts.
