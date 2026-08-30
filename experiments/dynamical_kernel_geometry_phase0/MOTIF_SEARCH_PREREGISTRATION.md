# Rooted-petal family search: frozen protocol

Frozen after two hand-designed families failed and before motif-search outcomes
were inspected.

## Grammar

Enumerate every labelled rooted petal with 2 or 3 vertices:

- every internal simple graph;
- every nonempty subset of petal vertices adjacent to a shared hub;
- retain only petals connected through the hub;
- attach either one or two degree-one leaves to the hub;
- compose `k=1,2,3` identical petals around the shared hub;
- apply the exact leaf rule to the first hub leaf.

Deduplicate families by their `k=1,2,3` graph6 sequence.  Retain only families
whose lift is bijective on the complete endpoint optimum manifold for every k.

## Frozen screen

- native global schedule, `T in {5,10}`, 120 midpoint steps;
- fit `log(P_reduced/P_original)` against `k`;
- rank by the largest fitted slope across the two frozen times;
- confirm the top 12 families with 480 steps;
- compute `0.1 <= s <= 0.9` gap distortion for confirmed candidates.

A candidate survives only with confirmed slope `>=0.15`, `R^2>=0.95`, absolute
success difference `>=0.25` at `k=3`, and gap distortion `<=1.25` at every k.
It must also differ by at least 20% in log ratio from the disconnected product
of its `k=1` member.  Otherwise the entire rooted-petal grammar is closed.
