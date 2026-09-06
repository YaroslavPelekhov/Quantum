# Three-row structural reduction and a genuinely uncovered quantum target

Date: 2026-09-06. C008, preregistration `2c4dc25`.
Status: uniform structural lemma and exact finite target reduction.
The target quantum inequality is OPEN; this is not an A-star claim.

## 1. Outcome

The extension is not merely a larger member of C007. The frozen full
3-by-3 root gives a 12-vertex SCF graph `K{S{aSfF~Fln` with 46 stable-set
vertices and exactly 36 facets. Earlier quantum theorems prove 35 facets.
The remaining obligation is precisely

`sum_(nine lights) <P_i>^2 + 2 sum_(three heavies) <P_h>^2 <= 3`.

This row is a genuine full-support facet. Its classical bound is three,
but no quantum upper bound is inferred from the classical hull. Proving
this ONE row would complete all weights on the target; its status remains
unproved until an operator argument or exact quantum certificate is checked.

The target has two disjoint independent triples, so it cannot be an
induced subgraph of any C007 G_m, whose triples all contain one vertex.
It contains an induced five-wheel, ruling out line graphs. Its binary
adjacency rank is six, ruling out an induced embedding into the published
two-qubit G15, whose adjacency rank is at most four. It has no copy/split
pair, complete-join decomposition or clique separator. These are explicit
exclusions of selected known routes, NOT a proof of literature novelty.

## 2. Uniform root lemma

Let E be any finite set of cells (r,c), with r in {0,1,2}, c>=0. Lights
are adjacent when their cells share a row or column. Add a heavy clique
H0,H1,Hc; their light NONneighbors are respectively row 0, row 1, column 0.
Write F(E) for this graph and R+ for the bipartite root with column 0 removed.

**Lemma.** F(E) is claw-free iff the matching number of R+ is at most two.
In that case it is simplicial claw-free, including when column 0 is empty.

Proof. A claw cannot have a light center with three light leaves: its
light neighbors are covered by its row and column cliques. Nor can it
have two heavy leaves, since heavies are adjacent. With one heavy leaf,
the other two leaves must belong to that heavy's light nonneighbor set,
which is a clique. Thus every claw has a heavy center and three light
leaves. The leaves are a root matching disjoint from the center's selector.
For H0 or H1 only two root rows remain, making three leaves impossible.
For Hc exactly the matchings of size three in R+ yield claws. This proves
both directions for arbitrary column count.

If column 0 is occupied, its light clique K is simplicial. A row-0 member
has outside neighbors in row 0 together with H1; a row-1 member has its
row with H0; a row-2 member has its row with H0,H1. Each set is a clique.
When column 0 is empty, temporarily add all three central cells. The
matching condition is unchanged, the enlarged graph is SCF, and deleting
the added vertices preserves SCF componentwise by the existing heredity
property. The heavy K3 also covers the empty-root boundary case. QED.

## 3. What can actually grow: a classical cover reduction

The ordinary bipartite matching/vertex-cover theorem gives a root vertex
cover of size at most two for R+. This use of matching theory is classical.
For completeness, take a maximum matching and alternating reachability
from unmatched row nodes. Choosing unreached rows and reached columns
covers every edge; no augmenting path exists, and exactly one endpoint
per matched edge is chosen. Its size equals the matching size.

This yields the following exhaustive possibilities, allowing overlaps and
degenerate covers of size zero or one:

| Cover form | Consequence for the graph construction |
|---|---|
| Two noncentral columns | At most nine lights and three heavies: order at most 12 |
| One row and one noncentral column | Outside the two designated columns all lights lie in one row and are true clique twins; collapsing them to one representative leaves at most 10 vertices |
| Two rows | The only remaining unbounded matching-pair families |

For the mixed case, all outside-column lights have exactly the same
neighbors outside their clique. Restoring their multiplicity is the known
vertex-splitting operation, not a new quantum composition rule. Its
weighted behavior uses the maximum twin weight. A core still needs its own
all-weight proof; a ten-vertex bound is not automatically covered by the
order-nine theorem.

If the two cover rows are 0 and 1, the graph is an induced subgraph of a
C007 G_m: use one shared column per occupied noncentral column, delete
unused light vertices and the private U,V. Row 2 can occur only at column
0. This is already all-weight proved. Covers {0,2} and {1,2} are symmetric
to each other under exchange of H0,H1, but are NOT assumed equivalent to
the C007 family. They remain a separate uniform proof obligation.

