# RankCert-MPS status

The required local exact-case research cycle is complete.

- Aer schedule runs: 100 / 100
- LR-vs-MR cohorts: 50 / 50
- BKS soundness violations after the documented numerical allowance: 0
- TVD soundness violations after the documented numerical allowance: 0
- Internally certified cohorts: 14 / 50
- Correct certified: 14 / 14
- Certified wrong signs: 0
- Exact-TVD-certified cohorts: 37 / 50
- 18q ibm32 internal coverage: 0 / 10
- 24q aves internal coverage: 0 / 10
- Final verdict: Outcome 2 - sound but too conservative

The first Phase III pass stopped on a zero-truncation floating-point TVD of
`2.0512216061805355e-10`, just above the provisional `2e-10` tolerance. The
immutable controls showed zero/negligible-truncation TVD up to
`2.2397708706965874e-8`; the resumed analysis therefore uses a separately
reported `1e-7` numerical floor. See `NUMERICAL_ROUNDOFF_AUDIT.md`. The original
stop is intentionally retained in `run_failures.json` as an audit trail.

The optional cuTensorNet certificate was not run because its installed
high-level `NetworkState` MPS API does not expose per-SVD discarded weights.
The 55q experiment was not run because the predeclared usefulness gate failed:
neither exact large case had any internal certificate coverage.

No cloud/QPU resource was used. No commit or push was performed. Frozen inputs
were not modified.
