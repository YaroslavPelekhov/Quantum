# Frozen spectral transfer of the signed low-bond policy

Locked on 2026-08-21 after completing sorted design analysis and before the
first spectral low-bond residual execution.

## Frozen design selection

The sorted exhaustive grid selects fixed residual bonds R32/R32 for
`published_lr` / `prior_matched_random`.  It is the minimum-cost pair in the
prespecified `{32,64,96,128}` grid and certifies the sorted exact-gap sign with
interval `[-0.453426, -0.038820]`.

The following SHA-256 identities freeze the design evidence:

- sorted low-bond residual JSON:
  `5c3718baddbed623367e9d91008c7160b522dfca77dde271b0570d2d9b4eed17`
- signed-decision summary before spectral low-bond execution:
  `b4a09c61188349b09924c613c2f069fc3ace829ffa68961850ddf6a2abb60a0e`
- signed-decision report before spectral low-bond execution:
  `0d7ba0bcf21555a36df6439b8621f1c0f6125dc08b6a3ecca6fbe8cb6945de60`

## Held-out execution

Run the identical primary schedule and residual ladder `{32,64,96,128}` on
spectral ordering with no change to centers, interval formula, numerical
allowance, or bond selection rule.  The primary held-out verdict is whether the
already selected R32/R32 pair strictly excludes zero.  The remaining ladder is
retained to test whether the nonmonotone path ordering transfers.

All failures, regression differences, and dense-audit violations must be
reported.  Exact spectral BKS values remain audit-only.

