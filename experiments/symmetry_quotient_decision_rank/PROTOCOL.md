# Frozen symmetry-quotient decision-rank protocol

Frozen after the MaxCut generalization failed and before held-out execution:
2026-08-28.

## Hypothesis

For symmetry-rich MIS instances, the generic rank signature of a fixed QAOA
ansatz crossed with the maximum-independent-set event is parameter invariant
and strictly smaller than both the event-incidence matching cap and the
individual-state Schmidt ranks.  The effect should survive a topology and size
transfer but disappear under probability-preserving independent phase
scrambling.

## Frozen design

- Development graphs: chains of 4 and 5 triangles (12 and 15 qubits).
- Held-out graph: a ring of 6 triangles (18 qubits), untouched until development
  passes.
- Each triangle is complete; distinguished vertex zero of adjacent triangles is
  connected by one bridge.
- Orderings: natural and Laplacian spectral.
- Exact depth-15 MIS QAOA with penalty 2, from `|+>`.
- Three fixed four-parameter schedule genomes, giving three state-pair
  comparisons.
- Event: all feasible maximum independent sets.
- Controls: capacity-two event matching cap, individual TT/Schmidt ranks, and
  independent probability-preserving phase scrambling.
- Rank tolerance: `1e-12`.

## Frozen gates

Every row must satisfy:

1. all three QAOA schedule pairs have identical rank profiles;
2. phase scrambling saturates the matching cap on all eligible cuts;
3. at least three eligible cuts have QAOA rank at most 75% of that cap; and
4. at least one deficit cut has both individual Schmidt ranks strictly larger
   than half the comparison rank.

Development requires 4/4 rows.  Only then may the two held-out ring orderings
run, with identical gates and no retuning.  Passing supports a new
symmetry/ansatz/event rank phenomenon, not an unconditional A* novelty claim.

