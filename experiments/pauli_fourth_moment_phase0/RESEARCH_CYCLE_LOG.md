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
