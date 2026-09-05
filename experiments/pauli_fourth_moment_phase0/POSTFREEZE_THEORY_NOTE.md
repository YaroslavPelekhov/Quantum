# Post-freeze theory note: convolution and one-logical-qubit extraction

Status: proved auxiliary statement, pending an independent proof audit and a
complete prior-art audit.  It is **not** a proof of preregistered claim T1.

Current SCF completion (2026-09-05): see
[the exact order-nine theorem](SCF_ORDER9_EXACT_THEOREM.md). All 128 nonrank
facet types are now proved, and a GMP-rational facet census with exact H/V
roundtrips establishes completeness. The intermediate counts below record
the chronological proof development, not the current unresolved count.

The next [generalization note](SCF_GENERALIZATION_THEOREMS.md) proves the
all-weights identity at arbitrary order for SCF graphs with `alpha<=2`,
proves clique-separator closure, and records exact obstructions to two
attempted extensions. The unrestricted weighted conjecture is still open.

## Setup

For an odd integer `K >= 3`, let

`tau = boxtimes_K(rho_1,...,rho_K)`

be the qubit quantum convolution of Bu--Gu--Jaffe.  Its Hermitian Pauli
expectations multiply, up to the fixed convention-dependent Clifford/sign
map:

`<P>_tau = product_a <P>_{rho_a}`.

The harmless Clifford/sign map is suppressed below because stabilizer
operations and the one-qubit stabilizer octahedron are Clifford invariant.

For qubits the convention factor in Bu--Gu--Jaffe is either the identity or
full matrix transpose: on a Hermitian Pauli word it is
`(-1)^(number of Y factors)`.  Full transpose maps stabilizer states to
stabilizer states and conjugates every fixed stabilizer branch to another
fixed stabilizer branch.  It can therefore be removed before the argument
and restored afterward without changing the conclusion.

## Proposition (one-logical-qubit convolution barrier)

Let a branch of a stabilizer protocol project `tau` onto a rank-two
stabilizer code, decode its single logical qubit, and condition on any branch
with nonzero probability.  The normalized logical output lies in the
one-qubit stabilizer octahedron.  The statement holds for arbitrary, unequal,
mixed input states and every odd `K >= 3`.

Consequently, no single-copy postselected stabilizer protocol whose output is
one qubit can distill magic from `tau`.

## Proof

Choose commuting stabilizer generators `g_1,...,g_{n-1}` for the code and
logical Pauli representatives `L_X,L_Y,L_Z`.  Write `Pi_s` for the syndrome
projectors.  For input `a`, set

`p_a(s) = Tr(rho_a Pi_s)`

and, whenever `p_a(s)>0`, let `v_a(s)` be the Bloch vector of the normalized
logical state obtained by projecting `rho_a` onto syndrome `s` and decoding.

Expand `Pi_s` in the abelian stabilizer group.  Multiplicativity of every
Pauli coefficient under convolution and Fourier inversion on the syndrome
group show that the unnormalized logical branch is a positive mixture over
syndrome tuples satisfying the convolution parity rule.  After
normalization, it is therefore a convex mixture of one-qubit states with
Bloch vectors

`u_j = product_a v_{a,j}(s_a),   j in {X,Y,Z}`.

Each conditional input is a valid qubit state, hence
`||v_a(s_a)||_2 <= 1`.  Holder's inequality with `K` equal exponents gives

`sum_j |u_j| <= product_a ||v_a(s_a)||_K`

and norm monotonicity for `K >= 2` gives

`product_a ||v_a(s_a)||_K <= product_a ||v_a(s_a)||_2 <= 1`.

Thus every component state satisfies the octahedron criterion
`|u_X|+|u_Y|+|u_Z| <= 1`.  Convexity proves the claim for the normalized
branch.  Zero-probability input syndromes contribute zero and may be omitted.

To pass from rank-two code projection to a general one-output-qubit
stabilizer protocol, use the fixed-branch stabilizer normal form.  Append
`|0>` ancillas, pull the branch's Clifford gates through its Pauli
measurements, and row-reduce the resulting stabilizer tableau.  A fixed
nonzero branch is a stabilizer-code projection followed by a Clifford
isometry.  Refine every discarded qubit by a complete stabilizer-basis
measurement.  Each refined branch then retains exactly one logical qubit and
has the rank-two form proved above; forgetting the refinement is a convex
mixture of those normalized outputs.  Appending `|0>` causes no mismatch:
`|0>` is a fixed point of every odd convolution, so the enlarged input is
again a convolution output.  Clifford covariance and convexity complete the
general statement.

## What this does and does not establish

- It is dimension independent and covers unequal inputs, mixed inputs,
  arbitrary stabilizer codes retaining one logical qubit, and postselection.
- It gives a new obstruction to extracting one-qubit magic from quantum
  convolution outputs, if the remaining prior-art and independent-proof
  audits pass.
- It does not show that `tau` itself belongs to the full `n`-qubit stabilizer
  polytope.  Higher-logical-dimensional stabilizer facets can contain
  information invisible to all one-logical reductions.
- This gap is strict already for physical three-qubit states.  The exhaustive
  audit in `one_logical_completeness_gap.json` gives a depolarized pure state
  outside `STAB_3` that passes all 1,260 rank-two-code/syndrome octahedron
  tests, together with an integer stabilizer-polytope separating witness.
- Therefore it does not yet imply T1 or the claimed `epsilon^-4` fractional
  colouring bound.

## Stronger conjecture exposed by the proof

The numerical program now tests the stronger statement

`boxtimes_3(rho_1,rho_2,rho_3) in STAB_n`

