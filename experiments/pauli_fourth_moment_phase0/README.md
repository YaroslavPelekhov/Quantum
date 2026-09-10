# Pauli fourth-moment phase 0

C038 completed: [every line graph is hbar-perfect for all weights](LINE_GRAPH_HBAR_THEOREM_C038.md).
The analytic proof uses a Majorana realization, nuclear-norm duality and
Edmonds' matching polytope. It yields the exact identity
`beta(L(R),w)=alpha(L(R),w)=nu(R,w)` at arbitrary size and an infinite
separation `L(K_(2k+1))` from the previously sufficient h-perfect class.
All 1,245 nonempty atlas roots pass the finite polar-factor stress audit;
47 small roots also pass a direct dense Jordan--Wigner norm check, and
five corruption-controlled tests plus a `python -S` witness verifier pass.
External proof review and publication priority remain open, so this is a
strong A-star candidate rather than an acceptance claim.

The [adversarial C038 priority audit](LINE_GRAPH_PRIORITY_AUDIT_C038.md)
separates the claim from free-fermion solvability, magic-state simulation,
measurement incompatibility, and classical skew-energy bounds. It also
records the main remaining risk: the weighted matrix inequality may exist
under different notation, and the SCF-rank/Edmonds proof is short once its
ingredients are combined.

Current fixed C014 result: [C031 exact certificate](C031_DIXON_GATE.md)
proves beta(G,w)=6 for the specified 24-vertex graph and weights. The
seven-qubit 1024-start attack and theta value 6.50657958 are historical
diagnostics, not its proof. The local manuscript now includes C031.
General H-SCF, literature priority, and publication significance remain open.
Historical test counts refer to their recorded snapshots, not every later
working copy. See the repository-level research_package for current checks.

C012 completed: [fixed closed XX graph, all weights](SCF_XX_CLOSURE_C012.md).
The independently complete 44-facet hull and the missing-facet control
pass. All rows reduce to known quantum bounds; this is a fixed-graph
corollary and a negative novelty screen, not general strip composition.

C011 completed: [published XX-strip all-weight corollary](SCF_XX_GATE_C011.md).
The source-defined 13-vertex graph has alpha=4 and 33 independently
complete exact facets. Its only extra weighted row is an induced C009
row. Deletion variants follow by heredity. This expands the covered class,
but supplies no new operator mechanism or unrestricted SCF theorem.

C010 completed: [all claw-free F(E), arbitrary column count and all weights](SCF_THREE_ROW_ALL_WEIGHT_C010.md).
The remaining row-pair cases are closed by a fixed-core endpoint lemma
and a uniform refinement proof. This is a theorem for the construction,
not all SCF graphs. External review and novelty remain open.

C009 completed: [fixed three-row all-weight theorem](SCF_THREE_ROW_GRAM_C009.md).
Independent full-algebra identities plus the spectral envelope close the
last facet of the C008 target. The complete rational hull gives all weights.
Nine new tests include corrupted-certificate controls. General SCF and
A-star novelty remain open; the next step is uniform extension, not a census.

C008 completed (historical): [three-row structural gate](SCF_THREE_ROW_STRUCTURAL_GATE.md).
An arbitrary-column structural proof and 4096-pattern exact audit isolate
a 12-vertex target outside the earlier hereditary family. Its complete
36-facet hull leaves exactly one quantum inequality unresolved. No beta
optimization was run; all 78 tests pass. C009 must attack that operator
obligation before another graph census.

C007 completed: [all weights for the unbounded G_m family](SCF_UNBOUNDED_ALL_WEIGHT_FAMILY.md).
A uniform classical refinement proof reduces arbitrary m to an exactly
verified fixed core. All non-C005 positive inequalities have alpha<=2
support, so the earlier quantum bounds complete all weights at every size.
The combined suite has 69 passing tests. The result is not unrestricted
H-SCF or confirmed A-star novelty; classical homogeneous-pair/flow tools
are explicitly credited to prior art.

C006 completed: [all-weight closure of G_1](SCF_G1_ALL_WEIGHT_CLOSURE.md).
All 27 facets and 34 stable vertices are exactly complete under both cdd.gmp
and a separate Fraction edge-clipping implementation. All weights are now
proved for the selected ten-vertex graph, not every G_m or every SCF graph.
The suite then had 55 tests, including a geometrically missing facet.

C005 completed: [signed rectangular Gram family theorem](SCF_RECTANGULAR_GRAM_FAMILY.md).
An exact coherent identity proves the frozen ten-vertex facet and its
unbounded fixed-weight family. This is not all-weight SCF perfection.
The suite at C005 had 45 tests; no numerical SDP was needed for C005.

C004 completed as a [structural/operator proof gate](SCF_CROSS_CLAW_OPERATOR_GATE.md):
36 one-sided-central cases, an exact cross-claw criterion and a C5 control
against lossless dephasing. The quantum coherent bridge is still unresolved.
The suite at C004 had 37 tests; its next step was the transfer/SOS gate.

C003 completed: [exact counterexample to generic almost-clique closure](ALMOST_CLIQUE_CLOSURE_COUNTEREXAMPLE.md).
Both local all-weight proofs, a three-qubit integer-state witness, and
incompatible boundary-event bounds are independently verified. Not an SCF
counterexample and not a new imperfect-graph claim.

