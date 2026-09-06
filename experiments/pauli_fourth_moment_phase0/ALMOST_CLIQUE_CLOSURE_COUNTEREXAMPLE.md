# Generic almost-clique quantum closure is false

Date: 2026-09-06. Research cycle C003.
Status: exact physical counterexample with exact local all-weight proofs.
The graph is the previously published G8; this is not a new imperfect-graph
claim and is not an A-star novelty claim. The unrestricted SCF conjecture
is NOT falsified: the combined graph contains a claw.

## Refuted statement

The following proposed rule is false:

> If G[A] and G[B] are hbar-perfect, A and B cover G, there are no edges
> between A\B and B\A, and A intersection B is a clique minus one edge,
> then G is hbar-perfect.

This is stronger evidence than an abstract local-marginal obstruction:
the global profile below comes from an explicit pure state, and BOTH
local graphs obey all weighted quantum uncertainty inequalities for all
states, not just for the displayed state.

## Exact three-qubit witness

Let G be graph6 `GCrdrk`, the first entry of the pinned `test8.txt`
benchmark of [Xu et al.](https://arxiv.org/html/2511.13531v1), upstream commit
`467eb611c09631fcf310da8dc73c35cb3b8fe098`. Its Pauli realization is, in order,

`XII, IXI, IIX, ZII, ZZI, ZZZ, YIY, XYY`.

Take the computational-basis state

`|psi>=(3,2,3,8,-5,2,-3,-1)/sqrt(125)`

and strictly positive weights

`w=(1,1,1,1,1,1,2,2)`.

The exact expectation numerators, with common denominator 125, are

`(-56,76,46,47,-79,47,-74,86)`.

Consequently,

`sum_i w_i <P_i>^2 = 47431/15625 = 3.035584`,

whereas exhaustive independent-set enumeration gives `alpha(G,w)=3`.
The gap is exactly **`556/15625`**, not a numerical tolerance effect.
All 255 global induced-subgraph rank inequalities nevertheless hold at
this physical squared profile. The violated inequality is weighted.

The numerical search found a lower bound about 3.044815499855; that value
is not used as an exact optimum claim. Deterministic rationalization gave
the much smaller state above, whose violation is verified using integers
and fractions only. No quantum processor was used.

## The separator and local all-weight proofs

Set

`S={0,6,7}`, `A={0,1,2,4,5,6,7}`, `B={0,3,6,7}`.

The only nonedge in S is `{0,7}`; vertex 6 is adjacent to both. There are
no edges between A\S and B\S. G[B] is `K4` with edge `{0,7}` removed.

The left graph G[A] is **not SCF**. Its proof must not be replaced by an
incorrect invocation of the SCF theorem on that entire side. Instead, its
stable-set polytope is exactly described by:

- seven nonnegativity constraints;
- six clique inequalities on `{0,4,6}`, `{0,5}`, `{1,4}`, `{1,5,7}`,
  `{2,5,7}`, and `{2,6,7}`;
- the rank inequality `x1+x2+x4+x5+x6+x7<=2`.

The six-vertex support of the last rank inequality IS SCF and has
independence number two. Thus the previously established SCF rank theorem
proves it for every physical state. Each other inequality follows from
clique uncertainty. The exact H-polytope has precisely the 18 stable-set
incidence vertices of G[A], so these inequalities prove hbar-perfectness
on the left for every nonnegative weight.

On the right, the two clique inequalities are

`x0+x3+x6<=1`, `x3+x6+x7<=1`,

together with four nonnegativity constraints. Their polytope has exactly
the six stable-set vertices of G[B], proving the right-side claim.

Completeness is independently verified: discovery uses exact GMP
double-description; acceptance enumerates all 3,432 seven-constraint
systems on the left and all 15 four-constraint systems on the right with
rational Gaussian elimination. The H-polytopes are bounded because every
coordinate has a nonnegativity constraint and occurs in a clique bound.
Every feasible full-rank intersection is a stable-set incidence vector,
and every stable-set vector is recovered. No numerical hull tolerance is
used in this proof of local all-weight perfection.

## A physical incompatibility of one boundary event

Let y be the probability of including both 0 and 7 in a classical stable-set
decomposition with the physical vertex marginals x. Exact local dual
certificates force

`383/15625 <= y_A <= 2036/15625`,

`2592/15625 <= y_B <= 3136/15625`.

Thus the two sides cannot share y, even though both local decomposition
problems are feasible. For the decisive bounds, every local stable set obeys

`y_A <= 2-x1-x2-x4-x5-x6-x7`,

`y_B >= -1+x0+x3+x6+x7`.

At the specified quantum profile the upper bound on the left is smaller
than the lower bound on the right by exactly `556/15625`. The acceptance
checker verifies the dual inequalities on every local stable set, not just
on a numerically selected decomposition.

## Why this does not refute SCF perfection

Vertex 0 together with leaves `{3,4,5}` induces a claw. In particular,
neither the general SCF theorem nor its order-nine version applies to the
whole graph. The local quantum statements and all global rank constraints
therefore cannot substitute for the missing GLOBAL SCF structure.

The result rules out an unconditional one-pair composition rule. A modified
rule with global claw-free/SCF hypotheses remains a different, unproved
statement and must exploit those hypotheses in the actual operator argument.

The boundary product is `P0 P7=IYY`. It commutes with every right-side
observable (including P3) but not with every left-side observable. Thus
centrality of this product on JUST ONE side does not repair the generic
rule either; this counterexample already has that property.

## Elementary positive-weight extension to all larger orders

The obstruction is not confined to order eight. Replace vertex 3 (which is
outside S) by a clique of m true twins, each of weight one. All other
weights stay unchanged. Every independent set can use at most one twin,
so the weighted independence number stays three. The left side is unchanged;
the right side remains a complete graph minus edge `{0,7}`, hence perfect.

For an explicit realization, use k=ceil((m-1)/2) ancillas and take m
mutually anticommuting Pauli operators Q_j from

`Z^k`, and `Z^(r-1) X_r I^(k-r), Z^(r-1) Y_r I^(k-r)` for r=1,...,k.

Replace P3 by `P3 tensor Q_j` and extend other observables by the identity.
On `|psi> tensor |0>^k`, only the first twin has nonzero expectation and it
has exactly the old expectation. The weighted quantum value and strict gap
therefore stay unchanged. All weights are positive; no zero-weight padding
is used. This proves failure for every graph order at least eight.

This extension is an elementary true-twin construction using familiar
Clifford operators, not an independent novelty claim. The code exactly
checks its first four nontrivial sizes (9 through 12 vertices).

## Preregistered benchmark audit and reproduction

The full screen covers 18 order-eight and 1,419 order-nine pinned benchmark
entries. Nine and 851 entries respectively have at least one almost-clique
separator, giving 39+5,314 decompositions. These 860 graph entries are NOT
all asserted to be counterexamples to closure: local perfection and a
physical violation are separately certified only for the selected witness.

The independent structural checker builds every separator from its unique
nonedge and a clique in the common neighborhood, whereas discovery checks
all vertex subsets using integer bitsets. Both methods agree on every
decomposition. A source-verifying run also checks the upstream hashes and
every graph6 row against the immutable published inputs.

From the repository root:

```text
python experiments/pauli_fourth_moment_phase0/run_almost_clique_closure_audit.py
python experiments/pauli_fourth_moment_phase0/verify_almost_clique_closure_audit.py --verify-upstream
python experiments/pauli_fourth_moment_phase0/extract_almost_clique_counterexample.py
python experiments/pauli_fourth_moment_phase0/verify_almost_clique_counterexample.py
```

Run discovery in a clean archive: the discovery commands regenerate their
two named result files. Witness extraction uses the recorded NumPy/SciPy/
NetworkX environment and `cdd.gmp` (pycddlib 3.0.2). Exact physical/local
acceptance needs only the Python standard library. Structural acceptance
also uses NetworkX; `--verify-upstream` may fetch the two public pinned files.

The current combined suite has 30 passing tests, including corrupted states,
wrong separator labels and deletion of the essential local rank inequality.

## Prior-art boundary

The published G8 and the hbar-perfection framework are due to
[Xu et al.](https://arxiv.org/abs/2511.13531). Their Section III lists join,
disjoint union, induced subgraphs, lexicographic product, copying and
splitting; it does not state the proposed almost-clique closure rule.
The main text and Appendix A.1 swap the numbering of copying and splitting,
so the operation definitions are used here rather than the property number.

This cycle adds an exact state, explicit local polyhedral proof and boundary
incompatibility certificate to our falsification suite. It is not evidence
that a new A-star theorem has been found. The next proof obligation is
SCF-specific, not a relabeling of generic marginal gluing.