for arbitrary inputs.  If true, self-convolution has Pauli coefficients
`<P>^3`; a stabilizer decomposition then supplies unsigned commuting-support
inclusion probabilities at least `|<P>|^3`.  Down-monotonicity would place
the entire vector `|<P>|^3` in the stable-set polytope and, a fortiori, place
`<P>^4` there.  Hence this stronger conjecture would improve T1 to the
universal exponent `kappa=3`, not merely prove the frozen exponent four.
Numerical support is not substituted for this missing global
stabilizer-polytope argument.

## Proposition (spin-factor witness barrier)

The one-logical result extends to a genuinely multi-logical family of
stabilizer witnesses.  Let `C,A_1,...,A_m` be Hermitian Paulis such that `C`
commutes with every `A_j` and the `A_j` are pairwise anticommuting.  Choose
the Hermitian signs in `C A_j` and define

`W = -C + sum_j (A_j + C A_j)`.

Then `Tr(W sigma) <= 1` for every stabilizer state `sigma`, and

`Tr(W boxtimes_K(rho_1,...,rho_K)) <= 1`

for arbitrary inputs and every odd `K >= 3`, up to the fixed transpose in
the convolution convention.

### Stabilizer bound

For a pure stabilizer state, Pauli expectations are zero or signed one.  If
`C` has expectation `+1`, then `C A_j` and `A_j` have equal expectation and
at most one of the pairwise anticommuting `A_j` can be nonzero; hence the
bound is `-1+2=1`.  If `C` has expectation `-1`, all paired terms cancel and
the value is one.  If `C` has expectation zero, a commuting stabilizer group
can contain at most one Pauli among all `A_j,C A_j`: two with distinct
indices anticommute, while containing both members of one pair would also
contain `C`.  The value is again at most one.  Convexity covers mixed
stabilizer states.

### Convolution bound

For input `a`, project onto the `C` eigenspaces and write their probabilities
as `p_a(s)`, `s in {+1,-1}`.  Let `v_a(s)` be the vector of conditional
expectations of the `A_j`.  Pairwise anticommutation gives
`||v_a(s)||_2 <= 1`.  With

`n_a(s,j) = p_a(s) v_a(s)_j`,

the two Pauli coefficients are

`<A_j>_a = n_a(+,j)+n_a(-,j)`,

`<C A_j>_a = n_a(+,j)-n_a(-,j)`.

After multiplication across an odd number of inputs, adding these two terms
keeps exactly the syndrome tuples with product `+1`.  For each tuple,
Holder and norm monotonicity give

`sum_j product_a v_a(s_a)_j <= product_a ||v_a(s_a)||_K <= 1`.

The total probability of the retained tuples is
`(1+product_a <C>_a)/2`.  The paired terms are therefore at most
`1+product_a <C>_a`, which cancels the witness contribution
`-product_a <C>_a` and proves the bound.

The integer three-qubit witness extracted by the completeness-gap LP has
`m=5` and exactly this form.  Its direct trilinear optimization over 5,000
random starts reached only numerical equality at one.  This result controls
a higher-logical stabilizer facet family, but no claim is made yet that all
stabilizer facets admit such a decomposition.

## Corollary (global CNC positivity of odd convolution)

Known structure theorems for maximal closed-noncontextual (CNC) phase-point
operators put every such operator, up to a Clifford, in the form

`A_CNC = A_spin tensor Pi_I`,

where `Pi_I` is a stabilizer-code projector and

`A_spin = 2^-m (I + sum_{j=1}^{2m+1} s_j A_j)`

for pairwise anticommuting Hermitian logical Paulis `A_j` and signs `s_j`.
Combining that classification with the argument above gives a global
statement: for every maximal CNC operator `A_CNC`,

`Tr[A_CNC boxtimes_K(rho_1,...,rho_K)] >= 0`

for arbitrary qubit inputs and every odd `K >= 3`.

Indeed, Clifford covariance reduces to the displayed factorization.  Fourier
expansion of `Pi_I` writes its convolution branch as a positive mixture over
tuples of input syndromes satisfying the convolution parity rule.  In every
component, the conditional logical expectation vectors of the pairwise
anticommuting `A_j` have Euclidean norm at most one.  Holder bounds the
absolute value of their componentwise `K`-fold product sum by one, so the
conditional expectation of `A_spin` is nonnegative.  Averaging over the
syndrome tuples proves the result.

Thus odd quantum convolution maps the whole state space into the region
that is nonnegative on every maximal CNC phase point.  This is stronger and
more global than the one-logical theorem, and it controls every stabilizer
inequality induced by a CNC operator.  It must not be confused with
membership in the CNC simulation polytope itself, nor with membership in the
smaller stabilizer polytope; neither follows by convex duality.

The CNC factorization is prior art (Raussendorf et al., PRA 101, 012350
(2020); Ipek et al., PRA 113, 032409 (2026); Okay, Research in the
Mathematical Sciences 13, 55 (2026)).  The checked sources do not connect it
to quantum convolution or state the global nonnegativity result above.

## Theorem (line-graph squared profiles are matching mixtures)

Let Pauli observables `P_e` be indexed by the edges of an arbitrary graph
`H`, with two observables anticommuting exactly when their edges share an
endpoint (so their anticommutation graph is `L(H)`).  Then, for every state,

`x_e = <P_e>^2`

belongs to `MATCH(H)=STAB(L(H))`.  Consequently, for every nonnegative edge
weight `w`,

`sum_e w_e <P_e>^2 <= nu(H,w) = alpha(L(H),w)`.