Current continuation: [research program](RESEARCH_PROGRAM_RU.md),
[cycle log](RESEARCH_CYCLE_LOG.md), and [boundary-route audit](SCF_BOUNDARY_ROUTE_AUDIT.md).
The C001/C002 scripts and independent verifiers distinguish structural
coverage, coordinatewise compatibility, and genuine quantum proof obligations.

This experiment tests a concrete route to the finite-exponent fractional
colouring question for large Pauli expectations.  The frozen hypothesis is
the weighted identity `beta_4(G,w)=alpha(G,w)`; if true, it implies
`chi_f(B_epsilon)<=epsilon^-4`.

The directory is deliberately isolated from the closed QAOA/MPS and DCS
branches.  See `PREREGISTRATION.md` for the decision rule and
`PRIOR_ART_AUDIT.md` for claim boundaries.

The original unrestricted fourth-moment and convolution conjectures remain
unproved. Separate scoped theorems are explicitly distinguished from those
conjectures; none is described as A-star-ready without external review.
The latest is [exact weighted SCF perfection through order nine](SCF_ORDER9_EXACT_THEOREM.md),
with 128/128 nonrank types proved and a fully rational completeness audit.

The subsequent [generalization theorems](SCF_GENERALIZATION_THEOREMS.md)
remove the vertex-count limit for SCF graphs with independence number at
most two and prove clique-separator closure. Exact counterexamples rule out
profile-only two-clique gluing and a proposed correlation completion. Run
`verify_scf_generalization.py` for solver-independent integer/rational checks.

## Reproduction

Small exact LP audit:

```powershell
python run_small_convolution_audit.py --max-qubits 4 `
  --cache-dir .cache/pauli-fourth-moment `
  --output small_triple_convolution.json
```

The six-qubit experiments use a deterministic 59 MB local cache which is
regenerated rather than committed:

```powershell
python build_n6_contexts.py `
  --cache-dir .cache/pauli-fourth-moment `
  --output .cache/pauli-fourth-moment/lagrangian_bases_n6.npy

python run_n6_adversarial.py `
  --contexts .cache/pauli-fourth-moment/lagrangian_bases_n6.npy `
  --mode triple --witnesses 30 --starts 160 --steps 2200 `
  --output n6_triple_convolution_adversarial.json
```

Use `--mode p4` for the frozen claim and `--mode shortcut` for the stronger
`max(r^2)` proof route.  `run_n6_cover.py` builds explicit unsigned covers;
`verify_n6_cover.py` recomputes a stored certificate independently.
`run_one_logical_identity_audit.py` compares the syndrome-mixture identity
against a direct density-matrix simulation of the defining CNOT circuit.
`run_one_logical_completeness_gap.py` exhaustively demonstrates that those
one-logical tests do not characterize the full three-qubit stabilizer
polytope.  `run_theta_shortcut_audit.py` falsifies the corresponding generic
theta-body shortcut (it requires CVXPY in addition to the packages below).
`run_multilogical_witness_audit.py` checks the first extracted spin-factor
witness covered by the analytic higher-logical theorem.
`run_cnc_positivity_audit.py` checks signs and normalization across canonical
maximal-CNC forms with several spin/syndrome dimensions and odd orders.
`run_line_graph_p3_audit.py` (legacy filename) checks the line-graph matching
constraints for Majorana realizations; the final theorem was strengthened
from exponent three to exponent two after the free-fermion audit.
`run_scf_hbar_falsification.py` runs the preregistered weighted attack on
genuinely non-line simplicial claw-free graphs.
`run_scf_facet_attack.py` enumerates stable-set vertices, extracts facet
directions, and targets every non-rank direction found in that candidate set.
`run_scf_theta_guided_attack.py` solves the first state-moment relaxation and
uses its optimistic profile to seed sign-enumerated attacks on those facets;
it also reproduces the published narrow-basin `G9` violation.
`run_scf_order9_census.py` exhaustively screens McKay's 261,080 connected
order-nine graphs with a pinned source hash.
`run_scf_order9_facet_census.py` quotients every non-rank SCF facet by
weighted-support isomorphism, and `run_scf_order9_guided_attack.py` exhausts
every sign orthant of the SDP profile for each representative.
`run_scf_order9_facet_reduction.py` verifies the analytic join reduction for
115 of the 128 types.  `state_moment_sdp.py` ports the real state-moment
hierarchy used for the remaining types; `run_state_moment_g9_control.py`
validates the port on the published `G9` bounds,
`run_scf_order9_state_moment.py` tests all 13 alpha-three residuals, and
`run_scf_order9_level3_atom.py` reproduces the level-3 bound for the final
explicit atom.  `run_scf_atom_spectral_reduction.py` proves the cancellation
pattern of its eight four-hole operators and reduces the remaining quantum
gate to a single scalar inequality, then runs a seeded interior falsification
test of that inequality.  It also verifies the exact univariate
factorization proving the inequality on the five primitive single-channel
support faces and independently tests all eight hole-generated faces.
`run_prior_art_scf_screen.py` downloads the Wang et al. imperfect-graph
benchmarks at a pinned upstream commit, verifies their SHA-256 hashes, and
screens them for the SCF property.
`run_published_g9_control.py` reproduces the narrow-basin weighted violation
reported by Wang et al. from their published warm-start state.

The GPU oracle requires PyTorch with CUDA.  The small exact audit requires
NumPy and SciPy; the graph-atlas audit additionally requires NetworkX.

See `POSTFREEZE_THEORY_NOTE.md` for the proved one-logical-qubit obstruction
and the exact boundary between theorem and conjecture.
