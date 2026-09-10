# C038: every line graph is hbar-perfect

Date: 2026-09-10.
Status: analytic theorem with independent finite audits; external proof review
and a complete publication-priority search remain required.

## Theorem

Let `R=(V,E)` be any finite simple graph, let `G=L(R)` be its line graph,
and let `w` be any nonnegative weight vector on `E`. Then

`beta(G,w) = alpha(G,w) = nu(R,w)`,

where `nu(R,w)` is the maximum weight of a matching of `R`. Equivalently,
every finite line graph is hbar-perfect.

The result follows from the following sharp matrix inequality.  If `A` is
a real skew-symmetric matrix supported on the edges of `R`, then

`(||A||_* / 2)^2 <= nu(R,w) sum_{e in E} A_e^2 / w_e`,

with zero-weight coordinates omitted.  Here `A_e` is the upper-triangular
entry on edge `e` and `||.||_*` is the nuclear norm.

## Proof

It is enough to retain the positive-weight edges.  Assign a Majorana
operator `gamma_v` to every vertex of `R` and represent edge `e={u,v}` by
the Hermitian involution `P_e=i gamma_u gamma_v`.  Two such operators
anticommute exactly when their edges share one endpoint, so their
frustration graph is `L(R)`.  The weighted beta number is independent of
the Pauli realization, and its Euclidean variational identity gives

`beta(L(R),w) = max_{sum_e c_e^2/w_e=1} ||sum_e c_e P_e||^2`.

Let `A` be the real skew matrix with upper-triangular entries `c_e`.
Orthogonal skew normal form has two-by-two blocks with singular values
`s_1,...,s_r`.  The Majorana bilinear has operator norm
`sum_j s_j = ||A||_*/2`.

Choose a real matrix `Q` with operator norm at most one attaining nuclear
norm duality, `<A,Q>_F=||A||_*`.  Replacing `Q` by `(Q-Q^T)/2` preserves
the pairing with skew `A` and does not increase its operator norm.  Thus
we may take `Q` skew-symmetric.  Put `x_e=Q_e^2` on every edge of `R`.

For every vertex `v`,

`sum_{e incident to v} x_e <= ||row_v(Q)||_2^2 <= 1`.

For every odd vertex set `S`, the principal matrix `Q[S]` is odd-order
skew-symmetric, hence has rank at most `|S|-1`.  Its singular values are
at most one, and therefore

`2 sum_{e in E(S)} x_e <= ||Q[S]||_F^2 <= |S|-1`.

These are precisely the degree and odd-set inequalities in Edmonds'
description of the matching polytope.  Consequently `x` is a convex
combination of matching incidence vectors and

`sum_e w_e Q_e^2 <= nu(R,w)`.

Since both `A` and `Q` are skew,

`||A||_*/2 = sum_e c_e Q_e`.

Weighted Cauchy--Schwarz now gives

`(||A||_*/2)^2`
` <= (sum_e c_e^2/w_e)(sum_e w_e Q_e^2)`
` <= nu(R,w)`.

This proves the beta upper bound.  A maximum-weight matching is a stable
set of `L(R)`; its Majorana bilinears commute, and a common eigenstate
attains the matching weight.  Hence equality holds.  Disconnected roots,
isolated root vertices, zero weights and singular `A` need no separate
argument: they are covered by restriction and continuity.

### Independent graph-polyhedral proof route

There is a useful second derivation which does not use the polar factor.
Every line graph is claw-free and has a simplicial star clique, and every
induced subgraph of a line graph is again a line graph.  The SCF rank lemma
therefore gives `sum_(e in U) <P_e>^2 <= alpha(L(R)[U])` for every edge
support `U`.  For a root vertex `v`, choose `U=delta(v)` and obtain the
degree inequality.  For every odd root-vertex set `S`, choose `U=E(S)` and
obtain

`sum_(e in E(S)) <P_e>^2 <= nu(R[S]) <= (|S|-1)/2`.

Together with nonnegativity these are Edmonds' complete matching-polytope
inequalities.  Hence the squared profile belongs to `MATCH(R)=STAB(L(R))`.
This route independently confirms the all-weight theorem.  The polar proof
is retained because it yields the sharper coefficient-dependent matrix
inequality directly and exposes why every blossom constraint appears.

## Strict extension beyond the published h-perfect route

The theorem is not just a reformulation of the known implication
`h-perfect => hbar-perfect`.  For every `k>=2`, `L(K_(2k+1))` is not
h-perfect.  Put `x_e=1/(2k)` on every edge of `K_(2k+1)`.  In the line
graph this vector satisfies nonnegativity, every clique inequality and
every induced odd-hole inequality:

- a star has value one;
- a triangle has value `3/(2k)<=1`;
- any odd cycle of length `l>=5` has value
  `l/(2k) <= (l-1)/2`.

But its total value is `(2k+1)/2`, whereas a matching has at most `k`
edges.  Thus the full odd-set matching inequality is violated by `1/2`.
The C038 theorem nevertheless proves that all these line graphs are
hbar-perfect.  This supplies an explicit infinite separation between the
new class and the previously sufficient h-perfect class.

## Consequences and scope

1. Every weighted quadratic Pauli uncertainty relation whose frustration
   graph is a line graph is exactly a maximum-weight matching problem.
2. The sharp Hamiltonian norm bound is computable in polynomial time by a
   weighted matching algorithm, without state simulation or an SDP
   hierarchy.
3. The proof exposes a direct convex-geometric bridge: the squared entries
   of a skew contraction lie in a matching polytope because odd principal
   skew matrices lose at least one rank.

This does not prove that every simplicial claw-free graph is hbar-perfect,
nor does it establish quantum validity of gear composition.  SCF systems
that are not line graphs still require the earlier Gram, exact-SOS or
composition arguments.  Searches of the closest beta-number, Pauli
joint-range, free-fermion, measurement-incompatibility, skew-energy and
line-graph literature found no statement of the theorem above.  However,
the uniform-coefficient shadow of the matrix inequality is close to
classical skew-energy/rank bounds, and the theorem combines several known
ingredients.  A negative keyword search is not a priority proof; see
`LINE_GRAPH_PRIORITY_AUDIT_C038.md` for the explicit overlap analysis.

## Reproduction

Run `run_c038_line_graph_hbar.py` to stress the matrix inequality on every
nonempty graph in the NetworkX atlas and to generate the exact strictness
witnesses `L(K5), L(K7), L(K9)`.  Run
`verify_c038_line_graph_hbar.py` with `python -S` for the standard-library
audit of the frozen witness records.  The campaign also compares the
trace-norm formula against dense Jordan--Wigner matrices in 47 small-root
cases; the maximum discrepancy is `7.11e-15`.  The proof above, not the
numerical stress campaign, establishes the arbitrary-size theorem.
