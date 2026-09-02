# CMRT offline Phase-0 final report

## Verdict

**KILL_CMRT_AS_ASTAR_SOURCE**.  The candidate passes 4 of
10 frozen gates.  It is not authorized for QPU spending and it
does not support an A* claim.

The potentially interesting part is real: approximate representation spread is
strongly associated with the simulator-to-noise-surrogate residual on the held-out
rows (descriptive Spearman **0.780**).  Rows are
clustered within 12 graphs and spread repeats across noise snapshots, so this point
estimate is not an independent-sample significance claim.  The association does
not become a useful selective decision rule.  CMRT accepts only
**27/108 (25.0%)** rows,
below the frozen 50% gate, even though those accepted signs are all correct.  Only
**9/12** held-out graph blocks receive
simultaneous interval coverage, below the required 11/12.

Six binding gates fail: G2_simultaneous_block_coverage, G3_selective_accuracy_and_coverage, G4_matched_error_reduction, G6_each_primary_snapshot, G7_shift_stress, G8_schedule_selection_not_fallback_driven.

## What was tested

- 36 connected, non-isomorphic, maximum-degree-three MIS graphs at 8--13 qubits;
- whole-graph split: 24 calibration and 12 held out;
- depths 2, 3, and 4;
- six approximate simulators per schedule: TT bond caps 2/4/8 crossed with
  natural and degree/BFS qubit orders;
- three primary coherent/readout/depolarizing noise surrogates plus one stronger
  shifted surrogate;
- a graph-block maximum nonconformity score, so all depths and primary snapshots
  are covered jointly rather than treated as independent rows.

The exact-equivalence audit has maximum probability-gap discrepancy
`1.086e-16` across
12 checks.  The full frozen run took
107.5 seconds.

## Held-out comparison

| method | accepted signs | selective accuracy | covered graph blocks | median interval width |
|---|---:|---:|---:|---:|
| `cmrt` | 27/108 (25.0%) | 1.000 | 9/12 | 0.000378299 |
| `exact_noiseless` | 33/108 (30.6%) | 1.000 | 10/12 | 0.000682693 |
| `gate_proxy` | 24/108 (22.2%) | 0.875 | 9/12 | 0.00175784 |
| `nominal_noise` | 42/108 (38.9%) | 1.000 | 10/12 | 0.000404555 |
| `single_high_bond` | 21/108 (19.4%) | 1.000 | 12/12 | 0.00108335 |
| `unscaled_ensemble` | 24/108 (22.2%) | 0.875 | 11/12 | 0.00112821 |

At CMRT's accepted count, both exact-noiseless and nominal-noise baselines have
zero sign error as well, so CMRT's frozen relative error reduction is **0%**, not
the required 25%.  CMRT beats the unscaled and gate-proxy rules only on a smaller
common subset; that does not satisfy the all-baseline claim.

## Binding gates

| gate | outcome |
|---|---:|
| `G10_prior_art_boundary` | PASS |
| `G1_spread_predicts_residual` | PASS |
| `G2_simultaneous_block_coverage` | FAIL |
| `G3_selective_accuracy_and_coverage` | FAIL |
| `G4_matched_error_reduction` | FAIL |
| `G5_not_dominated_by_strong_simulator` | PASS |
| `G6_each_primary_snapshot` | FAIL |
| `G7_shift_stress` | FAIL |
| `G8_schedule_selection_not_fallback_driven` | FAIL |
| `G9_integrity` | PASS |

On the deliberately shifted snapshot, CMRT keeps 25.0% coverage but its accepted
sign accuracy falls to **0.778**, below the
0.80 gate.  This is direct evidence that the calibrated abstention rule is not
robust to the device shift represented by the stress test.

## Schedule and measurement feasibility

Every one of the 108 graph-depth rows used the preregistered fallback.
Exact event probabilities lie between `4.749e-08` and
`5.985e-03`; the median absolute ideal schedule gap is only
`5.835e-05`.  A hardware ranking study built
from these schedules would therefore be shot-starved rather than merely
miscalibrated.  In the separate 4,096-shot audit, Bonferroni-adjusted descriptive
intervals resolve only **1/108**
contrasts (0.9%).

This failure is terminal under the frozen protocol.  Retuning schedules, widening
the event, or lowering the coverage gate after seeing the probabilities would be
a new post-hoc experiment and cannot rescue CMRT.

## Split limitation

The frozen global hash split is leakage-free but poorly stratified:
`{"8": 4, "10": 3, "11": 3, "12": 2}` held-out graphs by size.  It includes no
`n=9` or `n=13` graphs.  The split was not changed after this was discovered;
its limited external validity is another reason not to escalate.

## Real IBM archive smoke audit

The read-only loader recovered two distinct `ibm_boston` jobs from the local
submodule object database:

- `d8k7s4r2d42s73c9smo0`: lambda=1.0,
  105/20000
  raw feasible shots;
- `d8l8g8rqv2lc73865vhg`: lambda=2.0,
  221/20000
  raw feasible shots.

These are two jobs but only one graph and one backend; lambda changes between
them, and transpiled circuits and calibration snapshots are missing.  Their 190
within-job pairs are correlated.  They validate ingestion and provenance only;
they cannot calibrate or test conformal transfer.

## Research interpretation

The negative result is sharper than “we need more data.”  In a noiseless-outcome
offline setting deliberately favorable to detecting the mechanism, representation
spread correlates with residual size but fails to deliver the registered coverage,
matched-baseline advantage, shifted robustness, or shot feasibility.  Therefore
the conjunction does not justify real-server spending.

The broad neighboring space is also occupied by hardware circuit ranking,
capability models, device-transfer noise models, metamorphic quantum testing, and
conformal/selective prediction.  The correct action is to retain CMRT as a
falsified candidate and not rename it into another uncertainty or ranking claim.

## Reproduction

```powershell
python -m pytest experiments/cmrt_phase0 -q
python -m experiments.cmrt_phase0.run_phase0
python -m experiments.cmrt_phase0.finalize_phase0
```

No QPU job is submitted by any command above.
