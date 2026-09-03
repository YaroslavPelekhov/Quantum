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

### Hidden free fermions: proved rank bounds and an open weighted conjecture

The next preregistered object change replaces generator-level line graphs by
the strictly larger hereditary class of simplicial claw-free (SCF) graphs.
Chapman--Elman--Mann showed that every Hamiltonian with such a frustration
graph has a symmetry-resolved hidden free-fermion solution.

One new theorem survives a complete normalization audit:

`beta(G,1)=alpha(G)` for every SCF graph `G`.

Indeed, for `A=sum_i a_i P_i`, the coefficient of `u^2` in the generalized
characteristic polynomial `T(u)T(-u)` is exactly `-sum_i a_i^2`.  Thus every
symmetry sector has `sum_j epsilon_j^2=sum_i a_i^2` and at most `alpha(G)`
positive modes.  The free-fermion spectrum and Cauchy--Schwarz give
`||A||^2<=alpha(G)sum_i a_i^2`; the variational identity for beta and a
maximum independent-set eigenstate give equality.  Since SCF is hereditary,
every squared profile also satisfies every induced-subgraph rank inequality.

The stronger weighted statement

`beta(G,w)=alpha(G,w) for every w>=0`

remains a conjecture.  It cannot be inferred from the rank theorem: 26 of the
tested SCF graphs have genuine non-rank stable-set facets.  We therefore
enumerated the stable-set vertices, extracted their facet directions, and
attacked all 32 unique non-rank directions using 512 starts and 320
iterations per facet.  The largest ratio
was `1.000000000000006`; no violation was found.

A second attack used the first state-moment SDP relaxation to generate an
optimistic squared profile for each facet, then tried 512 sign patterns of
that profile as Hamiltonian starts.  This method reproduces the published
narrow-basin `G9` gap at `3.0448154999`, but again gave no SCF violation: the
largest ratio was `1.0000000000000049`.  The relaxation upper ratios were all
about `1.118034`, so they do not certify the claim; they serve only as
deliberately nonclassical guides into potentially hidden basins.

The broader preregistered suite covered 280 unique non-line SCF graphs,
including every connected graph-atlas candidate through seven vertices, the
published eight-vertex hidden-free-fermion example, adversarial completed
neighborhoods, and 200 accepted random graphs through ten vertices.  It used
19 uniform, lognormal, integer, and sparse weights per graph and 32 starts per
weight.  Across 20,000 random proposals, the largest nonuniform SCF ratio was
`1.0000000000000089`.  The anti-heptagon positive control reproduced its
known ratio `1.0469181607`.

The graph search was then made exhaustive at order nine using Brendan
McKay's canonical connected-graph census.  Its 2,088,640 source bytes were
verified by SHA-256 before parsing.  All 261,080 connected graphs were
screened; the code recovered the published control count of 4,494 claw-free
graphs, of which 4,308 are SCF and 3,598 are non-line SCF.  Complete
stable-set vertex enumeration found 701 non-rank facet occurrences in 550
graphs.  Weighted-support isomorphism reduced them to 128 classes, all with
coefficients in `{1/2,1}`.  An SDP-profile attack then exhausted all 29,664
sign orthants across those 128 classes, with 320 fixed-point iterations per
orthant.  The largest lower-bound ratio was `1.0000000000000049`; no
violation was found.  First-level SDP upper ratios ranged from `1.0786893` to
`1.1690223`, so this is a complete census and exhaustive seeded attack, not a
global proof over the continuous state space.

The coefficient pattern then yielded a genuine analytic reduction.  In 115
of the 128 types, the coefficient-one vertices form a clique completely
joined to the coefficient-half vertices.  The support is therefore a join
`K join H`, with `alpha(H)=2`.  The beta join rule, the clique bound, and the
SCF rank theorem prove the corresponding weighted facet inequality exactly.
This closes 115 finite order-nine facet types without numerical assumptions.

The remaining 13 types all have unweighted independence number three and
weighted independence number `1.5`.  We ported the real state-moment SDP
hierarchy and first reproduced the published `G9` bounds: level 1 gives
`3.2360679896` versus `3.236068`, and level 2 gives `3.0448153335` versus
`3.044815`.  Level 2 then closes 12 of the 13 SCF residual types to tolerance
`2e-5`.  One explicit atom remains: graph6 `HEhu|x|`, weights
`(1/2,1/2,1/2,1,1/2,1,1/2,1,1)`.  Independent level-2 solvers give upper
bounds `1.50013566` and `1.50014217`; level 3 lowers the bound to
`1.5000415786`.  A tighter level-3 run was stopped after more than 1,300 CPU
seconds without a result.  The hierarchy is converging toward the classical
value, but the remaining `4.16e-5` relaxation gap is not a proof.

