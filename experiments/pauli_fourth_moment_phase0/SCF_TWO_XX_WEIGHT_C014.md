# C014: one fixed joint weight and one local-sum control

Registered 2026-09-08 after C013's 300-second enumeration timeout and
before computing either weight below. SAME 24-vertex graph, unchanged
labels and edges. No new graph search and no complete hull enumeration.

Target weights: one on every vertex except original vertices 9,10 in
the LEFT XX copy, which receive weight two. This tests lifting one atom's
exceptional C009 weighting through a second atom and a linear connector.

Control weights: also double original vertices 9,10 in the RIGHT copy.
The sum of the two known C011 rows plus the connector edge inequality
gives upper bound seven. Test exact attainability; if attained this control
is already quantum-proved by summation, not a new result.

For both rows enumerate ALL stable sets twice (recursive graph bitsets
versus products of two exhaustive 11-vertex core censuses). Compute the
exact maximum and all tight sets, and verify affine rank of each tight
face in 24 dimensions with rational arithmetic. A target is a full facet
only if that rank is 24 in homogeneous coordinates. Also report exact
GF(2) rank of the adjacency matrix to budget a subsequent Pauli test.
No beta optimization, random starts, QPU or paid runs. Cap 300 seconds.

If the target is not facet-inducing, say so; validity of a classical
supporting inequality does NOT imply a new quantum bound. If it is a
facet, next isolate the operator obligation and compare to existing
geared/g-lifted inequalities before a separate quantum experiment.
The complete stable-set census checks this one row without needing a
complete H-description. No all-weight theorem follows from it.

Prior-art update: the author-hosted Galluccio--Gentile--Ventura technical
report R.661 (2007), Gear Composition of Stable Set Polytopes and
G-Perfection, gives a CLASSICAL full description through H and H with a
subdivided simplicial edge (Theorem 3.1). Its geared/g-lifted rows must
not be claimed as new polyhedral objects. That report has not yet been
audited in full or imported as a quantum premise.
https://www.iasi.cnr.it/~gentile/ClaudioGentileFiles/papers/MOR.pdf
Published metadata: https://doi.org/10.1287/moor.1090.0407

The open problem is quantum compatibility, not finding another name for
a classical facet. H-SCF and A-star remain open, external review pending.
