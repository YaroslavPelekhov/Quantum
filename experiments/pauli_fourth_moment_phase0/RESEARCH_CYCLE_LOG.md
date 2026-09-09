# Research cycle log

## C001 — registered 2026-09-06

Baseline: `7d9ed35`. Plan: [RESEARCH_PROGRAM_RU.md](RESEARCH_PROGRAM_RU.md).
Status: COMPLETE; finite structural coverage audit, not a quantum theorem.
Corpus and decision rules are frozen in section 6 of the plan before execution.

Read-only initial checks: worktree retains only the previously recorded
unrelated submodule/prior-art changes. All 13 residual support graphs were
screened against the known full two-qubit Pauli graph G15: none embeds as an
induced subgraph under NetworkX GraphMatcher. This is an exploratory
prior-art shortcut check, not a new proof or a priority certificate.

Current claim ledger:

- H-SCF, unrestricted weighted perfection: OPEN.
- Alpha<=2 and order<=9 scoped theorems: recorded proofs, external review pending.
- C001 one-pair separator route on the frozen corpus: DOES NOT COVER.
- Publication-level novelty: NOT CONFIRMED.

Exact result: 47 weighted types, 46 distinct graph6 inputs. All have a
two-clique separator. Minimum nonedge-pair counts are 1 for 36 types, 2 for
eight, and 3 for three. Two independent enumerators agree; P4/C4/K4 controls
pass. The 13 old residuals needing multiple pairs are type 15 (three) and
type 33 (two); the frontier adds nine such weighted cases.

Important limitation: this counts explicit boundary pair coordinates,
NOT the affine dimension of their feasible fibers. It rules out covering
the corpus using only separators with <=1 nonedge. It does not rule out a
deeper scalar reduction using additional identities or another decomposition.

Artifact: `results/pauli_fourth_moment_phase0/scf_separator_coverage.json`.
Verifier: `verify_scf_separator_coverage.py` (standard library, integer bitsets).

## C002 — registered 2026-09-06, before execution

Question: can pairwise-coordinate agreement replace simultaneous agreement
of all separator pair probabilities in the frozen SCF examples?

Corpus: all 11 C001 rows with minimum pair count >1, using exactly the saved
canonical separator and the original facet weights. Controls: the first
three C001 single-pair rows in saved order. No graph selection by beta values.

LP variables: a common vertex profile x and, FOR EACH boundary pair k,
separate left/right stable-set distributions with vertex marginals x.
Only the kth pair probability must agree for the kth copies. Include every
global induced-subgraph rank inequality. Maximize the original facet w.x.
This tests intersection of coordinate projections, not the full fibers.

If the maximum exceeds alpha(G,w), reconstruct a rational profile and all
per-coordinate local distributions and verify every constraint exactly.
The facet violation then proves that the full fibers are disjoint despite
overlapping every coordinate projection. This is an abstract marginal
counterexample, NOT a physical quantum counterexample. A numerically
nonpositive gap only records no witness for that chosen objective.

Use SciPy HiGHS for discovery, Fraction with maximum denominator 1,000,000
for candidate rationalization, reject unless all equalities, inequalities,
and strict violation hold exactly. No random seed is needed. The acceptance
verifier must not import SciPy, NumPy, or NetworkX. No automatic expansion
of graph order or paid compute is authorized by this protocol.

### C002 result — COMPLETE

Eight of 11 multi-pair attacks produce exact rational obstructions. Three
attacks and all three controls have no numerical violation for the tested
objective; no exact upper certificate is claimed for those six rows.
Type 33 supplies the cleanest example: either of two boundary coordinates
can separately agree, but their sum is forced to 1/4 on the left and 1/2
on the right. Exact local dual inequalities certify both forced sums.
The old weighted facet is violated by 1/8. See
[the boundary-route note](SCF_BOUNDARY_ROUTE_AUDIT.md) for the full example.

All eight witnesses pass a standard-library rational verifier. The combined
suite now passes 23 tests. H-SCF remains OPEN; these are abstract marginal
counterexamples, not quantum counterexamples or a new A-star claim.

## C003 — next cycle; prerequisite audit, not yet executed

Historical preregistration follows; this cycle is now complete (see result below).

Investigate the proposed closure of hbar-perfectness under a separator
which is a clique with one edge missing. This is a quantum statement,
stronger than the already proved classical one-pair gluing equivalence.

Before attempting a proof:

1. Read the exact graph-operation statements in Xu et al., including copy,
   split, join and induced-subgraph rules; check for a known closure result.
2. Freeze a structural screen on all 18 order-eight and 1,419 order-nine
   published imperfect benchmark entries at upstream commit
   `467eb611c09631fcf310da8dc73c35cb3b8fe098`. Verify the existing pinned hashes.
3. Search for clique-minus-one-edge separators with the C001 exact method.
   Do NOT call an imperfect graph alone a counterexample to closure: both
   sides must separately have rigorous hbar-perfectness certificates.
4. If a closure counterexample survives, extract/recompute a physical
   witness and certify the positive gap exactly. Numerical benchmark labels
   are discovery aids, not final proof. This would limit the generic rule,
   not H-SCF unless the combined graph is independently SCF.
5. If no counterexample appears, derive the operator statement explicitly;
   finite survival is not proof. Do not repeat C001/C002 under a new label.

This is the next bounded gate, not a promise that the closure statement is
true. The multi-pair case still requires simultaneous compatibility even
if this narrower closure can be proved.

Continuation is scheduled in the same task every two hours. Product usage
limits remain in force; no usage reset or paid resource was requested or used.

### C003 execution registration — 2026-09-06

Baseline `ce57a48`. No phase-zero Python calculations were running at start;
only the previously recorded unrelated worktree changes remain.

Primary-source check: Xu et al., arXiv:2511.13531v1, Section III and Appendix
A.1 explicitly cover join, disjoint union, induced subgraphs, lexicographic
product, false-twin copying and true-twin splitting. None of those displayed
statements is an almost-clique-separator closure theorem. The appendix swaps
the copy/split property numbering relative to the main text; use operation
names and definitions, not the number alone. Targeted phrase searches found
no matching separator theorem; this does not establish novelty.

Freeze the screen on all 1,437 pinned benchmark rows, in source order.
Enumerate EVERY proper separator with exactly one nonedge, not just the
minimum separator. Enumerate all unordered nonempty partitions of its
remaining components. Store all candidate decompositions and later require
separate exact local hbar-perfectness certificates before promoting a row
to a candidate counterexample to the quantum closure rule. Discovery uses
integer bitsets; verification will independently use graph-library
connectivity/nonedge enumeration. Positive structural control: C4; negative
control: K4. No quantum claim follows from a benchmark label alone.

### C003 witness-extraction subprotocol — before optimization

The screen finds 39 decompositions on nine order-eight entries and 5,314
on 851 order-nine entries. Select the FIRST benchmark row, `GCrdrk`, which
is the unique order-eight entry without an induced anti-C7. Its first
separator is S={0,6,7}, with nonedge {0,7}. The sides have seven and four
vertices. The seven-vertex side is not SCF, so do not use the SCF theorem on
it directly. An exact preliminary hull has only clique facets and one
rank facet supported on six vertices; certify that support and independently
verify completeness of the hull before claiming local hbar-perfectness.

The full graph's unique full-support facet is
`(1,1,1,1,1,1,2,2).x<=3`. Use the pinned three-qubit Pauli realization in
that benchmark row. Search at most 128 relative sign starts, at most 512
see-saw iterations each; no QPU or paid resource. Accept only an explicit
Gaussian-integer state whose rational squared-expectation value exceeds
the exact enumerated stable bound. Try deterministic rounding scales
1,2,3,4,5,8,10,16,32,64,128,1000,10000. Numerical survival/failure is not a
certificate. Discovery state precision may be reduced only after checking
the exact positive gap. No claim to discovery of the published G8 graph.

### C003 result — COMPLETE, generic quantum closure falsified

The selected G8 has two rigorously hbar-perfect local sides but is not
hbar-perfect globally. The exact three-qubit state is
`(3,2,3,8,-5,2,-3,-1)/sqrt(125)`, for the published Pauli realization and
weights `(1,1,1,1,1,1,2,2)`. Its value is `47431/15625`, exceeding the exact
bound three by `556/15625`. Every global rank inequality still holds.

On the single boundary event, exact local bounds are incompatible:
left y<=2036/15625, right y>=2592/15625. Both local all-weight perfection
proofs have independent rational polytope-completeness certificates.
The left side is NOT SCF; its only nonclique facet is supported on a
six-vertex SCF graph. The full graph has a claw centered at 0 with leaves
3,4,5. H-SCF is therefore NOT falsified. An elementary positive-weight
true-twin extension preserves the obstruction for every larger graph order;
this is not presented as a new graph-family discovery.

Independent checks cover all 1,437 source rows, all 5,353 decompositions,
and the exact physical/local certificate. Thirty combined tests pass.
See [the C003 proof](ALMOST_CLIQUE_CLOSURE_COUNTEREXAMPLE.md).
The generic almost-clique rule is CLOSED AS FALSE, not left as a candidate.

Clean-archive reproduction: commit `eb055ff` was exported with `git archive`
to a new temporary directory, without the local prior-art checkout. All
30 tests passed there. Both C003 discovery scripts were rerun against the
hash-verified immutable upstream inputs; their regenerated JSON files
matched the committed hashes. All 49 artifact hashes and both independent
C003 acceptance checks passed after regeneration.

