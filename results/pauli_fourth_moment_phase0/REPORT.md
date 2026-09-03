# Pauli fourth-moment / quantum-convolution phase 0

Date: 2026-09-03

## Verdict

The frozen weighted fourth-moment claim

`beta_4(G,w) = alpha(G,w)`

survived every completed numerical falsification test, including exhaustive
six-qubit separation over all `4,922,775` maximal commuting contexts.  It is
**not proved** and therefore is **not yet an A-star result**.

The experiments exposed a stronger candidate: the three-input qubit quantum
convolution of arbitrary states may always lie in the stabilizer polytope.
If true, it would imply the weighted stable-set inequality already at
exponent `3`, and therefore the universal fractional-colouring bound

`chi_f(G(B_epsilon)) <= epsilon^-3`.

This stronger statement also remains a conjecture.  No claim of confirmation
is made from numerics alone.

## Results that did survive

### Exact small-system stabilizer membership

For three independent Haar inputs, direct stabilizer-polytope LPs found no
triple-convolution violation:

| qubits | contexts | stabilizer vertices | trials | largest gauge |
|---:|---:|---:|---:|---:|
| 1 | 3 | 6 | 5,000 | 0.9324363156 |
| 2 | 15 | 60 | 5,000 | 0.8453893479 |
| 3 | 135 | 1,080 | 2,000 | 0.6779604221 |
| 4 | 2,295 | 36,720 | 100 | 0.4402937237 |

The gauge is at most one exactly for stabilizer mixtures.

### Exhaustive six-qubit separation

The six-qubit oracle scans all `4,922,775 x 64 = 315,057,600` pure
stabilizer states for signed witnesses, or all maximal commuting contexts for
nonnegative witnesses.

The committed generator rebuilt the 59 MB context cache independently in
24.7 seconds.  Its SHA-256
`bb1c58c87535192dd6405e4ac01cbfa292aa482f93929de522870abc78a46372`
matched the original research cache byte for byte.

- Frozen `p=4` claim: 80 dense/sparse witnesses, 384 state starts per witness,
  2,400 gradient steps, and six near-stabilizer perturbation scales.  Best
  normalized value: `1.0000000000000009`.
- Arbitrary three-input convolution: 30 signed dense/sparse witnesses, 160
  triples per witness and 2,200 steps.  Best normalized value:
  `1.0000000000000009`.
- Strong proof shortcut
  `max_i r_i^2 * sum_i w_i r_i^2 <= alpha(G,w)`: 40 dense/sparse witnesses,
  320 starts and 2,200 steps.  Best normalized value:
  `0.9999999999999382`.

Values within roughly `1e-15` of one are the deliberately included exact
stabilizer boundary controls, not evidence of a violation.

### Explicit six-qubit commuting covers

The stored certificates list genuine maximal commuting contexts and
nonnegative weights.  An independent verifier recomputes the state, Pauli
profile and cover.  Tiny negative LP slacks are corrected conservatively by
adding one containing context per deficient Pauli; every Pauli extends to a
maximal commuting context.

| profile | state | contexts | corrected cover weight |
|---|---|---:|---:|
| `|r|^3` | Haar | 351 | 0.6338726820205092 |
| `|r|^3` | distance-angle 0.15 from a stabilizer | 284 | 0.9674601769760257 |
| `r^4` | distance-angle 0.15 from a stabilizer | 268 | 0.9393478505014052 |

All three corrected weights are strictly below one.

### Complete graph-atlas shortcut test

All 1,252 nonempty non-isomorphic graphs on at most seven vertices were
tested with uniform and seeded log-normal weights (`2,504` cases).  No
violation of the strong shortcut was found.  The largest ratio was
`1.0000000000000024`, numerical equality at the stabilizer boundary.

### Why the shortcut still needs Pauli structure

The tempting abstract lift

`x in TH(G)  =>  max_i(x_i) x in STAB(G)`

is false.  A capped theta-body SDP found a ten-vertex counterexample with
uniform weights: `alpha(G)=4`, `max_i x_i=0.96`, and
`sum_i x_i=4.1866252598`, giving ratio `1.0047900622`.  The stored moment
matrix has minimum eigenvalue `-3.12e-10` and maximum affine residual below
`1e-11`; the violation is about four orders of magnitude larger.  Thus a
proof of the physically surviving shortcut must use constraints special to
Pauli expectation profiles, not theta-body membership alone.

