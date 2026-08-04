# Quantum × Evolutionary Computation: research map

Snapshot date: 2026-08-02

## Bottom line

The most defensible intersection is **classical evolutionary search used to design, tune, or compile a genuinely quantum computation**, followed by evaluation on a simulator and a real QPU. The weakest line is a “quantum-inspired evolutionary algorithm” that only runs classically and merely borrows qubit vocabulary.

The best project starting from the two suggested resources is:

> **Evolve transferable, hardware-aware QAOA schedules or circuit structures on QOBLIB instances, and package the evaluation as a Metriq-Gym benchmark.**

This connects a real optimization corpus (QOBLIB), a cross-provider execution layer (Metriq-Gym), and evolutionary computation where it has a clear reason to exist: mixed discrete/continuous, noisy, non-differentiable, multi-objective search.

## 1. Terminology: four different research programs

| Program | Where evolution runs | Where quantum enters | Assessment |
|---|---|---|---|
| Evolutionary quantum design | Classical CPU/GPU | The evolved object is a quantum circuit, ansatz, code, layout, pulse, or compiler policy | Strongest and easiest to evaluate honestly |
| Hybrid evolutionary–quantum optimization | Classical population loop | A QPU evaluates fitness or samples candidate solutions | Promising, but QPU-call cost and latency must be counted |
| Quantum-assisted evolutionary operators | Part of selection/mutation/crossover runs on a QPU | Claimed acceleration of the evolutionary loop itself | Early-stage; comparisons must include state preparation, shots, and I/O |
| Quantum-inspired EA | Entirely classical | Amplitudes/rotation gates are metaphors or probability representations | Valid classical optimization, but not evidence of quantum advantage |

The first two categories should be the main focus. They support falsifiable questions and fit existing benchmark infrastructure.

## 2. What the two starting points actually provide

### Metriq-Gym

Metriq is a community platform maintained by Unitary Foundation. `metriq-gym` is its Python runner: benchmark configurations are JSON-schema controlled, jobs can be sent through multiple provider integrations, and outputs share a standard result structure.

Current benchmark families in the checked-out repository:

- system/circuit performance: Mirror Circuits, EPLG, BSEQ, CLOPS;
- application-inspired: WIT, LR-QAOA, QML Kernel, QAT-OLE;
- QED-C algorithms: Bernstein–Vazirani, phase estimation, hidden shift, QFT.

The most relevant existing component is **LR-QAOA**. It benchmarks weighted Max-Cut using a fixed linear-ramp schedule and reports approximation ratio and probability of sampling an optimum. Its schema already exposes graph type, qubit count, QAOA depth, the two ramp slopes, shots, trials, and seed.

Important limitation: Metriq-Gym currently evaluates a fixed benchmark protocol. It is not itself an optimizer or a corpus of difficult real-world instances. An evolutionary contribution should therefore be a new benchmark protocol or a controlled variant of LR-QAOA, not an untracked search wrapper around arbitrary QPU calls.

Local source: [`metriq-gym`](./metriq-gym), commit `21a3d7f` (2026-07-30).

### QOBLIB

QOBLIB is the “Intractable Decathlon”: ten difficult optimization classes, instances, model formulations, known/best solutions, feasibility checkers, and standardized submission records.

| # | Class | Natural evolutionary angle | Quantum readiness |
|---:|---|---|---|
| 1 | Market Split | multiobjective/constraint handling, repair, hybrid local search | QUBO exists; quantum/annealing-related baselines exist |
| 2 | LABS | bit-string EA, linkage learning, QAOA/HUBO schedule search | Excellent small-QPU entry point; AQT QAOA baseline exists |
| 3 | Minimum Birkhoff Decomposition | variable-length genomes, memetic search | Quantum baseline exists; encoding growth is a challenge |
| 4 | Steiner Tree Packing | graph genotype, decomposition, coevolution | No submission yet; instances can be very large |
| 5 | Sports Scheduling | constraint-preserving variation, repair | Only one classical submission; quantum encoding is difficult |
| 6 | Portfolio Optimization | multiobjective/risk-aware evolution | QUBO exists but is dense and coefficient ranges are severe |
| 7 | Maximum Independent Set | graph-aware variation, evolutionary QAOA | Best-supported gate-model target; several QAOA baselines |
| 8 | Network Design | decomposition/cooperative coevolution | Sparse MIP becomes a much larger QUBO |
| 9 | Vehicle Routing | mature memetic baselines, hybrid subproblem solving | A recent classical memetic-GA submission already exists |
| 10 | Topology Design | novelty search / quality diversity over graphs | Natural evolutionary representation; no quantum submission found |

