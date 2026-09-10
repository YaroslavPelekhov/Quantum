# C038 adversarial priority audit: exact Pauli beta bodies of line graphs

Audit date: 2026-09-10.  Scope: public sources discoverable through the web,
arXiv full text, journal pages, and the local repository.  Status: a strong
priority candidate, not a proof of first discovery and not a venue guarantee.

## 1. Candidate claim, stated narrowly

For every finite simple root graph `R` and every nonnegative edge weight
`w`, the line graph satisfies

`beta(L(R),w) = alpha(L(R),w) = nu(R,w)`.

Equivalently, the entire beta body of `L(R)` is its stable-set polytope,
which is the matching polytope of `R`.  The proof also yields the weighted
matrix inequality

`(||A||_* / 2)^2 <= nu(R,w) sum_e A_e^2/w_e`

for every real skew matrix `A` supported on `R`.  The exact quantum claim is
the all-weight beta/matching identity.  It is not a claim that line graphs,
Majorana bilinears, free-fermion diagonalization, matching polytopes, skew
energy, or blossom algorithms are new.

## 2. Why this is more than another finite experiment

The arbitrary-size statement is analytic.  It has two independent proof
routes.

1. **Polar/matching route.**  Nuclear-norm duality produces a skew
   contraction `Q`.  The vector `x_e=Q_e^2` obeys every degree constraint.
   An odd principal skew matrix has rank at most `|S|-1`, giving every odd-set
   constraint.  Edmonds' theorem therefore places `x` in the matching
   polytope, and weighted Cauchy--Schwarz closes the bound.
2. **SCF-rank/polyhedral route.**  Line graphs are simplicial claw-free.
   Applying the independently derived SCF rank inequality to root stars and
   odd root-induced edge sets gives exactly the degree and blossom
   inequalities of the matching polytope.

The finite C038 computation is a fault detector, not the proof.  It audits
all 1,245 nonempty NetworkX-atlas roots, direct dense Jordan--Wigner norms in
47 small-root cases, and exact non-h-perfect witnesses from `K5`, `K7`, and
`K9`.  Maximum observed numerical errors are recorded in the frozen JSON.

## 3. Nearest source map

### 3.1 Weighted beta bodies and hbar-perfect graphs

Xu et al. define the weighted beta number, prove representation invariance,
define hbar-perfectness as equality of the beta and stable-set bodies for all
nonnegative weights, and prove that h-perfect graphs form a sufficient
subclass [1].  Their Section III lists joins, disjoint unions, induced
subgraphs, lexicographic products, copying, and splitting as closure
operations.  The searchable v1 full text contains neither the phrase “line
graph” nor “matching”.  This is direct evidence that C038 is not a theorem
explicitly stated in that version, but it is not evidence against an
unindexed source or an unpublished observation.

**Overlap:** the invariant, its representation independence, and the
h-perfect sufficient route are prior art.

**Difference:** C038 identifies the complete infinite class of line graphs,
handles every nonnegative weight, and gives the exact matching oracle.  The
family `L(K_(2k+1))` separates it from the h-perfect sufficient route: a
uniform fractional point satisfies clique and odd-cycle inequalities but
violates a blossom inequality by exactly `1/2`.

### 3.2 Line graphs and quadratic Majorana Hamiltonians

Chapman and Flammia prove that line-graph frustration structure is exactly
the generator-to-generator free-fermion setting and give the Majorana/Jordan--
Wigner realization [2].  Their paper reduces spectral calculations to a real
skew single-particle matrix.  Chapman, Elman, and Mann later extend
free-fermion solvability to simplicial claw-free frustration graphs [3].

**Overlap:** the line-graph-to-Majorana map and free-fermion diagonalization
are known and must be cited as input.

**Difference:** solvability of each Hamiltonian does not by itself identify
the support function of the squared-expectation body for all weights.  C038
adds the convex matching-polytope step that turns the family of skew-matrix
norms into an exact weighted beta body.

