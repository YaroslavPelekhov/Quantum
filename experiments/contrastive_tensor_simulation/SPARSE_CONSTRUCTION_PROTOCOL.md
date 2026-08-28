# Frozen sparse construction protocol

Frozen after the terminal signed diagonal contrast passed the equal-budget
kill test and before any sparse-completion outcomes were run.

## Question

Can `q(z)=p_B(z)-p_A(z)` be constructed from a small point-query subset rather
than from the full `2^n` terminal arrays?

The exact arrays act only as immutable point-query oracles and final audits.
The constructor may not read or factorize the full tensor.

## Frozen design

- Cases: `ibm32` (18q) and `aves-sparrow-social` (24q).
- Orderings: sorted and spectral.
- Methods: `A=published_lr`, `B=prior_matched_random`.
- Model: real tensor train fitted by bidirectional ridge ALS.
- Maximum TT ranks: `8` and `12`.
- Training queries: `24 * canonical_parameter_count`, sampled uniformly with
  deterministic seed `20260822 + case/order/rank offsets`.
- Holdout: 65,536 distinct uniform points not used for training.
- Sweeps: 12 bidirectional sweeps.
- Relative ridge: `1e-10` of the local normal-matrix mean diagonal.
- All BKS-support indices are excluded from training and holdout. They are
  evaluated only after fitting to compute Delta.

Training sets for different ranks are independently frozen by their seeds.
No rank, query multiplier, sweep count, or tolerance may be changed after
inspection.

## Success criteria

The sparse-construction branch passes only if, for rank 8 or 12:

1. aves has the correct Delta sign on both orderings;
2. absolute Delta error is below `0.1 * |Delta_exact|` on both orderings;
3. holdout relative RMSE is below `0.1` on both orderings;
4. the query fraction is below `2%` of the full tensor on both orderings.

Exact Delta and exact holdout values are audit-only. No rigorous global error
certificate is claimed from sparse samples. Failure closes the claim that the
terminal contrast advantage is constructible by generic uniform TT completion.
