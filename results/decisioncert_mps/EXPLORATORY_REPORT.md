# Decision-aware RankCert follow-up

## Status

This is a follow-up, not a replacement for RankCert-MPS. Cumulative surrogates
and stability envelopes are explicitly heuristic. The event-angle interval in
the next section is a separate rigorous consequence of the same global angle.

## Rigorous event-angle interval

For a projector event with approximate probability q and state-angle bound A,
measurement contractivity gives

`sin^2(max(0, asin(sqrt(q))-A)) <= p_exact <= sin^2(min(pi/2, asin(sqrt(q))+A))`.

This probability-aware interval certified 14 / 50 rankings with 0 wrong. Its per-case coverage is {'karate': 10, 'chesapeake': 2, 'football': 2, 'ibm32': 0, 'aves-sparrow-social': 0}. It is never wider than the generic additive event bound, but on this dataset it did not improve the 14 / 50 coverage because the accumulated angles on ibm32 and aves were already too large. This is a useful negative result: merely transforming the global angle more sharply is insufficient; a successful observable-aware method must reduce the angle contribution itself using BKS structure.

## Discarded-weight surrogates

| Internal quantity | BKS violations / 100 | TVD violations / 100 | Accepted rankings | Wrong accepted |
|---|---:|---:|---:|---:|
| sum_w | 3 | 33 | 31 / 50 | 0 |
| sqrt_sum_w | 0 | 0 | 21 / 50 | 0 |
| product_trace | 0 | 0 | 21 / 50 | 0 |
| rss_angle | 0 | 0 | 21 / 50 | 0 |

`sqrt(sum w)`, `sqrt(1-product(1-w))`, and the root-sum-square angle happened
to upper-bound every exact error in this dataset and accepted 21 / 50 rankings,
versus 14 / 50 for the rigorous angle sum. This is empirical evidence for
mostly incoherent error accumulation, not a theorem. The more aggressive
`sum(w)` accepted 31 / 50 but failed three BKS schedule checks and 33 TVD
checks; it is falsified as a bound.

The empirically clean square-root surrogates accepted 1 / 10 ibm32 rankings
but 0 / 10 aves rankings. They are useful candidates for future held-out
validation, not for guaranteed claims.

## Multi-setting decision stability

For each case, the stability envelope is the min/max MPS delta across all five
frozen settings and both orderings, widened by the predeclared numerical floor.

| Case | Internal stability envelope | Exact delta (audit only) | Decision | Correct |
|---|---:|---:|---:|---:|
| karate | [0.0864118, 0.0864122] | 0.086412 | accept | True |
| chesapeake | [-0.136099, -0.108668] | -0.134214 | accept | True |
| football | [0.0191922, 0.0518575] | 0.0192689 | accept | True |
| ibm32 | [-0.256811, -0.219681] | -0.246123 | accept | True |
| aves-sparrow-social | [-0.0128311, 0.138479] | -0.0121389 | reject | - |

The envelope accepted 4 / 5 case-level decisions, all correct, and rejected
aves because its internal winner changes with approximation. At the
case-ordering level it accepted 8 / 10, with 0 wrong. All 10 / 10 exact deltas lay inside the empirical envelopes. Leave-one-setting-out checks accepted 40 / 50 and made 0 wrong decisions.

This gate is attractive because it uses only repeated approximate simulations,
but unanimity is not a proof. Its value is operational: it detects the known
approximation-sensitive case without exact-state access.

## Independent schedule-pair validation

The frozen artifacts also contain `prior_evolutionary` (ES), which was not used
to develop the MR-vs-LR stability rule. Applying the unchanged envelope to
ES-vs-LR accepted 10 / 10 case-ordering decisions and 5 / 5 case-level decisions, with 0 and 0 wrong respectively. The exact delta lay inside 8 / 10 widened envelopes.

This independent-pair validation is encouraging: the 24q aves ES-vs-LR effect
is stable and correctly accepted, while its approximation-sensitive MR-vs-LR
effect is rejected. It is not external-case validation because the same five
instances and simulator family are reused.

## Frozen 55q implication

| Bond | Cutoff | LR BKS | MR BKS | Observed MR-LR |
|---:|---:|---:|---:|---:|
| 64 | 1e-04 | 153/10000 | 109/10000 | -0.0044 |
| 64 | 3e-04 | 116/10000 | 161/10000 | +0.0045 |
| 64 | 1e-03 | 41/15000 | 101/15000 | +0.004 |
| 96 | 1e-04 | 152/10000 | 134/10000 | -0.0018 |
| 96 | 1e-03 | 19/10000 | 70/10000 | +0.0051 |

The observed point-estimate signs are [-1, 1, 1, -1, 1]; the
signs supported by non-overlapping marginal Wilson intervals are
[None, None, 1, None, 1]. Therefore both the
point stability rule and a confidence-aware version reject the 55q decision.
These are reused finite-shot frozen counts, not a new execution, a simultaneous
confidence construction, or an exact statement.

## Scientific conclusion

The discarded-weight list alone cannot support a universally tighter rigorous
bound; its local angles contain no information about coherent orientation or
the BKS observable. The next serious algorithm should propagate BKS-observable
sensitivity backward through the circuit or construct validated upper/lower
tensor-network contractions. In the meantime, the multi-setting envelope is a
useful abstention heuristic: accept stable decisions, reject approximation-
sensitive ones, and never describe the result as certified.
