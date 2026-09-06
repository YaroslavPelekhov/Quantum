# All-weight Pauli uncertainty for the unbounded rectangular family

Date: 2026-09-06. C007, registrations `8a2d0f5` and `68d5ac8`.
Status: computer-assisted theorem with a uniform combinatorial proof and
an independently verified fixed-size rational certificate. External
mathematical review and quantum novelty/priority assessment remain open.

## 1. Theorem and what changed

For every integer m>=0, let G_m be the SCF anticommutation graph of
[C005](SCF_RECTANGULAR_GRAM_FAMILY.md), of order 2m+8. For every Pauli
realization, every density matrix rho and every nonnegative real vector w,

`sum_i w_i Tr(rho P_i)^2 <= alpha(G_m,w)`.

The bound is attainable, so `BETA(G_m)=STAB(G_m)` for every m. Thus the
family is hbar-perfect for ALL weights, including vectors with zero entries.
C005 proved only one fixed full-support weighting. C006 completed all
weights only at m=1. The present proof removes both restrictions together.

This does not prove unrestricted weighted SCF perfection, classify all
SCF graphs, or establish A-star novelty. It also does not introduce a new
polyhedral, flow, or simulation algorithm.

## 2. Explicit uniform polyhedral description

Use light vertices A0,B0,A1,B1,...,Am,Bm,Z,U,V and heavy vertices H0,H1,Hc.
Lights in a common row or column anticommute; the occupied root cells are
(0,j),(1,j) for j=0,...,m, plus (2,0),(0,m+1),(1,m+2). The heavies form a
clique; their light NONneighbors are row 0, row 1, and column 0 respectively.

For a nonnegative vector x, abbreviate

`a=x_A0, b=x_B0, c=x_Z, p=x_H0, q=x_H1, r=x_Hc`,

`A=x_U+sum_(j=1)^m x_Aj, B=x_V+sum_(j=1)^m x_Bj`,

`C=a+b+c+p+q+r`.

Let y=(a,b,c,A,B,p,q,r). Then the following conditions are necessary and
sufficient for `x in STAB(G_m)`:

1. Every coordinate of x is nonnegative.
2. y belongs to STAB(G_0), whose positive inequalities are listed below.
3. For every j=1,...,m,
   `x_Aj+x_Bj+r<=1` and `x_Aj+x_Bj+C<=2`.

The fifteen positive inequalities for STAB(G_0) are:

| Kind | Left sides, each bounded by the stated right side |
|---|---|
| Nine clique bounds, rhs 1 | a+b+c; a+c+q; a+A+q; b+c+p; b+B+p; c+p+q; A+q+r; B+p+r; p+q+r |
| Three rank bounds, rhs 2 | C+A; C+B; C-c+A+B |
| Two nonrank bounds, rhs 2 | a+c+A+p+2q+r; b+c+B+2p+q+r |
| C005 bound, rhs 3 | a+b+c+A+B+2(p+q+r) |

With nonnegativity and the per-column constraints, this is a description
by 4m+23 inequalities. The proof below establishes completeness for every
m, not just a formula fitted to a finite list of facet counts. We need
neither a uniform irredundancy claim nor a formula for the number of facets
to deduce the quantum theorem. At the four audited sizes, all listed rows
are indeed facets.

## 3. Fixed-core joint-event lemma

In a probability distribution over stable sets of G_0, let z be the
probability that both aggregate vertices U,V are selected. For a fixed
marginal y in STAB(G_0), the exact minimum possible joint probability is

`z_min=max(0,A+B+r-1,A+B+C-2)`.

This finite lemma has an exact certificate. Lift each of the 22 stable
incidence vectors of G_0 with the binary coordinate `1_{U,V in S}`. The
resulting nine-dimensional polytope has 24 facets. Exactly three of them
are lower bounds on z: the three expressions in the maximum above.
Every other facet is an upper bound on z or independent of z.

Discovery uses cdd.gmp rationals. A separate Fraction-only implementation
starts from all 512 vertices of the nine-dimensional cube and clips every
halfspace using exact edge ranks. It recovers precisely the 22 lifted
vertices; every supporting row has the required affine rank. In this
lemma, equality of the H-system INSIDE the cube suffices, since both
marginals and joint probabilities lie in [0,1].

