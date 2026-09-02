# Frozen preregistration: sequential-reference curvature boundary

Frozen on 2026-09-02 before inspecting this experiment's numerical output.

## Claim under test

Consider a local amplified amplitude/phase-estimation stage of odd coherent
depth `D`.  Each circuit lasts `T = tau D`.  A known reference circuit is run
immediately before and after the target, giving a sequential `R-T-R` block.
Both quadratures are measured and every reference circuit is charged at full
physical depth.

The proposed theorem pair is:

1. symmetric sequential references cancel every common affine wall-clock
   drift exactly;
2. under only `|d''(t)| <= kappa`, their worst-case interpolation bias is
   `Theta(kappa tau^2 D^2)`, with a matching indistinguishable bump
   construction.

Combining this bias with local amplified statistical error `Theta(1/D)` gives
the crossover

```text
kappa tau^2 D^3 = Theta(1)
```

and a sequential-calibration accuracy floor of order
`(kappa tau^2)^(1/3)` for a Heisenberg-depth choice `D = Theta(1/epsilon)`.

## Exact time model

The left reference, target and right reference occupy equal intervals

```text
R_left : [-3T/2, -T/2]
Target : [ -T/2,  T/2]
R_right: [  T/2, 3T/2].
```

Each circuit observes the interval average of `d(t)`.  The local branch of the
amplified phase is assumed known from an earlier coarse stage; this experiment
does not hide global alias resolution inside the curvature claim.

The estimator subtracts the mean reference phase from the target phase and
divides by `2D`.  With exact phases its deterministic error is

```text
average_target(d) - [average_left(d)+average_right(d)]/2.
```

## Frozen tests

1. Polynomial audit: constants and linear drift cancel to numerical tolerance;
   quadratic drift `d(t)=kappa t^2/2` gives bias exactly
   `-kappa T^2/2`.
2. Lower-bound witness: a compact `C^2` bump supported only inside the target
   interval, zero with two derivatives at its boundaries, makes two distinct
   target parameters exactly indistinguishable from all reference and target
   observations.  Its amplitude is chosen so `|d''|<=kappa`.
3. Shot-noise control: two-quadrature local estimation is simulated over the
   frozen depths, amplitudes, curvatures and 4096 deterministic trials.
4. Equal-cost direct control: a depth-one local estimator receives the same
   total physical depth and therefore `D` times as many repetitions.
5. Collapse test: normalized deterministic bias is regressed against
   `xi=kappa tau^2 D^3`.

## Pass, kill and novelty gates

The mathematical mechanism passes only if:

- affine drift cancels below `1e-10`;
- the quadratic bias ratio equals `-1/2` within `1e-8`;
- the compact bump respects the curvature constraint and produces equal
  observation laws below `1e-10`;
- the zero-curvature amplified RMSE slope lies in `[-1.1,-0.9]` and the
  equal-cost direct slope in `[-0.6,-0.4]`;
- the normalized curvature collapse has `R^2 >= 0.98`.

Passing those gates establishes only a correct theorem mechanism.  It becomes
an A* seed only if a fresh primary-source audit finds that the combined
sequential-reference lower bound, fully charged quantum depth, and cube-root
boundary are not already implied by established reference metrology,
interpolation, clock-noise or noisy-metrology results.

The direction is killed as A* novelty if the result is merely a classical
interpolation lemma with QAE notation, if simultaneous/spectator references
remove the boundary under the intended hardware model, or if the required
common-mode target/reference coupling is not experimentally falsifiable.

No Phase-0 outcome authorises QPU spending.

