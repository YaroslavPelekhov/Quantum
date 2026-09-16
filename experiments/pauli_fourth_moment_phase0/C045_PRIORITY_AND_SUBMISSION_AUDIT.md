# C045: priority and submission-focus audit

Audit date: 2026-09-16. Scope: the priority-sensitive claims in the C038
manuscript, with the C044 proof hardening treated as complete. This is a
documented adversarial search, not a legal priority opinion, an external
referee report, or a venue guarantee.

## 1. Claim frozen before search

The headline claim is deliberately narrow:

> For every finite simple root graph `R` and every nonnegative edge weight
> `w`, the Pauli beta body of the line graph is the matching polytope of `R`;
> equivalently, `beta(L(R),w)=alpha(L(R),w)=nu(R,w)` for every `w`.

The proof-specific bridge is:

> If `Q` is a real skew contraction, then the supported squared entries
> `x_e=Q_e^2` satisfy every degree and odd-set inequality and therefore lie
> in `MATCH(R)`.

The matrix corollary is:

> `(||A||_*/2)^2 <= nu(R,w) sum_e A_e^2/w_e` for every real skew matrix
> supported on `R` and every positive comparison weight `w`.

No priority is claimed for beta numbers, line-graph free-fermion
representations, nuclear/operator norm duality, skew energy, Edmonds'
polytope, or maximum-weight matching.

## 2. Source-by-source collision test

| Source | What is already there | Exact collision test | Verdict |
|---|---|---|---|
| Xu, Schwonnek, Winter, PRX Quantum 5, 020318 (2024) | beta number, representation invariance, joint numerical range, odd-cycle examples | Does the paper identify `BETA(L(R))` with `MATCH(R)` for arbitrary roots and weights? | No such theorem or matching-polytope mechanism was found in the article. The invariant is prior art. |
| Xu et al., arXiv:2511.13531v1 (2025) | hbar-perfectness, closure operations, numerical hierarchies, applications | Does the full searchable text state `line graph` or `matching`? | Neither phrase occurs in the accessible v1 HTML. The general framework is prior art; the line-graph theorem is not stated there. |
| Chapman--Flammia, Quantum 4, 278 (2020) | line-graph characterization of free-fermion-solvable Pauli Hamiltonians | Does spectral solvability give the all-weight squared-expectation body or all blossom inequalities? | No. The Majorana realization and spectral normal form are prior inputs; the convex body identification is additional. |
| Chapman--Elman--Mann, arXiv:2305.15625v1 (2023) | broader simplicial claw-free free-fermion framework | Does it state a matching-polytope beta-body theorem? | No searchable occurrence of `matching polytope`; it is a structural/spectral input to the secondary proof. |
| Edmonds, J. Res. NBS 69B (1965) | matching polytope and maximum-weight matching | Does it connect skew contractions or Pauli expectation squares to the polytope? | No. The polyhedral characterization is a central credited ingredient. |
| Tian--Wong, Discrete Appl. Math. 222 (2017) | relations between unweighted oriented skew energy and matching number | Does it use arbitrary real matrix entries, arbitrary positive comparison weights, or prove squared contraction profiles lie in `MATCH(R)`? | No such weighted/full-polytope statement was located. It kills novelty of a coarse unweighted skew-energy shadow, not the frozen theorem. |
| Gong et al., Linear Algebra Appl. 439 (2013) | extremal skew energy for integral-weighted oriented unicyclic graphs | Are its graph weights the comparison weights of the frozen inequality, and is the optimum maximum-weight matching? | No. It studies a restricted extremal graph-energy problem with integral arc weights. |
| Zhou et al., Linear Algebra Appl. 675 (2023) | trace-norm bounds for 0/1 oriented adjacency matrices in terms of rank and maximum degree | Does it contain support-sensitive arbitrary-entry/maximum-weight-matching control? | No. Its matrix and bound are different and orientation-specific. |
| McNulty, arXiv:2511.15954v1 (2025) | incompatibility robustness for line graphs, bounded through maximum skew energy; exact symmetric families | Is the optimized object the beta body, and are arbitrary nonnegative edge weights reduced to matching? | No. This is the closest quantum neighbor but a different invariant and generally a spectral bound rather than the frozen equality. |

## 3. Searches and alternate vocabulary

The audit repeated exact-title and full-text searches and deliberately changed
vocabulary across the three neighboring literatures:

