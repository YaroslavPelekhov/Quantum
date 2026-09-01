# Optimizer and four-atom capacity audit (frozen)

The optimistic three-atom synthesis gate failed, narrowly at `T=5`.  Before
interpreting this as a physical-realization gap, this audit tests both likely
confounders: insufficient global optimization and an overly aggressive atom
budget.

Only the preregistered near-miss horizon `T=5` is used, with both detuning
controls.

## Three-atom optimizer audit

- rescreen all 16 non-isomorphic colored topologies;
- expand every detuning and the port phase-rate bound from `[-3,3]` to
  `[-6,6]`;
- refine the four best topologies with four independent seeds each;
- fit on 129 times and validate on 1023 times.

Recovery requires the original 2% maximum, 1% relative-L2, and fivefold prefix
improvement thresholds in both controls.

## Four-atom capacity audit

- screen all 79 non-isomorphic colored four-atom topologies on 65 times;
- refine the five best with three independent seeds each on 129 times;
- use the same expanded optimistic parameter bounds;
- validate on 1023 times against a same-budget four-atom path prefix.

Four atoms still give `13/4 = 3.25x` physical atom compression.  This branch
advances if four atoms satisfy the same 2%/1%/fivefold thresholds in both
controls.  Failure of both audits closes all *static* surrogate realizations
inside this deliberately super-hardware control envelope.

