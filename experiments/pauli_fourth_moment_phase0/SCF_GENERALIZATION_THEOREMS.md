# Size-independent rank-to-weight lifting and the separator obstruction

Date: 2026-09-05. This continuation proves a general subclass theorem and
identifies an exact obstruction to two proposed general-proof shortcuts.
It does **not** prove weighted SCF perfection when `alpha(G)>=3` in general.
No A-star or publication-priority claim is made.

## 1. Theorem: uniform weights maximize the relative violation when alpha is two

For **any** finite graph with `alpha(G)=2`, not necessarily SCF,

`sup_(w>=0,w!=0) beta(G,w)/alpha(G,w) = beta(G,1)/2`.

Thus the largest relative quantum/classical separation is attained by
uniform weights. This is stronger than a zero-gap statement.

Let `G` be any nonempty finite graph with `alpha(G)<=2`. The following are equivalent:

1. `beta(G,w)=alpha(G,w)` for every nonnegative real weight vector `w`;
2. `beta(G,1)=alpha(G)`;
3. `beta(G[U],1)=alpha(G[U])` for every induced subgraph `G[U]`.

In particular, **every SCF graph with `alpha(G)<=2` is hbar-perfect,
without any bound on its number of vertices**. This corollary uses the
previously proved SCF rank theorem, not the order-nine enumeration.

### Proof

The first condition implies the others by specialization. The second implies
the third: a nonclique induced subgraph has independence number two and
beta at most `beta(G,1)=2` by monotonicity, while a clique has beta one.
For the converse, and the stronger ratio formula, consider the normalized weight polytope

`C={w>=0 : alpha(G,w)<=1}`.

Since every stable set has size at most two, its complete description is

`0<=w_i<=1`, and `w_i+w_j<=1` for every nonedge `{i,j}` of `G`.

Every vertex of `C` is half-integral. Here is the standard elementary proof,
included to avoid invoking an unverified polyhedral assumption. At an
extreme point form the graph of tight pair constraints among coordinates
strictly between zero and one. Such a component cannot touch an integral
coordinate by a tight pair equality. If a component is bipartite, perturb
the two parts by opposite sufficiently small amounts. This preserves all
tight equalities and preserves the slack inequalities in both directions,
contradicting extremality. Every fractional component therefore contains an
odd cycle. Its equations `w_i+w_j=1` force every value in that component
to be `1/2`. Thus every coordinate lies in `{0,1/2,1}`.

For an extreme weight, let `H` be its coefficient-one vertices and `L` its
coefficient-half vertices. The constraints imply that `H` is a clique and
is completely joined to `L`. Put `b=beta(G,1)`. If `alpha(G)=2`, then `b>=2`
and monotonicity gives

`beta(G[L],(1/2)1)<=b/2`,

while `beta(G[H],1)<=1`. The beta number of a complete join is the maximum
of the beta numbers of its parts, so `beta(G,w)<=max(1,b/2)=b/2` at every
extreme weight. Empty parts and the zero weight cause no exception. Convexity
of beta in `w` gives the same bound throughout `C`. Normalize an arbitrary
nonzero weight by `alpha(G,w)` to obtain the ratio upper bound. Uniform
weights attain `b/2`, proving the ratio identity. In particular, `b=2`
implies weighted perfection. The `alpha(G)=1` case is a clique and is
immediate. A common eigenstate of a maximum-weight independent set gives
the usual beta lower bound. QED.

For completeness, the join fact is an operator statement, not a classical
rank-polytope identity. The variational identity is

`beta(G,w)=max_(||a||=1) ||sum_i a_i sqrt(w_i) P_i||^2`.

Split this sum as `A+B` across a complete join. Every cross pair of
generators anticommutes, so `(A+B)^2=A^2+B^2`. If the local beta bounds
are `b_A,b_B`, then

`||(A+B)^2|| <= b_A||a_A||^2+b_B||a_B||^2 <= max(b_A,b_B)`.