The reverse inequality is attained by a common eigenstate of the commuting
Paulis indexed by a maximum-weight matching.  Hence every line graph is
`hbar`-perfect in the terminology of Wang et al.  On this class the original
large-expectation fractional-colouring conjecture is true with exponent two,
which is stronger than both the frozen exponent four and the cubic result
first found in this cycle.

### Proof through Majorana covariance and representation invariance

Use the canonical realization `P_uv=i gamma_u gamma_v`, where the `gamma_u`
are pairwise anticommuting Majorana operators.  For a state `rho`, let
`Gamma_uv=<i gamma_u gamma_v>`.  Positivity of the Majorana correlation
matrix gives `||Gamma||_op<=1`; explicitly, the matrix with entries
`Tr[rho gamma_u gamma_v]` is positive semidefinite, and the eigenvalues of
the real antisymmetric `Gamma` therefore lie in the required unit interval.

The squared row norm gives every degree constraint

`sum_(e incident v) x_e <= 1`.

For any odd vertex set `S`, the principal submatrix `Gamma_S` is an odd real
antisymmetric contraction.  It has at least one zero singular value and all
remaining singular values are at most one, so

`sum_(e in E_H(S)) x_e <= (1/2)||Gamma_S||_F^2 <= (|S|-1)/2`.

These are exactly Edmonds' degree and blossom inequalities; thus
`x in MATCH(H)` for the canonical realization.  The weighted beta radius is
representation-independent for Pauli realizations of a fixed
anticommutation graph (Xu--Schwonnek--Winter).  Therefore every realization
has the same weighted maximum `nu(H,w)`.  Since the matching polytope is a
downward-closed convex corner, separation by all nonnegative weights places
the entire beta body, and hence each concrete squared profile, in `MATCH(H)`.
The reverse inclusion follows from common eigenstates of matchings, so the
stronger body identity `BETA(L(H))=MATCH(H)` holds.

The elementary powered-blossom argument found before this strengthening
remains an independent proof that `x^(3/2)` enters the matching polytope from
only star and triangle uncertainty.  It is no longer the strongest result.

The squared-profile theorem also proves nonnegative odd-convolution overlap
for the known Jordan--Wigner line-graph phase points: Holder reduces the
multi-input expression to the single-input matching bound.

## Theorem (hidden free fermions satisfy every rank inequality)

Let `G` be simplicial claw-free (SCF), component by component, and let
`P_1,...,P_m` be any Pauli realization of `G`.  Then

`beta(G,1) = alpha(G)`.

Because SCF is hereditary, the same identity holds for every induced
subgraph.  Equivalently, every squared expectation profile in `BETA(G)`
satisfies all stable-set rank inequalities

`sum_(i in U) <P_i>^2 <= alpha(G[U])`.

This strictly extends the unweighted consequence of the line-graph theorem
to the hidden-free-fermion class of Chapman--Elman--Mann.  It does **not**
prove the weighted identity `beta(G,w)=alpha(G,w)`: SCF stable-set polytopes
can have non-rank facets.

### Proof audit

By representation invariance of beta, it is enough to use the fiducial
bosonization realization employed in the free-fermion proof; this avoids
accidental Pauli product identities present in some compact realizations.
Set `A=sum_i a_i P_i` in that realization.  In each generalized-cycle symmetry sector, the SCF
solution writes `A` as a free-fermion Hamiltonian with at most `alpha(G)`
positive single-particle energies `epsilon_j`.  Their generalized
characteristic polynomial is

`Z_G(-u^2)=T_G(u)T_G(-u)`.

The quadratic coefficient can be obtained without any sector assumption.
Writing `T_G(u)=I-uA+u^2 Q_G^(2)+O(u^3)` and using commutation of every
independent pair gives

`A^2 = (sum_i a_i^2) I + 2 Q_G^(2)`.

Hence

`Z_G(-u^2)=I-u^2 (sum_i a_i^2) I+O(u^4)`.

After restriction to any sector,
`Z_G(-u^2)=product_j(1-u^2 epsilon_j^2)`, so
`sum_j epsilon_j^2=sum_i a_i^2`.  The free-fermion spectrum and
Cauchy--Schwarz therefore imply

`||A||^2 <= (sum_j |epsilon_j|)^2`
`          <= alpha(G) sum_i a_i^2`.

Finally,

`max_rho sum_i <P_i>^2 = max_(||a||_2=1) ||sum_i a_i P_i||^2`,

so the upper bound is `alpha(G)`.  A common eigenstate of any maximum
independent set attains the reverse inequality.  Representation invariance
of beta transfers the statement across all Pauli realizations.  Applying the
same argument to every induced subgraph, which remains SCF, proves the rank
body inclusion.

## Open conjecture (SCF graphs are hbar-perfect)

The natural weighted strengthening is

`BETA(G)=STAB(G)` for every SCF graph `G`.

It survived the preregistered falsification suite, including exact attacks
on every non-rank stable-set facet found in the candidate set, but no proof
is claimed.  The missing step is precisely control of non-rank facets; the
free-fermion energy argument above supplies only Euclidean/rank bounds.

The subsequent exhaustive order-nine census found 4,308 SCF graphs among all
261,080 connected graphs, including 3,598 genuinely non-line cases.  Every
non-rank facet encountered had coefficients proportional to `1/2` and `1`.
After quotienting 701 occurrences by weighted-support isomorphism, all 128
remaining types survived every sign orthant of a first-moment-SDP-guided
see-saw attack.

## Proposition (115 of 128 order-nine facet types reduce to joins)

