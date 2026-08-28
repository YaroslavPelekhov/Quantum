# Numerical roundoff audit

The Phase III driver stopped as designed on
`chesapeake/bond128/published_lr/spectral`: Aer logged no truncations, hence
the truncation-only certificate was zero, while exact-vs-MPS TVD was
`2.0512216061805355e-10`, just above the initially provisional `2e-10`
comparison tolerance.

This is not evidence of a missing truncation event:

- the raw log contains zero `discarded_value` records;
- the same TVD is present in the immutable prior Aer artifact;
- the normalized state fidelity differs from one only at floating precision;
- other immutable no-truncation controls reach TVD
  `2.2397708706965874e-8` (`football/published_lr/spectral/bond128`).

The discrepancy comes from finite-precision repeated SVD/gate arithmetic in
Aer MPS versus Qiskit's exact statevector path. The accumulated-angle theorem
controls deliberate Schmidt truncation, not floating-point roundoff.

Before resuming Phase III, RankCert therefore froze a separate per-schedule
numerical allowance of `1e-7`, over four times the largest immutable
zero-truncation TVD control. It is not inferred from a configured cutoff and is
not included in `epsilon_mps`. For empirical soundness checks and ranking
intervals the effective half-width is

`min(1, epsilon_mps + 1e-7)`.

This floor is an empirical implementation allowance, not a formal forward
error theorem for Aer. Results report both the theorem-derived truncation term
and the effective interval. The original stop remains preserved in
`run_failures.json` as an audit trail.