**Priority risk:** once [1] and [2]/[3] are placed side by side, the second
SCF-rank proof is short.  A referee may regard the theorem as a non-obvious
but natural corollary rather than a new theory.  The paper therefore should
lead with the exact body, the blossom mechanism, and consequences, not with
free-fermion solvability itself.

### 3.3 The same complete line graphs in magic-state simulation

Zurel, Cohen, and Raussendorf use Pauli supports whose frustration graph is
`L(K_(2n+1))` to construct vertices of the Lambda/Pauli simulation polytope
[4].  Their theorem is about positive quasiprobability representations and
magic-state circuit simulation.  The proof uses the fact that the largest
stable set of `L(K_(2n+1))` has size `n`, but it does not characterize the
weighted squared-expectation beta body or prove all line graphs
hbar-perfect.

**Overlap:** the strictness family is not a new graph family in quantum
information, and the matching number of `K_(2n+1)` is already operationally
used there.

**Difference:** the polytope, objective, and theorem are different.  C038
must cite [4] near the `L(K_(2k+1))` family to prevent an inflated family-level
novelty claim.

### 3.4 Measurement incompatibility on line graphs

McNulty studies a graph invariant for the noise robustness of jointly
measuring binary observables.  For Majorana line graphs the paper derives
bounds using energy and skew energy of the root graph [5].

**Overlap:** anti-commutation graphs, quadratic Majoranas, line graphs, and
skew trace norms all appear in the neighboring problem.

**Difference:** incompatibility robustness is not the weighted beta number.
The cited result gives spectral bounds and exact expressions in selected
symmetric families, not `BETA(L(R))=MATCH(R)` for arbitrary roots and weights.
This is the closest conceptual neighbor found after the initial C038 proof,
and it belongs in the main related-work paragraph.

### 3.5 Classical skew energy and matching number

Tian and Wong explicitly study relations between skew energy (the nuclear
norm of an unweighted oriented skew-adjacency matrix) and matching number
[6].  Related graph-energy literature also contains the elementary
rank/Frobenius estimate.  In the unweighted orientation specialization,
C038 implies

`skew_energy(A) <= 2 sqrt(nu(R) |E(R)|)`,

which can also be obtained from `rank(A)<=2 nu(R)` and Schatten
Cauchy--Schwarz.  Therefore this unweighted corollary is not a safe novelty
claim.

**Difference still under audit:** C038 uses arbitrary real coefficients,
arbitrary positive comparison weights, and the maximum-*weight* matching in
a sharp inequality.  The proof identifies squared entries of every skew
contraction with a point of the full matching polytope.  The searches below
did not locate that exact weighted theorem, but matrix-analysis literature is
broad and this is the main residual priority risk.

### 3.6 Edmonds' matching polytope

Edmonds characterizes the convex hull of matchings by nonnegativity, degree,
and odd-set inequalities and supplies maximum-weight matching machinery [7].
This is a central, explicitly credited ingredient.  The new bridge, if
priority survives review, is that odd principal skew contractions generate
all blossom constraints for the Pauli beta problem.

## 4. Adversarial searches performed

The audit searched title/abstract/full-text combinations covering:

- `line graph` + `weighted beta number` / `hbar-perfect` / `Pauli uncertainty`;
- `matching polytope` + `Pauli` / `Majorana` / `squared expectation`;
- `skew symmetric` + `nuclear norm` / `trace norm` + `maximum weight matching`;
- `skew energy` + `matching number`, including exact-title searches;
- `L(K_(2n+1))` + Majorana / Pauli / matching;
- 2026 results using hbar-perfectness or citing the 2025 beta-body paper.

Negative results were checked against the full HTML of [1] and PDFs of
[2], [4], and [5], not only snippets.  Searches are query-dependent and do
not cover books, theses without indexing, non-English sources, private
communications, or papers posted after the audit date.

## 5. Falsification checklist for the theorem itself

