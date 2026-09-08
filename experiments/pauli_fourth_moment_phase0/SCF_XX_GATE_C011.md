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
