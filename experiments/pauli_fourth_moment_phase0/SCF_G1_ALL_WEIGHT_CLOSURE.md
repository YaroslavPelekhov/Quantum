# Exact all-weight closure of the first rectangular-Gram graph

Date: 2026-09-06. C006, preregistration `da1f93d`.
Status: exact computer-assisted theorem using the previously proved C005
and order-nine results; pending external mathematical and novelty review.
This is one ten-vertex graph, not all order-ten SCF graphs or all G_m.

Subsequent C007: [all weights are proved for every G_m](SCF_UNBOUNDED_ALL_WEIGHT_FAMILY.md)
by a uniform refinement argument. The present C006 certificate remains
the original one-graph result and an equality control for the later audit.

## Theorem

Let G_1 be the graph defined in [C005](SCF_RECTANGULAR_GRAM_FAMILY.md), in
the order A0,B0,A1,B1,Z,U,V,H0,H1,Hc. Its graph6 is `IrqaaulLw`; it is
isomorphic to the stored frontier graph `ICXmtizr_` under the already
verified map `(7,5,0,9,2,3,1,4,8,6)`.

For every Pauli realization of G_1, every density matrix rho, and every
nonnegative real weight vector w, including zero weights,

`sum_i w_i Tr(rho P_i)^2 <= alpha(G_1,w)`.

The bound is attainable. Equivalently `BETA(G_1)=STAB(G_1)` and G_1 is
hbar-perfect. The important strengthening over C005 is the quantifier
**every weight vector**, not another beta sample for the original weights.

## Complete facet ledger

The graph has exactly 34 independent-set incidence vectors. Its full
ten-dimensional STAB polytope has exactly 27 primitive facets:

| Kind | Number | Quantum proof |
|---|---:|---|
| Nonnegativity | 10 | Squares are nonnegative |
| Rank facets | 14 | Existing induced-SCF rank theorem |
| Proper-support nonrank facets | 2 | Existing all-weight SCF theorem through order nine; each support has seven vertices |
| Full-support nonrank facets | 1 | C005 signed rectangular Gram theorem |

The two proper-support inequalities, in the stated vertex order, are

`x0+x2+x4+x5+x7+2*x8+x9 <= 2`,

`x1+x3+x4+x6+2*x7+x8+x9 <= 2`.

The full-support inequality is

`x0+x1+x2+x3+x4+x5+x6+2*x7+2*x8+2*x9 <= 3`.

Every row, not merely a representative per orbit, is stored in
`scf_family_facet_closure.json`. The verifier checks all independent sets,
the exact support graph of each positive facet, and a matching theorem
route. No graph is accepted as SCF solely because a stored flag says so.

For an arbitrary state, the squared profile satisfies all 27 inequalities,
and therefore belongs to STAB by the exact completeness argument below.
Maximizing w.x over STAB yields the upper bound for every nonnegative w.
A common eigenstate of a maximum-weight commuting independent set attains
at least alpha(G_1,w); the upper bound forces equality. This reasoning does
not assert that every point of STAB is itself a single-state squared profile.

## Independent completeness, not just valid sampled facets

Discovery enumerates all stable sets and uses cdd.gmp exact rational
double description, followed by an exact H-to-V roundtrip with no rays,
fractional vertices, extra vertices or missing incidence vectors.

Acceptance uses a separately implemented standard-library Fraction
algorithm. It starts with all 1,024 vertices of the unit cube and inserts
the listed halfspaces one by one. At each step:

1. Keep old vertices on the feasible side, including those exactly on the cut.
2. Two distinct old vertices are adjacent precisely when the normals of
   their common active constraints have rank n-1. Rank is computed over Q.
3. Intersect every crossing edge with the new hyperplane using rational
   interpolation. Recompute its active constraints, allowing degeneracy.

Why this proves completeness: a new vertex of a full-dimensional polytope
cut by one halfspace lies either at an old feasible vertex or on a crossing
old edge. More generally, its minimal old face has dimension at most one,
since adding one active hyperplane can lower face dimension by at most one.
The common-active-constraint rank determines the dimension of the smallest
face containing two vertices; rank n-1 therefore detects exactly the edges.
Induction from the complete cube proves the whole final vertex set, rather
than merely verifying supplied candidate vertices. Every intermediate body
contains 0 and all unit vectors, so it remains full-dimensional.

