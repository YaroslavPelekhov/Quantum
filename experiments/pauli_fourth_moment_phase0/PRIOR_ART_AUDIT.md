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
- papers posted after arXiv:2608.20113 that answer its Question 8.