## C004 — next proof cycle, not yet executed

Aim: determine whether GLOBAL claw-free/SCF structure supplies an operator
inequality absent from generic local hbar-perfectness. Do not repeat the
already refuted unconditional closure rule or enlarge a census without
a new discriminating mathematical question.

Start with a separator having one nonedge {u,v}. The operator P_u P_v
commutes with every separator observable. Outside observables may commute
or anticommute with it according to their neighborhoods of u and v.
Derive exactly which pairs of neighborhood patterns across the two sides
are excluded by GLOBAL claw-freeness, then state a concrete, falsifiable
operator inequality using those exclusions. The commutation fact alone
does not imply that P_u P_v is central in the full observable algebra.
The C003 witness already has `P0 P7=IYY` central on the entire right side,
so one-sided centrality alone is insufficient and must not be proposed as
an untested repair of generic closure.

Before numerical work, write the lemma and check it against the exact G8
negative control (which must fail its structural hypotheses) and the
already proved SCF residuals with one-pair separators. If the proposed
operator bound is merely the desired global weighted inequality in new
notation, record the circularity and use the transfer/SOS route instead.
Only then freeze a bounded experiment or attempt the analytic proof.

Main H-SCF: OPEN. A-star novelty: NOT CONFIRMED. All C003 results are local
classical computation and exact mathematics, not QPU measurements.

### C004 execution registration — 2026-09-06, before computation

Baseline `67ab582`. No Python research processes are running. Preserve the
unrelated submodule, prior-art checkout and figure files.

First prove the exact cross-claw criterion: for L=A-S and R=B-S anticomplete,
assuming both local graphs claw-free, a new claw can only be centered in S.
Its leaves either comprise two nonadjacent neighbors in one outside side
and one in the other, or one neighbor in each outside side and a third in S.
The latter forbids boundary neighborhoods F,G with a common center s and
an adjacent boundary vertex outside F union G. This is an elementary
structural lemma, not a quantum uncertainty theorem.

Freeze the following proof-gate audit on the 36 one-pair C001 weighted rows
(35 distinct graphs), using their saved canonical boundaries. Record the
u/v neighborhood parity of every outside vertex, test whether J=P_u P_v
is central on neither/one/both sides, and independently verify the cross-claw
criterion. No larger graph census or numerical beta optimization is allowed
by this gate. C003 G8 is a negative control, not a locally claw-free example:
its left side already contains a claw. C4 is a both-central positive control;
C5 cut at a distance-two pair is a one-sided-central positive control.

For implementation acceptance exhaust every labelled graph compatible with
S={0,1,2}, nonedge {0,1}, L={3,4}, R={5,6}: 2^14 fixed-structure graphs.
Compare the structural criterion (including the local hypotheses) against
independent explicit four-vertex claw enumeration. Store counts and hashes;
acceptance must use only integer/standard-library calculations.

Analytic centrality gate: in a connected claw-free graph, global centrality
of J for a nonadjacent pair makes them false twins and forces alpha<=2.
Prove this directly. Thus a globally central-sector repair cannot resolve
the outstanding alpha>=3 class. One-sided centrality has no such conclusion.

Only propose a new quantum inequality if it actually follows from the
cross-claw exclusions and is stronger than an equivalent restatement of
the desired weighted facet. If no such argument is obtained, explicitly
record the proof gate as unresolved and switch the NEXT bounded cycle to
transfer/SOS on a frozen residual. Do not manufacture numerical support for
an unstated lemma. All proofs here require a separate priority assessment.

### C004 analytic micro-control — fixed before verification

An elementary operator pitfall deserves an explicit exact control, not an
optimization run. On C5 use Paulis `(XI,ZX,IZ,IX,YZ)`, boundary {0,2},
J=XZ and weights `(1,1,1,3,1)`. The product state `|++>` has value four,
while any state commuting with J has the last two expectations zero and
value at most two; `|+0>` attains two. Verify the specified two integer
vectors exactly. This refutes a lossless J-dephasing shortcut even on a
line graph, NOT the SCF inequality (its classical weighted bound is four).
The example is elementary and is not an independent novelty claim.

### C004 result — COMPLETE as a proof gate; bridge still unresolved

The exact cross-claw criterion and the connected-global-centrality
alpha-two proposition are proved in `SCF_CROSS_CLAW_OPERATOR_GATE.md`.
Every one of the 36 frozen one-pair weighted rows has J central on exactly
one side, never both. This does not cover multi-pair rows or establish
unrestricted structural coverage. The independent four-subset verifier
agrees with the structural criterion on all 16,384 frozen template graphs:
7,225 locally claw-free, 2,555 globally claw-free, 4,670 local-pass/cross-fail.

The fixed two-qubit C5 example exactly disproves lossless J-dephasing:
unrestricted optimum four, J-invariant optimum two, weighted stable bound
four. This elementary control is not a counterexample to H-SCF. It means
that dropping the off-diagonal sector block is not a valid proof step.
All 37 combined tests pass, including corruption controls.

No noncircular quantum compatibility bound was obtained from the cross-claw
conditions. The coherent block `E_+ C+C E_-` in H squared is still
uncontrolled; requiring positivity of the full weighted slack merely
restates the main claim. Do not call the structural result a quantum
composition theorem. No beta optimization or paid compute was run.

Prior-art update: the introduction of Fukai--Pozsgay--Vona,
arXiv:2605.31453v2 (31 August 2026), already provides path-product/Krylov
constructions and broader claw-free conserved-charge results. A new path
expansion must not be claimed without comparing their actual theorems.
This source was checked as adjacent prior art, not certified to imply or
contradict H-SCF. The missing quantum separator lemma remains unresolved.

Clean-archive reproduction: commit `5567555` was exported to a new temporary
directory. Rediscovery reproduced the C004 JSON hash exactly; all 50
artifact hashes, the independent C004 verifier and all 37 tests passed.

## C005 — next bounded transfer/SOS cycle, not yet executed

Use the FIRST stored order-ten frontier row, `ICXmtizr_`, weights
`(1,1,1,1,2,1,2,1,2,1)`, exact stable bound three. This selection uses source
order, not a newly observed beta value. Both local sides are covered by
the existing order-nine theorem, but global weighted perfection has only
numerical evidence. First test whether the EXISTING symbolic rank/join/
one-hole/Gram templates already prove this facet; an inherited template
success must be reported as coverage extension, not independent novelty.

If they do not, preregister a degree-two state-moment/SOS certificate search
before running it, using the full coherent algebra. Compare the certificate
support with the C004 parity split and identify exactly which cross-sector
terms are essential. The already proved type 24 and the exact C5 dephasing
example are positive controls; published G8 is an invalid-bound negative
control. Do not assume local perfection or one-sided centrality implies
the full inequality. A solver bound is not a certificate: require a
rational identity plus exact PSD verification, or report failure honestly.

The intended progress is an explicit coherent bridge or a sharply localized
failure of the proposed certificate class, not another finite no-violation
census. Only after an actual identity is understood should it be generalized
to a family or abstract lemma. H-SCF remains OPEN; A-star NOT CONFIRMED.

### C005 execution registration — 2026-09-06

Baseline `1efe3a6`; no research processes running; unrelated changes preserved.
The frozen target has one heavy clique {4,6,8}, alpha three, three four-holes
and three light-only independent triples. The one-hole template rejects its
three holes; two-hole templates do not apply. The full complement is
connected, so the immediate join reduction does not apply. Universal transfer
expansion has three nonscalar e2 terms and scalar e3. This is not evidence
that every possible inherited reduction has been exhausted.

The light graph is a bipartite line graph with a 3-by-4 root incidence
matrix. A rectangular extension of the EXISTING Gram method is promising:
in consistent cycle signs s,t use rows
`(a0,a7,a3,0)`, `(s*a9,t*a5,0,a1)`, `(0,a2,0,0)`.
Heavy vertices 4 and 8 select the first two Gram rows, while 6 selects
column 1. Check exact transfer identities, including the relation between
s,t and the three actual cycle operators. Do not set all cycle corrections
positive independently. If this works, it is inherited-method extension,
not a new SDP algorithm, and the conditional SOS search is unnecessary.

Before further computation, freeze a proposed unbounded extension for an
analytic identity check. Start with a bipartite root having three rows:
columns j=0,...,m contain entries A_j,B_j in rows 0,1; column 0 also
contains Z in row 2. Add one A-only column U and one B-only column V.
Light vertices are root edges and form its line graph. Add a clique of
three heavy vertices H0,H1,Hc. H0 commutes exactly with light row 0, H1
with light row 1, and Hc with light column 0; they anticommute with all
other lights. Give lights weight one and heavies weight two. There are
2m+8 vertices; m=1 should be weight-preserving isomorphic to the frozen
10-vertex target. For every m>=0, the candidate weighted bound is three.

Candidate central signs: K_j=-P_H0 P_H1 P_Aj P_Bj. Verify that each is a
central Hermitian involution, not just a boundary-central operator. Put
K_j*b_j in row 1 of B, a_j in row 0, Z amplitude in entry (2,0), and
the two private-column amplitudes in their respective rows. With M=B B^T,
the proposed identities are e1=L+H, e3=det(M), and
`e2=e2(M)+(h0,h1) M[0:2,0:2] (h0,h1)^T+hc^2 ||B[:,0]||^2`.
Together with the existing exact three-eigenvalue envelope this would
prove the fixed weighted inequality for every family size, not all weights.

