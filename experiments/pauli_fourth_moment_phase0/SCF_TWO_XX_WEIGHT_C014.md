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

## Completed exact structural outcome

Graph6: `WhENH}vZuo???@??b@GoP?@C?FG?Bw?J[?B]EBkE?O???oB`.
There are 2167 stable sets and alpha=6. The target row has exact bound
six and 88 tight sets with homogeneous rank 24: it IS a full facet.
In zero-based indices it is `sum(x_i for i=0,...,23)+x6+x7 <= 6`.
The second row has bound seven, eight tight sets and homogeneous rank
six, so is NOT a facet. Its quantum bound follows by summing the two
C011 atom rows and `x22+x23<=1`, and its stable optimum attains seven.

Both maxima and ALL tight sets match the independent exhaustive-core
product verifier. Fraction elimination independently confirms both ranks.
The Pauli binary adjacency rank is 14; a seven-qubit standard realization
is constructed and every pairwise (anti)commutation sign is checked by
binary symplectic products. This is a budget for simulation, not hardware.

The target's full facet status excludes proving this row solely by a
nonnegative sum of valid proper-support linear inequalities, including
induced C009/C011 rows and rank rows. Indeed any such representation of
a facet would require each positive summand's hyperplane to contain all
88 tight stable vertices; their affine span has codimension one, so each
summand must be the same full-support facet up to positive scaling.
That does not exclude a nonlinear reduction, known graph operation, or
the published geared/g-lifted machinery; priority is NOT established.

The precise quantum obligation is now `sum_i <P_i>^2 + <P6>^2 + <P7>^2
<=6` for the stated anticommutation graph, with arbitrary real states and
all allowed sign/central relations. It remains OPEN. No all-weight or
unrestricted SCF theorem follows. C015 must attack this fixed row rather
than resume a larger facet census.
