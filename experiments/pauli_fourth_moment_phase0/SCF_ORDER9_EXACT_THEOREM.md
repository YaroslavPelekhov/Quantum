# Exact weighted Pauli uncertainty on SCF graphs through order nine

Date: 2026-09-05. Status: computer-assisted theorem, with explicit exact
certificates; pending external mathematical and novelty review. This is not
a proof of the unrestricted weighted SCF conjecture or an A-star claim.

## Statement

Let `P_1,...,P_n` be Hermitian Pauli observables whose anticommutation graph
`G` is simplicial claw-free (SCF), component by component, and `n<=9`.
For every density matrix `rho` and every nonnegative real vector `w`,

`sum_i w_i Tr(rho P_i)^2 <= alpha(G,w)`.

The bound is attainable, so `beta(G,w)=alpha(G,w)` for every such weight.
Equivalently, the convex squared-expectation body satisfies
`BETA(G)=STAB(G)`: these SCF graphs are hbar-perfect.

This is an all-weights, all-states statement on a finite graph class, not a
claim that checking 128 sampled weight vectors proves an arbitrary graph
class. Completeness of the facet enumeration is essential.

## Proof architecture and exact census

1. The existing free-fermion argument proves every induced-subgraph rank
   inequality for every SCF graph, at arbitrary order. It uses the quadratic
   coefficient of the Chapman--Elman--Mann transfer polynomial. See the
   theorem and proof audit in [the theory note](POSTFREEZE_THEORY_NOTE.md).
2. The line-graph matching-polytope argument in that note covers all weights
   on line graphs, at arbitrary order.
3. McKay's hash-pinned connected order-nine universe contains 261,080
   graphs. The SCF classifier selects 4,308, including 710 line graphs and
   3,598 non-line graphs. The connected-universe and claw-free count controls
   match the source counts; the source hash is stored in the census artifact.
4. For **every** one of those 3,598 non-line graphs, the exact `cdd.gmp`
   double-description backend enumerates STAB from the complete set of
   independent-set incidence vectors. It finds 56,792 facets: 32,382
   nonnegativity, 23,709 rank, and 701 nonrank facet occurrences.
   All 3,598 exact H-to-V reverse conversions reconstruct the original
   incidence vectors with no rays, extra vertices, or missing vertices.
   In total, 98,304 stable-set vertices participate in these checks.
5. Exact weight-preserving graph isomorphism maps the 701 nonrank
   occurrences to the same 128 support types as the earlier exploratory
   floating-point census, with exactly the same multiplicity for every type.
   No tolerance test or floating-point hull is used by this final census.
6. The certificate ledger below proves every nonrank type. Together with
   nonnegativity and rank constraints, this proves that every squared
   profile lies in STAB. A common eigenstate of a maximum-weight independent
   set supplies the reverse inequality for beta.

| Mechanism | Representative indices | Types |
|---|---|---:|
| Clique join plus SCF rank theorem | listed in `scf_order9_facet_reduction.json` | 115 |
| Full scalar/KKT/boundary proof | 27 | 1 |
| One-hole envelope | 5, 7, 9, 33 | 4 |
| Collapsible two-hole envelope | 34, 48 | 2 |
| Commuting Gram triangle | 26 | 1 |
| Signed-sector square certificates | 44 | 1 |
| New transfer-polynomial Gram completions | 15, 23 | 2 |
| New exact rational state-moment duals | 24, 25 | 2 |
| Total | all 128 types, none left numerical | 128 |

To include smaller connected graphs, repeatedly duplicate a vertex as an
adjacent true twin until order nine. This preserves claw-freeness: two true
twins cannot both be leaves of an induced claw, or be its center and a leaf;
a claw using just one twin would give an original claw. It also preserves a
simplicial clique `K`. If the duplicated vertex is in `K`, include its twin
in `K`; otherwise leave `K` unchanged. Each required outside neighborhood
remains a clique. The original graph is induced in the extension, so the
order-nine bound restricts to it by zero weights outside the original graph.
Disconnected graphs follow by summing the inequalities for their components.