Independent finite audit: m=0,...,5, no beta optimization and no random
samples. Expand the FULL universal transfer polynomial and compare every
coefficient with the proposed Gram identities; use a second multiplication
algorithm for acceptance. Include corrupted cycle phase/Gram/graph controls.
An all-m claim requires the written combinatorial expansion, SCF proof,
and spectral-envelope argument, not just these six checks. Check nearby
prior art before calling this new. If an identity fails, retain the failure
and return to a separately preregistered SOS search on the original target.

### C005 result — COMPLETE, exact target and fixed-weight family theorem

The rectangular Gram bridge works. All transfer coefficients, including
odd-order cancellation, are independently checked using standard-library
integer word rewriting and sparse polynomials. No SDP, beta optimization,
amplitude sampling, QPU or paid compute was needed. This is an extension
of the existing Gram/envelope method, not a new optimization algorithm.

For every m>=0, the explicit SCF family G_m with 2m+8 vertices obeys
`sum_light <P_i>^2+2 sum_heavy <P_i>^2<=3`. The bound is tight and defines
a full-support nonrank classical facet. The exact central involutions are
`K_j=-P_H0 P_H1 P_Aj P_Bj`; their correlated signs give a 3-by-(m+3) matrix B.
Its Gram matrix satisfies the full e1,e2,e3 transfer identities. Row/column
Rayleigh bounds and the earlier exact envelope prove the quantum inequality.

The proof for ALL m uses a finite-support argument: any coefficient of the
degree-six transfer identity involves at most four noncentral columns
(every independent triple contains Z). Any hypothetical claw likewise uses
at most four columns. Thus the exact G_4 checks cover arbitrary m after
column relabelling and setting unused amplitudes to zero. This is not an
extrapolation from numerical survival. The separate audit m=0,...,5 covers
orders 8,10,12,14,16,18 and all coefficients. Exact facet-root ranks are
full in every audit case; a uniform affine-hull proof is also supplied.

G_1 is weight-preserving isomorphic to the frozen target `ICXmtizr_`, so
its recorded weighting now has exact beta three. No ALL-WEIGHTS assertion
for that graph or the family has yet been made. The old frontier JSON is
preserved as a historical numerical result. The remaining 33 frontier
weighted representatives have not received new certificates in this cycle.

All 45 tests pass. See `SCF_RECTANGULAR_GRAM_FAMILY.md` for the graph
construction, uniform proof, exact sector-sign convention and reproduction.
The proof also checks the monotone spectral-crossing branch explicitly.

Prior-art boundary: SCF transfer theory is Chapman--Elman--Mann; Gram
factorization, Cauchy--Binet and the spectral envelope are inherited tools.
Xu et al.'s state-polynomial hierarchy was checked as the unused fallback.
Classical nonrank families such as gear composition remain a necessary
graph/facet identification check before claiming priority. No new graph
family discovery or A-star novelty is asserted.

Clean-archive reproduction: commit `45097d0` was exported to a new temporary
directory. The C005 discovery script regenerated the exact same JSON hash;
all 51 artifact hashes, the independent Gram verifier and all 45 tests
passed. No local solver cache or prior-art checkout was required.

## C006 — next cycle: all-weight closure of the proved family

First check whether the target G_1 has any additional full-support nonrank
facet orbit beyond the newly proved weighting. All proper induced supports
have at most nine vertices and are already covered by the exact theorem.
An exact complete H/V facet audit could therefore establish all-weight
perfection of this PARTICULAR ten-vertex graph. Do not infer completeness
from the previously selected facet or from beta samples.

Then ask whether the arbitrary-m facet description reduces to the proved
family weighting and smaller supported inequalities. Before a family census,
formulate an explicit decomposition/facet claim and audit graph-theoretic
prior art, including possible alternate names and gear/clique-family
constructions. The C005 graph family is not automatically all-weight
hbar-perfect merely because one full-support facet has been proved.
Use exact small cases to falsify the proposed polyhedral claim; demand a
uniform proof for any unbounded conclusion. H-SCF remains OPEN and A-star
novelty NOT CONFIRMED. No new objective outside quantum research is opened.

### C006 preregistration — 2026-09-06, before new facet enumeration

Freeze the first subquestion only: does G_1 (canonical graph6 `IrqaaulLw`,
isomorphic to frontier target `ICXmtizr_`) have any full-support nonrank
facet other than the C005 weight (light 1, heavy 2, bound 3), up to graph
automorphism? Enumerate ALL independent sets and ALL rational STAB facets
using cdd.gmp, with exact H/V roundtrip. Store every primitive inequality,
not only the hoped-for facet. For every other positive facet, verify its
support is proper and componentwise SCF of order at most nine, or identify
an applicable rank theorem. A missing proof route blocks the all-weight
conclusion even if its numerical beta happened to look correct before.

Acceptance independent of cdd: a new standard-library Fraction algorithm
starts from the unit cube and clips one halfspace at a time. An edge joins
two old vertices iff their common active constraints have exact rank n-1;
new vertices are precisely intersections of crossing edges with the cut.
Keep boundary vertices. The bounded-polytope edge-clipping theorem proves
completeness inductively; do not merely check the supplied stable vertices.
Check that the supplied inequalities themselves imply the cube bounds,
and that the final vertex set is exactly the complete stable-set set.
Also verify facet validity and n-1 affine dimension independently.

Controls: small path and odd-cycle STAB polytopes; reject a corrupted
coefficient, graph binding, duplicate row, and deliberately omitted
full-support facet. The missing-facet control must expose an extra vertex,
not just fail a stored hash or expected count. Limit this cycle to G_1,
these small controls, and up to five minutes per exact verification. No
random seeds, beta optimization, larger family census, QPU or paid compute.
If another full-support weighting appears, retain it as a falsification
of the proposed coverage, not a counterexample to the quantum conjecture.

Prior-art gate: re-read the primary Xu et al. BETA/STAB formulation and
Chapman--Elman--Mann framework. Exact polyhedral enumeration and facet-wise
implication are established tools, not algorithmic novelty. The all-m
facet-description and gear identification question stays for a separate
registered cycle; C006 cannot establish an unbounded all-weight theorem.

### C006 result — COMPLETE, all-weight theorem for G_1

Exact cdd.gmp enumeration finds 34 stable vertices and 27 facets: ten
nonnegativity, fourteen rank, two seven-vertex proper-support nonrank,
and just one full-support nonrank facet, exactly the C005 weighting.
The two proper supports are componentwise SCF and covered by the existing
order-nine all-weight theorem. Hence every facet has a quantum proof,
which proves beta(G_1,w)=alpha(G_1,w) for all nonnegative real weights.
The graph is the stored frontier target `ICXmtizr_` up to the C005 map.

An independent standard-library Fraction algorithm, with no cdd or graph
library, starts from all 1,024 cube vertices and performs exact halfspace
edge clipping. Active-constraint rank detects all crossing edges, including
degenerate cases. Its complete final vertex set equals all 34 stable
incidence vectors. Cube boundedness, facet validity and facet affine rank
are checked independently. Deleting the C005 facet produces three exact
extra vertices; each has removed-facet value 13/4 rather than bound three.
These are classical completeness controls, NOT physical quantum states.

Implementation correction retained: the initial NEW discovery classifier
used maximal cliques only and incorrectly marked both seven-vertex supports
as non-SCF. The independent all-subsets classifier correctly accepted both.
Their simplicial cliques are all nonmaximal. Replacing the new search by
all-clique enumeration fixes the error; a dedicated regression records it.
The pre-existing order-nine classifier already enumerated all cliques, so
its census and theorems were unaffected. No SCF heredity counterexample was
found; the primary CEM Section IV.3 explicitly states that heredity.

Ten new tests and all 55 combined SCF tests pass. C005 universal identities
were reverified. No beta optimization, numerical SDP, larger family census,
QPU, paid compute or outside coordination was performed. See
`SCF_G1_ALL_WEIGHT_CLOSURE.md` and `scf_family_facet_closure.json`.

The old C005 and frontier JSON retain their stage-specific scopes. C006
does NOT prove every ten-vertex graph or all weights on every G_m. Exact
enumeration, polyhedral clipping and BETA/STAB implication are established
tools, not algorithmic novelty. H-SCF OPEN; A-star novelty NOT CONFIRMED.

Clean-archive reproduction of commit `24bafa9`: C006 rediscovery generated
the identical canonical JSON hash
`02297efed092d9cfa47512465a06b17d81299faef765c520a4a9214c562e43ca`.
All 52 artifact hashes and all 55 tests passed in a fresh exported source
directory. C006 and C005 independent verifiers additionally passed under
`python -S` (site packages disabled), confirming that acceptance imports
no cdd, NetworkX, SymPy or numerical solver. This is independent algorithmic
verification on the same host, not external peer review.

## C007 — next cycle: a uniform polyhedral gate, before more sizes

Candidate R_m: for every m>=0, every nonrank facet of STAB(G_m) either has
support S with alpha(G_m[S])<=2, or is the C005 full-support weighting up
to positive scaling and graph automorphism. This precise claim would,
combined with SCF rank, the already size-independent alpha<=2 theorem,
and C005, prove all-weight perfection of this unbounded family.