For 115 of the 128 weighted-support types, the unweighted independence
number is two and the normalized facet has weighted independence number one.
Write `K` for the vertices of coefficient one and `H` for the vertices of
coefficient `1/2`.  The set `K` is a clique: two nonadjacent vertices in `K`
would already have weight two.  Every vertex of `K` is adjacent to every
vertex of `H`: a missing edge would give an independent set of weight
`3/2`.  Hence the support graph is the join `K join H`.  Moreover
`alpha(H)=2`.

The beta number of a join is the maximum of the beta numbers of its two
parts.  Thus the clique inequality gives `beta(K,1)=1`, while the SCF rank
theorem above gives

`beta(H,(1/2)1)=(1/2)alpha(H)=1`.

Consequently all 115 of these non-rank facet inequalities are proved for
every Pauli realization.  The deterministic reduction audit checks the join
conditions type by type.  This is a finite order-nine statement, not yet a
classification theorem for arbitrary SCF graphs.

The 13 residual types all have unweighted independence number three and
weighted independence number `3/2`; none is disposed of by the join
argument.  A faithful implementation of the real state-moment hierarchy was
first validated on the published non-SCF `G9` control, reproducing its level-1
and level-2 bounds `3.2360679896` and `3.0448153335`.  At level 2 it closes 12
of the 13 residual types to `2e-5`.  The sole numerical atom is graph6
`HEhu|x|` with weights
`(1/2,1/2,1/2,1,1/2,1,1/2,1,1)`.  Its level-2 upper bound is
`1.5001356864`; level 3 lowers this to `1.5000415786` but does not certify the
classical value `1.5`.  A tighter level-3 solve was stopped after more than
1,300 CPU seconds without a result.  Therefore 115 types are analytically
closed, 12 more are numerically bounded at level 2, and exactly one explicit
atom remains open; no full weighted theorem is claimed.

## Lemma (exact spectral reduction of the final atom)

The remaining atom admits a sharper reduction than the generic SDP.  Put
`p_i=b_i^2`, where `b_i` are the Hamiltonian coefficients, and define

`L=sum_(i in {0,1,2,4,6}) p_i`,
`H=sum_(i in {3,5,7,8}) p_i`,
`D=3L+(3/2)H`.

Its generalized characteristic polynomial has three squared-mode roots and
coefficients

`e_1=L+H`, `e_3=p_0 p_1 p_2`, `e_2=q_0+2 sqrt(R)`,

in the extremal symmetry sector.  Here `q_0` is the sum `p_i p_j` over all
nonedges, and `R` is the sum of `product_(i in C) p_i` over the eight induced
four-holes.  The formula for `e_2` is exact: all hole-operator pairs
anticommute except `(C_4,C_7)` and `(C_5,C_6)`.  These two exceptional pairs
multiply to the same Pauli word with opposite signs and equal scalar
coefficients.  Their cross terms cancel, so the square of the non-scalar
fourth-order coefficient is exactly `R I`.

If `S` is the sum of the three positive single-particle energies, then

`((S^2-e_1)/2)^2=e_2+2 sqrt(e_3) S`.

Since the right crossing is unique for `S^2>=e_1`, the atom inequality is
reduced to the explicit nonnegative-variable inequality

`(L+H/4)^2 >= q_0+2 sqrt(R)+2 sqrt(p_0 p_1 p_2 D)`.                 `(A)`

Indeed, `(A)` evaluated at `D` forces `S^2<=D`; under the variational
normalization `2L+H=1`, this is exactly `S^2<=3/2`.  The operator-algebra
reduction to `(A)` is proved and checked symbolically.  Inequality `(A)`
itself survived one million seeded interior-simplex samples and is exact at
the equal light triple, but is not yet proved.  This replaces a 429-by-429
moment matrix by one concrete homogeneous inequality; it does not close the
final atom by itself.

## Lemma (five primitive faces of the final atom)

Normalize `(A)` by `2L+H=1`, so `D=3/2` and `0<=L<=1/2`.  Consider a support
contained in `{0,1,2} union C`, where `C` is one of the first five four-holes
listed in `scf_atom_spectral_reduction.json`.  Direct expansion shows that
only the named quartic monomial in `R` survives on each of these five faces.

On the first four faces, maximizing over the two nonzero heavy variables
with sum `H` is the largest-eigenvalue problem for a positive semidefinite
`2 by 2` matrix.  If its eigenvalues are `y>=z>=0`, the remaining light
variable is `x>=0`, and `x+y+z=L`, then the face objective is exactly

`xy+xz+yz+Hy+2 sqrt((3/2)xyz)`.                         `(B)`

On the fifth face the same reduction is an upper bound: the determinant of
the corresponding matrix is `K=p_1p_2+p_1p_4+p_2p_6`, so
`p_0p_1p_2<=p_0K`.  Thus `(B)` controls all five faces.

For fixed `y`, expression `(B)` is increasing in `sqrt(xz)`.  Since
`x+z=L-y`, AM--GM bounds it by its value at
`x=z=(L-y)/2`.  Write `y=s^2/6`.  The resulting univariate expression `E`
satisfies the exact identities

`dE/ds=-(s-1)(6L+s^2+4s)/12`,

`(1/4+L/2)^2-E=(s-1)^2(12L+s^2+6s+3)/48`.              `(C)`

Consequently the fixed-`L` maximum on every primitive face is
`L(1-2L)` for `L<=1/6` and `(1/4+L/2)^2` for `L>=1/6`.
The first branch lies below the target because their difference is
`(1-6L)^2/16`.  Hence `(A)` is proved on all five primitive faces.