## Proved auxiliary theorem

For every odd convolution order `K >= 3`, arbitrary unequal mixed inputs,
and every postselected stabilizer protocol with a one-qubit output, the
logical output is in the one-qubit stabilizer octahedron.  The proof resolves
each stabilizer-code syndrome branch into a convex mixture of componentwise
products of valid Bloch vectors; Holder's inequality bounds their `l1` norm
by one.  The fixed-branch stabilizer normal form extends the rank-two-code
argument to arbitrary one-output-qubit stabilizer protocols.

This is a genuine dimension-independent theorem, but it does not by itself
prove that the full many-qubit convolution output is a stabilizer mixture.
That missing higher-logical-dimensional step is exactly where the A-star
claim now lives.

As a separate algebra audit, direct density-matrix simulation of the CNOT
convolution was compared against the syndrome-mixture formula on 400 mixed
and 400 pure three-qubit postselection branches.  The largest identity errors
were `5.0e-16` and `5.32e-16`, respectively, and every reconstructed logical
Bloch vector was strictly inside the stabilizer octahedron.

### One-logical tests are provably incomplete globally

An exhaustive three-qubit test now makes the boundary above explicit.  For
2,000 seeded depolarizing rays, it enumerated all `315` rank-two stabilizer
codes, all four syndromes (`1,260` logical branches), and all `1,080` pure
stabilizer vertices.  It found a physical state with visibility
`0.3358463460` such that:

- every one-logical branch is inside the octahedron, with worst unnormalized
  excess `-0.0294439753` and every branch probability strictly positive;
- the state is outside `STAB_3`, with stabilizer gauge `1.0312863653`;
- a rounded integer separating witness attains exactly `1` on all stabilizer
  vertices and `1.0312863653` on the state.

Therefore the one-logical theorem cannot be promoted to global stabilizer
membership by a completeness argument.  A proof of the triple-convolution
conjecture must directly control genuinely multi-logical stabilizer facets.

### First genuinely multi-logical facet class proved

The integer separator above has a hidden spin-factor decomposition

`W = -C + sum_{j=1}^5 (A_j + C A_j)`,

where `C` commutes with all five `A_j` and the `A_j` pairwise anticommute.
Syndrome decomposition with respect to `C`, followed by Holder's inequality
on the five-dimensional conditional expectation vectors, proves exactly
that every odd-order (`K >= 3`) convolution of arbitrary inputs satisfies
`Tr(W tau) <= 1`.  The same argument works for any number of axes and any
Clifford image of this witness form.

As a numerical algebra check, 5,000 alternating product-state optimizations
for the extracted three-qubit witness reached
`1.0000000000000047`, equality to floating-point precision.  This is the
first proved higher-logical facet family in the project.  It is meaningful
progress toward the global conjecture, but it is not a classification of all
stabilizer facets and therefore does not close the A-star gate.

### Dimension-independent CNC-positivity theorem

The spin-factor proof combines with the known classification of maximal
closed-noncontextual (CNC) phase-point operators.  Up to a Clifford, each is
an anticommuting spin factor tensored with a stabilizer-code projector.
Consequently, for every maximal CNC operator `A` and arbitrary inputs,

`Tr[A boxtimes_K(rho_1,...,rho_K)] >= 0` for every odd `K >= 3`.

This covers a global, dimension-independent family of stabilizer-polytope
inequalities, including genuinely multi-logical ones.  The proof uses the
positive syndrome convolution followed by Holder on each conditional spin
factor.  It does **not** assert that the output belongs to the CNC simulation
polytope or the stabilizer polytope.

A direct canonical-form audit covered spin dimensions one through three,
zero through two syndrome qubits, convolution orders three and five, and 300
random sign/input instances per case (`5,400` total).  Every overlap was
positive; the smallest was `0.0289932941`.  This audit checks the convention
and normalization layer but is not used in place of the proof.

This is now the strongest theorem-level novelty candidate in the branch.
The CNC factorization itself is known; the checked CNC and convolution
literatures do not state their combination or the resulting positivity
theorem.  A-star status remains provisional until independent proof and
submission-grade prior-art audits are completed.

### Exact weighted exponent two on all Pauli line graphs

The initial powered-blossom argument gave exponent three, but an adversarial
free-fermion check strengthened it before claim freeze.  If the Pauli
anticommutation graph is the line graph `L(H)` of any graph `H`, then

