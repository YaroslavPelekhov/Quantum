# Post-freeze theory note: convolution and one-logical-qubit extraction

Status: proved auxiliary statement, pending an independent proof audit and a
complete prior-art audit.  It is **not** a proof of preregistered claim T1.

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