First adversarially audit alternate classical names and gear/clique-family
polyhedral results using their actual hypotheses, not abstracts. Then
preregister a bounded exact audit, for example m=0,2,3 as controls around
the completed m=1 case. A single extra alpha>=3 nonrank facet refutes R_m;
preserve its exact row and independent completeness certificate. Successful
small cases require a uniform proof, possibly by classifying tight stable
sets (all independent triples contain Z). Do not increase m without a
specific proof obligation. Any need for a larger independent verifier must
be preregistered and bounded; C006's cube checker is deliberately n<=10.

### C007 preregistration — 2026-09-06, before new family hulls

Baseline `e2209f4`; no Python research process was running. The four known
unrelated submodule/prior-art items remain untouched. Freeze R_m exactly
as above. Audit m=0,1,2,3 (orders 8,10,12,14), with m=1 a C006 equality
control. Do not extend the size list automatically. For each size enumerate
ALL stable sets and ALL primitive facets over cdd.gmp rationals, roundtrip
H/V, and classify nonrank facets by the exact independence number of their
support. The sole allowed alpha-three nonrank orbit is the C005 weighting.
One additional orbit falsifies R_m, not H-SCF. Save every row even on failure.

Acceptance: reuse C006's independent Fraction edge-clipping method, with
an explicit caller-selected cap raised ONLY to n<=14 for this cycle and
five minutes per graph. Preserve the old default cap of ten. Recheck SCF
componentwise by all cliques (not maximal cliques), facet root affine rank,
every stable-set incidence vector, and the complete final vertex set.
Check m=1 equals the old exact artifact. Corrupted and deliberately omitted
facets must fail geometrically. No random seeds, beta optimization, numerical
SDP, paid cloud or QPU. If a limit is reached, record the unverified case;
do not promote it to a theorem. A finite pass is NOT an all-m proof.

Prior-art gate read before enumeration: Galluccio--Gentile--Ventura's
author preprint ORL2.pdf, Definitions 1-2 and Theorems 1-2, defines an
eight-vertex gear and replacement of a simplicial edge. The two gear
triples {a,b1,b2} and {c,d1,d2} are disjoint. In contrast ALL G_m triples
contain Z, so no G_m contains an induced gear; hence the literal gear
composition theorem cannot directly identify G_m as its output. This does
not exclude fuzzy constructions, other liftings, or other classical names.
The source definition/figure was inspected in a rendered PDF page.

Letchford--Ventura, 'Strengthened Clique-Family Inequalities', Section 2.2
and Theorem 1, were read. Ordinary clique-family coefficients d,d-1 with
ratio two force d=2, making their rhs even; thus they cannot be exactly
the primitive C005 rhs-three facet. Strengthened MIR/clique sums can behave
differently. As a bounded PRIOR-ART IDENTIFICATION control, enumerate all
subsets of maximal cliques on these four graphs and test q=2,...,p-1 with
q<p/2 and p mod q !=0 against the stated strengthened formula. Record an
exact clique-multiplicity certificate if it reproduces the C005 facet;
failure to find one does not establish novelty. No integer-rounding rule
may be applied to quantum squared profiles just because it holds on STAB.

Pecher--Wagler, DOI 10.1016/j.disc.2009.03.031, warns that alpha-three
claw-free facets can have arbitrarily many coefficients. Its publisher
statement and concluding discussion were read, but no full classification
theorem from it is used. The known alpha>=4 descriptions cannot simply be
transferred to our alpha=3 family. All-m R_m still needs an independent
uniform proof if the finite exact tests pass. Quantum novelty is separate
from these classical polyhedral questions.

### C007 uniform-proof subprotocol — before computing a new lifted hull

The four exact hulls survive R_m and show a fixed eight-variable core.
All inequalities are the G_0 facets with U replaced by
A=sum_(j>0) x_Aj+x_U and V replaced by B=sum_(j>0) x_Bj+x_V,
plus, for each shared column j>0,
`x_Aj+x_Bj+x_Hc<=1` and
`x_Aj+x_Bj+x_A0+x_B0+x_Z+x_H0+x_H1+x_Hc<=2`.

Freeze a classical coupling lemma to prove this form for ALL m. Lift the
22 stable vertices of G_0 by the binary coordinate z=1_{U,V both chosen}.
Candidate exact lower fiber endpoint, for any y in STAB(G_0), is
`z_min=max(0,A+B+y_Hc-1,A+B+y_A0+y_B0+y_Z+y_H0+y_H1+y_Hc-2)`.
Enumerate this ONE nine-dimensional lifted polytope over cdd.gmp and
independently clip the cube with Fraction arithmetic (five-minute cap).
Check every facet, full affine rank, complete vertex set, and that these
are exactly all the lower-z inequalities. Other facets are zero-z or
upper-z inequalities, so decreasing any feasible z to this endpoint
preserves them. A missing lower facet or different endpoint kills this
candidate lemma. No additional family orders or quantum optimization.

Given z_min, set T=A+B-z_min. Refining each aggregate into its original
row labels is a transportation problem of total mass T, with forbidden
diagonal pairs (Aj,Bj) and the absent/absent pair. Its allowed bipartite
graph is complete minus a matching. Weighted Hall constraints then reduce
to the singleton conditions x_Aj+x_Bj<=T; the absent-label condition is
z_min>=0. The two extra per-column inequalities above enforce these
conditions. Check rational boundary/zero-mass and incompatible-diagonal
controls. A uniform theorem requires writing this conditional refinement
proof and checking the graph substitution, not just the lifted hull.

This is a CLASSICAL decomposition lemma after all quantum inequalities
are proved. It is not the falsified generic quantum separator-gluing rule
from C003, and it does not discard quantum coherences. Quantum validity of
the aggregated G_0 facets must be established separately: rank or alpha<=2
support, except the full C005 inequality. Then, and only then, the classical
lemma would imply all-weight perfection of every G_m.

### C007 completed — uniform ALL-WEIGHT family theorem, 2026-09-06

Both registered gates pass, followed by a uniform proof, not a finite-size
extrapolation. For every integer m>=0 and every nonnegative real weight,
every Pauli realization of G_m satisfies beta(G_m,w)=alpha(G_m,w).
The full proof and scope are in `SCF_UNBOUNDED_ALL_WEIGHT_FAMILY.md`.

Frozen exact hulls at orders 8,10,12,14 have respectively 22,34,50,70 stable
vertices and 23,27,31,35 facets. Each has exactly two nonrank alpha-two
supports and one remaining nonrank facet, C005. Independent full-cube
Fraction clipping verifies every hull, not merely the reported facet rows.
The order-ten hull exactly matches C006. MIR candidate counts are
209,559,1423,3492 with no match in this frozen grid; this is NOT an
absence, priority, or quantum-rounding certificate.

The lifted G_0 joint-event polytope has dimension nine, 22 vertices,
24 facets and exactly the three preregistered lower-z facets. An independent
complete rational clipping proof verifies the claimed z_min. The uniform
transportation argument uses a complete bipartite graph minus a matching;
Hall constraints reduce to singletons. It reconstructs a stable-set
distribution for every real x in the proposed 4m+23-row description,
including zero masses and saturated constraints, for every m.

All positive defining inequalities other than C005 have alpha<=2 support
uniformly: an independent triple requires Z and both noncentral rows,
and only the full core facet supports all three. The earlier all-size
SCF alpha-two theorem and C005 therefore prove quantum validity of the
entire description. R_m follows as a corollary. Uniform irredundancy of
every listed row is not asserted or needed. C005/C006 and the finite-gate
JSON flags retain their historical scopes; current summary records the
subsequent uniform proof separately.

Fourteen new regression/negative tests pass; the complete suite has 69
passing tests. Omitted lower-event and order-twelve full facets fail
geometrically, rather than through a hard-coded expected facet count.
Other controls cover corrupted endpoint/event/scope, exact transport at
boundaries, forbidden diagonal mass, weighted automorphism, and a positive
C7 MIR certificate. The old default cube dimension cap remains ten.

Prior-art boundary: the original gear definition and figure were checked
in the author PDF; disjoint gear triples exclude that literal construction
for every G_m, not all variants. Eisenbrand--Oriolo--Stauffer--Ventura,
Lemma 5 and its following remark, already exploit homogeneous pairs of
cliques to preserve a facet under selected edge deletions. Our row pair
is such a classical structure, and the Hall/flow theorem is standard.
Their quasi-line classification cannot directly cover G_m: each contains
the five-wheel with hub H1 and rim A0,Z,H0,Hc,U. Classical construction
or refinement novelty is NOT claimed. Quantum significance and priority
remain provisional, with external expert review pending.

Canonical new artifact hashes:

- `scf_uniform_facet_gate.json`:
  `7e83b5a5f04751d0a56507ff7fe2a978319a35faf0a6700a898a5371bbe954b8`.
- `scf_core_refinement.json`:
  `78be65169e9d0da98a49a90c610c33fcfc26580f296a2ab9c79170933fb641cb`.

No paid computation, QPU, numerical beta optimizer, external contact,
or unrelated-file change. H-SCF remains OPEN; A-star is NOT CONFIRMED.

Clean-archive reproduction of source commit `99ccd89`: both C007 discovery
scripts regenerated the identical canonical hashes listed above. All 54
artifact hashes passed in the exported directory, both new independent
verifiers passed under `python -S`, and all 69 SCF tests passed again
(19.441 seconds for the combined suite on this host). The exported source
had no repository cache or uncommitted input. This is separate algorithmic
verification and same-host clean reproduction, not external peer review.