`(<P_e>^2)_e in MATCH(H) = STAB(L(H))`.

Therefore, for every nonnegative weight vector,

`max_rho sum_e w_e Tr(rho P_e)^2 = nu(H,w)`.

For the canonical Majorana realization, the expectations form a real
antisymmetric covariance contraction.  Squared row norms give the matching
degree inequalities; every odd principal submatrix has rank at most
`|S|-1`, which gives every Edmonds blossom inequality.  Known invariance of
the weighted beta radius across Pauli realizations transfers the result to
all realizations of the same line graph.

This is not a perfect-graph corollary: line graphs can be imperfect (odd
cycles are elementary examples), while the result is weighted and exact.
It proves the original `chi_f <= epsilon^-2` bound on this entire class and
extends CNC positivity to the published Jordan--Wigner line-graph phase
points.  A seeded audit over Majorana realizations of every one of the 1,245
nonempty graph-atlas roots on two through seven vertices, 81 additional
random roots through nine vertices, 8,220 random-state instances, and 1,326
exact weighted-matching boundary controls found no blossom or weighted
violation.  Every boundary control attained one to numerical precision; the
largest random weighted ratio was `0.8958169`.  The initial targeted
prior-art search found free-fermion solvability, representation invariance,
and matching-polytope ingredients,
but not the squared-profile matching theorem stated in this form.  Because
the ingredients are close, its novelty status still requires a careful
expert audit.

## Prior-art status

The closest checked papers are:

- Bu--Gu--Jaffe (arXiv:2306.09292v2): convolution multiplication, Clifford
  covariance and stabilizer-input closure, but not arbitrary-input global
  magic breaking.
- Wang et al. (arXiv:2511.13531): generalized `beta(G,w,k)` and convergence
  only as `k -> infinity`.
- Liu et al. (arXiv:2607.26154v1): the closest squared-profile treatment; it
  separates weighted second moments from the unweighted fourth collision and
  does not give the weighted exponent-three or exponent-four theorem.
- Stempin--Llorens--Huber (arXiv:2608.20113): explicitly leaves existence of
  any finite universal exponent open and proves the lower exponent
  `2.07598...`.
- Patra et al. (arXiv:2409.04425): one-qubit magic-breaking criteria, but not
  the correlated many-qubit convolution statement.
- Raussendorf et al. (PRA 101, 012350), Ipek et al. (PRA 113, 032409), and
  Okay (Res. Math. Sci. 13, 55) provide the CNC phase-space framework and
  anticommuting-factor classification.  They do not state the odd-convolution
  CNC-positivity theorem found here.
- General theta-body/antiblocker literature supplies the standard
  `STAB(G) subset TH(G) subset QSTAB(G)` inclusions, but the explicit SDP
  counterexample above rules out the particular nonlinear scaling needed
  here.

No direct theorem collision was found.  The audit remains open until a
submission-ready literature search and independent proof reconstruction are
complete.

## What was falsified or ruled out

- Generic theta-body nonlinear scaling is false and cannot prove the
  Pauli-specific claim; an explicit feasible ten-vertex counterexample is
  stored.
- Clique uncertainty alone cannot certify arbitrary stable-set facets.
- Uniform four-copy stabilizer-frame marginals decay with dimension and do
  not yield a universal constant.
- One-logical-qubit freeness cannot be identified with membership in the full
  many-qubit stabilizer polytope; an exact three-qubit vertex/witness audit
  now separates the two notions.
- Numerical survival, even against the complete six-qubit oracle, is not a
  theorem.

## Next decisive gate

The next cycle must do one of two things:

1. prove that arbitrary three-input convolution is globally
   stabilizer-breaking, which would give the stronger exponent `3`; or
2. construct a higher-logical-dimensional stabilizer witness that violates
   it, then return to the frozen exponent-four claim without rebranding the
   failed stronger statement.

In parallel, the new CNC-positivity theorem needs independent proof
reconstruction and a complete literature audit.  It is a credible standalone
novelty route even if global stabilizer membership ultimately fails.

Additional random testing of the same scale is now secondary.  Real quantum
hardware is not the decisive validator for this theorem: the claim concerns
exact convex geometry, so hardware noise cannot confirm it.  Hardware becomes
relevant only after a constructive colouring/sampling protocol is derived.
