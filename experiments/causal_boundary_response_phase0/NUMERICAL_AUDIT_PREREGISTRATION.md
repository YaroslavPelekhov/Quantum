# Post-gate numerical audit (frozen)

The preregistered Phase 0 returned rank-64 residuals near machine precision.
Before any physical fitting, this audit tests whether that apparent
finite-horizon compressibility is a 256-by-256 discretization artifact.

For `k=13`, both detuning controls, and `T in {5,10,20}`, recompute the response
with Hankel sizes 128, 256, and 512 (255, 511, and 1023 time samples).  Report
1%, 1e-6 effective ranks, the rank-64 residual, and normalized leading singular
values.

The numerical opening survives only if, at size 512:

- the 1% effective rank differs from the registered size-256 value by at most
  one;
- the rank-64 residual remains below `1e-8`;
- the response starts at one to `1e-10`.

Failure stops the physical-surrogate search.  Passing only confirms a stable
numerical low-rank target; it does not establish a physical realization.