## C008 — next structural transfer gate, not a larger G_m audit

Follow Section 10 of `RESEARCH_PROGRAM_RU.md`: before a new census,
preregister an operator/root configuration not already a line graph or a
C007 refinement. A candidate is the three-row incidence construction with
heavy nonneighbor selectors row 0, row 1, column 0 and additional occupied
third-row cells. First check its structural obstructions: a matching of
size three outside column 0 produces a claw centered at Hc. This may
force a known small vertex cover and reduce the whole proposal; if so,
record the reduction rather than claim a new mechanism. No wider family,
new facet or quantum extension is asserted before this gate is executed.

### C008 preregistration — 2026-09-06, before the root census

Baseline `c1be185`; no Python research jobs were running. Preserve the four
unrelated submodule/prior-art items. Define F(E) for occupied cells E of a
three-row bipartite root: lights share an edge iff their cells share row or
column; three mutually adjacent heavies have light NONneighbors in row 0,
row 1 and column 0 respectively. Consider arbitrary finite column count.

Structural candidate S: the graph is claw-free iff the root restricted to
nonzero columns has matching number at most two. If column 0 is nonempty,
its light clique is simplicial, so claw-free implies SCF. Check necessity
and sufficiency by distinguishing light/heavy claw centers, not by a
finite extrapolation. A two-vertex cover of the noncentral bipartite root
should then split the class into two-row, two-column, and mixed covers.
This is an elementary use of classical matching theory, not new quantum
or graph-algorithm novelty.

Freeze ALL 4096 subsets of a 3-by-4 cell grid, in row-major bit order.
Record cell mask, graph6, exact matching number and minimum vertex cover,
claw witness if present, and a simplicial-clique witness when present.
No random seed or floating arithmetic. Discovery may use NetworkX;
acceptance must reconstruct the graph and independently enumerate claws,
stable triples and small covers using only the standard library. Check
all cliques, not only maximal ones, for the SCF classification. A single
structural mismatch kills S. The census checks the implementation, while
an arbitrary-column proof is required for S itself. Limit: five minutes
per script; stop and record any incomplete part.

Freeze ONE exact polyhedral target before seeing any hull: all nine cells
of the 3-by-3 root, with these same three heavies (12 vertices). It has a
nonempty central column and two noncentral columns, so S predicts SCF.
Test whether it lies outside the C007 hereditary family using the necessary
property that all independent triples have a common vertex; C007 and each
induced subgraph with alpha three have that property. Check a local
neighborhood obstruction to line graphs independently. Enumerate ALL target
STAB facets and vertices with cdd.gmp, then independently clip the complete
12-dimensional cube with Fraction arithmetic and the explicit n<=14 cap.
No other target hull or new numerical beta search is authorized by this
registration. Classify facet support alpha and compare proper supports
with earlier proved classes; do not assume the full (1-light,2-heavy) row
is a facet, sufficient, or quantum-valid.

Controls: empty root gives the heavy K3; three cells in distinct noncentral
rows and columns produce a claw at Hc; the C005 root is a covered positive
control. With all three heavy selectors being the three ROWS, explicitly
map the heavies to the triangle edges on row nodes: this is already a line
graph for any root and must not be counted as a new quantum family.
Corrupted root adjacency, cover, claw or scope claims must be rejected.

Prior-art gate: reread Chapman--Elman--Mann's line-graph definition and
SCF hypotheses and Xu et al.'s graph-operation framework in the original
arXiv HTML. Existing free-fermion solvability alone is not the all-weight
uncertainty theorem. A named-class reduction or known homogeneous-clique
operation must be matched with its hypotheses before use. This cycle aims
at a decisive structural target/reduction, not a claim of A-star novelty.

### C008 completed — uniform structure, one unresolved quantum target

The arbitrary-column proof shows F(E) is claw-free iff its noncentral root
matching number is at most two. Every claw-free F(E) is SCF: use the
central-column simplicial clique, or temporarily add that column and use
SCF heredity. A classical cover of size at most two separates two-column
cores of order <=12, mixed row/column cores of order <=10 up to known
vertex splitting, and the unbounded two-row cases. Rows {0,1} reduce to
C007; rows {0,2}/{1,2} remain a distinct conditional proof obligation.
The full argument is in `SCF_THREE_ROW_STRUCTURAL_GATE.md`.

All 4096 frozen root patterns pass independent verification. The matching
histogram is {0:8,1:264,2:1848,3:1976}; exactly 2120 graphs are claw-free
and SCF. Discovery's graph/matching implementation is checked by independent
four-subset degree enumeration, root matchings and minimal covers, not by
calling the same NetworkX routines. No mismatch or time limit occurred.

The fixed target, full 3-by-3 lights plus three heavies, has graph6
`K{S{aSfF~Fln`, 12 vertices, 46 stable incidence vectors and 36 facets.
Both cdd.gmp and independent complete Fraction cube clipping verify the
hull. Routes are 12 nonnegativity, 20 SCF rank, three SCF alpha-two supports,
and ONE unresolved full facet: weights one on all nine lights, two on the
three heavies, classical bound three. This is a reduction to a quantum
proof obligation, not a quantum upper-bound proof or numerical beta result.

The target has disjoint triples {0,4,8} and {1,5,6}, excluding every C007
induced subgraph with alpha three. A five-wheel with hub 10 and rim
(0,6,9,11,1) excludes line graphs. Binary adjacency rank six excludes the
published two-qubit G15 hereditary class, whose rank is at most four.
Independent checks find no copy/split pair, complete-join decomposition
or clique separator. This does not exclude every classical graph name,
every quantum theorem, or general lexicographic/module constructions.

Prior-art comparison read Xu et al., Section III and Appendix A, including
the copying/splitting definitions, their proofs, G15 proof and symplectic
rank bound. Vertex splitting and the small-cover reduction are known tools,
not novelty. The source swaps copy/split property numbers between the main
text and appendix; we bind usage to adjacency definitions. The three-ROW
selector variant has an explicit line-graph root using a triangle on the
row nodes; the map passes all 4096 grid controls and closes that apparent
extension as already covered. CEM's SCF definitions and heredity were
also reread in the primary HTML. No PDF-based inference was needed.

Nine new tests and the complete 78-test suite pass. Corrupt graph, matching,
cover, claw and quantum-scope controls are rejected. Omitting the target's
full facet fails geometrically. Both new verifier and its tests pass with
`python -S`. No paid compute, QPU, beta optimization, external contact or
unrelated-file mutation. Unrestricted H-SCF OPEN; A-star NOT CONFIRMED.

New canonical hashes:

- `scf_three_row_gate.json`, 1553613 bytes:
  `47994eca3772c8d2abdb3cb1722c259d11b9477272aa85e6f44c259fcc4bc33f`.
- `scf_three_row_target.json`, 13974 bytes:
  `6c0778cba29c689aea2a5acbe48dc35abc288b8fbc8f77ca449aab7685bcfb26`.

Clean-archive reproduction of source commit `9cdf86e`: C008 rediscovery
regenerated both canonical hashes exactly. All 56 artifact hashes passed,
the independent C008 verifier and nine tests passed with `python -S`,
and all 78 SCF tests passed again (26.577 seconds for the combined suite).
No repository cache or uncommitted source was used. This is same-host
clean reproduction with independent algorithms, not external peer review.

## C009 — candidate recorded before execution

Preregister before computing: for the fixed C008 target use amplitudes
a_j,b_j,c_j on rows A,B,C and r0,r1,rc on heavies. A candidate real sector
matrix has rows a_j, K_j b_j, Lambda_j c_j, where
K_j=-P_H0 P_H1 P_Aj P_Bj, Lambda_0=I, and
Lambda_j=-P_A0 P_C0 P_Aj P_Cj for j=1,2. These are only CANDIDATE signs;
their centrality, Hermitian involution relations and mutual consistency
must be checked in the FULL universal graph algebra before use.

With M=B B^T, test e1=tr(M)+r0^2+r1^2+rc^2,
e2=e2(M)+(r0,r1) M[0:2,0:2] (r0,r1)^T+rc^2 ||B[:,0]||^2,
and e3=det(M), including every zero odd transfer coefficient. Discovery
and independent adjacent-letter rewriting must agree exactly. Only if
these identities hold may C005's scalar envelope prove the full facet.
The old factorization through a single Z is unavailable, since all three
light rows now occupy all three columns. No numerical agreement alone
closes this obligation, and no unrestricted all-column/SCF theorem follows
from this fixed target without a separate uniform proof.

### C009 completed 2026-09-08 — fixed target all-weight theorem

Registration commit `9b657c5`. All five proposed signs are central,
Hermitian, mutually commuting involutions in the full 12-generator
algebra. All three even transfer identities pass exactly, with 12,39,21
monomials; all odd coefficients vanish. Discovery uses inversion parity;
independent acceptance uses adjacent-letter rewriting, squared minors
for e2 and det(B)^2 for e3. Neither assumes independent sector signs.

The analytic Rayleigh/envelope/correct-branch argument closes the full
(1-light,2-heavy) facet with exact beta=3. Together with rechecked complete
C008 rational hull and earlier rank/alpha-two bounds, this proves ALL
nonnegative weights for the fixed target `K{S{aSfF~Fln` and its induced
subgraphs. Details: [C009 proof](SCF_THREE_ROW_GRAM_C009.md).
No all-column family theorem or general H-SCF result follows yet. A-star
novelty remains NOT CONFIRMED; external mathematical review is pending.

