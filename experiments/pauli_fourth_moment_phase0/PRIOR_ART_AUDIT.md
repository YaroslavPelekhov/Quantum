# Prior-art audit: weighted fourth moments of Pauli expectations

Status at freeze: no direct collision found; audit remains open.

## Closest results checked

- Xu, Schwonnek, and Winter, *Bounding the Joint Numerical Range of Pauli
  Strings by Graph Parameters*, arXiv:2308.00753.  Defines the weighted
  second-moment beta number, proves graph-operation rules, and gives the
  anti-`C_7` separation `beta_2>alpha`.
- King et al., *Triply efficient shadow tomography*, arXiv:2404.19211.
  Reduces the relevant two-copy Clifford protocol to an efficiently
  sampleable fractional colouring of the large-expectation anticommutation
  graph.
- Wang et al., *Simultaneous variances of Pauli strings, weighted independence
  numbers, and a new kind of perfection of graphs*, arXiv:2511.13531.
  Defines `beta(G,w,k)` and proves only convergence to `alpha(G,w)` as
  `k -> infinity`; no universal finite exponent is stated in the inspected
  source.
- Stempin, Llorens, and Huber, *Counterexamples to the fractional coloring
  conjecture for triply efficient shadow tomography*, arXiv:2608.20113.
  Disproves the exponent-two conjecture, establishes a lower exponent
  `2.07598...`, and explicitly leaves existence of any finite universal
  exponent open.
- Liu et al., *Graph Theoretic Approach to Quantum Nonstabilizerness*,
  arXiv:2607.26154v1.  Appendix C explicitly separates (i) weighted linear
  functionals of the squared Pauli profile, (ii) the unweighted global
  self-collision `sum_P <P>^4`, and (iii) state-dependent MWIS/dephased
  purity.  It proves the stabilizer optimum of the squared functional is
  `alpha(G,w)` and records the ordinary unweighted fourth-moment identity,
  but does not assert the weighted fourth-moment upper bound in T1.  This is
  a particularly close non-collision and confirms that the missing step is
  not merely a change of notation.
- Bu, Gu, and Jaffe, *Stabilizer Testing and Magic Entropy via Quantum
  Fourier Analysis*, arXiv:2306.09292v2.  For odd qubit convolution it proves
  multiplicativity of Pauli characteristic functions, Clifford covariance,
  and closure when all inputs are stabilizer states.  The inspected source
  does not state that convolution of arbitrary input states is in the
  stabilizer polytope, nor the one-logical-qubit no-distillation statement
  recorded in the post-freeze theory note.
- Patra et al., *Qubit magic-breaking channels*, arXiv:2409.04425.  Gives
  necessary and sufficient geometric criteria for one-qubit magic-breaking
  channels and shows that tensor products of individually magic-breaking
  qubit channels need not be magic-breaking.  It covers the one-qubit
  diagonal-channel special case behind the Holder step, but not the
  correlated many-qubit convolution channel or arbitrary stabilizer-code
  postselection considered here.
- Raussendorf et al., *Phase-space-simulation method for quantum computation
  with magic states on qubits*, Phys. Rev. A 101, 012350 (2020), introduces
  the CNC simulation framework.  Ipek et al., *Phase-space tableau
  simulation for quantum computation*, Phys. Rev. A 113, 032409 (2026), and
  Okay, *Polyhedral classical simulators for quantum computation*, Research
  in the Mathematical Sciences 13, 55 (2026), give the maximal-CNC
  anticommuting-factor structure used in our corollary.  These are essential
  structural prior art.  The inspected sources do not discuss quantum
  convolution and do not state that arbitrary odd convolution is
  nonnegative on every maximal CNC phase-point operator.
- De Carli Silva and Tuncel, *An Axiomatic Duality Framework for the Theta
  Body and Related Convex Corners*, arXiv:1412.2103.  Develops the relevant
  theta-body and antiblocker framework.  It does not supply the nonlinear
  inclusion needed by the shortcut; our explicit ten-vertex SDP point shows
  that inclusion is false for a generic theta body.
