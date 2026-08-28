# Signed Decision-Gap COT and residual-policy rank reversal

## Executive result

A signed, recentered decision interval replaces the previous absolute-sum COT
ranking width. It retains all computable signed telescope contributions in the
center and keeps the unknown compressed-observable remainder fully adversarial.

On `ibm32/confirm/sorted`, the new interval certifies fixed residual R32/R32:

- recentered MR-minus-LR gap: `-0.246122939`;
- certified paired remainder: `0.207303396`;
- exact-gap interval: `[-0.453426, -0.038820]`;
- strict margin to zero: `0.038820`;
- nominal cubic residual work versus R256/R256: `0.001953125`;
- nominal residual-work saving: `99.8046875%`.

The legacy absolute-sum COT width at R32 is `0.274872`, larger than the MPS gap
`0.254904`, and therefore abstains. The gain comes from a different rigorous
interval construction, not a changed forward simulation.

The R32/R32 pair was selected on sorted ordering, hash-frozen, and transferred
unchanged to spectral ordering. It remains certified:

- recentered gap: `-0.246123004`;
- paired remainder: `0.019073642`;
- interval: `[-0.265197, -0.227049]`;
- strict margin: `0.227049`;
- same `99.8046875%` nominal residual-work saving.

This is ordering-level held-out transfer on one graph, not cross-graph scaling.

## The signed interval

For trajectory `s`, the exact telescope error is

`E_s = p_s^MPS - p_s^exact = sum_t c_(s,t)`.

Compressed backward observables give the signed center

`C_s = sum_t ctilde_(s,t)`

and residual-aware COT certifies `|E_s-C_s|<=R_s`. For the decision gap
`Delta = p_B-p_A`,

`Delta_exact in Delta_MPS - (C_B-C_A) +/- (R_A+R_B)`.

The previous certificate used `sum_(s,t)|ctilde_(s,t)| + R_A+R_B` around the
uncorrected MPS gap. On sorted ordering its absolute first term is `0.067568`,
whereas the magnitude of the paired signed center is only `0.0087815`, a
`7.694x` inflation. On spectral the corresponding factor is `6.601x`.

The new construction does not assume that unknown errors cancel. Only the
fully computed center is signed; the entire remainder remains worst-case.

## Frozen low-bond ladder

### Sorted design

| fixed residual bond | paired remainder | signed margin | signed | legacy |
|---:|---:|---:|:---:|:---:|
| 32 | 0.207303 | 0.038820 | yes | no |
| 64 | 0.232107 | 0.014016 | yes | no |
| 96 | 0.234274 | 0.011849 | yes | no |
| 128 | 0.219199 | 0.026924 | yes | no |
| 256 | 0.143049 | 0.103074 | yes | yes |
| 512 | 0.024084 | 0.222039 | yes | yes |

All three prespecified sub-R128 points pass the signed certificate and fail the
legacy one. R32 is both the cheapest and the tightest among R32/R64/R96/R128.

### Frozen spectral transfer

| fixed residual bond | paired remainder | signed margin | signed | legacy |
|---:|---:|---:|:---:|:---:|
| 32 | 0.019074 | 0.227049 | yes | yes |
| 64 | 0.021290 | 0.224833 | yes | yes |
| 96 | 0.020444 | 0.225679 | yes | yes |
| 128 | 0.017854 | 0.228269 | yes | yes |

R128 remains the tightest spectral low-bond point, but the sorted-selected R32
policy transfers with a large strict margin and is minimum-cost within the
frozen candidate set.

## Certified residual-policy rank reversal

The fixed-bond residual recurrence is path-dependent. A smaller bond can
discard more locally yet create a represented residual state whose later
propagation and recompression yield a tighter certified operator enclosure.

On sorted ordering, R32 is tighter than R64 at 329/556 LR checkpoints and
301/556 matched-random checkpoints. The integrated LR corrections are:

- R32 `0.207211`;
- R64 `0.231993`;
- R96 `0.234152`;
- R128 `0.219082`.

On spectral ordering, R32 is tighter than R64 at 286/556 LR and 270/556
matched-random checkpoints. R128 remains globally tightest, but R32 becomes
locally tightest in the late prefix. For both spectral schedules the full
R32-versus-R128 reversal first appears at the audited `t=128` checkpoint. The
matching onset across schedules supports an ordering-controlled reset
hypothesis, but does not prove it.