Current local submission-directory snapshot:

| Problem | Submission groups | Notable gap or baseline |
|---|---:|---|
| Market Split | 6 | classical and annealing-style baselines |
| LABS | 7 | AQT hardware QAOA for N = 6, 8, 10, 12 |
| Birkhoff | 5 | quantum black-box baseline |
| Steiner | 0 | completely open, but high implementation risk |
| Sports | 1 | almost empty benchmark field |
| Portfolio | 3 | no obvious evolutionary/quantum submission |
| Independent Set | 12 | richest quantum baseline set: simulator and hardware QAOA among others |
| Network | 1 | almost empty |
| Routing | 1 | classical graph-based memetic GA, 56 instance records |
| Topology | 3 | classical mathematical-programming baselines |

The LABS AQT baseline is particularly useful: depth-one QAOA, 200 shots, with parameters found by SciPy differential evolution. This is already an explicit evolutionary foothold, but only for two continuous parameters and without a systematic EA-vs-optimizer or transfer study.

Local source: [`QOBLIB`](./QOBLIB), commit `5240786` (2026-07-31).

## 3. Research themes worth pursuing

### A. Evolutionary quantum architecture search

Genome: gate types, targets, connectivity, parameter sharing, depth, or higher-level circuit modules. Fitness: task loss plus resource and noise penalties.

Why evolution fits: the search space mixes categorical structure, variable length, continuous angles, hard hardware constraints, and non-differentiable sampled objectives.

Open questions:

- Do evolved circuits transfer to larger instances rather than merely memorize a small unitary?
- Can grammar/DSL representations enforce scalable, interpretable structure?
- Does multiobjective evolution reveal a useful Pareto front between solution quality, two-qubit gates, depth, and QPU cost?
- How much benefit survives transpilation and real-device noise?

Evidence: automated evolutionary design has rediscovered QFT, Deutsch–Jozsa, and Grover using a scalable DSL; recent EXAQC work jointly searches topology and parameters; quality-diversity methods have been applied to variational circuits.

### B. Evolutionary parameter schedules for QAOA/VQAs

Genome: `(beta, gamma)` vectors, spline/control points, Fourier coefficients, parameter-sharing rules, or schedule generators. A genotype can describe parameters for all depths and instance sizes rather than optimizing every instance independently.

This is the quickest route to a strong experiment because it can reuse Metriq’s LR-QAOA implementation and QOBLIB’s known objectives.

The scientifically interesting version is **transfer/meta-optimization**:

- train schedules on a subset of graphs or sequence lengths;
- freeze them;
- evaluate on unseen instances, larger sizes, and different QPUs;
- compare under an equal number of circuit evaluations.

A per-instance GA that simply spends more evaluations than COBYLA/SPSA is not a compelling result.

### C. Hardware-aware circuit and compiler co-design

Genome: logical circuit, initial layout, routing choices, gate decompositions, dynamical-decoupling choices, or pruning thresholds.

Objectives:

1. task score or fidelity;
2. two-qubit gate count/depth;
3. estimated and measured error;
4. wall-clock and QPU time;
5. monetary cost where available.

Metriq’s cross-provider abstraction makes this unusually attractive. The main test should be whether a circuit evolved on one calibration snapshot or provider remains good on a later snapshot or another provider.

### D. Quality diversity rather than one “best” circuit

MAP-Elites or another QD algorithm can build an archive indexed by descriptors such as depth, entangling-gate count, connectivity demand, expressibility, robustness, or provider.

Why it matters: QPU calibration drifts, so an archive of diverse high-quality circuits may be more useful than one fragile optimum. At dispatch time, the system can select an elite that matches the current hardware constraints.

### E. Evolving benchmark instances

Instead of evolving a solver, evolve parameterized QOBLIB-like instances that maximize disagreement between solvers or hardware backends.

Possible objectives:

- maximize the performance gap between two algorithms under equal budgets;
- produce instances where solver ranking changes across devices;
- maximize sensitivity to noise, connectivity, or coefficient precision;
- retain application constraints and diversity through MAP-Elites.

This could expose benchmark blind spots, but it is a second project: synthetic hardness can overfit the compared solvers and lose practical relevance.

### F. Evolutionary quantum error-correction design

Evolve stabilizer/CSS codes, decoders, or code layouts for measured device-specific noise. A 2024 study found best-known-distance codes in 145 of 171 tested `[[n,k]]` combinations up to 20 physical qubits and reported a 3.9× lower undetectable-error rate for a tailored `[[12,1]]` code under one biased Pauli model.

