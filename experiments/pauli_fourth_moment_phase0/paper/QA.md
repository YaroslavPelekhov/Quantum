# Manuscript QA - 2026-09-09

- Research snapshot: `4dc9dc7bc26cca5ea3a7f4cfa66cc4f7fc969a83`.
- Output: `output/pdf/weighted_pauli_uncertainty_manuscript.pdf` (12 A4 pages).
- SHA-256 of delivered PDF: `d00e9a3b1cd3682e43a58ec53e4b24cdefe3acb5ad710df40fc3fd63b80a519d`.
- Source: `main.tex`; build: `build.ps1`; read-only consistency check: `check_paper.py`.
- Two-pass MiKTeX pdfLaTeX build succeeded, shell escape and automatic package installation disabled.
- Final LaTeX log: no overfull/underfull boxes, unresolved references, or citation warnings. MiKTeX separately displayed its installation-update reminder; no installation update was attempted.
- All twelve pages rendered with Poppler and visually inspected. After the final content correction, pages 8-12 were rendered and inspected again; pages 1-7 did not change.
- Removed two initial overfull boxes by allowing filename wrapping and separating graph6 identifiers.
- Corrected first-moment Gram-vector indexing to `v_(i+1)`; explicitly identified the eight-vertex positive control and its published source figure.
- PDF has no form, JavaScript, or encryption. Author metadata is not fabricated.

## Mathematical checks rerun for the manuscript

All seven following standard-library acceptance programs passed:

1. `verify_scf_rectangular_gram_bridge.py`
2. `verify_scf_uniform_facet_gate.py`
3. `verify_scf_core_refinement.py`
4. `verify_scf_three_row_gram.py`
5. `verify_scf_two_xx_weight.py`
6. `verify_scf_two_xx_attack.py`
7. `verify_scf_two_xx_baseline.py`

`check_paper.py` additionally checks all 64 existing artifact hashes,
the main hull counts, target weights/ranks, the completed-start and
convergence counts, the saved physical best value, exact relaxation
objective, and open-claim flags. It checks LaTeX labels/citations too.
It does not mechanically verify every line of the analytic proofs.

The quoted 127-test full clean run belongs to the preceding research
cycle, not to this manuscript build. All optimizer trajectories were
not rerun. No experiment artifact was edited and the mathematical
manifest remains at 64 artifacts; the PDF is a presentation artifact.

## Remaining review gates

External mathematical and novelty review; human approval of authorship,
affiliations, disclosures and submission venue. C014 quantum validity
remains open. No assertion of confirmed A-star novelty or acceptance.