## New Gram completions: types 15 and 23

Write `p_i=a_i^2`, with `a_i>=0`; original amplitude signs can be absorbed
into the Pauli generators. Let `L` and `H` be the light and heavy squared
amplitude masses. The variational normalization is `2L+H=1` because the
facet weights are respectively `1/2` and `1`.

For type 15 the light vertices are `{0,1,2,3,4,5,7}` and the heavy vertices
are `{6,8}`. Use

```text
B15 = [ a7   a3   a0 ]
      [ a2    0  -a4 ]
      [ a5  -a1    0 ].
```

For type 23 the light vertices are `{0,1,2,3,5,6}` and the heavy vertices
are `{4,7,8}`. Use

```text
B23 = [ a3   a0    0 ]
      [ a1  -a6    0 ]
      [ a5    0   a2 ].
```

In both cases `M=B B^T>=0`, `tr M=L`. Direct universal-algebra expansion
of `T(u)T(-u)` and the operator triangle inequality give, in every sector,

`e_2 <= e_2(M)+H lambda_max(M)`, `e_3 <= det(M)`.

For type 15, the heavy branch scores are squared norms of column 0 and row
0 of `B15`. For type 23, heavy vertex 4 is column 0, and the heavy pair
`{7,8}` is the principal block of rows/columns `{1,2}` of `M`. Rayleigh
quotients and principal-submatrix interlacing therefore prove the displayed
heavy bound without solving a nonconvex amplitude optimization.

The determinants are

`det B15 = -a0*a1*a2-a1*a4*a7-a3*a4*a5`,

`det B23 = -a0*a1*a2-a2*a3*a6`.

Importantly, the independent transfer expansion detects nonscalar sixth-order
terms in precisely these two residuals. Type 15 includes a six-letter Pauli
word, so it would be incorrect to assume that `e_3` contains only independent
triple squares or four-hole terms. The sum of the absolute coefficients is
exactly the displayed determinant squared, in each case.

Let `x,y,z` be the three eigenvalues of `M`, with `y` largest. Then
`x+y+z=L` and the already established spectral crossing argument reduces
the beta bound to

`xy+xz+yz+(1-2L)y+2sqrt((3/2)xyz) <= (1/4+L/2)^2`.

For fixed `L,y`, increasing `xz` increases the left side, so replace
`x=z=(L-y)/2`. Set `y=s^2/6`. The difference becomes exactly

`(s-1)^2 (12L+s^2+6s+3)/48 >= 0`.

Thus both new types have `beta=alpha=3/2`. The committed script checks
the entire transfer expansion independently of the older word-rewriting
implementation, both Gram identities, all heavy branches, and the envelope.

## Exact state-moment duals: types 24 and 25

Numerical facial reduction was used only to discover candidate duals of the
already published state-polynomial relaxation. This hierarchy is prior art;
we do not claim to have invented it.

The final certificates contain rational matrices `B,Q` and a fully explicit
74-element basis `f` of state-polynomial operator words. They satisfy

`3/2 - sum_i w_i <P_i>^2 = Re <f^* (B Q B^T) f>`.

For type 24, `Q` is 42-by-42; for type 25, it is 40-by-40. In both cases,
the verifier constructs an exact rational factorization `Q=L D L^T`, checks
that **every** pivot of `D` is strictly positive, and checks every coefficient
of the displayed polynomial identity exactly. Consequently `B Q B^T` is
positive semidefinite and the right side is nonnegative in any state.

The verifier independently derives Pauli product signs from inversion parity,
checks the graph6-to-edge binding, checks Hermiticity of scalar expectation
factors, and enumerates the stable-set lower bound exactly. It imports no
numerical solver and needs no discovery cache. Approximate decimal pivot
values in the result are informational only, not proof tolerances.

Nine regression tests pass. Negative controls corrupt the graph, a weight,
positive definiteness, and the polynomial identity; all are rejected. The
positive-definite but wrong-identity control ensures that checking positivity
alone is not enough for acceptance. These tests are not a proof-assistant
formalization or external peer review.

