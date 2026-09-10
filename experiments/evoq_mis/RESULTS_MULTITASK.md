# Graph-normalized multi-instance QAOA

Run date: 2026-08-02. This is a local Qiskit Aer simulator experiment, not a QPU result.

## Pre-fixed protocol

The protocol was fixed before optimizing or evaluating the new test suite.

- Train family: full QOBLIB `mammalia-kangaroo-interactions` plus deterministic induced subgraphs with 11, 13 and 15 vertices.
- Validation: full QOBLIB `farm`; previously observed, so it is not called a test set.
- New frozen test: the first 17 vertices of QOBLIB `karate`, `chesapeake` and `aves-sparrow-social`.
- The frozen graphs have 30, 26 and 108 edges and exact MIS optima 10, 9 and 3, providing sparse and dense cases.
- Shared depth-two QAOA genome: one penalty, two mixer angles and two cost angles.
- Multi-task fitness: `0.7 * mean(task scores) + 0.3 * minimum(task score)`.
- Hamiltonian normalization: divide every Ising `h` and `J` coefficient by `max(max_i |h_i|, |J|)` separately for each graph.
- Twelve paired replicates and exactly 300 genome evaluations per method per replicate.
- Compared methods: normalized multi-task differential evolution, unnormalized multi-task differential evolution and normalized multi-task random search.
- Approximate work: 43,200 train statevector circuit executions, followed by exact transfer and finite-shot/noise checks.

## Main result: normalization works

| Stage | Normalized DE | Unnormalized DE | Difference | Wins | Bootstrap 95% CI | Paired t-test |
|---|---:|---:|---:|---:|---:|---:|
| Train family | 0.3884 | 0.2985 | **+0.0899** | 10–2 | [0.0481, 0.1334] | p=0.00230 |
| Validation `farm` | 0.2648 | 0.1944 | **+0.0703** | 10–2 | [0.0299, 0.1154] | p=0.01055 |
| New frozen test | 0.2509 | 0.1676 | **+0.0833** | **11–1** | **[0.0465, 0.1247]** | **p=0.00218** |

The normalization effect is positive on train, validation and the previously unseen QOBLIB-derived test suite. Both the bootstrap interval and paired tests remain clear on the new test.

Per frozen graph, normalized versus unnormalized DE mean scores were:

| Frozen graph | Normalized DE | Unnormalized DE |
|---|---:|---:|
| `karate_first17` | 0.2447 | 0.2006 |
| `chesapeake_first17` | 0.2645 | 0.1692 |
| `aves-sparrow-social_first17` | 0.2891 | 0.1768 |

Thus the aggregate result is not caused by one test graph.

## Evolution effect

Against normalized random search, normalized DE was clearly stronger on the train family:

- mean 0.3884 versus 0.3235;
- 10–2 paired wins;
- bootstrap interval for the difference `[0.0146, 0.1071]`;
- paired t-test `p=0.0242` and one-sided Wilcoxon `p=0.0212`.

Generalization evidence is weaker:

- validation: 0.2648 versus 0.2337, wins 6–6;
- frozen test: 0.2509 versus 0.2328, wins 7–5;
- frozen-test difference interval `[-0.0252, 0.0607]`, paired t-test `p=0.452`.

The defensible claim is therefore that graph-scale normalization is robustly useful. Evolution improves training consistently but has not yet shown a statistically clear test advantage over an equal-budget normalized random search.

## Champion and finite shots

The train-selected normalized-DE champion came from replicate 9:

- penalty: `1.9690861817`;
- mixer angles: `2.4291695720`, `3.0458159206`;
- cost angles: `0.6599543218`, `6.2831853072`;
- train aggregate: 0.5108;
- validation: 0.3272;
- frozen-test aggregate: 0.3170.

On the original `mammalia` graph, its ideal raw optimum rate was 4.08% and noisy raw optimum rate 1.76%. Raw feasibility fell from 80.23% ideal to 31.05% under the generic noise stress test. Repair recovered optimum solutions frequently, but repair metrics are not used to claim quantum quality.

On sparse transfer graphs, the raw optimum probability remains low: approximately 0.06% on `farm`, 0.11% on `karate_first17` and 0.40% on `chesapeake_first17` in ideal shots. This is the principal limitation before hardware execution.

## Promotion decision

The pre-registered promotion gate **passes**: all five mean and majority checks are true. This authorizes the next simulator stage—larger 20–24-qubit induced graphs and hardware-aware topology/noise models. It does not establish quantum advantage and does not yet justify spending QPU time without an additional raw optimum-probability threshold.

## Artifacts

- `results_multitask_normalized/results.json`: full protocol, every replicate, comparisons, exact metrics and shot trials.
- `results_multitask_normalized/replicate_summary.csv`: compact paired results.
- `results_multitask_normalized/train_paired.png`: train comparison.
- `results_multitask_normalized/validation_paired.png`: validation comparison.
- `results_multitask_normalized/frozen_test_paired.png`: frozen-test comparison.
- `results_multitask_normalized/best_solution.txt`: exact feasible QOBLIB solution `[2, 6, 7, 8]`.
