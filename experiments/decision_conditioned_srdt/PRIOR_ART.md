# Prior-art audit and novelty boundary

Audit date: 2026-08-24.

The algebraic ingredients are not new:

- Difference densities are established objects in quantum chemistry; see the
  [Chem. Rev. review](https://doi.org/10.1021/acs.chemrev.9b00447).
- The symmetric anticommutator is the Jordan product and already appears in
  conditional quasi-states, states over time, and weak-value constructions;
  see [Fullwood and Parzygnat](https://pmc.ncbi.nlm.nih.gov/articles/PMC5627384/)
  and the later
  [Jordan-product observable-over-time formulation](https://arxiv.org/abs/2412.11659).
- Observable-centred tensor-network evolution is established; Heisenberg-picture
  DMRG explicitly evolves the observable of interest rather than the whole state
  ([Hartmann et al.](https://arxiv.org/abs/0808.0666)). Conventional DMRG density
  truncation is reviewed by [Schollwoeck](https://arxiv.org/abs/cond-mat/0409292).
- Spectral low-rank density-matrix truncation is also used in circuit simulation,
  for example in
  [low-rank noisy-circuit evolution](https://www.nature.com/articles/s41534-021-00392-4).

The candidate methodological novelty is therefore deliberately narrower: use
the spatial partial trace of the Jordan product of a *paired signed state
contrast* and a *decision effect* as the truncation object; then apply
absolute-eigenvalue truncation to obtain an exact global comparison-gap trace,
an exact discarded-eigenvalue error decomposition, and a trace-norm certificate.
The frozen comparison against both decision-blind SRDT and state-averaged bases
is also specific to this work.

Targeted searches did not locate this exact construction and claim package.
That negative search is not proof of priority. Any publication should describe
the result as a candidate new comparison-oriented truncation primitive and ask
domain reviewers to check the weak-value, tensor-network, and goal-oriented
model-reduction literatures before making a stronger priority claim.
