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
