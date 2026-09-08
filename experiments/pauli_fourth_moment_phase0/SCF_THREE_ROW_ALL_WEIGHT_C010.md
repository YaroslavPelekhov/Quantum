# C010: all-weight closure for every claw-free F(E)

Date: 2026-09-08. Registrations d7408bd and ae59ad0.
Status: computer-assisted theorem with a uniform refinement proof;
external review and novelty/priority remain open.

## Theorem and exact scope

Let E be any finite set of cells (r,c), r in {0,1,2}, c>=0. Join light
vertices when cells share a row or column. Add a clique H0,H1,Hc with
light nonneighbors row 0, row 1 and column 0, respectively. If this graph
F(E) is claw-free, then for any Pauli realization, density matrix rho,
and nonnegative real weights w,

`sum_i w_i Tr(rho P_i)^2 <= alpha(F(E),w)`.

Equality is attainable, hence BETA(F(E))=STAB(F(E)). Vertex count and
weights are unrestricted within this construction. This does not classify
all SCF graphs or prove unrestricted H-SCF. It uses C007, C009 and known
induced-subgraph/splitting closure; it is not a new simulation algorithm.

## 1. The remaining D_m family

Use all three central cells and m noncentral columns each with rows 0,2.
The order of D_m is 2m+6, m>=0. Write a=A0, b=B0, c=C0,
p=H0, q=H1, r=Hc for the six fixed coordinates, and
A=sum_{j=1}^m x_Aj, C=sum_{j=1}^m x_Cj, K=a+b+c+p+q+r.

The fixed core replaces the two noncentral row groups by private vertices
U,V in different columns. Its sorted cell order is
(0,0),(0,1),(1,0),(2,0),(2,2), followed by H0,H1,Hc,
so coordinate order is (a,A,b,c,C,p,q,r). Its STAB polytope has 21 vertices
and 17 facets. The nine positive facets are

```
a+A+q <=1              a+b+c <=1
a+c+q <=1              A+q+r <=1
b+c+p <=1              c+C+p+q <=1
C+p+q+r <=1            a+A+b+c+p+q+r <=2
a+A+c+C+p+2q+r <=2.
```

**Uniform description.** x belongs to STAB(D_m) iff x>=0, its aggregate
vector (a,A,b,c,C,p,q,r) is in this core polytope, and for every j,

`x_Aj+x_Cj+q+r<=1`, `x_Aj+x_Cj+K<=2`.

The displayed description has 4m+15 rows if all coordinate rows and all
core positive rows are retained; redundancies at small m are allowed.
No uniform facet-irredundancy formula is claimed.

## 2. Exact fixed-core endpoint

Lift each core stable incidence vector by z=1_{U,V selected}. The complete
9-dimensional lifted polytope has 21 vertices and 18 facets. Its ONLY
lower-z facets are

`z>=0`, `z>=A+C+q+r-1`, `z>=A+C+K-2`.

Consequently every feasible core marginal admits a distribution with
`z_min=max(0,A+C+q+r-1,A+C+K-2)`.
To see sufficiency, start with any feasible z*, lower it to z_min,
observe that upper-z facets remain satisfied and z-independent facets
are unchanged. Moreover 0<=z_min<=z*<=min(A,C), so the endpoint stays in
the unit cube. Full-cube rational clipping independently verifies the
complete lifted hull, not just validity of the three lower bounds.

## 3. Uniform refinement proof

Necessity of the description follows by mapping any stable set to its
two row-presence flags. The pair clique bound is immediate. For the
second pair row the induced support is the fixed six vertices plus one
matched pair and has independence number at most two.

For sufficiency choose the core distribution with z=z_min and put
`T=A+C-z=min(A+C,1-q-r,2-K)`.
The two pair rows and nonnegativity imply x_Aj+x_Cj<=T for every j.

Construct a transportation table with row masses (x_A1,...,x_Am,T-A)
and column masses (x_C1,...,x_Cm,T-C), where final labels mean absence.
Forbid same-column pairs (j,j) and the absent/absent cell. Each row
forbids one distinct column. The weighted Hall conditions reduce to the
singleton forbidden-pair tests, because any set of at least two rows
sees every column. The matched tests are exactly the inequalities above;
the absent test is 2T-A-C<=T, equivalent to z>=0. Thus a table exists.
For m=0 all row mass is zero and the empty refinement is immediate.

