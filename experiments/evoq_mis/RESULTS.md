# First real quantum-evolution experiments: results

Run date: 2026-08-02. All runs used Qiskit Aer locally; no QPU credentials or hardware results are implied.

## What was run

- QOBLIB train graph: `mammalia-kangaroo-interactions`, 17 vertices and 91 edges.
- Independent held-out QOBLIB graph: `farm`, 17 vertices and 39 edges.
- Exact exhaustive verification found optimum sizes 4 and 10 respectively.
- Depth-one QAOA genome: QUBO penalty `lambda`, mixer angle `beta`, cost angle `gamma`.
- 12 paired searches: differential evolution versus random search, each with exactly 60 statevector evaluations per replicate.
- The champions were tested with eight ideal samples of 4,096 shots and four noisy samples of 256 shots.
- Noise stress test: depolarizing probability 0.001 on one-qubit gates and 0.01 on `RZZ`; this is not a device calibration.

Search fitness used the raw quantum distribution only:

`E[feasible size] / exact optimum + 0.25 P(optimum) + 0.10 P(feasible)`.

Classical repair was evaluated after sampling but was not allowed to influence parameter search.

## Main result

| Search method | Mean score over 12 | Std. dev. | Median | Best |
|---|---:|---:|---:|---:|
| Differential evolution | 0.1812 | 0.1089 | 0.1539 | **0.3618** |
| Equal-budget random | **0.1907** | 0.0953 | **0.2121** | 0.3015 |

Paired wins were 6–6. Therefore this experiment does **not** establish an evolutionary-search advantage at the current budget and depth.

The best evolutionary genome was:

- `lambda = 1.05`
- `beta = 2.5323777168`
- `gamma = 6.1566128119`

On the train graph its exact raw distribution had feasibility probability 0.7123, optimum probability 0.01267, and unconditional expected feasible size 1.1498. The best random-search genome had lower feasibility (0.3983) but higher optimum probability (0.04919), exposing an important multi-objective trade-off hidden by any single scalar score.

## Held-out transfer

On `farm`, without retraining, the evolutionary champion scored 0.1891 versus 0.04784 for the random champion and 0.01074 for the fixed schedule. However, its exact probability of sampling the optimum was only 0.0000171. The transfer result is promising for feasible mass, not for optimum success probability.

## Finite shots and repair

| Champion | Ideal raw optimum | Ideal repaired optimum | Noisy raw optimum | Noisy repaired optimum |
|---|---:|---:|---:|---:|
| Differential evolution | 1.21% | 82.32% | 0.68% | 82.71% |
| Random search | **5.09%** | 86.14% | **1.95%** | 87.70% |
| Fixed schedule | 0.06% | **94.52%** | 0.10% | **94.14%** |

The fixed schedule is poor in the raw quantum distribution but excellent after deterministic repair. This is evidence that repair dominates this small dense instance; repaired success alone must not be presented as quantum or evolutionary improvement.

The best repaired independent set was vertices `[2, 6, 7, 8]`, size 4. It is exactly feasible under exhaustive verification and matches the known QOBLIB solution pattern included with the benchmark.

## Promotion decision

Promotion to a larger instance or QPU is **rejected for this version**. The exact optimum, raw feasibility, and held-out-versus-fixed checks pass, but both robustness checks fail:

- evolutionary mean does not beat equal-budget random search;
- evolutionary search does not win a strict majority of paired runs.

The next scientifically useful iteration is a constraint-preserving MIS mixer or a multi-objective archive over feasibility and optimum probability, followed by depth `p=2` with a larger evaluation budget. A repair-only classical baseline should remain explicit.

## Artifacts

- `results/results.json`: full configuration, all replicate scores, exact metrics, shot trials, circuit statistics, and promotion proof.
- `results/search_history.csv`: evaluation history for the representative paired replicate.
- `results/search_convergence.png`: convergence plot for that representative replicate.
- `results/best_solution.txt`: QOBLIB-compatible binary decision vector.
