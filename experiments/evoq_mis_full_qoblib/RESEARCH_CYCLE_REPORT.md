# Full QOBLIB research-cycle report

## Outcome

The cycle produced a paper-grade result on real QOBLIB instances, but the most
defensible novelty is **benchmark sensitivity**, not a universal superiority
claim for evolutionary search.

At the published Aer/MPS setting (bond 64, truncation threshold 1e-3), the
matched-budget random-search nonlinear ramp achieved 101
BKS hits in 15,000 blind shots (0.6733%)
versus 41 (0.2733%) for the
published linear ramp. The paired difference was 0.4000%
with bootstrap 95% CI [0.2467%,
0.5533%] and exact paired sign-flip
p=0.000244. Estimated shots for 95% chance
of at least one BKS sample fell from 1095 to
444.

The nonlinear ramp also increased feasible rate from
50.13% to 90.18%
and near-BKS rate from 11.21% to
15.70%. The evolutionary champion reached
89.99% feasibility but did not improve BKS hit rate,
so matched random search beat the evolutionary operator under the same 120
candidate evaluations per replicate.

## Stronger novelty: an MPS-induced rank reversal

Tightening only the MPS truncation threshold changed the BKS conclusion. At
bond 64 / threshold 1e-4 with 10,000 shots per method, published LR reached
1.53% BKS hits while the nonlinear ramp reached 1.09%. At the intermediate
threshold 3e-4, the nonlinear ramp still led 1.61% to 1.16%. Increasing bond
64→96 while keeping threshold 1e-3 preserved the nonlinear advantage (0.70%
versus 0.19%), identifying the truncation threshold—not the bond cap—as the
dominant factor in this experiment.

Crucially, the nonlinear ramp retained higher near-BKS and feasible mass at
every tested setting. Thus optimum-hit ranking is fragile while distributional
quality ranking is robust. Approximate tensor-network benchmark papers should
therefore publish convergence sweeps and avoid selecting algorithms from a
single truncation setting.

## Exact-state calibration

The same protocol was calibrated on the real 12- and 15-qubit ES60FST kernels,
where complete statevectors are available. At threshold 1e-3, total-variation
distance from exact is 0.0518/0.0509 for the published ramp and 0.0742/0.0702
for the nonlinear ramp on es60fst01/03. The MPS BKS bias is positive and larger
for the nonlinear ramp: +0.0342 and +0.0185, versus +0.0158 and +0.0074. At
threshold 1e-6, all four state fidelities exceed 0.99983, total variation falls
below 0.00266, and absolute BKS error falls below 0.00023. At shared thresholds,
bonds 32--128 are numerically identical. Bond 16 differs only for the nonlinear
es60fst01 circuit at threshold 1e-4, where total variation changes by less than
0.0005. Thus the discarded-weight threshold, rather than the bond cap once it
reaches 32, controls these small-kernel errors.

## Benchmark protocol

- Real full instances: QOBLIB `es60fst01`/`03` for training, `es60fst04` for
  validation, and blind `es60fst02` (186 vertices, BKS 88) for testing.
- Published graph preprocessing: exact degree-0/1 rules, degree-2 folding,
  recorded high-degree pruning; the test kernel has 55 qubits and 91 edges.
- QAOA depth 15; 1365 RZZ, 825 RZ, and 825 RX gates before measurement.
- Raw samples only: unfold plus feasibility filter; no constraint repair,
  greedy fill, or archived solution.
- Search: three seeds, 120 candidates per method, 256 shots on each of two
  training instances. Deployment: 15 paired jobs × 1000 shots per method.
- QOBLIB and external baseline code are commit-pinned in result provenance.

## Interpretation and promotion gate

The preregistered primary claim that evolutionary search improves BKS transfer
failed. The broader nonlinear-ramp claim passes at the exact published
benchmark setting but fails the simulator-robust BKS promotion gate because of
the threshold-dependent rank reversal. The main-paper-worthy claim is instead:

> On a 55-qubit, depth-15 QOBLIB MIS benchmark, MPS truncation can reverse the
> ranking of transferred QAOA schedules for optimum-hit probability even when
> near-optimal and feasible-mass rankings remain stable.

This aligns with the purpose of QOBLIB as a reproducible comparison framework
([Koch et al., 2026](https://doi.org/10.1038/s43588-026-00991-1)) and addresses
a gap in recent simulator benchmarking, which emphasizes runtime/accuracy
tradeoffs but does not establish schedule-ranking stability for optimization
observables ([Mazumder et al., 2026](https://arxiv.org/abs/2607.09882)). Recent
QAOA transfer work already covers parameter rescaling
([Sureshbabu et al., 2024](https://doi.org/10.22331/q-2024-01-18-1231)) and
penalty-scale resonance ([Grover, 2026](https://arxiv.org/abs/2607.09927)), so
the simulator-stability angle is better differentiated than another penalty or
normalization rule.

## Artifacts

- `results/blind_test.json`: 45 full test rows and paired inference.
- `results/mps_sensitivity.csv`: bond/threshold factorial audit.
- `results/figures/blind_method_comparison.png`: blind method metrics.
- `results/figures/mps_threshold_sensitivity.png`: rank-reversal figure.
- `results/figures/exact_mps_calibration.png`: exact-state convergence figure.
- `PROTOCOL_DEVIATIONS.md`: preserved transpilation audit and correction.
