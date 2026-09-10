# EvoQ-MIS: graph-normalized evolutionary QAOA transfer

This experiment applies the portfolio's core idea—executable evolutionary search with an exact verifier and held-out promotion—to a real QOBLIB maximum-independent-set instance.

## Protocol

- Train instance: `mammalia-kangaroo-interactions` (17 vertices, 91 edges).
- Held-out transfer instance: `farm` (17 vertices, 39 edges).
- Quantum model: depth-one QAOA by default, simulated with Qiskit Aer.
- Genome: QUBO penalty, mixer angle(s), and cost angle(s).
- Search: 12 independent fixed-budget differential-evolution runs.
- Baselines: 12 paired equal-budget random-search runs and a fixed schedule.
- Verification: exhaustive enumeration of all 131,072 bit strings per graph.
- Robustness: eight ideal 4,096-shot samples and four 256-shot samples with a generic depolarizing-noise stress test. Noisy statevector trajectories are deliberately smaller because they are much more CPU-intensive.
- Post-processing: deterministic conflict removal and greedy augmentation; never used by the search objective.

The scalar training score is fully reported and intentionally keeps raw quantum feasibility separate from repaired solution quality:

`E[feasible size] / optimum + 0.25 P(optimum) + 0.10 P(feasible)`.

## Run

From the workspace root:

```powershell
& .\.venv\Scripts\python.exe .\experiments\evoq_mis\run_experiment.py
```

Outputs are written to `experiments/evoq_mis/results/` as JSON, CSV, PNG, and a QOBLIB-checkable solution file.

## Depth-2 replicated Pareto experiment

The stronger follow-up uses 12 paired replicates, 300 exact evaluations per method and a Pareto audit of all raw quantum objectives:

```powershell
& .\.venv\Scripts\python.exe .\experiments\evoq_mis\run_p2_pareto.py
& .\.venv\Scripts\python.exe .\experiments\evoq_mis\evaluate_p2_transfer.py
```

Its artifacts are kept separately in `experiments/evoq_mis/results_p2_pareto/`.

## Graph-normalized multi-instance experiment

The promoted follow-up trains one shared schedule across four QOBLIB-derived graphs and compares normalized DE, unnormalized DE and normalized random search:

```powershell
& .\.venv\Scripts\python.exe .\experiments\evoq_mis\run_multitask_normalized.py
```

Its artifacts are in `experiments/evoq_mis/results_multitask_normalized/`.

## Complete research cycle

The full exploratory, ablation, scale-up, hardware-aware, confirmatory, random-subgraph, classical-sanity and Metriq-Gym cycle is summarized in `RESEARCH_CYCLE_REPORT.md`. To reproduce every stage:

```powershell
& .\experiments\evoq_mis\run_research_cycle.ps1
```

This is intentionally compute-intensive. The final primary confirmatory result is in `results_confirmatory/results.json`; the independently predeclared vertex-order robustness test is in `results_random_subsets/results.json`.

## Main manuscript

The submission-ready, venue-neutral manuscript package is in `paper/`:

- `paper/main.tex` and `paper/references.bib`;
- four regenerated publication figures and machine-readable CSV tables;
- `paper/output/pdf/gsn_qaoa_mis_manuscript.pdf`, a visually verified seven-page two-column manuscript including the appendix.

The title, abstract and claims center on the result that survives every frozen test: maximum-coefficient normalization improves zero-shot transfer. Evolutionary superiority, quantum advantage and QPU readiness are explicitly not claimed.