This lemma is not the full atom proof.  The remaining three hole-generated
support faces activate three quartic monomials simultaneously, and a fully
supported point can activate all eight.  A counterexample, if one exists,
must therefore exploit coupled hole channels rather than a single primitive
channel.  The stored audit tests all eight hole-generated support faces with
100,000 seeded points per face; their largest value-minus-envelope is
negative, but only the five-face statement above is promoted to a theorem.

## Lemma (stationarity restriction for coupled hole channels)

There is also an exact restriction on a fully interior maximizer.  Put
`X=p_3+p_5`, `Y=p_7+p_8`, `x=p_5/X`, and `y=p_8/Y`, and hold the five light
variables and `X,Y` fixed.  Up to a constant, the scalar objective has form

`A x+B y+2 sqrt(R_0+R_1x+R_2y-Kxy)`,

where

`A=X(p_0-p_2)`, `B=Y(p_0-p_1)`,
`K=p_0(p_4+p_6)XY`.

At an interior stationary point, direct differentiation gives
`R_x=-A sqrt(R)` and `R_y=-B sqrt(R)`.  Substitution into the Hessian yields

`det Hessian=-K(K+AB)/R`.

For a fully supported point `K>0`; a local maximum therefore requires

`p_0(p_4+p_6)+(p_0-p_2)(p_0-p_1)<=0`.                `(D)`

In particular, an interior coupled-channel maximum is impossible unless
`p_0` lies strictly between `p_1` and `p_2`, with their separation large
enough to offset `p_0(p_4+p_6)`.  Outside this wedge the two-dimensional
heavy split has no interior local maximum and its maximum lies on a boundary.
This is a necessary condition, not yet an exclusion of the residual wedge.

## Lemma (no fully interior heavy-simplex maximum)

The residual wedge can itself be excluded.  Keep all five light variables
fixed and optimize over the four heavy variables with fixed sum `H`.  Eliminate
`p_8`, so the heavy simplex has dimension three.  At an interior stationary
point, the preceding first-derivative equations reduce the Hessian to

`sqrt(R) Hess(objective)=M=Hess(R)-vv^T/2`,

where `v` is the heavy linear coefficient vector after elimination.

Condition `(D)` says that `p_0` must lie strictly between `p_1` and `p_2`.
The atom automorphism interchanges `p_1,p_2` together with the corresponding
light and heavy orbits, so take without loss of generality
`p_1=p_0+x`, `p_2=p_0-y`, with `x>=0` and `0<y<p_0`.  Direct expansion gives

`det(M)=p_0 P(x)/2`,

where `P` is quadratic in `x`, has leading coefficient `p_0 p_4^2>0`, and

`disc_x(P)=16 p_4^2 p_6 (y-p_0)(p_4+p_6)`
`          *(p_0p_4+p_6y)(p_0+p_4+p_6)<0`.

Thus `P(x)>0` for every real `x`, so `det(M)>0`.  But the determinant of a
negative-semidefinite `3 by 3` matrix is nonpositive.  The stationary Hessian
therefore cannot be negative semidefinite, contradicting the second-order
condition for a local maximum.

Hence, for every fixed positive light profile, the heavy-variable maximum is
attained with at least one of `p_3,p_5,p_7,p_8` equal to zero.  Combined with
the previous lemma, this removes the entire fully coupled heavy interior.
The atom proof is now reduced to the four three-heavy boundary families; it
does not yet follow solely from the five primitive-face lemma.

## Lemma (classification of the three-heavy relative interiors)

Assume all five light variables are positive and exactly three heavy
variables are positive.  None of the four resulting relative interiors can
contain a maximizer of `(A)`.

First set `p_5=0` and abbreviate

`a=p_0, b=p_1, c=p_2, d=p_4, e=p_6,`
`r=p_3, t=p_7, u=p_8, z=sqrt(R), w=sqrt(3abc/2)`.

The heavy KKT equations imply `b=a+x`, `z=dk`, and `k=e+h` with `x,h>0`.  Three of
the remaining equations are linear in `c,t,u`; their coefficient determinant
is

`-a^2 b d^2 k(a-b)(e-k)^2`,

which is nonzero in the positive relative interior.  After this exact linear
elimination, one equation solves for `d`, and the cross-class equation factors
as

`x(a+x)(12ae+14ah+9eh-3h^2)=0`.                         `(E)`

Put `v=h/e` and `y=x/e`.  Positivity and `(E)` give `v>3` and

`a/e=3v(v-3)/(2(7v+6))`.

The normalization and light-radical equations then independently give

`e_N=6(v-3)(v+1)(7v+6)`
`    /[v(29v+21)(3v^2+14vy-9v+12y)]`,

`e_W=54(v-3)^2(v+1)(7v+6)`
`    /[v(11v+21)^2(3v^2+14vy-9v+12y)]`.

Every denominator is positive for `v>3,y>0`, and their difference factors as

`e_N-e_W=-24(v-3)(v+1)(5v-42)(7v+6)^2`
`          /[v(11v+21)^2(29v+21)(3v^2+14vy-9v+12y)]`.

Hence `v=42/5` and `a/e=21/20`.  Restoring the normalization shows that this
is the complete one-parameter stationary ridge

`p_0=21rho/20,                    p_1=47/686,`
`p_2=235/(117649rho),             p_6=rho,`
`p_4=54/343-41rho/20-235/(117649rho),`
`p_3=188/343-47rho/5,             p_7=94/343,`
`p_8=47rho/5-94/343,              p_5=0`.               `(F)`

Here positivity of `p_3,p_8` requires `10/343<rho<20/343`.  Direct exact
substitution gives the constant target gap

`(L+H/4)^2-q_0-2sqrt(R)-2sqrt(3p_0p_1p_2/2)=48/2401`.