The reverse inequality selects just one part. This is the established
quantum join property, also recorded in
[Xu et al., Section III](https://arxiv.org/html/2511.13531v1).

### What the theorem does not say

It does not identify the classical rank relaxation with STAB. For the
five-wheel (`C5` plus a universal hub), the vector with every coordinate
`1/3` satisfies every rank inequality. Nevertheless it violates

`sum_cycle x_i+2x_hub<=2`

by `1/3`. The theorem excludes this vector from the *quantum* squared-profile
body using the join operator inequality. Omitting that step would be wrong.

The ratio result genuinely uses `alpha=2`. For a generic boundary example,
take the join of a universal vertex with the disjoint union of `anti-C7`
and an isolated vertex. This connected nine-vertex graph has `alpha=3`.
Writing `b=beta(anti-C7,1)>2`, the known disjoint-union and join rules give
uniform ratio `(b+1)/3`; weights supported just on `anti-C7` give the larger
ratio `b/2`. This graph is not claw-free, so it is not a counterexample to
the SCF conjecture. It only excludes an unrestricted extension of the ratio
theorem to independence number three.

The unrestricted-size conclusion has an exact finite implementation audit:
172 atlas graphs with `alpha<=2` and 1,725 connected order-nine SCF graphs
produce 177,287 extreme weights. Every weight is half-integral, and all
2,945 mixed light/heavy cases have the required complete-join structure.
The numerical counts audit the implementation; the proof above, not those
counts, establishes the arbitrary-size theorem.

## 2. Proposition: hbar-perfectness is preserved by clique separators

Suppose `V(G)=A union B`, there are no edges between `A\B` and `B\A`,
and `S=A intersection B` is a clique. If `G[A]` and `G[B]` are hbar-perfect,
then so is `G`.

Indeed, a quantum squared profile restricts to STAB on each side. Let
`mu_A,mu_B` be its two stable-set distributions. A stable set meets the
clique `S` either in the empty set or in exactly one vertex. The marginal
distribution on `S` is therefore determined by the shared profile:

`pi({s})=x_s`, `pi(empty)=1-sum_(s in S)x_s`.

For each boundary event `J` of positive probability, couple the two sides
conditionally independently. The probability of a compatible pair
`(I_A,I_B)` is `mu_A(I_A) mu_B(I_B)/pi(J)`, where
`I_A intersection S=I_B intersection S=J`. Zero-probability events carry no
mass and are omitted. The union is stable, its weights sum to one, and all
vertex marginals equal the original profile. Thus the profile lies in STAB.
This argument can be iterated along a clique-separator tree.

This is a direct application of standard classical marginal gluing, not a
claimed new quantum-simulation primitive. It gives an unbounded closure of
the proved classes but does not cover all SCF graphs.

## 3. Exact failure of profile-only two-clique-separator gluing

Replacing a clique separator by a separator covered by two cliques is not
justified by the preceding proof. The computational attack produces exact
obstructions on **all 13** hard order-nine-or-smaller residual types, even
after imposing **every global rank inequality**. All local stable-set
decompositions and every rank check are independently verified rationally.

A compact eight-vertex example is type 7, graph6 `GQuvSw`. Let

`S={0,5,6}`, `A={0,1,3,4,5,6,7}`, `B={0,2,5,6}`.

The separator is covered by cliques `{0,6}` and `{5}`. The profile is

`x=(1,1,1,0,1,1,1,1)/3`.

On `A`, it is the equal mixture of stable sets `{0,1}`, `{4,5}`, `{6,7}`.
On `B`, it is the equal mixture of `{0}`, `{2}`, `{5,6}`. It also satisfies
all 255 nonempty induced-subgraph rank inequalities. But for

`w=(1,1/2,1/2,1/2,1,1/2,1,1/2)`

the value is `5/3`, whereas `alpha(G,w)=3/2`.

The inconsistency can be localized exactly to **one missing joint event**.
In every left decomposition of this profile, the pair event `{5,6}` has
probability zero; in every right decomposition it has probability `1/3`.
These statements are certified by exact LP-dual inequalities over every
local stable set, not just by the displayed example distributions.

Consequently this is not merely an unfortunate choice of local decompositions:
their boundary distributions cannot be made compatible. It is also **not a
quantum counterexample**. The already proved eight-vertex theorem tells us
that this abstract vector cannot be the squared profile of a physical state.

## 4. Exact formulation of the missing boundary lemma

For an arbitrary separator `S`, local distributions glue if they have the
same full stable-set distribution on `S`. When `S` is covered by two cliques,
every stable subset of `S` has size at most two. Its full distribution is
therefore determined by single-vertex and nonedge-pair probabilities:

`pi({i,j})=y_ij`,

`pi({i})=x_i-sum_j y_ij`,

`pi(empty)=1-sum_i x_i+sum_{i<j} y_ij`.

For each side define `Y_A(x_A)` as the set of separator pair probabilities
obtainable from stable-set distributions on `A` with marginals `x_A`, and
similarly for `B`. A global stable-set decomposition exists **if and only if**

`Y_A(x_A) intersection Y_B(x_B)` is nonempty.

Necessity is restriction of a global distribution; sufficiency follows from
the explicit conditional coupling above using the common boundary law.
This is a classical exact equivalence, not an assumption that its right
side holds for quantum states. Local hbar-perfectness establishes only that
the two sets are separately nonempty. A genuinely new quantum argument must
establish a common point, in an applicable decomposition of SCF graphs.

## 5. A natural quantum pair formula also fails

We tested the exploratory completion

`y_ij=max(0,(r_i^2+r_j^2+r_ij^2-1)/2)`,

where `r_i=<P_i>` and `r_ij=<P_i P_j>` for commuting pairs on `S`.
It is motivated by the commuting two-observable constraints, but pairwise
plausibility is not a global compatibility theorem.

For each of the 13 separator cases we tested up to 128 seeded
Gaussian-integer pure-state vectors. The formula fails on five types:
15, 23, 26, 33, 44. Each stored failure contains an explicit integer complex
state, binary Pauli labels, rational expectations, and a separating linear
inequality checked against every lifted stable-set vertex. The eight cases
without a discovered failure are not promoted to a theorem.

The all-pairs variant already has a simple exact two-qubit counterexample.
Take all 15 nonidentity two-qubit Pauli strings and

`|psi>=(1,2,3,4)/sqrt(30)`.

For this SCF graph, `alpha=3`; its hbar-perfectness is already known from
[Xu et al., Appendix A.2](https://arxiv.org/html/2511.13531v1).
Every genuine lifted stable-set distribution obeys

`2 sum_i x_i - sum_nonedge_ij y_ij <= 3`,

because a stable set of size `k<=3` contributes `2k-k(k-1)/2<=3`.
Here `sum_i x_i=3`, but the proposed formula gives `sum_ij y_ij=121/50`.
The inequality evaluates to `179/50`, violating its bound by **`29/50`**.
This all-pairs control is separate from the five actual separator failures.
Neither falsifies hbar-perfectness; both falsify the proposed completion.

## 6. Reproduction and next proof obligation

Exact independent verification needs only the Python standard library:

```text
python experiments/pauli_fourth_moment_phase0/verify_scf_generalization.py
```

It implements the Pauli action on Gaussian-integer state vectors using
binary labels and integer phases. No numerical matrix multiplication,
rounding tolerance, graph library, or solver is used in certificate acceptance.
The discovery scripts use the already recorded NumPy/SciPy/NetworkX versions
and exact `cdd.gmp` (pycddlib 3.0.2).

To rediscover the three artifacts from the repository root, choose a new
output directory and run the following commands. The tracked reference
artifacts are not overwritten. The recorded discovery environment used
NumPy 2.2.6, SciPy 1.16.3, NetworkX 3.5, and pycddlib 3.0.2; the latter
provides `cdd.gmp`. Discovery counts can depend on solver tie-breaking, but
acceptance of the stored rational witnesses does not.

```powershell
New-Item -ItemType Directory .cache/scf-generalization-reproduction
python experiments/pauli_fourth_moment_phase0/run_scf_rank_two_lift.py --input results/pauli_fourth_moment_phase0/scf_order9_census.json --output .cache/scf-generalization-reproduction/rank_two.json
python experiments/pauli_fourth_moment_phase0/run_scf_gluing_obstruction.py --input results/pauli_fourth_moment_phase0/scf_order9_facet_reduction.json --output .cache/scf-generalization-reproduction/gluing.json
python experiments/pauli_fourth_moment_phase0/run_scf_pair_completion_audit.py --input .cache/scf-generalization-reproduction/gluing.json --output .cache/scf-generalization-reproduction/pairs.json --samples 128
python -m unittest discover -s experiments/pauli_fourth_moment_phase0 -p 'test_scf*.py' -v
python experiments/pauli_fourth_moment_phase0/verify_scf_research_bundle.py
```

The next valid proof obligation is no longer “local profiles ought to glue”.
It is to establish a quantum boundary-compatibility principle giving common
pair-event probabilities, or find a different operator argument that bypasses
such a decomposition. It also remains necessary to prove that the chosen
decomposition covers the desired unrestricted SCF class. The arbitrary-size
`alpha<=2` theorem and clique-separator closure are proved; the unrestricted
weighted SCF conjecture and A-star significance remain open.

The half-integral polytope and classical gluing arguments are standard tools.
The prior-art starting points remain the
[SCF free-fermion theorem](https://arxiv.org/abs/2305.15625) and the
[hbar-perfection framework](https://arxiv.org/html/2511.13531v1).
This continuation does not claim priority for those ingredients or infer
publication novelty from unsuccessful exact-phrase searches.

In particular, the uniform-weight ratio statement has a close classical
analogue in imperfection-ratio results for triangle-free graphs and their
complements; see [Koster--Wagler](https://optimization-online.org/wp-content/uploads/2005/12/1256.pdf).
This is a material prior-art constraint on how to position the beta
specialization, not a reason to omit its proof or its SCF corollary.