The root lemma and this cover argument, not the finite census, establish
the arbitrary-column structural reduction. They do not classify all SCF
graphs or prove quantum perfection of all F(E).

## 4. Fixed target and exact completeness

Order the full 3-by-3 target lights row-major:

`(0,0),(0,1),(0,2),(1,0),(1,1),(1,2),(2,0),(2,1),(2,2),H0,H1,Hc`.

The complete facet ledger is:

| Route | Facets |
|---|---:|
| Nonnegativity | 12 |
| Previously proved SCF rank inequalities | 20 |
| Previously proved arbitrary-size SCF alpha<=2 support theorem | 3 |
| Full (1-light,2-heavy) row; quantum proof open | 1 |

cdd.gmp discovers the hull with rational H/V roundtrip. A separate
standard-library Fraction edge-clipping algorithm starts from the complete
12-cube and recovers exactly the same 46 stable-set vertices, verifies
facet affine ranks, and proves that the H-system itself implies the cube.
Deleting the full facet creates spurious vertices and is caught geometrically.
The three proper nonrank supports are independently checked to be SCF with
alpha at most two. No additional target hull or beta optimization was run.

Concrete route-exclusion certificates use zero-based indices:

- Disjoint triples: {0,4,8} and {1,5,6}.
- Five-wheel: hub 10, induced rim (0,6,9,11,1). Its neighborhood cannot
  be covered by two cliques, whereas every line-graph neighborhood can.
- Binary rank: independent XOR elimination gives rank six. A two-qubit
  Pauli graph has an adjacency factorization through a four-dimensional
  symplectic form, so every induced subgraph has rank at most four.
- Exhaustive subset/pair checks find no clique separator, copy pair,
  split pair or disconnected complement (complete-join decomposition).

## 5. Falsification controls and literature boundary

Every subset of the frozen 3-by-4 grid was inspected: 4096 graphs,
2120 claw-free/SCF and 1976 with a claw. The noncentral matching-size
histogram is {0:8,1:264,2:1848,3:1976}. Discovery uses neighborhood triples
and bipartite matching; acceptance reconstructs edges and independently
checks four-vertex degree patterns, root matchings, covers and clique
witnesses. It imports neither a graph library nor a numerical solver.

If the three heavy selectors are all three ROWS instead, map each heavy
to the root triangle edge joining the other two row nodes. This represents
the entire construction as a line graph for arbitrary E. The mapping is
also checked on all 4096 grid patterns. That apparent extension is a known
case and is excluded as a research direction.

Nine new tests include corrupted graph/matching/cover/claw, empty and C005
controls, missing target facet, false quantum scope, and binary-rank checks.

Primary-source comparison used [Chapman--Elman--Mann, Definitions 3 and
SCF/heredity statements](https://arxiv.org/html/2305.15625v1) and
[Xu et al., Section III and Appendix A](https://arxiv.org/html/2511.13531v1).
The latter already supplies induced-subgraph, copy/split, join and
lexicographic-product closures and proves the two-qubit G15 case. We use
those established operations as exclusions or conditional reductions, not
as novel mechanisms. Their main-text/appendix copy-versus-split numbering
is inconsistent; the adjacency definitions, not the property number,
determine which operation is used here. A search not finding this target
does not establish priority. No A-star, hardware or simulation-speed claim.

## 6. Reproduction and next gate

```text
python experiments/pauli_fourth_moment_phase0/run_scf_three_row_gate.py
python -S experiments/pauli_fourth_moment_phase0/verify_scf_three_row_gate.py
python -S -m unittest discover -s experiments/pauli_fourth_moment_phase0 -p "test_scf_three_row_gate.py" -v
```

Discovery requires NetworkX and cdd.gmp; independent acceptance is
standard-library only. Five-minute per-script/cube limits remain in place.

C009 should preregister an exact coherent Gram/transfer test for the ONE
remaining target row. A candidate must retain correlations between light
cycle signs and the heavy-row signs; the third light row now occupies
multiple columns, so the old C005 determinant shortcut cannot simply be
copied. Require equality of every universal transfer coefficient, including
vanishing odd powers, and centrality/Hermitian signs. Only after that gate
may the old scalar envelope be reused. No new graph census is needed to
decide this first operator question. General H-SCF and A-star remain open.