To deduce the formula, first take any stable-set decomposition of y. It
supplies some feasible z*. Lower z* to the displayed z_min. All lower-z
inequalities hold by construction, all upper-z inequalities remain true,
and zero-z inequalities are unchanged. Moreover `0<=z_min<=z*<=1`, so the
point stays inside the cube and hence inside the exactly verified lifted
polytope. In particular `z_min<=min(A,B)` and `1-A-B+z_min>=0`.

## 4. Uniform refinement: why the graph size no longer matters

Collapse the clique {A1,...,Am,U} to U and {B1,...,Bm,V} to V. Every
vertex in each clique has the same neighbors outside these two cliques.
Between the cliques the only edges are the matching pairs Aj-Bj. A
stable set of G_m therefore projects to a stable set of G_0. This proves
necessity of the core condition; the two per-column bounds are respectively
a clique inequality and a rank-two induced-support inequality.

For sufficiency, suppose all the displayed constraints hold and choose
a core distribution with joint mass z=z_min. Write

`T=A+B-z=min(A+B,1-r,2-C)`.

T is the probability that at least one row is selected. The original
coordinates specify how much mass each row label must receive. Remove
the absent/absent mass 1-T temporarily. On the remaining mass T construct
a transportation table with:

- row supplies x_A1,...,x_Am,x_U and an absent-row supply T-A;
- column demands x_B1,...,x_Bm,x_V and an absent-column demand T-B;
- forbidden cells (Aj,Bj), and the absent/absent cell;
- all other cells allowed, including the private pair (U,V).

Both total supply and total demand equal T. Each row forbids at most one
column, and these forbidden columns are distinct. Consequently any set
of two or more row labels has all column labels as neighbors. The weighted
Hall conditions for a transportation flow reduce to singleton conditions:

`x_Aj+x_Bj<=T` for j=1,...,m,

and `(T-A)+(T-B)<=T`, the latter equivalent to z>=0. A row with no forbidden
column has the trivial bound that its supply does not exceed total mass.
These conditions are sufficient by the ordinary max-flow/min-cut theorem:
every cut is exactly a supply-versus-neighbor-demand condition. No new
matching or flow theorem is asserted.

All singleton conditions hold: x_Aj+x_Bj<=A+B by nonnegativity, and the two
registered per-column inequalities bound it by 1-r and 2-C as well. Thus
a feasible table exists. Its joint non-absent mass is A+B-T=z, the A-only
mass is A-z, and the B-only mass is B-z.

Use the table's conditional label distributions for each of the four
aggregate presence patterns in the chosen core distribution, independently
of the remaining core vertices given that pattern. This preserves every
specified marginal and all core adjacencies. It never chooses the forbidden
pair Aj,Bj, so every refined outcome is a stable set of G_m. The resulting
distribution has marginal x, proving x in STAB(G_m).

Zero-probability presence patterns need no conditional distribution. T=0
is the empty-row case. Zero supplies, private-label masses, and equality
in the Hall conditions are covered by the same non-strict inequalities.
The argument is valid for real probabilities, not just rational samples.

## 5. Quantum validity of every inequality

The classical refinement argument is used ONLY after the quantum bounds
are established. It does not assume that arbitrary classical local
profiles arise from a quantum state, and it is not the generic quantum
separator-gluing rule falsified in C003.

The C005 uniform construction proves that every G_m is SCF and that its
only independent triples contain Z and one noncentral vertex from each
row, in distinct columns. Thus a support obtained by expanding a core
facet can contain a triple only if the core support contains all of Z,U,V.
The exact G_0 facet table shows that ONLY the full C005 inequality has
all three. Every other positive core facet therefore has support of
independence number at most two, for every m.

Such induced supports are SCF componentwise and obey the already proved
[size-independent all-weight alpha<=2 theorem](SCF_GENERALIZATION_THEOREMS.md).
Their weighted stable bound equals the core bound: stable sets project
to core stable sets, while choosing the private representatives U,V
embeds every core stable set. This proves every expanded core inequality
quantum-mechanically, apart from the full one, which is precisely C005.

The per-column clique bound is elementary. The support of the second
per-column bound is {A0,B0,Z,H0,H1,Hc,Aj,Bj}. It has independence number
at most two: its only two noncentral row candidates Aj,Bj are adjacent.
SCF heredity and the same alpha<=2 theorem prove that bound as well.

Hence every squared Pauli profile satisfies the complete classical
description of Section 2, so lies in STAB(G_m). Its support function at
any nonnegative w is at most alpha(G_m,w). A common eigenstate of a
maximum-weight independent set attains the reverse bound. This proves
the theorem for all weights, mixed/pure states, Pauli signs and all m.

