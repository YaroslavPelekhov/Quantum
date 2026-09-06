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
