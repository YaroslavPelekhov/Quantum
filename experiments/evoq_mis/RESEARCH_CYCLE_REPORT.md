# Graph-Scale Normalization for Transferable Evolutionary QAOA Policies

Research cycle completed: 2026-08-03.

## Executive finding

The strongest supported result is a simple graph-wise normalization of the MIS Ising Hamiltonian. Before every QAOA circuit is built, all local and pair coefficients are divided by

`s(G, lambda) = max(max_i |h_i|, |J|)`.

A single depth-two schedule evolved on 11–17-qubit QOBLIB-derived training graphs then transfers more reliably across graph densities and sizes than the identical evolutionary protocol without normalization.

The result survived a pre-declared confirmatory evaluation on three previously unused QOBLIB-derived graphs with 20, 22 and 24 qubits:

- normalized DE mean score: `0.20230`;
- unnormalized DE mean score: `0.13322`;
- paired difference: `+0.06908`;
- paired wins: `10–2`;
- bootstrap 95% CI: `[0.03443, 0.10552]`;
- paired t-test: `p=0.00374`;
- one-sided Wilcoxon: `p=0.00122`.

All pre-declared primary checks passed.

## Research question

Can a low-data, encoder-free transformation make shallow QAOA schedules transferable across MIS graph families and sizes, while retaining an auditable evolutionary workflow and avoiding target-graph optimization?

This is deliberately narrower than general QAOA parameter transfer. Learned GAT and graph-conditioned meta-optimizer approaches already exist. The candidate contribution is an inexpensive coefficient normalization combined with paired evolutionary evaluation, exact proof objects and frozen-graph promotion gates.

## Method

For the MIS QUBO

`C(x) = -sum_i x_i + lambda sum_(i,j) x_i x_j`,

the Ising coefficients are

`h_i = 1/2 - lambda deg(i)/4`, `J_ij = lambda/4`.

The normalized circuit uses `h_i/s` and `J_ij/s`, where `s=max(max_i |h_i|, |J|)`. This preserves the eigenstate ordering within an instance while making the phase scale less dependent on graph degree.

The shared genome contains five values: QUBO penalty, two mixer angles and two cost angles. Differential evolution and random search receive identical exact-statevector budgets. Search fitness excludes classical repair:

`E[feasible size]/optimum + 0.25 P(optimum) + 0.10 P(feasible)`.

The multi-task training aggregate is `0.7 mean + 0.3 minimum`, although the objective ablation shows that this robust weighting is not independently established as beneficial.

## Experiment ladder

### 1. Depth-one pilot

Twelve paired 60-evaluation searches on the 17-vertex `mammalia-kangaroo-interactions` graph produced a 6–6 tie. Evolution did not beat equal-budget random search on average. The gate remained closed.

### 2. Depth-two Pareto audit

Twelve paired 300-evaluation searches yielded 7,200 evaluated genomes and a 16-point Pareto front. Differential evolution won 10 of 12 training pairs, but the frozen transfer advantage was uncertain. This established the feasibility/optimum-probability trade-off and motivated graph-scale normalization.

### 3. Normalized multi-instance training

The protocol used four training graphs, `farm` as validation and three new 17-vertex frozen graphs. Normalized DE versus unnormalized DE:

| Stage | Normalized | Unnormalized | Difference | Wins | Bootstrap CI | t-test |
|---|---:|---:|---:|---:|---:|---:|
| Train | 0.3884 | 0.2985 | +0.0899 | 10–2 | [0.0481, 0.1334] | 0.00230 |
| Validation | 0.2648 | 0.1944 | +0.0703 | 10–2 | [0.0299, 0.1154] | 0.01055 |
| Frozen 17-qubit test | 0.2509 | 0.1676 | +0.0833 | 11–1 | [0.0465, 0.1247] | 0.00218 |

### 4. Zero-shot scale-up

The same schedules were transferred without optimization to `ibm32:first20`, `football:first22` and `johnson8-2-4:first24`.

Normalized versus unnormalized DE aggregate difference was `+0.05989`, with 10–2 wins, bootstrap CI `[0.02540, 0.09865]` and paired `p=0.01015`.

Raw optimum probability nevertheless became very small at scale. Mean normalized-DE optimum probabilities were approximately `0.035%`, `0.021%` and `0.0012%` on the 20/22/24-qubit graphs. The contribution improves the distribution but does not solve optimum concentration.

### 5. Pre-declared confirmatory suite

The final graphs were declared in `NOVELTY_AUDIT.md` before evaluation:

- `insecta-ant-colony1-day38:first20`, 142 edges, optimum 5;
- `sloane_1dc_64:first22`, 109 edges, optimum 5;
- `hamming6-4:first24`, 48 edges, optimum 10.

The primary normalization endpoint passed with `p=0.00374`. The secondary normalized-DE versus normalized-random comparison was positive (`+0.03932`, wins 8–4, positive bootstrap CI) but did not cross a two-sided 0.05 t-test threshold (`p=0.0614`). Evolutionary superiority should therefore be described as suggestive, not confirmed.

## Ablations and negative results

### Robust objective weighting

The `0.7 mean + 0.3 minimum` objective did not significantly beat mean-only or single-instance training on frozen 17-qubit graphs. The normalization result cannot be attributed to this weighting, and robust aggregation should not be advertised as independently validated.

### Feasibility-preserving mixer

A guarded vertex-flip mixer achieved feasible probability exactly one and superficially excellent scores. Inspection showed that evolution drove the rotations to `beta≈pi/2` or `pi`; the state became a deterministic degree-ordered greedy independent set. One schedule produced the optimum with probability one on the small suite, but this was classical greedy behavior embedded in a unitary circuit. Its evolutionary transfer comparison failed, and the branch was not promoted.

