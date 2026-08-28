# Frozen ansatz-event rank-signature protocol

Frozen before synthetic QAOA execution: 2026-08-28.

## Hypothesis

For a fixed circuit architecture, diagonal event, ordering, and cut, the
DCS-operator rank has a parameter-independent generic signature: almost all
schedule pairs attain the same rank, which can be strictly below the generic
event-incidence matching cap and far below the full-state Schmidt ranks.

This stage tests the phenomenon on newly generated data; no frozen Taiwan/QOBLIB
statevector is used to select graphs, parameters, or thresholds.

## Cohorts

- Development: a 12-node chorded cycle and a seeded 14-node random 3-regular
  graph.
- Held-out transfer: a seeded 16-node Erdos-Renyi graph.
- Ansatz: exact depth-3 MaxCut QAOA from `|+>`, three parameter schedules fixed
  in the runner.
- Orderings: natural and Laplacian spectral.
- Event: all bitstrings with cut value at least `maximum - 1`.
- Cuts: every nontrivial cut.
- Controls: an independently phase-scrambled version of the first schedule pair
  and the capacity-two event matching bound.
- Numerical rank tolerance: `1e-12`.

## Frozen gates

Development supports promotion only if, on all four case/order rows:

1. all three schedule pairs have identical rank profiles;
2. phase scrambling saturates the event matching cap on every cut not capped by
   the left Hilbert dimension;
3. at least one cut has QAOA rank no more than 75% of the cap; and
4. on at least one such cut, each compared state's Schmidt rank is strictly
   larger than half the DCS rank (ruling out the simplest individual-state-rank
   explanation).

Held-out transfer uses the same gates without retuning.  Passing establishes a
reproducible ansatz-event rank phenomenon, not yet a proof of literature novelty
or an end-to-end scalable algorithm.