All 87 combined SCF tests pass (28.378 seconds); 57 artifact hashes pass.
Nine new tests pass, including wrong sign/coefficient/graph and overclaim
rejection. No numerical optimization, paid compute, QPU or external contact.
Artifact canonical LF SHA-256:
`34b89211fd99fbc77819c1ad68734425a3d96effae89d477d7289e55071ea2db`.

Next obligation (C010, not yet registered or run): combine C008's uniform
root-cover classification with C009 heredity, explicitly identify the
remaining unbounded two-row cases {0,2}/{1,2}, and test whether the same
Gram bound extends there. Mere additional fixed graphs are not the goal.

Clean reproduction of commit `cd89705`: archived the tracked phase-0
experiment and result directories into a fresh temporary directory.
C009 rediscovery regenerated its canonical hash exactly; all 57 artifact
hashes passed, the independent verifier passed with `python -S`, and all
87 SCF tests passed again (27.980 seconds). This is same-host clean
source reproduction, not an external reviewer or a different machine.

## C010 — completed 2026-09-08: uniform all-weight F(E) closure

Registrations d7408bd (four D_m hulls) and ae59ad0 (adaptive fixed core).
The frozen D_0,...,D_3 graphs have orders 6,8,10,12 and exact facets
11,17,23,27; every discovered positive facet uses rank or alpha-two bounds.
The separate private-row core has 21 stable vertices and 17 facets.
Lifting the joint row-presence event gives a 9D polytope with 21 vertices,
18 facets and exactly three lower-z inequalities, matching the registration.
Independent Fraction full-cube clipping verifies both the endpoint and
each of the four expanded H-descriptions. Dropping a lower facet creates
spurious vertices; corrupted endpoint, graph-scope and event controls fail.

A uniform transportation/Hall argument proves completeness for every m.
All independent triples in D_m require B0 and both expanded row groups;
none of the core positive facets supports all three. Thus every expanded
row has alpha<=2 support uniformly, and earlier quantum theorems suffice.
This closes all weights on D_m without a new Gram inequality.

C008's uniform two-node root cover now closes ALL claw-free F(E):
two-column and mixed covers use C009 plus known splitting, rows {0,1}
use C007, and rows {0,2}/{1,2} use D_m. Explicit induced maps/twin-quotient
witnesses pass on all 2120 previously registered claw-free grid patterns.
The analytic cover proof, not that finite audit, provides uniformity.
Proof: [SCF_THREE_ROW_ALL_WEIGHT_C010.md](SCF_THREE_ROW_ALL_WEIGHT_C010.md).

No paid runs, numerical beta optimization, QPU, external contact or
unrelated changes. General H-SCF OPEN; A-star NOT CONFIRMED. Hall, matching
and splitting are known tools, not new algorithms. The precise quantum
construction theorem still needs external mathematical and priority review.

All 95 SCF tests pass (30.543 seconds), including eight new C010 tests.

Clean reproduction of df6f6c8 regenerated both C010 artifact hashes
exactly, verified all 59 artifacts, reran the independent verifier with
python -S, and passed all 95 tests (30.660 seconds) in a fresh archive.
Only tracked phase-0 sources/results were archived; no uncommitted source
was used. This is same-host reproduction, not external peer review.

Next C011 (not registered/run): adversarially test the significance and
coverage boundary of this completed construction. F(E) always has alpha<=3:
lights use three rows and a heavy's nonneighbors form a clique. Therefore
no size increase of this construction can settle arbitrary-alpha SCF.
Compare against known claw-free polyhedral theorems before selecting a
genuinely uncovered SCF class; do not relabel F(E) as general SCF.

## C011 — completed 2026-09-08: published XX-strip all-weight corollary

Registration f8497ac. The Chudnovsky--Seymour source's full printed page 6
was rendered and visually checked before graph transcription. Frozen eight
deletions of vertices 11,12,13, no beta optimization. Full graph
`LhEM?rcNLhleuo`: order 13, alpha 4, 85 stable vertices, 33 facets.
The quadruple {3,6,7,8} in source labels excludes hereditary F(E).

Independent full-cube Fraction clipping verifies all eight hulls. For the
full graph, 17 positive rank rows and two alpha-two rows use earlier
theorems. Its sole remaining row is on an 11-vertex induced subgraph of
C009; every edge and nonedge of the map is independently verified.
C009 is itself rechecked. Thus all weights of the full XX graph follow,
and its variants follow by heredity. This is a corollary, not a new
operator principle or a newly discovered graph. Details: SCF_XX_GATE_C011.md.
Removing the C009-supported facet creates spurious rational vertices.

Classical strip-composition literature was audited but not imported as a
quantum theorem: compatibility of auxiliary marginals remains an extra
obligation. General H-SCF and A-star remain open. Next C012 is a separately
registered explicit XX-strip closure, not an unproved generic gluing rule.

## C012 — completed 2026-09-08: fixed closed-XX all-weight corollary

Registration ad8602c: the source XX graph plus edges (7,14),(14,15),(15,8).
Exact target `NhEM?rcNLhleuo?_?GG`, 15 vertices, alpha 4, 203 stable
vertices, 44 facets. Independent integer graph reconstruction checks
claw-freeness and the simplicial clique {14,15}. Every positive facet's
support is checked componentwise. Routes: 26 rank, two alpha-two, and
one C011-induced row; 15 nonnegative coordinate facets complete the hull.
The sole exceptional row is precisely the earlier 11-vertex C009 support,
not a new cross-boundary quantum inequality.

Acceptance history is retained, not hidden: old hard dimension cap 14
rejected the first run before calculation; explicit cap was extended to
the registered 15. Dense-first clipping completed the full hull but its
missing-facet control exceeded 300 seconds. Sparse-first then exceeded
300 seconds on the full hull. An exact candidate-edge index completed
BOTH full rational cube clipping and the missing-facet control. It unions
all (n-1)-active-row-subset candidates, falls back to the full pair scan
on degeneracy, and applies the unchanged exact rank test. No acceptance
tolerance or mathematical premise was weakened; default dimension 10
and the 300-second clipping limit remain unchanged.

This proves the frozen graph for all nonnegative weights as a corollary
of C011, not general composition. As a novelty screen, the single-atom
closure is negative. See SCF_XX_CLOSURE_C012.md. All 61 artifact hashes
pass; canonical C012 SHA-256 is
`aebf38efcca01d9836615cb857bffe42dcee6cc4b3c3bb4734c7cb16728bc683`.

C013 was preregistered as b140900 before its calculation, conditional on
complete C012 acceptance. It tests TWO interacting XX atoms with one
linear connection. Classical subdivision facet preservation was checked
against de Vries pp.150-151 and Wolsey's source metadata: it is not a
quantum completeness or composition theorem. No paid/QPU runs or
external correspondence. H-SCF OPEN; A-star novelty NOT CONFIRMED.

## C013-C016 — completed bounded gates, quantum obligation remains open

C013 registration b140900 froze two XX cores connected through one
clique interface and a linear connection. Its discovery process timed
out after 300 seconds, with no completed artifact; no full hull is claimed.

C014 registration 6456fed switched to two fixed weights on the SAME
24-vertex graph. Exhaustive recursion and independent products of two
11-vertex core censuses agree on all 2167 stable sets. Alpha=6. One
weighted atom gives bound six, 88 tight sets and homogeneous rank 24:
a genuine full-support facet. Both weighted atoms give bound seven but
face rank six; that control follows from summing the known atom rows.
The binary rank is 14 and all pairs in the seven-qubit Pauli realization
are checked exactly. This is not a quantum proof or a new classical facet
claim. The full facet cannot be obtained solely by a nonnegative sum of
valid proper-support rows. See SCF_TWO_XX_WEIGHT_C014.md.

C015 registration 832dcc8 froze 1024 starting sign classes modulo Pauli
conjugation, 64 steps per start, a G8 positive control and two target
controls. NumPy eigh failed after the 64-start checkpoint. The second
registered batch replayed from that checkpoint with a SciPy EVR fallback,
checked eigenpair residuals, and completed every class in 214.594 seconds.
Twelve resumed-start fallback calls; 144 starts met the convergence test,
the other 880 reached the iteration cap. Best saved state independently
reevaluates to 6.000000000000059. G8 reevaluates to 3.0448154998549777>3,
and the double-weight control to 7.000000000000041, consistent with seven.
No physical violation found. All trajectories were NOT independently
replayed; saved best/control states were checked by independent bitwise
Pauli action. No numerical result is used as a universal upper bound.

C016 registration 689f911 froze one rationalization of the first-moment
relaxation. The 25D matrix satisfies all affine equations exactly and has
25 positive Fraction LDL pivots; reconstruction is exact. Objective
325328979/50000000=6.50657958 proves theta>6 for this target. It is NOT a
quantum density matrix or a physical counterexample. Degree histogram
{4:2,6:12,7:4,8:6} excludes direct ordinary gear composition, whose two
unattached hubs have degree five. Definitions 2.2/2.4 in the author-hosted
R.661 gear report were read; no claim of auditing its full 35 pages or
excluding general strip/fuzzy/sequential-lifting results is made.

