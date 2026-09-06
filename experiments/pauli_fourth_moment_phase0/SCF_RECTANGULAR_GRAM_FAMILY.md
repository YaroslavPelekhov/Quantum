# A signed rectangular Gram proof for an unbounded SCF facet family

Date: 2026-09-06. Cycle C005, preregistration `1909d6e`.
Status: exact computer-assisted family theorem, pending external review.
This extends the existing Gram/envelope method. It is NOT a new SDP method,
an all-weights theorem for this family, unrestricted H-SCF, or confirmed A-star novelty.

Subsequent C006 addendum: [all weights on G_1 are now proved](SCF_G1_ALL_WEIGHT_CLOSURE.md)
by a complete independent facet audit. The present C005 statement and its
artifact remain fixed-weight. Subsequent C007 supplies the missing
[all-m, all-weight theorem](SCF_UNBOUNDED_ALL_WEIGHT_FAMILY.md), using a
uniform classical refinement proof and a separately verified core lemma.
The historical C005 artifact flags intentionally remain unchanged.

## 1. Family and theorem

For an arbitrary integer m>=0, define a bipartite root graph by its occupied
cells in a three-row incidence matrix. For j=0,...,m there are light edges
A_j in cell (0,j) and B_j in cell (1,j). Additionally there are

- Z in cell (2,0);
- U in cell (0,m+1);
- V in cell (1,m+2).

The light anticommutation graph is the line graph of this root: two lights
are adjacent exactly when their cells share a row or a column. Add three
heavy vertices H0,H1,Hc, mutually adjacent. Their light NONneighbors are
respectively the whole first row, the whole second row, and column zero.
Call the resulting graph G_m. It has 2m+8 vertices.

Theorem. For every m>=0, every Pauli realization of G_m, and every state rho,

`sum_light <P_i>^2 + 2(<P_H0>^2+<P_H1>^2+<P_Hc>^2) <= 3`.

The bound is attainable and is a full-support nonrank facet of STAB(G_m).
In particular beta(G_m,w)=alpha(G_m,w)=3 for these FIXED weights. No assertion
about arbitrary weights is implicit in this statement.

G_1 is weight-preserving isomorphic to the frozen order-ten target
`ICXmtizr_`, with target weights `(1,1,1,1,2,1,2,1,2,1)`. In the family
ordering A0,B0,A1,B1,Z,U,V,H0,H1,Hc the map to target labels is

`(7,5,0,9,2,3,1,4,8,6)`.

Thus that previously numerical-only weighted facet now has an exact proof.
This does not certify every facet of that ten-vertex graph.

## 2. Graph hypotheses and classical facet

Each G_m is claw-free. One exact, finite verification suffices for arbitrary
m: a claw uses four vertices, hence at most four distinct noncentral column
indices. Relabel those indices into {1,2,3,4}; keep column zero, U,V,Z and
the heavy vertices fixed. All adjacencies are preserved, so such a claw
would occur in G_4. The independent verifier exhausts all four-subsets of
G_4 and finds no claw. The same embedding covers m<4 by deleting columns.
This bounded-support argument, not an extrapolation from several graph
sizes, establishes the unbounded claim.

The clique K={A0,B0,Z} is simplicial. Outside K, the neighbors of A0 are
`{A_j:j>0} union {U,H1}`, a clique. The neighbors of B0 are
`{B_j:j>0} union {V,H0}`, also a clique. The outside neighbors of Z are
{H0,H1}. Therefore G_m is SCF for every m.

An independent set containing a heavy vertex has at most one light vertex,
because each heavy's light NONneighbors form a clique. An all-light stable
set is a root matching, of size at most three. The set {U,V,Z} has size
three, and {H0,U} has weight three. Thus alpha(G_m)=alpha(G_m,w)=3.
Every independent triple consists of Z and one vertex from each other row,
in distinct noncentral columns (including the two private columns).

The displayed inequality is a facet, not merely a valid weighting. Suppose
an affine functional is constant c on its tight stable sets. The tight
pairs {H0,A_j}, {H0,U} force all first-row coefficients to have one value a.
The pairs {H1,B_j}, {H1,V} similarly give one value b on the second row.
The pairs {Hc,A0}, {Hc,B0}, {Hc,Z} force a=b and the Z coefficient also
equal to a. The triple {U,V,Z} gives c=3a; all heavy coefficients are then
2a. Consequently the affine hull of tight roots has just this one defining
hyperplane, of dimension |V|-1. STAB is full-dimensional, so it is a facet.
The verifier also checks its root rank rationally for all six audit sizes.

