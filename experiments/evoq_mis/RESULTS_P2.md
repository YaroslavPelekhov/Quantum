# Depth-2 QAOA with replicated evolution and Pareto audit

Run date: 2026-08-02. These are local Qiskit Aer results, not QPU measurements.

## Protocol

- QOBLIB train instance: `mammalia-kangaroo-interactions`, 17 vertices, 91 edges, exact MIS optimum 4.
- Frozen held-out instance: `farm`, 17 vertices, 39 edges, exact MIS optimum 10.
- Depth-two QAOA with five evolved parameters: one QUBO penalty, two mixer angles and two cost angles.
- 12 independent paired replicates.
- Exactly 300 statevector evaluations per method and replicate: 3,600 for differential evolution and 3,600 for random search.
- 7,135 unique genomes and a three-objective Pareto front over raw feasibility, optimum probability and unconditional expected feasible ratio.
- Eight ideal 4,096-shot trials and four noisy 256-shot trials for selected representatives.
- Deterministic repair is excluded from search fitness.

## Search result

| Method | Mean best score | Std. dev. | Median | Best | Paired wins |
|---|---:|---:|---:|---:|---:|
| Differential evolution | **0.3198** | 0.0419 | **0.3414** | 0.3708 | **10/12** |
| Equal-budget random | 0.2742 | 0.0564 | 0.2701 | **0.3881** | 2/12 |

The evolutionary method is much more consistent, while random search still produced the best single outlier. The paired mean difference was `+0.04557` for evolution. The one-sided Wilcoxon test gave `p=0.0212`, but the two-sided paired t-test gave `p=0.0714` and the bootstrap 95% interval `[-0.00019, 0.08629]` still touches zero. This is encouraging evidence, not a definitive result.

Across each method's 300 evaluated points per replicate, evolution also won:

- optimum-probability maximum: 9 of 12 pairs, mean 0.04370 versus 0.03346;
- feasible-probability maximum: 8 of 12, mean 0.7599 versus 0.6238;
- expected-feasible-ratio maximum: 7 of 12, mean 0.2541 versus 0.2185.

## Pareto result

The non-dominated front contains 16 genomes. No single genome maximizes all desired properties.

- Best evolutionary composite genome: raw optimum probability 2.83%, feasibility 57.64%, expected-feasible ratio 30.61%.
- Best observed optimum probability: 7.06%; this genome came from random search and has expected-feasible ratio 22.99%.
- Best expected-feasible ratio: 31.36%; also a random-search outlier, with optimum probability only 0.58%.

This validates the portfolio's multi-objective/archive framing: reducing the experiment to one scalar hides materially different quantum distributions.

## Finite-shot and noise check

For the best evolutionary composite genome:

- ideal raw optimum rate: 2.82%;
- noisy raw optimum rate: 2.25%;
- ideal repaired optimum rate: 94.48%;
- noisy repaired optimum rate: 92.09%.

The compiled depth-two circuit has depth 49 and 284 operations, including 182 `RZZ` gates. The generic noise model uses depolarizing probabilities 0.001 for one-qubit gates and 0.01 for `RZZ`; it is a stress test, not hardware calibration.

## Frozen held-out audit

All 12 schedules were selected on the train graph and then frozen before exact evaluation on `farm`.

| Method | Mean held-out score | Std. dev. | Median | Paired wins |
|---|---:|---:|---:|---:|
| Differential evolution | **0.1517** | 0.0817 | **0.1718** | **7/12** |
| Equal-budget random | 0.1226 | 0.0768 | 0.1374 | 5/12 |

The mean difference is positive (`+0.02903`) but not robust: bootstrap 95% interval `[-0.03548, 0.09329]`, paired t-test `p=0.415`, one-sided Wilcoxon `p=0.190`.

## Decision

The depth-two experiment is clearly stronger than the first depth-one pilot, but the promotion gate remains **closed** because train uncertainty barely includes zero and transfer uncertainty is large. This prevents selecting a flattering single seed or relying on repair-dominated success.

The best next experiment is graph-scale-normalized QAOA or multi-instance training, keeping `farm` frozen as the test language. Hardware execution should wait until that transfer gate passes.

## Artifacts

- `results_p2_pareto/results.json`: all configuration, replicates, Pareto genomes and finite-shot results.
- `results_p2_pareto/transfer_audit.json`: paired statistics and frozen held-out proof.
- `results_p2_pareto/all_evaluations.csv`: all 7,200 evaluated points.
- `results_p2_pareto/pareto_front.csv`: 16 non-dominated genomes.
- `results_p2_pareto/paired_scores.png`, `pareto_landscape.png`, `held_out_paired_scores.png`: verified plots.