All 127 tests passed: 121 in the combined run (449.757 seconds) and six
C016 tests (0.170 seconds). The first all-suite invocation incorrectly
used python -S, which hides NetworkX required by the historical benchmark
test; it was stopped and not accepted. The old explicit-cap regression
also needed its upper rejection changed from 15 to 16 to reflect C012's
registered opt-in 15, while the default rejection at 11 is preserved.
Both issues were fixed before the accepted combined run.

Next: an exact operator/spectral lemma or physical counterexample for
C014's ONE full facet. Do not restart a larger census or use more random
starts as a substitute for the proof. General H-SCF, C014's quantum bound,
priority and A-star novelty remain OPEN. No paid jobs, QPU or external
review/contact. The existing two-hour research heartbeat was inspected;
no duplicate automation or limit reset was created.

Clean-source acceptance: a fresh git archive of a7a92f3 reproduced C011,
C012, C014 and C016 discovery outputs. All 64 bundle artifact hashes
matched. Independent python -S acceptance of C014, saved C015 physical
witnesses and C016 passed. The complete unittest suite then passed all
127 tests in 441.989 seconds, including C011/C012 exact completeness and
negative controls. Terminal marker: CLEAN_REPRODUCTION_C011_C016_PASSED.
C015 optimizer trajectories were not rerun in this clean reproduction;
the saved physical witnesses were reevaluated independently. This clean
acceptance applies to a7a92f3 code/data; subsequent publication notes are
documentation-only. Quantum C014 and A-star novelty remain OPEN.

## 2026-09-09: manuscript draft, no new scientific acceptance

At the user's request, authored a 12-page English LaTeX/PDF manuscript:
Weighted Pauli uncertainty for structured simplicial claw-free graphs:
exact certificates and a composition frontier. Its main theorem is the
restricted all-m, all-weight G_m result, with the coherent Gram proof,
fixed-core refinement, three-row result and two XX corollaries. C014
is explicitly an open problem, not an accepted upper bound. C010's
broader construction and historical census are not additional principal
theorems of this focused manuscript. Research snapshot remains 4dc9dc7.

Rechecked C005 rectangular Gram, C007 uniform finite gate and core
endpoint, C009 universal identities plus target hull, C014 facet,
C015 saved states, and C016 exact relaxation witness with python -S.
Paper ledger checker passes 64 hashes and headline/scope consistency.
This drafting turn did NOT rerun the historical full 127-test suite;
its 441.989-second clean-run result is explicitly attributed to the
preceding research snapshot. PDF built twice, all 12 pages rendered and
visually inspected; affected pages checked again after corrections.
No final LaTeX overfull/underfull boxes or unresolved references.
Source, builder, Russian review checklist and QA record are in paper/.
No author identities/affiliations were invented; no journal/arXiv
submission or external reviewer contact occurred. Publication priority
and external mathematical review remain outstanding.

## Experimental pivot — 2026-09-09 Moscow (2026-09-08 UTC)

User requests multi-hour empirical research rather than further proof census.
Registered operational Pauli protocol at 3237886 before held-out optimization.
Six systems, three frames, five channels/strengths, eight repetitions, three
equal-wall-budget methods. Primary endpoint is finite-measurement detection
power under exact local channels, not the optimized quartic/proxy alone.
G9 and antiC9 are held-out; C009 is a proved negative, C014 remains open.
Generic significance optimization is already prior art (Jungnitsch 2010),
as is noise-generated magic; these are explicitly excluded novelty claims.

Twelve engine tests pass (last prelaunch rerun: 0.318 s). Development-only
pilot completed one G8/no-noise cell in 2.781 s and reproduced 3.044815 > 3.
Pilot uses 0.5 s/method and 32 Monte Carlo datasets, not the production
budget of 3 s/method and 256 datasets. No held-out optimization used for
tuning. Source, protocol and input hashes will be recorded by the runner.
Production is capped at 10800 seconds and 720 complete paired cells; a
numerical C014 violation pauses the campaign for independent review.
This entry records prelaunch validation, not a completed production run.
No QPU, paid API, circuit preparation demonstration or A* confirmation.

### Operational phase 0 completed and audited — 2026-09-09

All 720 paired cells completed in 7018.094 seconds, no runner errors.
Post-run independent dense-Pauli/full-Kraus evaluation accepted 2160 saved
states (maximum mean error 1.55e-15), and separately implemented intervals
replayed all 6480 measurement records of 256 datasets. Frozen protocol,
runner/input hashes, complete job schedule and allocations match. Shared
NumPy/SciPy/RNG remain; optimizer trajectories were not rerun and earlier
graph certificates were not reproved by this audit. No QPU data.

The preregistered gain >=0.10 over BOTH baselines in EACH held-out family
fails at all three budgets. G9 damping power is zero for all methods.
At 10M shots antiC9 has ideal/noise-aware/score power
0.0000813802 / 0.0144856771 / 0.0151367188; gain over noise-aware is only
0.0006510417. Lower budgets give zero. C009 max excess 1.11e-14 and C014
4.44e-14 are roundoff-scale, not physical counterexamples. Close this
specific experimental advantage candidate, not general quantum research.
Do not rescue it by changing the frozen split or hyperparameters.

See ../pauli_operational_phase0/COMPLETED_AUDIT_RU.md and verify_completed.py.
No new campaign launched. A-star novelty remains unconfirmed. Next task
is a different, preregistered experimental capability after a prior-art
gate, not another significance optimizer or mathematical census.

### Post-campaign capability and structural-diversity gate — 2026-09-09

Rejected generic two-copy/Bell quadratic measurement as a new contribution:
the commuting lift is already explicit in Xu et al. IV.2, equations
(10)-(14), and doubling-qubit expectation estimation is existing work
(arXiv:2412.14466; abstract-level check only). Cotler--Gong--Kannan,
Noisy quantum learning theory (2026), also blocks treating noise resilience
of Bell/SWAP primitives as an untouched topic; its oracle assumptions must
be matched rather than importing its bounds into our different task.

Registered a bounded exact G8/G9 structural diagnostic before execution
in ../pauli_operational_phase0/NEXT_CAPABILITY_GATE.md. Discovery finds two
weight-preserving G8 induced embeddings in G9, no copy/split pair. Separate
stdlib acceptance verifies the map i -> i+1, omitting G9's XIII vertex of
weight one. All edges/nonedges and weights agree; changed weight and word
controls are rejected. No equality of noisy tasks or beta is inferred.

Correct the structural-diversity interpretation: G9 is a held-out instance
containing development G8, and antiC9 is another size of development's
anticycle family. They are not two structurally unrelated held-out families.
Keep the frozen protocol unchanged and attach this qualification to the
completed report. Failed operational gain remains failed. No large new
campaign, new quantum theorem, QPU call or A-star confirmation.

### Correlated-copy target gate — 2026-09-09

Read Fawzi--Kueng--Markham--Oufkir (2024), Results / Evaluating a learning
algorithm, in the primary PMC full text. Their conditional post-measurement
target and explicit obstruction to unconditional-marginal estimation already
address the proposed generic non-IID route. Filip (2002) likewise already
distinguishes uncorrelated-input purity from correlated-input witness use
(primary abstract only). Do not call these distinctions new.

COPY_CORRELATION_GATE.md gives the elementary common-latent-bit argument:
for arbitrary N, universal estimation of unconditional F=<X>^2+<Z>^2
to epsilon<1/2 with failure delta<1/2 is impossible on the two constant
product strings and their balanced mixture, by linearity of outcome
probabilities. Random pairing cannot help that permutation-invariant source.
This is a specialization of the known target obstruction, not our new theorem.

Three frozen rational two-qubit controls pass under python -S: independent
maximally mixed, classically correlated mixture, and Bell pair all have
marginal I/2, but <XX+ZZ> is respectively 0,1,2. Classical bias and an
inter-copy entanglement witness are distinct. Weighted Cauchy-Schwarz still
bounds every inter-copy separable state's score by the corresponding
one-copy universal beta bound; it does not identify marginal squares.

No new optimization campaign. The IID archive is unaffected. Before a
new operational hypothesis, specify conditional target or an explicit
mixing/reset access resource and compare with the existing non-IID theory.
No A-star novelty established; the article goal remains open.

### Process-memory literature gate and causal-filter counterexample — 2026-09-09

Generic memory detection is already covered by process-tensor witnesses,
including White et al. Quantum 9,1695 (2025) for unitary-only control and
Srivastava et al. PRResearch 8,023258 (2026) for RB blind spots. Their
classical/quantum memory assumptions cannot be replaced by a memoryless
depolarizing null. No old scalar hardware-witness claim was reopened.

During theorem-level reading, selected a specific unverified ingredient:
White et al. Section 5.1 pseudoinverse rank-preserving causal filter and
its stated finite iteration bound. Registered d=2,k=1,r=1, GHZ fixed-point
test, two valid controls and ten seeded Ginibre inputs before calculation
in ../pauli_operational_phase0/CAUSAL_PROJECTION_GATE.md.

The normalized equation-(50) transcription leaves GHZ exactly fixed with
causal residual 1/2. Analytically, sum_j sqrt(p_j)|j,j,j> is a noncausal
fixed point for any positive p_j, with squared defect
(1-1/d) sum_j p_j^2. A separate Fraction verifier checks two rational
projectors (residual squares 1/4 and 17/50). All ten random rank-one tests
miss 1e-9 after three iterations, but reach it numerically by 30. These
are not an exact proof of generic convergence; cutoff and roundoff remain.

