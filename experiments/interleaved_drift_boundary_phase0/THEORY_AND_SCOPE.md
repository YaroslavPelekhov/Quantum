# Sharp local theorem and its limits

## Sequential block

Three equal-duration circuits run consecutively as reference, target,
reference.  A depth-`D` circuit lasts `T_D = tau D`; the circuit-centered
common per-query drift is the interval average `g_D(c)`.  Translation of a
common sensitivity kernel preserves the smoothness bound

```text
||g_D''||_infinity <= kappa.
```

The exact-phase corrected estimator has drift error

```text
b_D = g_D(0) - [g_D(-T_D)+g_D(T_D)]/2.
```

The midpoint interpolation remainder gives the sharp upper bound

```text
|b_D| <= kappa T_D^2 / 2.
```

Quadratic drift attains equality.  For unequal center distances `h_-` and
`h_+`, linear interpolation gives `|b_D| <= kappa h_- h_+ / 2`; actual
timestamps, reset time and readout gaps must therefore replace nominal depth
in any hardware use.

## Matching local lower bound

Even noiseless full-phase observations cannot improve the order.  Two
quadratic drift worlds can agree on both reference averages while shifting the
target average by opposite amounts.  Equivalently, the compact registered
`C^2` bump is zero with two derivatives at target boundaries and has

```text
average_target(bump) = 2 kappa T_D^2 / 105.
```

Changing `theta` by that amount makes every target and reference quadrature
probability identical.  This gives an explicit minimax absolute-risk lower
bound `kappa T_D^2 / 105`.  A piecewise-quadratic `W^(2,infinity)` extremizer
improves the constant, but the current smooth polynomial is sufficient for the
matching `Theta(kappa T_D^2)` statement.

## Crossover, not universal floor

With a constant number of shots, local amplified statistical error is
`Theta(1/D)`.  Since `T_D = tau D`, balancing it with the drift term gives

```text
kappa tau^2 D^3 = Theta(1),
epsilon_H = Theta((kappa tau^2)^(1/3)).
```

This is the point where a Heisenberg-depth choice `D=Theta(1/epsilon)` stops
being reliable.  It is not the global minimax accuracy floor.  Below the
crossover one can shorten `D` and buy more repetitions.

For total cost `Q`, the local fixed-depth envelope is

```text
R(Q,D) ~ 1/sqrt(QD) + kappa tau^2 D^2.
```

Its interior optimum has

```text
D ~ [(kappa tau^2)^2 Q]^-1/5,
R ~ (kappa tau^2)^1/5 Q^-2/5.
```

At still larger budgets `D` reaches one and an adversarial sequential
calibration floor of order `kappa T_1^2` remains.  Turning this envelope into a
theorem for every adaptive multi-depth QAE protocol requires a global
modulus-of-continuity/KL argument; Phase 0 does not claim it.

## Model dependence

The cube-root exponent requires drift measured as per-query eigenphase or
frequency.  If the nuisance is instead one additive circuit phase, division by
`D` changes the bias to `Theta(kappa tau^2 D)` and the crossover becomes a
square root.  Concurrent spectator references, finite-dimensional parametric
drift, stochastic rather than adversarial drift, noncommuting errors, or
target/reference sensitivity mismatch also change or invalidate the theorem.

The correct result is therefore a local sequential-reference boundary under a
specific common-mode model, not a universal law of noisy QAE.

