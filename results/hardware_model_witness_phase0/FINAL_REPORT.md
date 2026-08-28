# Phase-0 final report: matched hardware noise-model witnesses

## Verdict

**KILL_ASTAR_DIRECTION**.  The direction is killed by: prior_art_core_capability_exists, random_majority_at_90_percent_1024.

This is a simulator-only falsification result.  It does not contain QPU data.

## Exact result

- Enumerated sequences: 87,296
- Identity candidates: 6,048
- Matched equivalence classes: 124
- Matched pair hypotheses: 842,736
- Exhaustive best `P(0)` gap: 0.010490330501
- Declared-model gap for the same pair: 0
- High sequence: `Yp Ym Ym Yp Xp Xm Xm Xp` (`P(0)=0.999999995405`)
- Low sequence: `Xp Xp Ym Ym Xm Xm Yp Yp` (`P(0)=0.989509664904`)
- All frozen matching checks pass: True

## Baselines

- Cyclic-shift gap: 0.005353005096 (51.028% of exhaustive optimum).
- GST-like maximum process-fidelity residual: 0.009041049864
  (0.862 times the matched-pair gap).
- Random 1024-pair median fraction of optimum:
  99.116%; success rate at 90%:
  100.000%.

## Statistical and transfer checks

- Bonferroni-corrected 10,000-shot intervals separated: True.
- Minimum expected shots for corrected separation: 4433.
- Held-out draws preserving ordering: 100.000%.
- Held-out draws retaining at least half the training gap: 53.333%.
- Gate-local depolarizing negative-control gap: 0 by construction and exact channel symmetry.

## Interpretation

The matched constraint can produce a real counterexample to a scalar isolated-gate
model, but the physical capability is not new: GST germs, iterative RB, and
context/model-violation tests already design circuits that amplify precisely
these hidden coherent or contextual errors.  The experiment asks whether the
matching constraint adds a nontrivial search advantage.  The frozen kill gates
above decide that question without relaxing thresholds after seeing results.

Accordingly, no hardware run is authorized from this branch.  The code and
negative result are retained as a reproducible closed-hypothesis record.
