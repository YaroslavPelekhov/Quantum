# Prior-art boundary: event-conditioned output queries

Audit frozen on 2026-09-02 for the Phase-0 screen. This is an adversarial
claim boundary, not an assertion that an exhaustive literature search proves
novelty.

## Binding verdict

The broad proposal

> compile a finite or logically described event into a compact tensor or
> decision diagram, attach it to a quantum circuit, and jointly optimize its
> variable order and contraction schedule

is not a safe novelty claim. Its principal components and several forms of
cross-guidance between representation order and contraction order are already
present in tensor-train, weighted-automata, decision-diagram, weighted model
counting, tensor-network, and quantum-simulation literature.

The only reason to continue is to test whether the **specific pair**
\((C,f)\) admits a non-topological algebraic characterization and an infinite
separation not captured by the known objects below.

## Exact equivalences that are already known

For an event indicator \(f\) and a fixed variable order, the rank of every
prefix/suffix truth-table unfolding is:

- the minimum exact TT/MPS bond at that cut;
- the operator-Schmidt rank of its diagonal event projector;
- the minimum linear weighted-automaton state dimension for the corresponding
  finite Hankel slice.

This follows from standard TT ranks and Hankel-rank minimality, not from a new
event-query theorem:

- [Oseledets, Tensor-Train Decomposition, 2011](https://doi.org/10.1137/090752286)
- [Carlyle and Paz, Realizations by stochastic finite automata, 1971](https://doi.org/10.1016/S0022-0000(71)80005-3)
- [Li, Precup, and Rabusseau, Connecting Weighted Automata and Tensor Networks, 2020](https://arxiv.org/abs/2010.10029)
- [Crosswhite and Bacon, Finite automata for caching in matrix product algorithms, 2008](https://doi.org/10.1103/PhysRevA.78.012356)
- [Bellante et al., finite-language tensor-network compilation, 2026](https://arxiv.org/abs/2602.02698)

For a linear-code event, the logarithm of fixed-order TT rank equals the
matroid connectivity/trellis-state exponent. Optimizing that linear order is
the established matroid pathwidth/trellis-complexity problem:

- [Kashyap, Matroid pathwidth and code trellis complexity](https://arxiv.org/abs/0705.1384)
- [Jeong, Kim, and Oum, constructive FPT algorithms for branch/path/rank width](https://arxiv.org/abs/1507.02184)

Consequently, a circuit-cut term plus a code-event-rank term can reduce to a
direct-sum subspace-arrangement pathwidth. Such a special case cannot support
a new-width claim.

## Closest collisions

| prospective claim | prior collision | consequence |
|---|---|---|
| event/query as an added factor in exact probability evaluation | graphical-model marginalization, weighted model counting, and scalar TN contraction | query-aware elimination in general is old |
| separate diagram and elimination orders | [ADDMC](https://arxiv.org/abs/1907.05000) and [DPMC](https://arxiv.org/abs/2008.08748) | two-order optimization is not new |
| factor structured tensors while building a contraction tree | [FactorTree / graph-decomposition WMC](https://arxiv.org/abs/1908.04381) | representation/tree co-design is occupied |
| generic exact circuit contraction governed by graph width | [Markov and Shi](https://arxiv.org/abs/quant-ph/0511069) | a new name for augmented-network width is insufficient |
| hyperoptimized paths and slicing | [Gray and Kourtis](https://quantum-journal.org/papers/q-2021-03-15-410/) and [Huang et al.](https://doi.org/10.1038/s43588-021-00119-7) | all representations need equal path/slicing optimization |
| path-guided decision-diagram index order | [FTDD Path, 2026](https://arxiv.org/abs/2607.27971) | contraction-to-DD cross-guidance is occupied |
| exact structural-rank cost for schedule/layout search | [Hyper-optimized Quantum Lego schedules, 2026](https://doi.org/10.22331/q-2026-05-05-2092) | semantic/rank-aware cost alone is occupied |
| simulation controlled by an algebraic graph rank | [Quadratic Sums-of-Powers, 2026](https://arxiv.org/abs/2605.29944) | rank-width/FPT and separations from TN/DD widths are direct competitors |
| depth-oriented tensor simulation and postselection | [Matrix Product Evolution, 2026](https://arxiv.org/abs/2608.03472) | a spatial event MPO is not the only relevant representation |
| selected or batched amplitudes | [Pan and Zhang](https://doi.org/10.1103/PhysRevLett.128.030501) | one event network must beat path reuse and batching |

BDD and ZDD variable-order sensitivity is classical:

- [Bryant, 1986](https://doi.org/10.1109/TC.1986.1676819)
- [Minato, 1993](https://doi.org/10.1145/157485.164890)
- [Bollig and Wegener, optimal OBDD order improvement is NP-complete](https://doi.org/10.1109/12.537122)

OBDD layer width counts distinct residual subfunctions, whereas TT/MPO width
is their linear rank. OBDD hardness or size lower bounds do not automatically
transfer to TT rank and may not be cited as if they do.

## Candidate reductions that must be attempted first

Before naming a new event-conditioned width, attempt an explicit reduction to:

1. weighted pathwidth, vertex separation, or cutwidth of an expanded graph;
2. line-graph treewidth/contraction complexity of the augmented TN;
3. edge/vertex congestion and carving width of a contraction tree;
4. project-join trees and query-aware variable elimination;
5. linear rank-width or rank-width of a path-sum/SOP graph;
6. matroid pathwidth or subspace-arrangement pathwidth;
7. optimal TT/ROABP/BDD variable ordering;
8. an ordinary generic optimizer over a finite family of event encodings.

An empirical mismatch with one heuristic is not evidence of non-reducibility.
The burden is a proof or a counterexample to the exact invariant.

## Claims forbidden by this boundary

- first exact finite-event projector;
- first compact event MPO;
- first exact event probability without a statevector;
- first joint qubit/event ordering;
- first representation-aware contraction planning;
- first semantics- or rank-aware schedule cost;
- spectral ordering is optimal;
- reduced input bond guarantees lower internal width;
- a heuristic score is a new complexity parameter;
- an advantage measured only against independent amplitude contractions.

## Narrow admissible A* target

A future claim is admissible only if it supplies all of:

1. a pair-dependent algebraic invariant for \((C,f)\) with a precise
   computational model;
2. matching or nontrivial upper/lower bounds for exact event probability;
3. an explicit infinite family separating it from event-only TT/BDD width,
   circuit-only contraction/rank width, and topology of the augmented network;
4. an efficient exact/FPT or certified approximation algorithm that is not
   ADDMC, FactorTree, FTDD Path, generic TN search, or rank-width DP under a
   change of notation;
5. broad held-out end-to-end evidence against all mandatory Phase-0 baselines;
6. a new exact/certified capability beyond the existing depth-two 55-qubit
   result.

Until then, the strongest safe statement is:

> Known fixed-order Hankel/TT machinery gives a compact exact event projector,
> and the motivating QOBLIB instance shows that event factorization can
> interact strongly with practical contraction feasibility. Whether that
> interaction defines a new general algorithmic regime must be subjected to
> the Phase-0 falsification protocol rather than assumed.