This is an important control: feasibility alone can make a quantum distribution look dramatically better while hiding a classical deterministic algorithm.

### Classical repair

Repair frequently raised optimum rates above 80–95%, even for poor raw schedules. All principal claims therefore use raw distributions. Repaired success is reported only as operational post-processing.

## Hardware-aware audit

After decomposition to `rz/sx/x/cx`, deterministic routing produced the following CX counts:

| Graph | Unconstrained | Line | 5×5 grid | 30-qubit hex lattice |
|---|---:|---:|---:|---:|
| 20 qubits | 172 | 1,822 | 613 | 787 |
| 22 qubits | 208 | 2,842 | 892 | 1,114 |
| 24 qubits, dense | 600 | 10,836 | 2,943 | 3,657 |

At independent error proxies of 0.1% per one-qubit operation, 1% per CX and 2% per measurement, the 24-qubit grid no-error survival proxy is `4.54e-14`. Hardware-routed noisy MPS was attempted with both 128 and 16 shots but failed to complete the first 20-qubit case within a practical CPU budget. No noisy sample results were fabricated.

The result is simulator-interesting but not QPU-ready with this dense RZZ construction. Topology-aware problem embedding, sparse/decomposed formulations or a different mixer is necessary.

## Metriq-Gym cross-check

The repository's actual `metriq_gym.circuits.qaoa_circuit` generator was run locally for its weighted 10-qubit 1D LR-QAOA benchmark. With 4,096 Aer shots:

| Layers | Approximation ratio | Optimum probability | Two-qubit gates |
|---:|---:|---:|---:|
| 3 | 0.6735 | 0.93% | 27 |
| 5 | 0.7054 | 1.20% | 45 |
| 7 | 0.7262 | 1.73% | 63 |
| 10 | 0.7523 | 2.51% | 90 |

The exact uniform-random approximation ratio is 0.5. This confirms the local benchmark stack independently of the custom MIS implementation.

## Novelty assessment

The evidence supports a **promising empirical contribution**:

> Max-coefficient normalization is a simple, encoder-free method for improving zero-shot transfer of shared depth-two MIS QAOA schedules across QOBLIB-derived graph families, densities and sizes.

It is potentially suitable for a workshop paper or a focused benchmarking/short paper after comparison with learned transfer baselines. It is not yet defensible to claim:

- a first-ever normalization method;
- quantum advantage;
- superiority to classical MIS solvers;
- superiority to GAT or graph-conditioned QAOA meta-optimizers;
- QPU readiness.

## Main-manuscript completion cycle

A further predeclared robustness suite fixed six random induced subgraphs before evaluation: two 20-vertex subsets of sparse `es60fst01`, two 22-vertex subsets of `aves-sparrow-social`, and two 24-vertex subsets of dense `MANN-a9`. This removes reliance on the earlier `first-k` convention.

Normalized versus unnormalized DE improved the six-graph aggregate score by `+0.10807`, with 10-2 paired wins, bootstrap CI `[0.05787, 0.16027]`, paired `p=0.00231`, and one-sided Wilcoxon `p=0.00122`. The raw unconditional approximation-ratio improvement was `+0.08877` (`p=0.00238`), and feasible probability improved by `+0.16485` (`p=0.02127`). The robustness gate passed all four predeclared checks.

The equal-budget normalized DE versus normalized random comparison remained non-significant (`+0.04080`, `p=0.358`). This reinforces the manuscript's narrow claim: graph-scale normalization is supported; evolutionary superiority is not.

A classical sanity audit covered 12 scale-up, confirmatory and random-subset graphs. Minimum-degree greedy was exactly optimal on 8/12 and averaged ratio 0.899; the best of 1,000 random-order greedy restarts was optimal on 12/12. The manuscript therefore explicitly rules out quantum advantage and competitive MIS-solver claims.

The released GAT transfer repository was audited at commit `ab8434ffcb2cfcac16d136d8677f327752d9ca8d`. It contains a checkpoint, but its checked-in evaluation requires absent parameter-output directories and missing large-graph embeddings at declared paths and uses a different ER/target-embedding protocol. `EXTERNAL_BASELINE_AUDIT.md` records the exact incompatibilities; no invented GAT score is reported.

The completed venue-neutral manuscript is `paper/main.tex`; the compiled and visually inspected PDF is `paper/output/pdf/gsn_qaoa_mis_manuscript.pdf`. It contains four figures, three tables, a raw-metric appendix, related work, statistical protocol, hardware audit, external-baseline audit, limitations and reproducibility statement.

## Remaining work before an actual submission

1. Replace anonymous author placeholders with names, affiliations, funding and contribution statements.
2. Select a target venue and adapt its class file, page limits and data-availability policy.
3. If the venue expects hardware evidence, obtain access to a named calibrated backend and predeclare the execution/noise-mitigation protocol.
4. If a learned-baseline comparison is mandatory, obtain a runnable reference environment or missing artifacts from the baseline authors and standardize the Hamiltonian/depth/adaptation budget.
5. Create an external timestamp or public repository release for the artifact and preregistration record.

## Reproducibility

Environment: Python 3.13, Qiskit 2.5.1, Qiskit Aer 0.17.2, NumPy 2.5.1, SciPy 1.18.0.

Run the complete local pipeline from the workspace root with:

```powershell
& .\experiments\evoq_mis\run_research_cycle.ps1
```

The launcher is intentionally expensive and may take tens of minutes. Result directories are separate so exploratory, ablation and confirmatory artifacts are not overwritten across stages.