## Corrections retained in the record

The type-44 relation audit previously mixed oriented cycle words with a
sorted target word. In the stated oriented convention **all three** pairwise
products have sign minus, including `h0*h2=-h1`. The corrected audit divides
by the target-word phase. The used constraint `s0*s1*s2=-1` and both
square-certificate branches were already correct; the beta conclusion does
not change. This is now covered by a dedicated regression test.

The initial Qhull census was exploratory, not an exact completeness proof.
Its final replacement is the GMP-rational enumeration with exact H/V
roundtrips. Historical result files keep their stage-specific status, while
the current summary and this note state the completed result.

The artifact manifest previously hashed Windows CRLF bytes, which differed
from Git's LF blobs. The manifest now explicitly hashes JSON as UTF-8/LF and
binary artifacts byte-for-byte. A scoped Git attribute preserves LF for these
JSON files. The bundle verifier checks both working files and staged Git
blobs, so the published files can be checked independently of host platform.

## Reproduction

Run from the repository root. Pure exact verification of each new dual needs
only Python and SymPy (`1.13.1` used here):

```text
python experiments/pauli_fourth_moment_phase0/rationalize_scf_dual.py --verify results/pauli_fourth_moment_phase0/scf_exact_dual24.json
python experiments/pauli_fourth_moment_phase0/rationalize_scf_dual.py --verify results/pauli_fourth_moment_phase0/scf_exact_dual25.json
python -m unittest discover -s experiments/pauli_fourth_moment_phase0 -p test_scf_exact_completion.py -v
python experiments/pauli_fourth_moment_phase0/verify_scf_research_bundle.py
```

The complete exact polyhedral rerun additionally uses `pycddlib==3.0.2`
(`cdd.gmp`, not `cdd`) and NetworkX (`3.5` used here):

```text
python experiments/pauli_fourth_moment_phase0/run_scf_exact_facet_census.py --input results/pauli_fourth_moment_phase0/scf_order9_census.json --facets results/pauli_fourth_moment_phase0/scf_order9_facet_census.json --output results/pauli_fourth_moment_phase0/scf_exact_facet_census.json
```

The four new mathematical certificates are `scf_gram_completion.json` (two
types), `scf_exact_dual24.json`, and `scf_exact_dual25.json`. Rational dual
recovery can be rerun from the committed discovery caches with `--cache`
and `--output`; `python-flint==0.9.0` is optional SymPy acceleration.
Numerical discovery additionally used NumPy 2.2.6, SciPy 1.16.3, CVXPY 1.9.2,
CLARABEL and SCS. The 11.5 MB of discovery caches are provenance, not trusted
inputs to standalone verification.

## Novelty boundary and the next general gate

The closest work already defines hbar-perfectness, graph closure rules,
state-polynomial relaxations, and numerical classifications through order
nine: [Xu et al., arXiv:2511.13531](https://arxiv.org/html/2511.13531v1).
Its Section IX.1 also informally claims an inclusion involving claw-free
solvability. Read literally for all claw-free graphs, that statement conflicts
with its own anti-C7 counterexample. We have not found a precise weighted SCF
theorem there, but this passage is an important anticipation risk, not proof
that our conceptual connection is entirely new.

The free-fermion structure itself is
[Chapman--Elman--Mann's theorem](https://arxiv.org/abs/2305.15625).
The new contribution candidate is the exact weighted certification and the
Gram constructions, not hidden-free-fermion solvability or the SDP hierarchy.
The present proof also depends on our preceding analytic type-27 argument;
it is not 128 independently formalized proof-assistant certificates.

The next serious gate is a size-independent weighted theorem, preferably a
graph-composition rule with an operator-level proof. Classical descriptions
of claw-free stable-set polytopes do not automatically apply to squared Pauli
expectations. Simply enumerating more small graphs, applying known graph
closures, or obtaining a tighter numerical upper bound is insufficient to
claim this gate has passed. Quantum hardware is not the decisive test for
this theorem; no paid cloud or QPU jobs were submitted.
