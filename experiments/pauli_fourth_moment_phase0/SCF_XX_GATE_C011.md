# C011: a published structural atom outside the three-row bound

Registered 2026-09-08, before calculation. Starting source 23ebd3e.
Freeze the eight XX-strip graphs obtained by deleting a subset of vertices
11,12,13 from the 13-vertex construction in Chudnovsky--Seymour,
The structure of claw-free graphs, printed p.6. That complete page has
been visually checked against the extracted text.
Source: https://www.math.u-szeged.hu/~hajnal/courses/PhD_Specialis/Chudnovsky.pdf

Original one-based adjacency: cycle 1-2-3-4-5-6-1;
7:{1,2}; 8:{4,5}; 9:{6,1,2,3}; 10:{3,4,5,6,9};
11:{3,4,6,1,9,10}; 12:{2,3,5,6,9,10}; 13:{1,2,4,5,7,8}.
Each list adds edges to earlier vertices; there are no unspecified edges.

Question: do these published SCF atoms have positive STAB facets not
covered by SCF rank, alpha<=2, order<=9 or the fixed C009 hereditary class?
First check the full graph, its simplicial/claw-free witnesses, and exact
alpha before using any quantum theorem. Independently reconstruct the
edge lists and every stable set. Discover eight rational hulls via cdd.gmp.
Independent Fraction full-cube checks have five-minute limits per graph;
an unfinished check is not acceptance. Max order 13; no beta optimization,
randomness, QPU or paid jobs. The subset order is deletion masks 0,...,7.
If the full graph is all-weight proved, heredity covers its seven variants;
do not count them as seven independent quantum advances.

Controls: original labels retained, the explicit stable quadruple
{3,6,7,8} checked, wrong edges/scope rejected, missing facets checked
geometrically. Uncovered facets are proof obligations, not quantum violations.

Prior-art boundary: XX-strips and strip decompositions are published
classical objects, not newly discovered here. Galluccio--Gentile--Ventura's
2014 Parts I/II give classical W/G-perfection results under stated class
conditions; their abstracts do not license a quantum closure theorem.
Faenza--Oriolo--Stauffer's 2010 Lemma 18 combines classical strip facets
through auxiliary graphs; it does not assert that a Pauli squared profile
admits compatible auxiliary variables. The fetched text contains a proof
sketch, and the repository subsequently denied full PDF rendering; this
source is not used as an accepted quantum proof premise.

Our all-weight F(E) theorem cannot cover an alpha>=4 graph by heredity,
since every F(E) has alpha<=3. That exclusion says nothing about all other
known closure operations or novelty. General H-SCF and A-star remain open.

## Completed outcome: all-weight perfection of the full published XX graph

The full graph has graph6 `LhEM?rcNLhleuo`, 13 vertices, alpha=4, 85 stable
incidence vertices and 33 exact STAB facets. The complete rational hull is
verified independently by Fraction clipping from all 8192 cube vertices.
The sixteen-node graph or a general strip composition is not being claimed.

Facet routes: 13 nonnegativity, 17 SCF rank, two SCF alpha<=2 supports,
and ONE remaining row, in original one-based labels:

`x1+x2+x3+x4+x5+x6+2*x9+2*x10+x11+x12+x13 <=3`.

Its support is induced in C009. The exact map (C009 zero-based vertex to
XX original one-based vertex) is

`0->1, 1->11, 2->6, 3->13, 4->4, 5->5, 6->2, 7->3, 8->12, 10->9, 11->10`.

C009 vertex 9 is omitted. The other nine light weights are one, and
the two remaining heavy weights are two. Independent adjacency comparison
checks BOTH edges and nonedges, without calling the discovery isomorphism
routine. Its weighted stable maximum is three. Therefore C009 proves this
row quantum mechanically by induced-subgraph heredity.

All other positive rows follow from the prior arbitrary-size SCF rank
and alpha-two theorems, with componentwise SCF checked on each support.
Every squared Pauli expectation profile satisfies a complete description
of STAB, so `beta(XX,w)<=alpha(XX,w)` for every w>=0. A joint eigenstate
of a maximum-weight commuting stable set attains the reverse bound.
This proves all-weight perfection, not merely a few sampled weights.

Deleting any subset of vertices 11,12,13 follows at once by heredity.
The eight finite hulls (33,30,30,29,26,23,23,22 facets) are implementation
checks, not eight independent quantum advances. Further induced subgraphs
and true-clique-twin expansions follow by the already published closures.
Arbitrary fuzzy edge changes and arbitrary strip compositions do NOT follow.

The source-defined stable quadruple {3,6,7,8} excludes every hereditary
F(E) graph by alpha, so the full graph is genuinely outside that proved
construction. Nevertheless the new proof is a COROLLARY of C009 and prior
quantum bounds, not a new operator mechanism. No first-discovery claim
about XX graphs or their classical polytope is made.

The independent verifier rechecks C009 itself. Removing the sole C009
facet produces extra rational vertices; these violate the removed row.
That is a geometric negative control, not a physical quantum state.

## Remaining general obstacle

The classical strip decomposition tells us which auxiliary polytopes are
needed, but not why one physical Pauli profile supplies compatible auxiliary
variables across a composed graph. Generic quantum gluing was falsified in
C003; it must not be silently reused. The next targeted question is an
explicit SCF closure of the XX strip, with a separately registered graph
and facet obligation. Proving the atom alone does not prove that closure.
External review, unrestricted H-SCF and A-star novelty remain open.
