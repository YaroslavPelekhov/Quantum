# Observable-Telescope RankCert: research pilot

## Main result

The observable-aware exact-backward verifier materially improves the rigorous
RankCert coverage on the frozen QOBLIB-derived cohort.

- On the complete 7q matrix it certifies **14 / 20** LR-vs-MR
  rankings, versus **4 / 20** for accumulated-angle RankCert,
  with zero wrong certified signs.
- On the real 18q `ibm32` circuit, accumulated-angle RankCert is vacuous
  (pair width 2.0) for all tested settings. The new verifier certifies both
  `confirm` and `cutoff1e-5` on sorted ordering.
- The released low-resource point remains uncertified. This is the correct
  abstention: its new width is 0.524066 while the observed gap is 0.219681.

### Complete 7q matrix

| Case | Observable-telescope certified |
|---|---:|
| chesapeake | 8 / 10 |
| football | 6 / 10 |

The new method adds 10 strict decisions over the prior bound.
The maximum telescope-identity error is
2.665e-15; the maximum frozen-run
regression error is 5.551e-16.

### Targeted 18q resource ladder (`ibm32`, sorted)

| Setting | Max bond | Cutoff | MPS MR-LR gap | Pair bound | Certified | Prefix replay, LR+MR (s) | Peak block environments (MiB) |
|---|---:|---:|---:|---:|:---:|---:|---:|
| released | 64 | 1e-03 | -0.219681 | 0.524066 | no | 140.6 | 136 |
| confirm | 128 | 1e-04 | -0.254904 | 0.067568 | yes | 232.0 | 520 |
| cutoff1e-5 | 1024 | 1e-05 | -0.248347 | 0.008709 | yes | 978.9 | 520 |

The exact gap is -0.246123 for all three rows. `confirm` is the practically
important point: bond 128 and cutoff 1e-4 already preserve the certified
method ranking. The stricter bond-1024 `cutoff1e-5` point narrows the pair bound
further to 0.008709 but costs substantially more replay time.

Across all 18q rows, the maximum telescope-identity error is 4.441e-16
and the maximum difference from the frozen RankCert final BKS probability is
9.992e-16.

## Certificate construction

Let `Pi` be the BKS event projector and let `U_(t:T)` be the exact suffix after
checkpoint `t`. For the approximate MPS prefix state `phi_t`, define

`q_t = <phi_t | U_(t:T)^dagger Pi U_(t:T) | phi_t>`.

The first value is the exact BKS probability and the final value is the MPS BKS
probability. Hence

`p_MPS - p_exact = sum_t (q_t - q_(t-1))`

and the triangle inequality gives the rigorous trajectory-specific bound

`|p_MPS - p_exact| <= sum_t |q_t - q_(t-1)|`.

For an LR-vs-MR comparison, the two schedule bounds are added. A ranking is
certified only when the absolute approximate gap exceeds this paired width.

The BKS projector is low rank in this benchmark: rank 1 for chesapeake, rank 4
for football, and rank 2 for ibm32. On 18q, exact backward vectors are processed
in reverse blocks. Forward checkpoint states are obtained by independent
uninterrupted prefix replay from `|0>`; this avoids a verified Aer behavior in
which restarting from a saved MPS can change later SVD truncations.

## What is and is not claimed

This is a strict **a posteriori feasibility verifier**, not yet a scalable
internal MPS certificate. It uses exact backward suffix propagation with cost
exponential in qubit count. It does not infer rigor from Aer discarded weights,
and it does not claim performance on noisy hardware or finite-shot sampling.

The evidence consists of the full 40-trajectory 7q matrix plus three targeted
18q resource points on one ordering. The 18q result establishes scale transfer
for this frozen benchmark, but broader QOBLIB cases, orderings, and independent
circuits are still required for a main-paper generalization claim.

## Next research step

The paper-level algorithmic target is a scalable observable-aware verifier:
represent the backward BKS projector as a compressed MPO, propagate it through
the suffix, and attach a rigorous error budget to every MPO compression. The
exact-backward implementation here is the oracle against which that compressed
method should be calibrated. A successful method must retain the 18q
certificates above while bounding its own compression error and avoiding exact
`2^n` state vectors.