This challenges the universal written finite guarantee, NOT the authors'
actual unretrieved code, almost-sure convergence, hardware data, or main
unitary-witness result. Before proposing any novel causal sampler, audit
publisher PDF, implementation/updates and operator-scaling prior art.
No external messages, paid run, QPU call or confirmed A-star contribution.

### Publisher and diagonal-dynamics audit — 2026-09-09

The previous status-only turn was no research progress; this continuation
completed the publisher-PDF verification (visually, pages 26–27) and
derived the full diagonal support-count recurrence for the causal filter.
Added CAUSAL_PUBLISHER_AUDIT.md and check_diagonal_causal_filter.py in the
operational folder. All 255 nonempty diagonal supports / 1530 exact finite
iterates pass the closed-form check. A separable rank-two noncausal fixed
point removes entanglement as an explanation for the failure. Unequal
column counts also separate finite rank preservation from possible rank
loss in the asymptotic limit. No generic-ensemble failure rate is inferred.
Existing low-rank Sinkhorn warnings prevent presenting low-rank failure
itself as novelty. Author code remains unretrieved; noncommuting dynamics
and sampling-measure significance remain open research gates.

### General support-rank invariant — 2026-09-09

Previous goal turn was progress (publisher audit, diagonal theorem and
published exact checks). This continuation extended the one-step result
to arbitrary PSD inputs, without a diagonal/commutation assumption.
The normalized filter preserves global rank, marginal rank and the
support of the earlier marginal at every finite exact iteration.
Causal output is possible iff rank(M)=dim(B)*rank(R); in that case one
step suffices. A strict initial deficit therefore prohibits ALL finite
exact termination. Asymptotic convergence and numerical truncation are
separate questions. This is not a proof about every multi-time pass.

Preregistered a 90-input d=2,3,4 / rank=1,...,d / ten-seed one-step sweep.
All predictions passed. Thirty full-support cases had residual <=1.894e-14;
sixty deficient cases had residual 0.125311–0.516817. One pure causal
positive control also passed. Full spectra are saved in the new result
JSON. This corrects interpretation in both directions: generic low-rank
finite failure is stronger than a measure-zero example, but generic
d=2,r=2 one-step sampling succeeds and must not be attacked using the
exceptional diagonal rank-two example. Novelty and sampling relevance
remain unconfirmed; no new A-star label or paid/hardware run.

### Alternating multi-time support audit — 2026-09-09

Extended the exact invariant to all nested tail-marginal ranks under any
sequence of the equation-50 tail filters. Generic Ginibre exact finite
repair has threshold r>=d^(2k-1); below it the top causal rank equality
is impossible at finite time. This closes the mathematical gap between
the one-step obstruction and alternating multi-time updates, not the
gap to author-code reproduction or sampling significance.

Frozen 40-run, 200-update sweep included both time orders, k=2,3, low-rank
and threshold-rank inputs. Ten descending full-support controls passed
after a single sweep, max residual 8.257e-14. Explicitly retained 38
numerical rank-threshold mismatches rather than calling all ranks verified.
For the first mismatch, a post-hoc independent 80-digit calculation found
the small marginal eigenvalue still positive at ~8.48e-16, consistent
with exact rank preservation and numerical near-boundary loss. All raw
spectra retained. Not all mismatches were independently replayed; no
asymptotic rate, sampling-bias estimate, or A-star novelty claim follows.

### Practical causal-cutoff claim falsified — 2026-09-09

Previous cycle was progress: exact multi-time invariant and numerical
precision audit. This cycle deliberately tested whether that technical
obstruction has practical consequences for temporal negativity.
Registered 20 paired rank-two inputs and five rank-eight controls, each
at cutoffs 1e-8/1e-12/1e-14 with common residual tolerance 1e-9. All 75
runs converged in 1–11 sweeps. The primary median negativity difference
was 2.3852e-12 versus the registered 0.01 relevance gate; median paired
trace distance 2.4339e-10, maximum 1.5558e-9. Gate FAILED.

Saved all 75 terminal states and independently rechecked them and all 75
pair comparisons with explicit indices/SVD, without importing the sampler.
The physical-instability interpretation is closed in this regime. Exact
finite-iteration correction remains a limited mathematical result, not
an established major contribution; original hardware or physical claims
were not refuted. Do not keep searching cutoff settings to rescue it.
The A-star objective is still unmet and active, but this branch should
not be its main claim without independently justified new significance.

### Deterministic-memory prior-art gate and return to C014 — 2026-09-09

Inspected Milz/Pollock/Modi PRA98,012108 (2018), Sections IV and V.1,
including the actual SWAP invisibility/selective-break equations 26–27.
The proposed deterministic-only invisible memory example is a direct
trace-preservation extension, so it is rejected before a large run.
Added the precise access restrictions and source mapping in
../pauli_operational_phase0/DETERMINISTIC_MEMORY_PRIOR_GATE.md.

Revalidated C014 and C016 using their existing exact independent scripts.
The full classical facet at six and rational theta witness 6.50657958
remain valid; the quantum upper bound remains unresolved. This is a
return to the manuscript's real open operator obligation, not a new name
for any falsified experimental effect. No new theorem or experiment is
claimed from the revalidation. Next proof work needs constraints stronger
than theta with central-sector coverage, not additional random starts.

### C017 two-copy PPT route — 2026-09-09

Built a Bell-diagonal PPT relaxation of the fixed C014 quadratic objective,
using sparse intermediate four-by-four partial-transpose transforms rather
than a dense two-copy operator. Registered G8 positive control and C014,
one thread and 60-second cap each. The direct one-qubit formula check passed;
G8 numerical optimum was 10/3 within rounding. A subsequent exact rational
primal repair gives 333333354/100000135, verified with integer transforms
and an independent direct small character matrix. It is a feasible relaxed
value, not a physical counterexample and not an upper proof.

C014 has 131072 variables / 114689 equalities / 589824 nonzeros. It timed
out without a primal incumbent after the frozen 60 seconds. Saved this
failure explicitly; no C014 numerical bound or theorem follows. The next
useful implementation effort is a proved symmetry/dual reduction before
another solve, not more random-state starts or increased time by default.
Graph-universal representation coverage and rigorous dual certification
remain obligations if this relaxation eventually returns six.

### C018/C019 symmetry and constraint-generation audit — 2026-09-09

Derived distinct affine Bell and linear PT actions, verified 16 valid
weighted graph automorphisms against every label and objective coordinate.
Exact orbit partitions reduce 16384 probability entries to 5184 masses,
but a dense orbit matrix exceeds the frozen size budget, so C018 stopped
without constructing or solving it. Registered C019 before a different
bounded constraint-generation run on the same fixed relaxation.

C019 solved 20 truncated LPs in 40.875 seconds, ending with 608 cuts,
objective 9.54659 and full PT minimum -0.00120769. Every saved candidate
fails full PPT. An independent Walsh-convolution verifier reproduced all
20 minima and original-objective values. No PPT witness above six, exact
upper certificate, or physical violation was obtained. This is useful
implementation and failed-route evidence, NOT an improved quantum bound
or a confirmed A-star result. All unsatisfied constraints remain in scope.

### C020 exact exclusion of standalone PPT route — 2026-09-09

Switched from unfinished upper-bound LPs to a preregistered primal
feasibility search on the SAME full-coordinate PPT relaxation. Fixed
PDHG parameters, uniform start, no restarts; first checkpoint at 100
iterations already yielded a uniformly repaired objective 6.56518.
Runtime 0.187 seconds. Converted this candidate to rational probabilities
and performed exact uniform feasibility repair. Objective is exactly
3282590033509/500000010289 >6. All 16384 probabilities and PT coordinates
are strictly positive and normalized. Original C014 weights/labels and
source hash verified; objective rebuilt from local Bell eigenvalue tables.

Both integer local PT and integer Walsh convolution agree in all
coordinates. Verification passes with python -S; six negative/positive
controls pass. Therefore the standalone PPT relaxation cannot establish
C014's bound six, regardless of further optimizer budget. This is not
a separable/tensor-square witness, so no uncertainty violation is claimed.
PPT optimum, stronger relaxations and the original operator inequality
remain open. The completed exact exclusion replaces timeout uncertainty
about this proof route, but is not claimed as A-star novelty.

### C021 symmetric-support PPT and exact near-six bound — 2026-09-09

Previous turn produced an exact exclusion of standalone PPT. Added the
independently justified pure-identical-copy support condition, not merely
swap invariance. C020 has exact nonzero antisymmetric mass and is therefore
excluded. Frozen PDHG with G8 control and C014, no restarts: G8 retained
its violation; C014 after 20000 steps / 21.938 sec gave numerical primal
5.99999999942047 and dual 6.000000000000007.

Converted the dual to rational nonnegative coordinates and computed the
actual exact maximum rather than asserting rounding to six. Certified
upper is 6+33/25600000000000 for the archived C014 representation.
All 16384 dual coordinates / 8256 symmetric support inequalities verified
via integer local transform and integer Walsh convolution, source and
objective regenerated; python -S verification and five tests pass.
This genuinely improves the fixed-representation upper estimate, but
the small positive remainder remains: no exact facet, graph-universal
theorem, or A-star claim. Near-active-orbit diagnostics may guide a next
registered rational certificate recovery, not substitute for its proof.