## 3. The central signs and the coherent matrix

Use real Hamiltonian amplitudes a_j,b_j,c,p,q on A_j,B_j,Z,U,V, and
r0,r1,rc on the heavy vertices. Amplitude signs are allowed; no positivity
assumption on them is needed. For each common column define

`K_j = -P_H0 P_H1 P_Aj P_Bj`.

Every K_j is a Hermitian involution central in the FULL generator algebra.
This follows by commuting each generator through the four factors: the
number of anticommutations is even, including for the two heavy row
selectors, the heavy column selector, and Z. The square and adjoint signs
are plus. Thus all K_j commute, and we may restrict to an actual simultaneous
eigenspace with eigenvalues epsilon_j in {+1,-1}. It is harmless if some
sign configurations do not occur in a particular Pauli representation:
the argument bounds every configuration, including all those that do occur.

In such a sector form the REAL 3-by-(m+3) matrix

```text
B = [       a0          a1  ...          am    p    0 ]
    [ epsilon0*b0 epsilon1*b1 ... epsilonm*bm   0    q ]
    [        c           0  ...           0    0    0 ].
```

Set M=B B^T. It is positive semidefinite by construction. Put

`L=sum_j(a_j^2+b_j^2)+c^2+p^2+q^2`,

`H=r0^2+r1^2+rc^2`.

The actual off-diagonal entry
`M_01=sum_j epsilon_j a_j b_j`
retains interference between all shared columns. Its signs must NOT be
maximized independently of the light-cycle signs. This is a global central
cycle decomposition, not the invalid dephasing in the boundary operator J
from C004: the entire Hamiltonian commutes with every K_j here.

## 4. Universal transfer identities

Let Q_k be the sum of amplitude-weighted products over independent k-sets,
and `T(t)=I-t Q1+t^2 Q2-t^3 Q3`. The existing SCF transfer framework gives

`T(t)T(-t)=I-e1*t^2+e2*t^4-e3*t^6`.

For G_m, the exact identities in the universal graph algebra are

`e1=L+H`,

`e2=e2(M)+(r0,r1) M[{0,1},{0,1}] (r0,r1)^T + rc^2 ||B[:,0]||^2`,

`e3=det(M)`.

Here e2(M) is the sum of the three principal 2-by-2 minors. These are
identities, not bounds obtained by independently taking absolute cycle signs.
For an explicit scalar form, let q_light be the sum of a_i^2*a_j^2 over
commuting light pairs. Then

`e2(M)=q_light-2 sum_(i<j) epsilon_i epsilon_j a_i b_i a_j b_j`,

and

`det(M)=c^2*((p^2+sum_(j>0)a_j^2)*(q^2+sum_(j>0)b_j^2)
                  -(sum_(j>0)epsilon_j*a_j*b_j)^2)`.

The latter also follows directly from Q3 squared. Write A and B for the
Hamiltonian sums on the noncentral portions of rows zero and one, including
U and V, and Q=P_H0 P_H1. Then Q^2=-I and
`[A,B]=2 Q sum_(j>0)epsilon_j a_j b_j`. Q commutes with AB+BA.
Since A^2 and B^2 are their scalar row masses,
`((AB+BA)/2)^2=A^2 B^2-(sum_(j>0)epsilon_j a_j b_j)^2`.
Z commutes with both noncentral row sums, proving the determinant formula.

### Why the exact finite identity certificate proves every m

The independent verifier expands ALL coefficients of T(t)T(-t), including
the vanishing odd powers, and compares the three even coefficients with
the matrix expressions in the universal Pauli algebra. Discovery uses
inversion parity and SymPy; acceptance uses adjacent-letter rewriting and
integer/Fraction sparse polynomial arithmetic, with no numerical solver.

To extend these identities beyond the audited sizes, inspect an amplitude
monomial. At degree at most four, it involves at most four noncentral
columns. At degree five it comes from a pair times a triple; every triple
contains Z, leaving at most four other vertices. At degree six it comes
from two triples, both containing Z, again leaving at most four other
vertices. On the proposed matrix side the only degree-six expression is
det(B B^T), which has a factor c^2 because row two has only one nonzero
entry; it too involves at most four noncentral columns.