The atom can nevertheless be reduced exactly beyond the generic SDP.  Its
eight induced four-hole operators have only two commuting pairs; those pairs
multiply to the same Pauli word with opposite signs and equal coefficients,
so all exceptional cross terms cancel.  The extremal fourth-order
characteristic coefficient is therefore `q_0+2 sqrt(R)`.  Combining this
with the scalar first- and sixth-order coefficients reduces the desired
quantum bound to one explicit homogeneous inequality over nine nonnegative
variables:

`(L+H/4)^2 >= q_0+2 sqrt(R)+2 sqrt(p_0 p_1 p_2 D)`,

where `D=3L+(3/2)H`.  The operator reduction is exact and the scalar
inequality survived one million seeded interior-simplex samples, with minimum
observed gap `0.00171428` and equality on the expected boundary.  The scalar
inequality itself remains unproved; this is a dimensional collapse of the
last gate, not its numerical promotion.

A further analytic step closes every primitive single-channel boundary face
of the atom.  After `2L+H=1`, maximizing the two heavy variables on each of
the first five hole-generated faces gives three nonnegative variables
`x+y+z=L` and the upper envelope

`E=xy+xz+yz+(1-2L)y+2 sqrt((3/2)xyz)`.

For fixed `y`, this is increasing in `sqrt(xz)`, so `x=z=(L-y)/2` is the
worst case.  With `y=s^2/6`, the derivative and target gap factor exactly as

`dE/ds=-(s-1)(6L+s^2+4s)/12`,

`(1/4+L/2)^2-E=(s-1)^2(12L+s^2+6s+3)/48`.

Thus the fixed-`L` face maximum is `L(1-2L)` below `L=1/6` and the target
itself above `L=1/6`; all five primitive faces are proved.  The other three
hole-generated supports can activate three quartic monomials at once.  They,
and the fully coupled interior, remain open.  An independent 100,000-point
test on each of all eight faces found maximum value-minus-envelope
`-1.71626e-5`.  This is a strict reduction of the open mechanism: any
counterexample must use coupled hole channels, but the full scalar inequality
is not yet promoted to a theorem.

As an independent warm-state control, the published narrow-basin
`G9` instance was initialized from its reported approximate state.  The
objective moved from `2.9924593427` to `3.0448154987`, reproducing the
published weighted violation within `4.99e-7`; this is important because
ordinary random starts were reported to stop at the classical value `3.0`.

Finally, the pinned public benchmark files from Wang et al. were screened
structurally at upstream commit
`467eb611c09631fcf310da8dc73c35cb3b8fe098`.  None of the 18 known
eight-vertex or 1,419 known nine-vertex hbar-imperfect graphs is SCF.  Their
hard subsets contain 9 and 295 graphs respectively, again with zero SCF
members.  The files are downloaded by commit and checked byte-for-byte by
SHA-256 before classification.

This is the strongest current A-star route, but it is not yet an A-star
result.  The rank theorem is proved and plausibly novel; the order-nine
non-rank obstruction has been reduced from 128 types to one explicit atom.
The general weighted theorem still lacks a proof and external expert
prior-art review.

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

The immediate target is no longer another random search.  It is the single
order-nine atom `HEhu|x|`.  The decisive routes are:

1. prove a concentration lemma showing that coupled hole channels cannot
   exceed the now-exact primitive-face envelope; or
2. extract and rationalize a sparse dual/SOS certificate for the residual
   coupled-channel region, then verify the identity exactly.

A physical Pauli state with value above `1.5+1e-7` would instead falsify the
weighted conjecture.  Current see-saw lower bounds attain only the classical
value, whereas the SDP figures above are relaxation upper bounds and cannot
serve as physical counterexamples.

In parallel, the CNC-positivity theorem still needs independent proof
reconstruction and a submission-grade prior-art audit.  Real quantum hardware
is not the decisive validator for these exact convex-geometric claims;
hardware becomes relevant only after a constructive colouring or sampling
protocol is derived.
