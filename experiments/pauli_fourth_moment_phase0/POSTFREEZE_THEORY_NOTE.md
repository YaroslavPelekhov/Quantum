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