More importantly, the derivative obtained by transferring mass from `p_8`
to the missing coordinate `p_5` is

`3(343rho-10)(2470629rho^2-579670rho+9400)`
`/[33614rho(4823609rho^2-370440rho+4700)]`.             `(G)`

The two quadratic factors in `(G)` have respective endpoint values
`(-5400,-16000)` and `(-2000,-500)` on
`[10/343,20/343]`.  Both are convex, hence negative throughout that interval;
all other factors are positive.  Thus `(G)>0`, so every point of `(F)` is
unstable toward the missing heavy channel and cannot be a maximizer of the
full problem.  The atom automorphism proves the same statement for `p_8=0`.

For the other orbit, set `p_3=0`.  The heavy KKT equations give
`b=a+x`, `z=ek`, and `p_5=(d(a+x)-xk)/a`.  Exact row reduction of the
`p_4-p_6`, `p_5-p_8`, and `z^2=R` equations gives

`(d-k)p_7=0`.                                             `(H)`

Since `p_7>0`, equation `(H)` forces `k=d` and consequently `p_5=d`.
At these values the radical equation and the remaining heavy equation have
left sides whose sum is

`(a+x)(d+p_8)=p_1(p_4+p_8)>0`,

so they cannot both vanish.  Therefore this relative interior has no
stationary point at all.  The atom automorphism gives the same exclusion for
`p_7=0`.

Consequently a global maximizer with all five light coordinates positive has
at least two zero heavy coordinates.  The exact atom proof is now reduced to
the six two-heavy faces and their descendants, together with strata on which
at least one light coordinate is zero.  The symbolic identities in `(E)`--`(H)`
are checked by the executable reduction script.

## Lemma (three of the six two-heavy faces)

The face with heavy support `{p_3,p_7}` is already the fifth primitive face
proved by `(B)`--`(C)`.  Two further faces reduce to the same envelope.

Consider heavy support `{p_3,p_8}`.  For fixed light variables and heavy sum
`H`, maximization over the two heavy coordinates is `H y`, where `y` is the
largest eigenvalue of

`M=[[p_2+p_4, sqrt(p_4(p_0+p_6))],`
`   [sqrt(p_4(p_0+p_6)), p_0+p_6]]`.

Let the other eigenvalue be `z` and put `x=p_1`.  Then

`y+z=p_0+p_2+p_4+p_6`, `yz=p_2(p_0+p_6)`,

so `x+y+z=L`.  The light-only quadratic part is

`p_0p_1+p_0p_2+p_1p_2+p_1p_4+p_2p_6`
` <=x(y+z)+yz`,

with exact slack `p_1p_6`.  Likewise

`p_0p_1p_2<=xyz`,

with product slack `p_1p_2p_6`.  Therefore the complete face objective is
bounded by `(B)`, and `(C)` proves the target inequality.  The atom
automorphism sends this face to `{p_5,p_7}`, proving that face as well.

Thus only three two-heavy faces remain: the symmetric pair `{p_3,p_5}` and
`{p_7,p_8}`, and the invariant face `{p_5,p_8}`.  Their lower-dimensional
boundaries and the zero-light strata remain part of the exact gate.

## Lemma (the three residual two-heavy faces)

None of the three residual two-heavy relative interiors can maximize `(A)`.

On `{p_3,p_5}`, write `a=p_0`, `c=p_2=a+x`.  Interior heavy stationarity
forces

`sqrt(R)=(a+x)p_4p_6/x`, `p_5=(a+x)p_4p_6/x^2`, `x>0`.

The `p_1-p_6` light equation then gives

`p_1=(a+x)(x-p_6)/x`,

so positivity implies `x>p_6`.  After these substitutions, let `E_4`,
`E_2`, and `E_cross` denote the remaining cleared KKT equations.  Exact
elimination gives the especially short identity

`E_2-x E_4=a p_4(2p_6-x)`.

Thus `x=2p_6`.  The two remaining KKT equations together with
`2w^2=3p_0p_1p_2` have a lexicographic elimination polynomial

`p_6^2(4p_6+7)(1372p_6-5)`.

There is therefore exactly one positive solution.  In vertex order it is

`(p_0,p_1,p_2,p_3,p_4,p_5,p_6,p_7,p_8)`
`=(3/49,47/1372,47/686,94/343,20/343,94/343,5/1372,0,0)`.

Its target gap is again `48/2401`, while the derivative obtained by moving
mass from `p_3` to the missing coordinate `p_8` is `24/49>0`.  It is not a
maximizer of the full problem.  Symmetry closes `{p_7,p_8}`.

Finally consider the invariant face `{p_5,p_8}` and put
`sqrt(R)=p_4p_6k`.  Heavy stationarity, the `p_4-p_6` light equation, and
`z^2=R` give

`p_1=(p_4k-p_5)(p_6k+p_5)/(p_5+p_8)`,

`p_2=(p_4k+p_8)(p_6k-p_8)/(p_5+p_8)`,

`w=-p_0(p_5-p_4k)(p_8-p_6k)/(p_5+p_8)`.

Positivity of `p_1,p_2` forces `p_4k>p_5` and `p_6k>p_8`.  Both factors in
the numerator of the last display are then negative, so its right-hand side
is strictly negative, contradicting `w=sqrt(3p_0p_1p_2/2)>0`.  This face has
no positive stationary point.

All six two-heavy relative interiors are now closed.  Every support with at
most one heavy coordinate is contained in one of the five primitive faces,
so `(A)` holds there.  Consequently `(A)` is proved on the entire stratum
where all five light coordinates are positive.  What remains is the union of
the five zero-light boundary strata; these cannot be silently removed by the
interior KKT argument and require a separate boundary proof.

