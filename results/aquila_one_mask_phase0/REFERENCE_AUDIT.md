# Adaptive-ODE reference audit

## Verdict

**CONFIRMED_OPTIMIZATION_MESH_FALSE_POSITIVE.**

The frozen differentiable optimizer used two midpoint propagations per 0.25 us
knot interval.  It found near-unit values on that grid, but the values fell
monotonically under grid refinement and converged to the adaptive DOP853
reference below.  The original `KILL_ONE_MASK_PHASE0` decision is therefore
strengthened, not reversed.

| target | selected source | seed | adaptive-ODE fidelity | quantized fidelity |
|---:|---|---:|---:|---:|
| `0101` | direct_full_c6 | 4100 | 0.787188 | 0.787195 |
| `1010` | direct_full_c6 | 4100 | 0.683809 | 0.683802 |


This is a useful systems lesson: exact hardware bounds and a differentiable
optimizer do not make a pulse physically valid if the propagation mesh is too
coarse for the always-on `C6/r^6` scale.  Any later pulse optimization must put
an adaptive reference solver or a converged interaction-picture integrator
inside the acceptance loop.