The table has joint-present mass z and single-present masses A-z,C-z.
Within each core presence pattern use its corresponding normalized
table block to choose actual row labels, retaining the conditional
distribution of all six fixed vertices. Zero-mass blocks are unused.
Every vertex in a row has identical neighbors among the fixed vertices,
and the table excludes precisely the forbidden cross-row matching.
Hence this refines the core law to stable sets of D_m with exactly x as
marginals. No assumed quantum joint-event distribution is used here:
this is an ordinary classical STAB completeness proof.

## 4. Quantum justification of every row, for all m

Every independent triple in D_m contains B0 and one noncentral vertex
from each of rows 0,2, in distinct columns. A heavy vertex cannot be in a
triple: H0 has only its row-0 clique as nonneighbors, H1 only B0, and Hc
only the central clique. Light triples need all three rows, and row 1
contains only B0; its central column excludes A0,C0 from such a triple.

None of the nine positive core facets has all of B0,U,V in its support.
After row expansion its support therefore has alpha<=2 for EVERY m.
Every expanded stable set projects to a core stable set, so its weighted
stable bound is at most the listed rhs. SCF heredity and the existing
arbitrary-size alpha<=2 theorem imply its quantum validity. The two
per-column rows also have alpha<=2 supports, so the same argument applies.
The description is complete, so every squared Pauli profile lies in
STAB(D_m). Maximizing any nonnegative linear weight proves the upper
bound. A joint eigenstate of a maximum-weight commuting stable set gives
the lower bound, even with dependencies/signs among Pauli generators.

## 5. From D_m to every claw-free F(E)

C008 proves uniformly that the noncentral bipartite root has matching
number <=2, hence a vertex cover of size <=2. The following cases exhaust
that cover, including zero/one-vertex covers by adding a dummy cover node.

- Two columns: rename them 1,2. F(E) is induced in the full C009 3-by-3
  target. Missing central cells are just deleted vertices.
- One row plus one column: all cells outside that column and column 0
  occupy that row. Their light vertices form true clique twins. Collapse
  that clique to one vertex, map its column to 2 and the covered column
  to 1. The core is induced in C009. Restore multiplicity by known
  vertex splitting (the effective nonnegative weight is the maximum).
- Rows {0,1}: induced in C007's G_m by assigning a shared column to
  each occupied noncentral column and deleting unused cells/private ends.
- Rows {0,2}: induced in D_m by completing both rows and column 0.
- Rows {1,2}: exchange row 0 with row 1 and H0 with H1, then apply D_m.

This is the reason the theorem holds at arbitrary size. The four D_m
hulls are implementation checks, not extrapolation to all m.

## 6. Verification and prior-art boundary

Frozen D_m audit, m=0,1,2,3: orders 6,8,10,12; STAB vertices 12,19,30,45;
facets 11,17,23,27. cdd.gmp discovery and independent Fraction clipping
agree. The lifted core endpoint and expanded descriptions are independently
verified; all template positive supports have alpha<=2. Historical
discovery flags remain false for a uniform theorem, which is supplied by
the analytic argument above.

The [Xu et al. closure operations](https://arxiv.org/html/2511.13531v1)
and classical Hall transportation are reused, not new contributions.
The quantum foundations are the earlier SCF rank/alpha-two results and
the [CEM free-fermion framework](https://arxiv.org/html/2305.15625).
This cycle adds a uniform closure proof for the explicit F(E) construction;
it does not establish that no equivalent theorem exists in the literature.
Novelty and A-star significance remain provisional/unconfirmed.

Reproduce discovery with run_scf_d_family.py and run_scf_d_core.py (cdd.gmp).
Run verify_scf_d_closure.py with python -S for independent acceptance.

Clean reproduction of source commit df6f6c8: both C010 discovery artifacts
regenerated with identical canonical LF hashes. All 59 artifact hashes,
the independent python -S verifier and all 95 SCF tests passed in the
fresh archive (30.660 seconds for the suite). This is same-host clean
reproduction, not external mathematical review.

Canonical SHA-256:

- scf_d_family_c010.json (30933 bytes):
  fe179e2361fd44ecba3358e33a7abe27563ee91cded08903fe893762e757b167.
- scf_d_core_c010.json (6831 bytes):
  08e07ab89cdb8fd0cabb15ca03b327422c75c46a99d9b8e3cdf10d27b79d49aa.