This is a rank reversal among certified upper-bound policies. It is not a
claim that lower-bond MPS state approximations are generally more accurate.

## Equal-work causal reset intervention

The proposed onset mechanism was tested, rather than inferred from the fixed-
bond correlation. Four policies use R32 in exactly one 64-checkpoint window
and R128 everywhere else. Their cubic residual work is identical and is
`0.110811` of an R256/R256 reference. The window predictions were frozen before
execution: `193--256` for sorted and `129--192` for spectral.

| ordering | policy | paired remainder | signed margin |
|---|---|---:|---:|
| sorted | `reset_129_192` | 0.215773 | 0.030350 |
| sorted | `reset_193_256` (frozen prediction) | 0.205546 | 0.040577 |
| sorted | **`reset_257_320`** | **0.175749** | **0.070374** |
| sorted | `reset_321_384` | 0.203154 | 0.042969 |
| spectral | `reset_129_192` (frozen prediction) | 0.0177052 | 0.228418 |
| spectral | `reset_193_256` | 0.0167679 | 0.229355 |
| spectral | **`reset_257_320`** | **0.0152018** | **0.230921** |
| spectral | `reset_321_384` | 0.0153698 | 0.230753 |

Both frozen onset-aligned predictions fail. The same unexpected window,
`257--320`, minimizes both the LR correction and the matched-random correction
on both orderings: four independent ordering-by-method comparisons. The
effect is delayed: an active R32 window can initially increase the bound, then
leave a smaller propagated enclosure tens of checkpoints later.

This falsifies the simple claim that the observed fixed-bond reversal onset is
the local cause of the low-bond benefit. It instead supports a path-memory
mechanism in which the useful compression window occurs earlier in the reverse
trajectory. The common `257--320` winner is a post-hoc discovery and requires a
new frozen replication; it is not promoted to a confirmed prediction here.

## Audits and reproducibility

- Fixed-bond dense operator violations: `0/144` across two orderings, two
  schedules, four low bonds, and nine selected checkpoints per trajectory/bond.
- Equal-work intervention violations: `0/144` across two orderings, two
  schedules, four reset windows, and nine selected checkpoints per trajectory.
- Every reported exact gap lies inside its interval. Exact values are
  audit-only and excluded from interval construction and bond selection.
- The recentered-gap audit error is `6.239e-8` on sorted and `-2.743e-9` on
  spectral.
- Thirty-three relevant unit/integrity tests pass after the reset-intervention
  artifact tests.

The prespecified R128 repeatability threshold of `1e-10` was too strict. Sorted
repeat differences are `5.926e-7` for LR and `1.650e-9` for matched-random;
spectral differences are `2.238e-10` and `4.168e-11`. All repeated runs remain
independently enclosed and all verdicts are unchanged. This is retained as a
floating-point reproducibility limitation, not silently relaxed into a pass.

## Novelty and claim boundary

Signed residual correction is related to classical goal-oriented and
dual-weighted-residual estimators. The elementary center-plus-remainder
identity is not claimed as a universally new theorem. The scoped contribution
is its combination with compressed backward quantum observables, a paired
algorithmic decision interval, and residual-policy allocation.

The empirical rank reversal adds an algorithmic finding: the audited recursive
certificate does not admit a monotone bond ordering, so binary bond search and
purely local greedy allocation can miss cheaper, tighter trajectories. The
equal-work intervention strengthens that boundary: the benefit is
path-dependent and delayed, while the initially proposed onset-local mechanism
is experimentally falsified.

The results establish within-policy feasibility and ordering transfer. They do
not establish global resource optimality, full-COT wall-clock acceleration,
hardware accuracy, interval-arithmetic rounding guarantees, independent-graph
scaling, or a new complexity class.

## Subsequent direction decision

The compression-memory/reset-window line is retained as an ablation and
diagnostic result, but is no longer advanced as the central novelty. The next
frozen cycle instead tested comparison-native tensor simulation. Its full
density-operator M/D claim failed the structural and trace-norm kill criteria,
while a narrower signed diagonal contrast tensor produced a large equal-budget
ranking and certification advantage. See
`results/contrastive_tensor_simulation/REPORT.md`.
