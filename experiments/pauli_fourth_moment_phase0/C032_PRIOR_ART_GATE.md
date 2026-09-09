# C032: fixed-graph applicability audit, not proof of priority

2026-09-09. Audit C014 against the explicit closure rules in
[Xu et al., arXiv:2511.13531v1 (2025), Section III](https://arxiv.org/html/2511.13531v1).
These include joins, disjoint unions, induced subgraphs, lexicographic
products and twin creation; Theorem 4 covers h-perfect graphs.
Section IX.1 broadly asserts inclusion of claw-free graphs, but the
paper's own anti-heptagon counterexample is claw-free (independence number
two forbids a claw). That sentence cannot serve as a general theorem.
The inspected Section III does not supply a weighted SCF theorem.

[Chapman--Elman--Mann, arXiv:2305.15625v1](https://arxiv.org/html/2305.15625)
provides an SCF free-fermion decomposition. It is already our spectral
input, not a new contribution. A weighted independence bound requires an
additional argument; this audit does not infer it from solvability alone.

## Exact audit to run

Verify the C014 graph/facet and C031 certificate. Check connectivity of
G and its complement; all true/false twin pairs; and whether G has any
proper nontrivial module. For each vertex pair, start its module closure:
an outside vertex distinguishing two current members must belong to
every module containing the current set. Record every forced addition.
If every pair forces all vertices, G is modular-prime, excluding a
nontrivial lexicographic-product last step. Verify addition traces exactly.

The nonuniform full-support facet already excludes h-perfectness. These
tests concern direct last-step applicability ONLY. They do not exclude
induced embeddings into larger known perfect-in-the-quantum-sense graphs,
more complicated combinations of operations, or other papers/theorems.
No claim of first discovery follows from a negative search.

## Exact outcome

C014 and its complement are connected. There are no true or false twins.
For every one of 276 vertex pairs, the recorded forced-addition trace
reaches all 24 vertices. Each addition is checked by two distinct
adjacency statuses to current members. Any module containing the initial
pair must therefore contain every vertex: C014 is modular-prime.
Its verified nonuniform full-support facet rules out h-perfectness.
Three structural tests pass (prime P4, nonprime C4, invalid addition).
C031 exact-six verification was rerun before this audit.

These results exclude direct application of join, union, twin-creation,
nontrivial lexicographic-product last steps and the h-perfect class
theorem. Induced embedding into an arbitrary larger graph is NOT excluded;
being larger than the published 15-vertex example only excludes that
particular host. Classical gear composition is also not excluded.
The 2007/2009 full classical gear theorem needs its own detailed audit.

## Publication consequence

C031 can be described as an exact certificate for a nonuniform
full-support facet on a modular-prime 24-vertex graph. It cannot yet be
described as an all-weight result, a new graph operation, or a first
solution of a published open problem. The next conceptual target is a
quantum composition argument that covers multiple coupled atoms, with
classical composition machinery credited and its quantum extension
proved rather than assumed. Another isolated certificate alone would
not resolve the generalization or A-star significance requirements.
