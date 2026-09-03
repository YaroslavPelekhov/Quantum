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

The GPU oracle requires PyTorch with CUDA.  The small exact audit requires
NumPy and SciPy; the graph-atlas audit additionally requires NetworkX.

See `POSTFREEZE_THEORY_NOTE.md` for the proved one-logical-qubit obstruction
and the exact boundary between theorem and conjecture.