The verifier separately checks that the listed H-system implies the cube
bounds: all nonnegativity inequalities are present, and for each coordinate
i there is a positive row with w_i=rhs and every w_j>=0, giving x_i<=1.
Thus intersecting with the initial cube does not hide unbounded rays or
missing regions. Finally, the resulting vertex set is exactly the 34
enumerated stable vertices. Validity and affine dimension nine of each
listed supporting hyperplane are independently checked as well.

## Adversarial controls and an implementation correction

Deleting the C005 facet, while retaining the other 26, produces three
additional rational vertices. One is

`(1/4,1/4,0,0,1/4,1/4,1/4,1/4,1/4,1/2)`.

It obeys every retained inequality but has value `13/4 > 3` on the removed
one. Both exact algorithms recover all three extras. This is a classical
polyhedral witness, NOT a quantum state or a violation of the quantum bound.
It tests actual completeness: the missing-facet regression fails because
of an extra vertex, not a mismatched hash or expected facet count.

The initial new discovery classifier incorrectly searched only maximal
cliques for a simplicial clique. Both seven-vertex supports exposed this
mistake. Their simplicial cliques are nonmaximal; the separate all-subsets
checker accepted them correctly. The discovery search now enumerates all
cliques, as required by the definition. This was an error in new C006 code,
not a counterexample to SCF heredity. The earlier order-nine classifier
already used all cliques and was not affected. A regression verifies that
every simplicial clique in these two supports is strictly extendible.

Other controls cover P4 and C5 polytopes, rational intersections, retained
boundary vertices, wrong graph, wrong coefficient, duplicate row, and an
incorrect quantum proof route. The C006 suite has ten tests; the combined
SCF suite has 55. No numerical SDP, beta optimization, QPU or paid compute
was needed for this cycle.

## Prior art, limits and next gate

The definition of hbar-perfectness and the BETA/STAB support-function
framework are from [Xu et al., Section II](https://arxiv.org/html/2511.13531v1#S2).
SCF structure, including the definition of simplicial clique and heredity,
is from [Chapman--Elman--Mann, Sections II and IV.3](https://arxiv.org/html/2305.15625v1).
Facet enumeration, edge clipping, and facet-wise implication are established
polyhedral tools. No new optimization algorithm is claimed here.

This cycle extends a checked quantum theorem from one weighting to all
weights on one graph. The all-m all-weight statement, unrestricted H-SCF,
graph-family priority, and A-star novelty remain unconfirmed. The two
original frontier files and C005 artifact retain their historical scopes.

The next concrete hypothesis is that every nonrank facet of G_m either
has support of independence number at most two or is the C005 full-support
weighting, up to positive scale and automorphism. Rank facets and the first
kind are already quantum-controlled at arbitrary size; C005 controls the
second. This would establish all-weight perfection of every G_m IF proved.
It is a conjecture, not an inference from G_1. Before enumerating more
family members, audit classical gear/clique-family facet descriptions and
freeze a bounded falsification protocol. Require a uniform proof for m,
not merely another successful list of sizes.

## Reproduction

From the repository root, independent verification needs only Python's
standard library and committed certificates:

```text
python experiments/pauli_fourth_moment_phase0/verify_scf_family_facet_closure.py
python experiments/pauli_fourth_moment_phase0/verify_scf_rectangular_gram_bridge.py
python -m unittest discover -s experiments/pauli_fourth_moment_phase0 -p "test_scf*.py" -v
python experiments/pauli_fourth_moment_phase0/verify_scf_research_bundle.py
```

The full combined suite also uses the dependencies of preceding cycles.
Regenerating the C006 discovery artifact requires NetworkX and pycddlib
with its **cdd.gmp** exact backend, not floating-point cdd:

```text
python experiments/pauli_fourth_moment_phase0/run_scf_family_facet_closure.py
```

Run regeneration in a clean archive and compare the canonical UTF-8/LF
artifact hash. This does not require any numerical discovery cache.