## Theorem (completion of the last SCF atom)

The zero-light boundary admits two direct sum-of-squares certificates, which
complete `(A)` on the full nonnegative simplex.

First take `p_0=0` and abbreviate

`K=p_1p_8+p_2p_5+(p_3+p_5)(p_7+p_8)`,

so `R=p_4p_6K`.  With `T=(L+H/4)^2`, exact expansion gives

`16(T-q_0-4p_4p_6-K/4)`
` =(4p_1-4p_2+p_3-4p_4+p_5+4p_6-p_7-p_8)^2`
`  +48p_1p_2+48p_1p_4+12p_1p_8+12p_2p_5+48p_2p_6`.    `(I)`

Every term on the right is nonnegative, while

`4p_4p_6+K/4-2sqrt(p_4p_6K)`
` =(2sqrt(p_4p_6)-sqrt(K)/2)^2>=0`.                       `(J)`

Equations `(I)`--`(J)` prove `(A)` on `p_0=0`.

If `p_4=0`, only `R=p_0p_5p_6p_7` survives.  For fixed light variables and
heavy sum, the heavy maximum is either the `p_3` vertex, the `p_8` vertex, or
the largest-eigenvalue allocation on the `{p_5,p_7}` block.  Each of these
supports lies in one of the five primitive faces, so `(A)` follows from
`(B)`--`(C)`.  Atom symmetry proves `p_6=0`.

If exactly one of `p_0,p_1,p_2` vanishes while the other two are positive,
turning on the missing coordinate by `epsilon` increases
`2sqrt(3p_0p_1p_2/2)` by a positive multiple of `sqrt(epsilon)`.  Maintaining
the linear normalization changes the polynomial terms and the target by only
`O(epsilon)`.  Such a point therefore cannot maximize the violation.
The only boundary not already covered by `p_0=0` and symmetry is consequently
`p_1=p_2=0`.

On that final boundary put

`K=p_0(p_3+p_7)+p_4(p_7+p_8)+p_6(p_3+p_5)`.

Two more exact identities apply:

`16(T-q_0)=(4p_0+4p_4+4p_6-p_3-p_5-p_7-p_8)^2+16K`,    `(K)`

and, for

`(x_1,...,x_6)=(p_0p_3,p_0p_7,p_4p_7,p_4p_8,p_6p_3,p_6p_5)`,

`K^2-4R=(x_1-x_2-x_3-x_4+x_5+x_6)^2`
`        +4x_1x_2+4x_1x_3+4x_2x_5>=0`.                  `(L)`

Thus `(K)` gives `T-q_0>=K`, and `(L)` gives `K>=2sqrt(R)`, proving `(A)`.

For completeness, if `R=0` in the positive-light stratum, positivity of
`p_0,p_1,p_2,p_4,p_6` forces at most one heavy coordinate to be nonzero, so
the point lies in a primitive face.  Otherwise all differentiations used in
the heavy-face lemmas are legitimate.  Compactness of `2L+H=1`, the
square-root boundary argument above, the exhaustive heavy-support
classification, and `(I)`--`(L)` therefore cover every point.

Consequently the last atom `HEhu|x|` with weights
`(1/2,1/2,1/2,1,1/2,1,1/2,1,1)` satisfies `beta(G,w)<=3/2` exactly.  Equality
is attained classically, hence `beta(G,w)=alpha(G,w)=3/2`.  All algebraic
identities in this completion are checked symbolically by the executable
reduction script.

## Proposition (four one-hole residual types)

Four further residual weighted-support types have graph6 strings `HCXmtiz`,
`GQuvSw`, `HCZTmyz`, and `HQjRexz` (representative indices 5, 7, 9, and 33).
Each has exactly one induced four-hole.  Its heavy vertices form a clique,
the hole alternates between two heavy and two light vertices, every
independent triple is light-only, and no vertex is anticomplete to the hole.
Consequently, in the extremal generalized-cycle sector,

`e_2=q_0+2sqrt(product_(i in C)p_i)`

and `e_3` is the ordinary sum of the light independent-triple monomials.

Fix the total light mass `L` and hence the heavy mass `1-2L`.  For the two
heavy vertices in the hole, maximizing over their allocation gives the top
eigenvalue `y` of the positive semidefinite matrix

`[[A,sqrt(p_rp_s)],[sqrt(p_rp_s),B]]`,

where `A,B` are their light non-neighbour masses and `r,s` are the two light
hole vertices.  Let `z` be the other eigenvalue and
`x=L-A-B`.  Direct expansion, separately for all four graphs, gives

`q_light <= xy+xz+yz`, `e_3<=xyz`, and `x,y,z>=0`.

For every remaining scalar heavy branch, its non-neighbour mass is one of
three aggregate variables `y`; an explicit partition of the other light
vertices into aggregates `x,z` again gives the same two inequalities.  The
differences are sums of monomials with nonnegative integer coefficients; the
complete partitions and slacks are stored in `scf_one_hole_certificates.json`.
If `y` is not the largest aggregate, replacing it by the largest can only
increase the term `(1-2L)y`, while leaving the symmetric terms unchanged.
Thus every heavy branch is bounded by the already proved envelope

`xy+xz+yz+(1-2L)y+2sqrt((3/2)xyz)`, `x+y+z=L`.

Its fixed-`L` maximum is `L(1-2L)` for `L<=1/6` and
`(1/4+L/2)^2` for `L>=1/6`.  The former is itself at most the latter because

`(1/4+L/2)^2-L(1-2L)=(6L-1)^2/16`.

