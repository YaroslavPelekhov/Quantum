# Frozen protocol

Frozen on 2026-08-03 before any `es60fst02` candidate evaluation.

## Primary hypothesis

A schedule selected by finite-shot robust evolutionary search on the complete
QOBLIB `es60fst01` and `es60fst03` instances transfers without retuning to the
held-out `es60fst02` instance and improves BKS-hit probability over the
published linear-ramp schedule at equal deployment depth and shots.

## Secondary hypotheses

1. Evolutionary search beats matched-budget uniform random search on the blind
   test.
2. The selected schedule improves feasible probability and probability mass at
   BKS-1 or better.
3. Improvements survive pairing by simulator seed and a bootstrap confidence
   interval over replicate jobs.

## Fixed choices

- QAOA depth: 15.
- MIS QUBO penalty: 1.5.
- Hamiltonian scaling: the published maximum quadratic-coefficient scaling.
- Reduction: the published reduction with `max_degree=4`.
- No repair, no greedy fill, no use of archived solutions.
- Search space: `delta_beta in [0.15, 1.20]`, `delta_gamma in [0.05, 1.00]`,
  `beta_power,gamma_power in [0.30, 2.50]`.
- Selection: training score first, one frozen validation ranking on
  `es60fst04`, then one champion per search method.
- Primary held-out instance: `es60fst02`; its outcomes are never used to select
  a schedule.
- Baselines: published LR `(0.7,0.4,1,1)` and uniform random search with exactly
  the same number of training circuit evaluations as evolutionary search.

The promotion gate for a main-paper claim is: positive paired mean difference
in BKS-hit rate versus the published baseline, a 95% bootstrap interval not
crossing zero, and no material loss in feasible probability. Failure is
reported as a negative result rather than tuned away.