Strong extension: replace the idealized independent Pauli model with a device-derived, possibly correlated error model and include decoder cost/connectivity as objectives. This is high-impact but less directly connected to QOBLIB.

### G. Quantum-assisted evolutionary operators

Examples include quantum sampling for population generation, Grover-like selection, quantum crossover, or quantum subproblem solvers inside a memetic algorithm.

Treat this as exploratory. Any speedup claim must count encoding/state preparation, shots, compilation, queue-free end-to-end runtime, and classical baselines. If only fitness evaluation is quantum, describe the method as a hybrid EA, not a “quantum genetic algorithm.”

## 4. Recommended project: EvoQBench

### Research question

Can multiobjective evolutionary search learn QAOA schedules or shallow ansatz structures that **transfer across unseen QOBLIB instances and across QPUs**, while outperforming fixed LR-QAOA and standard classical parameter optimizers under equal circuit-evaluation and runtime budgets?

### Why this is a good first project

- It has immediate simulator-only experiments and a clean path to hardware.
- QOBLIB supplies fixed instances, optima/best-known values, checkers, and reporting rules.
- Metriq-Gym supplies provider-neutral dispatch and standardized results.
- Evolution is justified by mixed structure/parameters and multiple objectives.
- Negative results remain publishable and useful if the protocol is rigorous.

### Initial task set

1. **LABS N = 6, 8, 10, 12** for direct comparison with the AQT depth-one baseline.
2. **QOBLIB MIS**, beginning with the two small social-network instances in the 2025 hardware QAOA submission, then the reduced `es60fst02` workflow used by the 2026 simulator/hardware submissions.
3. Keep Metriq weighted Max-Cut as an out-of-domain transfer test, not the sole training benchmark.

### Candidate genotype

Start simple:

- schedule representation: Fourier or spline coefficients generating all `beta_p, gamma_p`;
- optional per-layer mixer choice from a small valid library;
- optional edge coloring/order or parameter-sharing mask;
- depth `p` as an evolvable integer;
- deterministic repair to respect angle bounds and hardware constraints.

Do not begin with arbitrary gate-by-gate genetic programming. Its search space and evaluation cost will obscure the first result.

### Fitness and reporting

Use a Pareto formulation rather than a hidden weighted sum:

- maximize approximation ratio or best feasible objective;
- maximize optimum/near-optimum sampling probability;
- minimize QPU calls and total shots;
- minimize two-qubit depth after transpilation;
- minimize total wall-clock, CPU time, QPU time, and estimated cost;
- optionally maximize robustness over noise seeds/calibration snapshots.

Report the complete distribution across at least 20–30 independent optimizer seeds where simulation cost permits. QOBLIB requires at least five stochastic runs and recommends ten or more, but a research comparison normally needs stronger statistics.

### Baselines

- Metriq LR-QAOA fixed schedule;
- random search with the same evaluation budget;
- differential evolution, matching the LABS QOBLIB baseline;
- SPSA and one deterministic derivative-free method such as COBYLA;
- standard fixed-depth QAOA with per-instance optimization;
- a classical heuristic for solution-quality context, clearly separated from the quantum-circuit comparison.

### Experimental split

- training instances: small subset of LABS/MIS;
- validation instances: unseen instances of the same sizes;
- test instances: unseen larger sizes and one out-of-domain graph family;
- hardware test: frozen finalists only, on at least two providers or two calibration dates;
- ablations: no crossover, no diversity objective, parameters-only, architecture-only, no hardware penalty.

Never select the final circuit on the test QPU data; otherwise “hardware transfer” becomes hardware overfitting.

### Minimum publishable claim

A credible result is not “EA found better angles once.” It is one of:

- better quality at the same number of circuit evaluations;
- equal quality with fewer shots or shallower transpiled circuits;
- statistically better transfer to unseen sizes/instances;
- a stable Pareto archive that adapts to multiple QPUs;
- a careful negative result showing where evolutionary search loses after all overheads are counted.

## 5. Concrete implementation path

### Phase 0 — reproducible local baseline

- Run Metriq LR-QAOA on Aer for its three graph modes.
- Parse selected QOBLIB LABS/MIS instances and validate returned solutions with QOBLIB checkers.
- Create one common result record containing algorithm quality, shots, circuit evaluations, depth, two-qubit gates, and separated CPU/QPU/total time.

### Phase 1 — parameter-only evolution

