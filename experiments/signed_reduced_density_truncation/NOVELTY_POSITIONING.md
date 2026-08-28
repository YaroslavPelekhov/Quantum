# Novelty boundary

The contribution under test is **not** multi-state/state-averaged DMRG, which
uses a positive weighted average of target-state density matrices.  It is also
not incremental circuit simulation or multiple-amplitude contraction.

The candidate new element is a signed, indefinite truncation target
`Gamma=rho_B-rho_A` with an exact worst-case observable certificate.  Retained
modes are ordered by absolute eigenvalue, and the resource objective is local
contrast error rather than either state fidelity.

Difference density matrices themselves are established in quantum chemistry,
where positive/negative eigenspaces are interpreted as attachment and
detachment densities.  That descriptive use is prior art and is not claimed as
new here.  The scoped candidate contribution is the use of the reduced
difference as a tensor-network truncation target, its sharp minimax observable
certificate, and the two-circuit resource comparison.

Closest established lines checked before implementation:

- Schollwoeck's DMRG review: density-matrix truncation and MPS foundations.
  https://arxiv.org/abs/cond-mat/0409292
- qTask: reuse after circuit modifications, not signed minimax truncation.
  https://arxiv.org/abs/2210.01076
- Liu et al.: shared multiple-amplitude tensor-network contraction, not a
  contrast density or trace-norm certificate.
  https://arxiv.org/abs/2212.04749
- Rogerson and Roy: reverse-mode differentiable MPS simulation, not finite
  two-circuit signed truncation. https://arxiv.org/abs/2408.12583
- Difference-density/attachment-detachment analysis in electronic-structure
  theory (established object, different computational role):
  https://doi.org/10.1021/acs.chemrev.9b00447

This is a scoped computational prior-art audit, not a legal patentability or
exhaustive literature claim.  The identity `Gamma=rho_B-rho_A`, trace-norm
duality, and Eckart--Young--Mirsky theorem are standard; novelty, if sustained,
lies in their use as the truncation primitive for comparison-native tensor
simulation.