The registered R_m also follows: every facet of a full-dimensional
polytope described by finitely many halfspaces is proportional to one of
its defining nonredundant rows. All our positive rows except C005 have
alpha<=2 support. This is a uniform proof, independent of whether every
candidate row remains irredundant at all m.

## 6. Falsification audit and reproducibility

| m | Graph order | Stable vertices | Exact facets | Nonrank alpha<=2 | Other nonrank |
|---:|---:|---:|---:|---:|---|
| 0 | 8 | 22 | 23 | 2 | C005 only |
| 1 | 10 | 34 | 27 | 2 | C005 only |
| 2 | 12 | 50 | 31 | 2 | C005 only |
| 3 | 14 | 70 | 35 | 2 | C005 only |

Every hull has an exact cdd.gmp roundtrip and independent complete Fraction
clipping. The m=1 rows equal the C006 artifact exactly. These are finite
implementation audits, not the reason the uniform theorem holds.

Negative tests remove a core lower-z facet and an order-twelve full facet;
each fails geometrically because of extra vertices. Other tests corrupt
the endpoint, joint-event vertex, or scope claim. Exact flow controls
cover zero mass, private labels, saturated Hall constraints and an
incompatible same-column pair. A C7 control validates the MIR formula.
The C007 test file adds fourteen tests to the preceding 55.

```text
python -S experiments/pauli_fourth_moment_phase0/verify_scf_uniform_facet_gate.py
python -S experiments/pauli_fourth_moment_phase0/verify_scf_core_refinement.py
python -S -m unittest discover -s experiments/pauli_fourth_moment_phase0 -p "test_scf_core_refinement.py" -v
python -m unittest discover -s experiments/pauli_fourth_moment_phase0 -p "test_scf*.py" -v
```

Discovery uses NetworkX and the exact cdd.gmp backend; the uniform gate
imports no numerical optimizer. Run discovery in a clean archive, first
`run_scf_uniform_facet_gate.py`, then `run_scf_core_refinement.py`, and
compare the canonical UTF-8/LF hashes. Independent acceptance works with
site packages disabled. No paid cloud or QPU was used.

## 7. Prior-art and significance boundary

The original [gear-composition paper](https://www.iasi.cnr.it/~gentile/ClaudioGentileFiles/papers/ORL2.pdf)
defines an eight-vertex gear and an edge replacement retaining it as an
induced subgraph. Its gear has disjoint stable triples {a,b1,b2} and
{c,d1,d2}. No G_m can contain that gear, since every triple of G_m contains
Z. This excludes the literal construction, not all fuzzy/lifting variants.

The ordinary clique-family formula cannot directly equal the primitive
rhs-three C005 facet: coefficient ratio 2 forces coefficients 2 and 1,
but then its right side is even. The
[strengthened clique-family/MIR formula](https://eprints.lancs.ac.uk/id/eprint/155944/1/clique_family.pdf)
is broader. A frozen search over subsets of maximal cliques found no
match on m=0,1,2,3 (209,559,1423,3492 candidate subset/q pairs). Repeated
cliques, general CG multipliers, alternate graph presentations and other
proofs are not excluded. A failed bounded search is NOT a novelty proof.

The two expanded rows form a **homogeneous pair of cliques**, an established
classical structure. [Eisenbrand--Oriolo--Stauffer--Ventura, Lemma 5 and
its following remark](https://www.iasi.cnr.it/~ventura/PaoloVenturaFiles/papers/EOSV06.pdf)
already use homogeneous-pair edge deletion to preserve a selected facet.
We do not claim classical clique refinement as a new contribution. Their
complete quasi-line theorem cannot be applied directly: G_m contains the
five-wheel with hub H1 and rim A0,Z,H0,Hc,U, so it is not quasi-line.

[Pecher--Wagler](https://doi.org/10.1016/j.disc.2009.03.031) give alpha-three
claw-free examples with arbitrarily complicated facet coefficients; our
restricted family theorem must not be promoted to all claw-free or all
SCF graphs on that basis. No classification from that paper is assumed.

The quantum foundation is [Chapman--Elman--Mann](https://arxiv.org/html/2305.15625v1)
and the beta/hbar-perfect framework is [Xu et al.](https://arxiv.org/html/2511.13531v1).
The potential contribution is the rigorous quantum all-weight extension
beyond line graphs on this explicit unbounded family, using the signed
Gram bound. Its significance and priority still need adversarial comparison
and external expert review. Correctness, novelty, and A-star standing
remain separate judgments.