The spectral crossing argument used for the final atom therefore proves
`beta(G,w)<=3/2` for all four one-hole types.  Maximum stable sets attain
equality.  Together with the 115 join reductions and `HEhu|x|`, this makes
120 of the 128 order-nine non-rank SCF facet types exact; eight residual types
remain only numerically certified at this stage.

## Proposition (two collapsible two-hole residual types)

Residual types `HQjRezu` and `HQjdvZu` (indices 34 and 48) each have two
induced four-holes whose charge operators anticommute, so their squared
fourth-order contribution is the sum of the two hole monomials.

For `HQjRezu`, both holes use the same heavy pair `{0,8}`.  Their two light
pairs share `p_7`, hence the effective squared off-diagonal entry is
`p_7(p_1+p_3)`.  The heavy-simplex maximum is again one `2 by 2` block plus
the isolated heavy-2 branch.  With the other eigenvalue and unused light mass
as the remaining aggregate variables, exact expansion gives

`q_slack=p_5(p_1+p_3+p_7)`,
`e_3_slack=p_5(p_1p_4+p_3p_4+p_6p_7)`.

The isolated branch has

`q_slack=p_1p_6+p_3p_6+p_4p_7`,
`e_3_slack=p_4p_6(p_1+p_3+p_7)`.

For `HQjdvZu`, the two heavy leaves `0,2` have exactly the same light
non-neighbour score `p_1+p_3`.  An orthogonal rotation combines their heavy
amplitudes; the direction perpendicular to the two cycle couplings decouples.
The remaining effective block has squared off-diagonal `p_1p_7`.  Its slacks
are

`q_slack=p_5(p_1+p_7)`,
`e_3_slack=p_5(p_1p_4+p_3p_7)`.

The isolated heavy-6 branch has

`q_slack=p_1p_3+p_4p_7`,
`e_3_slack=p_3p_4(p_1+p_7)`.

All displayed expressions are nonnegative.  Both graphs therefore reduce to
the same proved three-variable envelope and satisfy `beta=alpha=3/2`.
The executable exact audit verifies the graph structure, cycle
anticommutation, profile equality, determinants, and every polynomial slack.
The order-nine exact count is now 122 of 128 at this stage.

## Proposition (the commuting cycle triangle `HEhutx~`)

Residual type 26 has three pairwise commuting hole charges.  In the oriented
cycle convention their exact relations are `h_0h_1=h_2`, `h_0h_2=h_1`, and
`h_1h_2=h_0`; hence the all-positive sector is admissible and maximizes their
positive coefficients.  On heavy vertices `{3,7,8}`, the fixed-light
quadratic form is

`M=diag(p_2,p_1,0)+u u^T`,
`u=(sqrt(p_4),sqrt(p_6),sqrt(p_0))`.

It is positive semidefinite.  Direct symbolic expansion gives

`tr(M)=L`,
`e_2(M)=p_0p_1+p_0p_2+p_1p_2+p_1p_4+p_2p_6=q_light`,
`det(M)=p_0p_1p_2=e_3`.

Thus the three eigenvalues of `M` are exactly the three nonnegative aggregate
variables required by the proved fixed-`L` envelope, and the largest one is
the heavy-simplex branch coefficient.  The sole isolated heavy vertex 5 uses
aggregates `(x,y,z)=(p_1,p_0+p_4+p_6,p_2)` and has exact slacks

`xy+xz+yz-q_light=p_2p_4+p_1p_6`,
`xyz-e_3=p_1p_2(p_4+p_6)`.

Therefore `HEhutx~` also satisfies `beta=alpha=3/2`.  The executable audit
checks the oriented Pauli-word relations and all three spectral invariants
symbolically.  The exact order-nine count is now 123 of 128, leaving five
residual types.

## Proposition (the signed commuting-cycle type `HQjVJr\`)

The three oriented hole charges of residual type 44 obey
`h_0h_1=-h_2`, `h_0h_2=-h_1`, and `h_1h_2=-h_0`.  Hence their sector signs
satisfy `s_0s_1s_2=-1`.  Put

`a=sqrt(p_1p_6)`, `b=sqrt(p_2p_7)`, `t=s_0s_1`,

so `s_2=-t`.  The two mixed-hole terms form a heavy `{0,8}` block with
off-diagonal `s_0a+s_1b`; the all-light hole changes the scalar light term by
`-2tab`.  The block diagonals are

`A=p_1+p_3+p_7`, `B=p_2+p_6`,

and the unused light mass is `x=p_4`.  For both `t=+1` and `t=-1`,

`det M=(sqrt(p_1p_2)-t sqrt(p_6p_7))^2+p_3(p_2+p_6)>=0`,

while exact expansion gives

`x(A+B)+det M-(q_light-2tab)=p_4(p_2+p_7)>=0`,

`x det M-e_3`
` =p_4[(sqrt(p_1p_2)-t sqrt(p_6p_7))^2+p_2p_3]>=0`.

Thus every mixed-hole sector reduces to the proved three-variable envelope.
For the isolated heavy-5 branch choose

`(x,y,z)=(p_1+p_3,p_2+p_4+p_7,p_6)`.

The positive all-light channel is absorbed by

`xy+xz+yz-q_light-2sqrt(p_1p_2p_6p_7)`
` =(sqrt(p_1p_7)-sqrt(p_2p_6))^2+p_1p_6+p_3p_7>=0`,

and `xyz-e_3` is a sum of five nonnegative cubic monomials.  Hence
`HQjVJr\` satisfies `beta=alpha=3/2`.  The exact count is 124 of 128; the
remaining representatives are 15, 23, 24, and 25.