Relabel these at most four column indices into G_4. Setting all unused
column amplitudes to zero reduces both the transfer polynomial and the
Gram formulas to the smaller induced family member; there are no hidden
contributions from unused columns. Word-reordering phases are carried by
the same generator permutation, so a zero identity is invariant under this
relabelling. Every coefficient for arbitrary m is therefore certified by
the exact G_4 expansion. The audits at m=0,...,5 are implementation checks;
the finite-support reduction is the reason an all-m theorem follows.

## 5. Spectral upper bound, including the crossing condition

The row pair is a principal submatrix of M. A column norm squared is a
Rayleigh quotient of B^T B, whose largest eigenvalue equals that of M.
Consequently the heavy part is at most H*lambda_max(M). Writing the three
nonnegative eigenvalues of M as x,y,z, with y largest, gives

`e2 <= xy+xz+yz+H*y`, `e3=xyz`, `x+y+z=L`.

Normalize the weights to one-half on lights and one on heavies. The usual
beta variational identity permits normalization `2L+H=1`, so 0<=L<=1/2
and e1=1-L. The already used three-eigenvalue envelope is

`xy+xz+yz+(1-2L)y+2sqrt((3/2)xyz) <= (1/4+L/2)^2`.

For fixed L,y its left side increases with xz; replace x=z=(L-y)/2 and
write y=s^2/6. The difference is exactly

`(s-1)^2*(12L+s^2+6s+3)/48 >= 0`.

Both discovery and acceptance verify this polynomial identity independently.

For clarity, this coefficient inequality implies the spectral bound on the
correct branch. In an SCF free-fermion sector pad with zero modes if needed
and write the three nonnegative single-particle energies as nu_i. Their
squared elementary coefficients are e1,e2,e3, and put S=sum_i nu_i.
Then `f(S)=0` for

`f(t)=((t^2-e1)/2)^2-e2-2t*sqrt(e3)`.

The envelope gives f(sqrt(3/2))>=0. For t>=sqrt(3/2),
`f'(t)=t*(t^2-e1)-2sqrt(e3)>0`: e1<=1 and
`e3=xyz<=(L/3)^3<=1/216` suffice. Hence S cannot exceed sqrt(3/2).
This proves beta<=3/2 for the normalized weights and <=3 for the original
weights. A common eigenstate of P_H0 and P_U attains the lower bound three.

Zero amplitudes, repeated/zero eigenvalues, arbitrary Pauli signs and mixed
states cause no exception. The identities are polynomial, the bounds use
closed inequalities, and the variational identity optimizes over all states.

## 6. Scope, provenance and reproduction

The family theorem is stronger than a six-size numerical survival result:
it has a uniform proof and exact coefficient certificates. Nevertheless it
proves just one nonrank facet weighting per G_m, not hbar-perfectness of G_m
for all weights. Other facets and unrestricted SCF remain open. The original
order-ten frontier JSON remains unchanged as a historical numerical result;
the new exact target proof is recorded separately.

The foundation is the
[Chapman--Elman--Mann SCF transfer/free-fermion theorem](https://arxiv.org/html/2305.15625v1).
The Gram/envelope method was already used in this repository for types 15
and 23; the current contribution is its consistent signed rectangular
completion and explicit uniform family. Rectangular Gram factorization,
Cauchy--Binet, Rayleigh bounds and finite-support polynomial checking are
standard mathematics, not invented here.

The [Xu et al. state-polynomial hierarchy](https://arxiv.org/html/2511.13531v1#A2.SS1)
was checked as the planned fallback; no SDP was needed or run in this cycle.
Classical nonrank facet families, including
[Galluccio--Gentile--Ventura gear composition](https://doi.org/10.1016/j.orl.2008.01.003),
remain a relevant priority comparison. We have not established whether G_m
or this facet has another classical name, nor whether an equivalent quantum
inequality is already a known consequence. No novelty-priority claim follows
from unsuccessful phrase searches. The adjacent 2026 path-product work
recorded in C004 is not used in this proof.

```text
python experiments/pauli_fourth_moment_phase0/run_scf_rectangular_gram_bridge.py
python experiments/pauli_fourth_moment_phase0/verify_scf_rectangular_gram_bridge.py
python -m unittest discover -s experiments/pauli_fourth_moment_phase0 -p "test_scf*.py" -v
```

Run rediscovery in a clean archive to preserve the reference JSON. Discovery
uses NetworkX and SymPy; independent acceptance uses only the standard
library. The audit covers 8,10,12,14,16,18 vertices and every universal
coefficient, not sampled amplitudes or sampled cycle signs. The current
combined suite has 45 tests, including wrong cycle phases, wrong Gram
entries, incorrect transfer coefficients and unsupported all-weights claims.