- Edmonds' matching-polytope theorem supplies the odd-set description used
  in the line-graph proof.  The targeted search found standard fractional-
  matching half-integrality, blossom separation, and power-rounding work for
  dynamic/bipartite matching.  It did not find the statement that squared
  entries of a physical Majorana covariance contraction form a matching-
  polytope point, nor its weighted Pauli beta consequence.
- Zurel, Cohen, and Raussendorf, *Simulation of quantum computation with
  magic states via Jordan-Wigner transformations*, Phys. Rev. A 112, 042602
  (2025), constructs phase-point operators with line-graph anticommutation
  structure.  Chapman and Flammia, *Characterization of solvable spin models
  via graph invariants*, Quantum 4, 278 (2020), prove the generator-to-
  generator Majorana representation precisely for line-graph frustration
  graphs.  Chapman, Elman, and Mann, *A Unified Graph-Theoretic Framework for
  Free-Fermion Solvability*, PRX Quantum 4, 030304 (2023), extend solvability
  to simplicial claw-free graphs.  Full-text searches of both free-fermion
  papers found no covariance-matrix, squared-expectation, beta-body, or
  matching-polytope statement.  Conversely, full-text searches of the beta
  and hbar-perfect papers found no line-graph or matching statement.  Thus
  the ingredients are established and unusually close, but the exact body
  identity `BETA(L(H))=MATCH(H)` was not found in the targeted search.
- Grewal et al., *Improved Stabilizer Estimation via Bell Difference
  Sampling*, arXiv:2304.13915.  Supplies fourth-copy/Weyl-distribution Fourier
  identities that may be useful for a proof, but no weighted stable-set
  decomposition was found in the inspected source.
- Leone, Oliviero, and Hamma, *Stabilizer Renyi entropy*, arXiv:2106.12587.
  Studies global moments of the full Pauli spectrum; no graph-weighted
  maximum-commuting-set inequality was found.

## Known non-collisions and traps

- `chi_f(G; |b|)=R_M^#`-type robustness identities do not imply a universal
  epsilon-only bound because the magic resource can scale with the state.
- Schur-squaring a theta lift gives a doubly-nonnegative matrix, not in
  general a completely-positive lift.  Generic theta-body squaring is not a
  valid route to `STAB`.
- More strongly, `max_i(x_i) x in STAB(G)` is false for generic
  `x in TH(G)`: `theta_shortcut_audit.json` records a feasible ten-vertex
  counterexample with ratio `1.0047900622`.
- Passing every postselected one-logical stabilizer-code octahedron test does
  not characterize the full stabilizer polytope.  The three-qubit separating
  state and exact integer vertex witness are stored in
  `one_logical_completeness_gap.json`.
- The full-Pauli identity `sum_P |Tr(rho P)|^4 <= 2^n` is much weaker than the
  weighted induced-subgraph statement.
- Clique uncertainty `sum_{i in C}<S_i>^2<=1` proves only clique constraints,
  not arbitrary stable-set facets.

## Remaining adversarial searches

- state-polynomial and noncommutative moment inequalities at degree four;
- contextuality/exclusivity results phrased as two-copy classicality;
- completely-positive versus doubly-nonnegative Pauli Gram matrices;
- stabilizer/Weyl-distribution decompositions over Lagrangian subspaces;
- noncommutative `L_p` and hypercontractive inequalities for
  quasi-Clifford algebras;
- magic-breaking/stabilizer-breaking Pauli channels and normal forms for
  postselected stabilizer operations;
- any positivity-preserver or hypercontractive result equivalent to odd
  convolution being nonnegative on all maximal CNC phase points;
- papers posted after arXiv:2608.20113 that answer its Question 8.
- fermionic covariance, matching-polytope, or free-fermion results under
  alternative terminology that could subsume the line-graph theorem.