- Implement NSGA-II or CMA-ES/DE over a compact transferable schedule.
- Compare against random search, DE, SPSA, and COBYLA under identical evaluation budgets.
- Use exact/noiseless simulation first, then shot noise and device noise models.

### Phase 2 — restricted structure search

- Add depth, mixer library, and parameter-sharing masks.
- Cache duplicate circuits and use racing/multi-fidelity evaluation: few shots early, more shots for finalists.
- Maintain a held-out test set.

### Phase 3 — Metriq benchmark contribution

Add an “Evolutionary/Transfer QAOA” benchmark with:

- a JSON schema for instance reference, frozen genome/schedule, depth, shots, and seed;
- a result type containing quality, uncertainty, feasibility, compiled resources, and timing;
- deterministic circuit construction from the saved genome;
- simulator tests and one end-to-end example;
- no online evolution inside the standard benchmark run unless optimization cost is explicitly part of the benchmark.

### Phase 4 — QOBLIB submission

- Produce valid solution files and canonical summary CSVs.
- Separate CPU, GPU, QPU, and total runtime.
- Record seeds, versions, preprocessing, postprocessing, number of feasible/successful runs, and negative outcomes.

## 6. Threats to validity

- **Evaluation-budget bias:** population methods can look better merely because they evaluate more circuits.
- **Simulator bias:** statevector fitness does not predict finite-shot noisy hardware performance reliably.
- **Transpiler leakage:** comparing logical depth while ignoring compiled two-qubit depth is misleading.
- **Instance leakage:** optimizing schedules on every test instance does not demonstrate transfer.
- **Calibration overfitting:** a circuit tuned to one QPU snapshot may age quickly.
- **Feasibility masking:** QUBO penalty tuning and classical repair can dominate the claimed quantum contribution.
- **Classical-work omission:** preprocessing, optimization, and postprocessing must be included in end-to-end comparisons.
- **Quantum-inspired labeling:** a classical probabilistic representation is not a quantum computation.
- **No-free-lunch baseline choice:** compare with mature problem-specific heuristics, not only weak generic optimizers.

## 7. Ranked topic shortlist

| Rank | Topic | Novelty | Feasibility | Benchmark fit | Recommendation |
|---:|---|---|---|---|---|
| 1 | Transferable evolutionary QAOA schedules on QOBLIB + Metriq | High enough | High | Excellent | Start here |
| 2 | Multiobjective hardware-aware ansatz/layout co-design | High | Medium | Excellent | Natural second paper |
| 3 | Quality-diversity archive across QPUs/calibrations | High | Medium | Very good | Strong distinctive angle |
| 4 | Evolution of device-tailored QEC codes/decoders | High | Medium-low | Outside QOBLIB | High-impact parallel direction |
| 5 | Evolved adversarial benchmark instances | High | Medium | Good | Follow-up after solver baseline |
| 6 | Quantum-assisted mutation/crossover/selection | Unclear | Low | Weak | Exploratory only |
| 7 | Generic quantum-inspired EA on classical benchmarks | Low | High | Weak | Avoid as main research claim |

## 8. Primary reading list

1. Metriq platform paper: https://arxiv.org/abs/2603.08680
2. Metriq-Gym documentation: https://unitaryfoundation.github.io/metriq-gym/
3. QOBLIB paper: https://doi.org/10.1038/s43588-026-00991-1
4. QOBLIB repository/site: https://github.com/ZIB-AOPT/QOBLIB and https://zib-aopt.github.io/QOBLIB/
5. Automated quantum algorithm design with a scalable DSL and evolutionary search: https://doi.org/10.1140/epjqt/s40507-026-00472-4
6. EXAQC neuro-evolutionary circuit design: https://arxiv.org/abs/2602.03840
7. Quality Diversity for Variational Quantum Circuit Optimization: https://arxiv.org/abs/2504.08459
8. Adaptive diversity-based quantum circuit architecture search: https://doi.org/10.1103/PhysRevResearch.6.033033
9. Multi-objective evolutionary architecture search for PQCs: https://pmc.ncbi.nlm.nih.gov/articles/PMC9857551/
10. Evolutionary design of quantum error-correction codes: https://arxiv.org/abs/2409.13017
11. Genetic programming with an explicit quantum-advantage-aware fitness: https://arxiv.org/abs/2501.09682
12. Early automated quantum circuit design with genetic programming: https://ntrs.nasa.gov/citations/20000057532

## Decision

Proceed with **parameter-only transferable QAOA evolution on LABS + MIS**, design the result format to match both Metriq and QOBLIB from day one, and delay arbitrary circuit-topology evolution until the baseline and evaluation budget are solid.