- `line graph` with `weighted beta`, `Pauli uncertainty`, `hbar-perfect`,
  `matching polytope`, and `maximum-weight matching`;
- `skew-symmetric contraction`, `antisymmetric contraction`, `squared
  entries`, `odd-set inequalities`, and `blossom inequalities`;
- `nuclear norm`, `trace norm`, `Schatten 1-norm`, `Ky Fan norm`, `skew
  energy`, and `maximum-weight matching`;
- `fermionic covariance matrix`, `Majorana bilinear`, and `matching
  polytope`;
- weighted oriented-graph energy, skew rank, Pfaffian/Tutte-matrix, and
  algebraic matching literature.

Primary or publisher sources were preferred. The current arXiv records for
the three closest recent preprints expose only v1 as of the audit date. The
negative result remains query- and access-dependent: books, unindexed theses,
non-English sources, inaccessible full text, and unpublished observations
cannot be excluded.

## 4. What survived and what did not

### Surviving priority-sensitive package

1. The all-weight identity `BETA(L(R))=MATCH(R)` for every finite simple
   root graph.
2. The specific blossom mechanism: odd principal skew contractions lose one
   rank, which supplies every odd-set facet.
3. The support-sensitive weighted nuclear-norm inequality with
   maximum-*weight* matching and arbitrary real supported entries.
4. The strict `L(K_(2k+1))` separation from the previously cited
   h-perfect sufficient route.

### Claims explicitly removed from the novelty surface

- line graphs are free-fermion solvable;
- skew energy is related to matching number or rank;
- Edmonds' description and matching algorithms;
- the beta invariant and representation invariance;
- the graph families `L(K_(2k+1))` themselves;
- a quantum speedup, hardware advantage, or new matching algorithm.

## 5. Section 7 structural risk after C044

The external review correctly identified the simplicial claw-free quasi-line
extension as the largest proof risk. C044 replaces the earlier geometric
three-arc sketch by a self-contained left/right sumset argument and separately
handles the boundary `n=2p+1`. The audit suite covers 38,772 induced
one-vertex deletions, 1,027,351 admissible algebra rows through order 160,
4,194,302 deficit subsets, and 3,803,174 exact circulant cliques through
order 30. This is strong falsification support, but the extension is now
positioned as secondary because it depends on the exact classical quasi-line
facet classification.

## 6. Submission restructuring decision

The manuscript is refocused on one theorem:

- title and abstract lead only with exact line-graph Pauli uncertainty via
  the matching polytope;
- the SCF quasi-line theorem is labeled a secondary extension;
- the central atlas baseline and skewness ablation remain in the main text;
- scaled random ensembles, density/weak-coupling stress, the extended
  reproducibility ledger, and the expanded prior-art map are appendices;
- the main text now closes with an explicit contribution hierarchy and
  priority boundary before those appendices.

This removes the appearance of two competing papers and makes the empirical
work serve the proof mechanism instead of carrying the novelty claim.

## 7. Verdict

**The central line-graph theorem remains a strong A/A-star candidate after
the expanded adversarial search. Priority is supported, not certified.** No
exact collision was found for the conjunction of all-weight Pauli beta body,
full matching-polytope mechanism, and support-sensitive weighted matrix
inequality. The closest sources each contain one neighboring ingredient but
not the conjunction.

The remaining irreducible risk is rediscovery under a matrix-analysis or
fermionic-covariance formulation not captured by searchable metadata. The
paper must therefore say “we prove” and “we found no prior statement,” not
“first” or “definitively novel.” Refereeing remains the next independent
priority check; more random experiments cannot close that risk.

## Primary/public sources checked

1. https://journals.aps.org/prxquantum/abstract/10.1103/PRXQuantum.5.020318
2. https://arxiv.org/html/2511.13531v1
3. https://quantum-journal.org/papers/q-2020-06-04-278/
4. https://arxiv.org/html/2305.15625v1
5. https://nvlpubs.nist.gov/nistpubs/jres/69B/jresv69Bn1-2p125_A1b.pdf
6. https://www.sciencedirect.com/science/article/pii/S0166218X17300252
7. https://www.sciencedirect.com/science/article/pii/S0024379513001493
8. https://www.sciencedirect.com/science/article/abs/pii/S0024379523002483
9. https://arxiv.org/html/2511.15954v1
