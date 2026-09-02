# Sequential-reference curvature boundary: Phase-0 report

## Mathematical verdict

**PASSES_MATHEMATICAL_PHASE0**.  A* novelty verdict:
**KILL_SIMPLE_CURVATURE_AS_ASTAR**.  No QPU run is authorised.

## Exact results

- Affine RTR interpolation bias: `6.94e-18`.
- Quadratic ratio `bias/(kappa T^2)`:
  `-0.500000000000` (exact prediction `-0.5`).
- Compact-bump target shift: `0.00012660952381`.
- Compact-bump maximum `|d''|`: `2.3e-05`
  against registered bound `2.3e-05`.
- Maximum two-quadrature probability gap between the two lower-bound worlds:
  `0`.
- Resulting two-point minimax absolute-risk lower bound:
  `6.33047619048e-05`.

For every common drift with `|d''|<=kappa`, sequential equal-duration RTR
interpolation has error at most `kappa T^2/2`; quadratic drift saturates the
constant.  The compact target-only C2 bump establishes a matching
`Omega(kappa T^2)` indistinguishability lower bound.

## Shot-noise and resource controls

- Median zero-curvature amplified RMSE slope versus fully counted physical
  depth: `-0.9842`.
- Median equal-cost direct-depth-one slope: `-0.4979`.
- Curvature collapse `R^2`: `1.000000000000`.
- Fitted collapse slope: `0.500000000000` (prediction `0.5`).

Thus the mechanism produces the crossover
`kappa tau^2 D^3 = Theta(1)` when a local Heisenberg schedule uses
`D=Theta(1/epsilon)`.  This is not an absolute estimation floor.  Below that
crossover a protocol may shorten coherent depth and buy more repetitions,
progressively reverting toward standard-quantum-limit scaling.

## Novelty boundary

Correct mathematics is necessary but not sufficient.  The independent
primary-source audit found direct prior art for symmetric drift cancellation,
interleaved Ramsey references, time-symmetric phase smoothing and temporal
quantum limits.  The sharp `C^2` constant is classical optimal interpolation,
and the cube-root follows by balancing it with `1/D`.  The simple claim is
therefore closed as A* novelty even though its theorem mechanism is correct.

The still-open object is substantially harder: a minimax optimal design over
wrapped Bernoulli likelihoods, arbitrary adaptive multi-depth schedules, noisy
duration-matched anchors, full wall-clock/query budgets and a Holder drift
ball.  That is not claimed or proved by this Phase 0.
