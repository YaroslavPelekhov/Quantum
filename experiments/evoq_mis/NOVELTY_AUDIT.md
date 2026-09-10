# Novelty audit and research hypotheses

Audit date: 2026-08-03. This document separates an empirical contribution candidate from claims already covered by prior work.

## Closest prior directions

1. **MIS parameter transfer with learned graph representations.** Xu et al. propose graph-attention parameter transfer for MIS and train on 12/14-vertex graphs before transferring to larger instances: https://arxiv.org/abs/2504.21135
2. **Graph-conditioned QAOA meta-optimization.** Nguyen and Safro condition a learned parameter generator on graph embeddings across MaxCut, MIS, Maximum Clique and Minimum Vertex Cover: https://arxiv.org/abs/2604.25275
3. **Graph representations and donor selection.** Falla et al. connect QAOA transferability to local graph structure and degree properties for MaxCut: https://arxiv.org/abs/2401.06655
4. **Feasible-subspace mixers.** Logical-X/subspace mixers and newer constrained-mixer constructions already provide general mechanisms for feasibility preservation: https://arxiv.org/abs/2306.17083 and https://arxiv.org/abs/2603.05187
5. **Warm-started constraint-preserving QAOA.** Iterative warm-start XY mixers have reported large gains and hardware demonstrations for other constrained problems: https://arxiv.org/abs/2604.02083

## What is not claimed

- Parameter transfer itself is not novel.
- Evolutionary optimization of variational circuits is not novel.
- Constraint-preserving mixers are not novel.
- Classical repair after quantum sampling is not evidence of quantum advantage.
- A simulator win over random parameter search is not a win over state-of-the-art classical MIS solvers.

## Contribution candidate tested here

**Proof-gated graph-scale normalization for shared QAOA policies.** A single five-parameter depth-two MIS QAOA schedule is evolved across a family of QOBLIB-derived graphs after normalizing every graph's Ising coefficients by its maximum local coefficient. Training optimizes a mean/worst-case aggregate, and promotion requires frozen-graph transfer, equal-budget baselines, exact verification and explicit raw-versus-repaired metrics.

The contribution is intentionally lightweight: unlike GAT/meta-optimizer approaches, it needs no learned graph encoder, parameter labels or target-graph adaptation. Its value must come from robust zero-shot transfer and low optimization/data cost.

## Pre-registered hypotheses

- **H1 — normalization:** coefficient normalization improves frozen-graph transfer over the identical unnormalized evolutionary protocol.
- **H2 — evolution:** normalized evolution improves train-family performance over equal-budget normalized random search; test advantage is evaluated separately.
- **H3 — scale:** schedules trained only at 11–17 qubits retain useful raw feasible mass and outperform unnormalized schedules on frozen 20–24-qubit QOBLIB-derived graphs.
- **H4 — constraints:** a feasibility-preserving MIS mixer removes penalty calibration and infeasible mass, but must be audited for optimum concentration and implementation cost.
- **H5 — hardware realism:** dense MIS cost layers suffer substantial routing overhead and noise; graph normalization cannot by itself solve compilation cost.

## Frozen scale-up suite

The following instances were selected before any schedule evaluation:

- first 20 vertices of QOBLIB `ibm32`;
- first 22 vertices of QOBLIB `football`;
- first 24 vertices of QOBLIB `johnson8-2-4`.

The suite spans graph families and sizes not used for training. No schedule will be reoptimized on it. Exact enumeration and exact statevector probabilities are used where memory permits; shot metrics are derived only after the exact distribution is frozen.

## Final confirmatory suite

After the exploratory scale and hardware audits, a second untouched suite was fixed before evaluation:

- first 20 vertices of QOBLIB `insecta-ant-colony1-day38`;
- first 22 vertices of QOBLIB `sloane_1dc_64`;
- first 24 vertices of QOBLIB `hamming6-4`.

The final method is frozen as max-coefficient-normalized, mean/worst-case multi-instance depth-two QAOA with differential evolution. Its existing 12 schedules are compared with the already-frozen unnormalized-DE and normalized-random schedules. No angle, penalty, graph subset, score weight or baseline may change after this declaration.

## Random-induced-subgraph robustness suite

This additional suite was declared on 2026-08-03 before evaluating any of the schedules on these vertex sets. It tests whether the reported normalization effect is an artifact of choosing the first vertices in each source file. The three source instances were not used in training, scale-up, or the final confirmatory suite. Two independently seeded subsets are fixed per source; vertex identifiers below are one-based.

- `es60fst01`, 20 vertices, seed 4101: 8, 14, 17, 26, 28, 29, 40, 48, 50, 52, 53, 58, 60, 64, 76, 85, 105, 107, 118, 121.
- `es60fst01`, 20 vertices, seed 4102: 3, 8, 13, 17, 36, 37, 41, 56, 59, 62, 67, 73, 83, 88, 104, 105, 106, 111, 117, 118.
- `aves-sparrow-social`, 22 vertices, seed 5201: 1, 5, 6, 7, 9, 10, 11, 15, 17, 18, 23, 25, 27, 29, 34, 35, 38, 40, 43, 44, 46, 47.
- `aves-sparrow-social`, 22 vertices, seed 5202: 2, 3, 7, 8, 9, 13, 14, 16, 20, 21, 25, 26, 27, 28, 32, 34, 39, 42, 43, 44, 46, 49.
- `MANN-a9`, 24 vertices, seed 6301: 1, 4, 5, 7, 8, 9, 10, 11, 14, 15, 19, 20, 22, 24, 25, 27, 29, 30, 31, 34, 41, 42, 43, 45.
- `MANN-a9`, 24 vertices, seed 6302: 1, 2, 7, 8, 9, 10, 11, 12, 17, 18, 20, 21, 24, 26, 29, 32, 34, 36, 38, 39, 40, 43, 44, 45.

The schedules, circuit depth, Hamiltonian, normalization rule, and metrics remain frozen. The primary endpoint is the paired replicate-level difference in the raw composite score, averaged over all six graphs, between normalized DE and the identical unnormalized DE protocol. The same four promotion checks as the final confirmatory suite apply: positive mean, strictly positive 95% paired bootstrap interval, two-sided paired t-test below 0.05, and a majority of replicate wins. Approximation ratio, feasible probability, and optimum probability are secondary sensitivity endpoints. Normalized random search remains a secondary optimization-control comparison.
