# Pauli fourth-moment phase 0

This experiment tests a concrete route to the finite-exponent fractional
colouring question for large Pauli expectations.  The frozen hypothesis is
the weighted identity `beta_4(G,w)=alpha(G,w)`; if true, it implies
`chi_f(B_epsilon)<=epsilon^-4`.

The directory is deliberately isolated from the closed QAOA/MPS and DCS
branches.  See `PREREGISTRATION.md` for the decision rule and
`PRIOR_ART_AUDIT.md` for claim boundaries.

No result in this directory should be described as proved or A-star-ready
until the confirmatory gates in the preregistration all pass.

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
explicit atom.
`run_prior_art_scf_screen.py` downloads the Wang et al. imperfect-graph
benchmarks at a pinned upstream commit, verifies their SHA-256 hashes, and
screens them for the SCF property.
`run_published_g9_control.py` reproduces the narrow-basin weighted violation
reported by Wang et al. from their published warm-start state.

The GPU oracle requires PyTorch with CUDA.  The small exact audit requires
NumPy and SciPy; the graph-atlas audit additionally requires NetworkX.

See `POSTFREEZE_THEORY_NOTE.md` for the proved one-logical-qubit obstruction
and the exact boundary between theorem and conjecture.