| Failure mode | Check | Outcome |
|---|---|---|
| Wrong Majorana factor of two | Dense Jordan--Wigner operator norm versus `||A||_*/2` | 47/47 pass; max error `7.11e-15` |
| Polar witness not skew/contractive | Explicit SVD polar factor, skew projection, row and odd-set audits | 1,245/1,245 roots pass |
| Missing blossom constraints | All odd root subsets enumerated through order seven | max excess `2.22e-15` |
| Bound fails under weights | Integer weights 1--7 and signed coefficients on every atlas root | max ratio `1+2.22e-16` |
| Separation family accidentally h-perfect | Exact rational clique/odd-cycle checks and violated total matching row | `K5`, `K7`, `K9` pass; symbolic argument covers all `k>=2` |
| Result only one Pauli realization | Uses published representation invariance of beta | scope is all finite-dimensional exact realizations |
| Numerical evidence substituted for proof | Two analytic proofs kept in source and manuscript | arbitrary size does not depend on atlas enumeration |

## 6. Current novelty verdict

The previous QAOA symmetry/compression claims remain closed.  C038 is a
genuinely different quantum-theory object and is the first result in the
current repository that simultaneously has:

- an arbitrary-size theorem;
- all nonnegative weights;
- an exact polynomial-time oracle;
- a strict infinite separation from the previously cited sufficient class;
- two proof routes and corruption-controlled computational checks.

The defensible internal label is **strong A/A* candidate, priority not yet
externally confirmed**.  It is stronger than a benchmark observation and
stronger than the fixed C031 certificate.  It is not defensible to write
“definitely A*”, “first ever”, or “new free-fermion solution”.

The largest remaining threat is rediscovery as a short consequence of known
SCF spectral identities plus Edmonds, or the existence of the weighted skew-
matrix inequality in matrix-analysis literature under different notation.
The correct next step is expert proof/priority review, ideally by authors
working on beta bodies, free-fermion frustration graphs, and matching
polytopes, followed by a timestamped preprint only after authorship and
disclosure decisions.

## 7. Submission-strengthening actions

1. Keep the theorem and matrix inequality as the headline; demote C031 and
   the SCF construction to a separate section or companion manuscript if
   editorial focus requires it.
2. Add a concise consequences section: exact uncertainty region, exact
   ground-energy bound through the beta variational identity, and a
   polynomial-time separation oracle via weighted matching.
3. Obtain at least two independent mathematical readings: one quantum/
   Majorana expert and one combinatorial-optimization or matrix-analysis
   expert.
4. Ask the nearest authors a precise priority question, including the theorem
   statement and proof, rather than asking whether the topic “looks novel”.
5. Do not spend QPU budget to validate an analytic identity.  Hardware can
   illustrate uncertainty saturation but cannot establish the theorem or its
   priority.

## Sources

1. Z.-P. Xu et al., *Simultaneous variances of Pauli strings, weighted
   independence numbers, and a new kind of perfection of graphs*,
   arXiv:2511.13531v1 (2025), https://arxiv.org/abs/2511.13531v1
2. A. Chapman and S. T. Flammia, *Characterization of solvable spin models
   via graph invariants*, Quantum 4, 278 (2020),
   https://doi.org/10.22331/q-2020-06-04-278
3. A. Chapman, S. J. Elman, and R. L. Mann, *A Unified Graph-Theoretic
   Framework for Free-Fermion Solvability*, arXiv:2305.15625v1 (2023),
   https://arxiv.org/abs/2305.15625v1
4. M. Zurel, L. Z. Cohen, and R. Raussendorf, *Simulation of quantum
   computation with magic states via Jordan--Wigner transformations*,
   Physical Review A 112, 042602 (2025),
   https://doi.org/10.1103/ng4l-96kd
5. D. McNulty, *A Graph-Theoretic Approach to Quantum Measurement
   Incompatibility*, arXiv:2511.15954v1 (2025),
   https://arxiv.org/abs/2511.15954v1
6. F. Tian and D. Wong, *Relation between the skew energy of an oriented
   graph and its matching number*, Discrete Applied Mathematics 222,
   179--184 (2017), https://doi.org/10.1016/j.dam.2017.01.004
7. J. Edmonds, *Maximum matching and a polyhedron with 0,1-vertices*,
   Journal of Research of the National Bureau of Standards B 69B, 125--130
   (1965), https://doi.org/10.6028/jres.069B.013
