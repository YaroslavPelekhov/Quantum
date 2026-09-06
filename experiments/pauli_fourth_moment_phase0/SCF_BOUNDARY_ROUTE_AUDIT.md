# Boundary-route audit: scalar coverage and coordinatewise failure

Date: 2026-09-06. Preregistered research cycles C001 and C002.
These are exact diagnostic results about a proposed proof route, not a
proof or a physical counterexample to unrestricted weighted SCF perfection.

## C001: what the separator route actually covers

For the frozen 13 residual plus 34 targeted order-ten weighted types, an
exhaustive separator search finds a two-clique separator for every type.
There are 46 distinct graph6 inputs. The minimum number of nonedge pairs
on a two-clique separator is:

| Pair coordinates | Weighted types | Distinct graph6 inputs |
|---|---:|---:|
| 1 | 36 | 35 |
| 2 | 8 | 8 |
| 3 | 3 | 3 |

The search uses connected components and bipartite complements. Independent
verification enumerates unions of cliques and components with integer
bitsets, checks every possible separator and side partition, and verifies
the minimum and the canonical witness. P4, C4, K4 give 0, 1, and no proper
separator, respectively. Graph orders and input hashes are bound to the
previous artifacts.

This falsifies coverage by separators containing at most one nonedge pair.
It does NOT prove a minimum affine dimension of the feasible boundary law,
nor exclude an algebraic compression using identities specific to a state.
It also does not classify unrestricted SCF graphs. The saved side sizes
are at most nine, so the previously proved finite theorem covers each
side in this diagnostic corpus; the missing issue is their compatibility.

## C002: individual pair agreement does not give joint agreement

For each of the 11 multi-pair cases, introduce a common profile x and,
separately for each boundary pair k, local distributions on both sides.
Those distributions share the vertex marginals x and the kth pair
probability, but may differ for different k. Impose every global rank
inequality as well. Maximizing the existing facet detects eight strict
violations. All eight have exact rational witnesses and independently
verified stable-set distributions. Three single-pair controls give no
numerical violation. The other three attacks also give no violation for
their tested objective; no exact upper-bound claim is attached to them.

Geometrically, every coordinate projection of the two feasible fibers
intersects, but the fibers themselves are disjoint. This general possibility
is elementary convex geometry; the contribution of this audit is the
explicit, rank-augmented witnesses inside the actual SCF test corpus.
It is not a claimed new principle of quantum nonlocality.

### A nine-vertex exact example

Type 33, graph6 `HQjRexz`, has the canonical separator

`S={0,1,3,7}`, with cover `{0}` and `{1,3,7}`,

`A={0,1,2,3,4,6,7,8}`, `B={0,1,3,5,7}`.

The only pair coordinates are `y01` and `y03`. Take

`x=(1/2,1/4,0,1/4,1/4,1/4,1/4,1/4,1/4)`.

Every global rank inequality holds. A right-side distribution is the
equal mixture of `{0,1}`, `{0,3}`, `{5}`, `{7}`, giving
`(y01,y03)=(1/4,1/4)`.

On the left, the equal mixture of `{0,1}`, `{3,4}`, `{6,7}`, `{0,8}` gives
`(1/4,0)`. The equal mixture of `{0,3}`, `{1,4}`, `{6,7}`, `{0,8}` gives
`(0,1/4)`. Both have exactly the same x on A. Therefore either coordinate
can separately agree with the right side.

Nevertheless EVERY left decomposition must have `y01+y03=1/4`,
whereas EVERY right decomposition must have `y01+y03=1/2`.

Explicit certificates, valid on every local stable-set incidence vector,
prove this without assuming that the displayed mixtures are unique. For A:

`-1+x0+x1+x3+x7 <= y01+y03 <= 1-x4-x7-x8`.

At the specified profile both bounds equal 1/4. For B:

`-1+x0+x1+x3+x5+x7 <= y01+y03 <= x1+x3`,

and both equal 1/2. The independent verifier checks these rational dual
inequalities against all local stable sets, including the empty set.

Equivalently, the original facet weights

`w=(1/2,1,1/2,1,1/2,1/2,1/2,1,1)`

give `w.x=13/8` while `alpha(G,w)=3/2`, an exact gap of `1/8`.
This vector is NOT the squared profile of a physical state: the previously
proved order-nine theorem rules that out. The example locates a missing
quantum constraint; it does not violate that theorem.

## Reproduction

From the repository root, with the previously recorded NumPy, SciPy and
NetworkX discovery environment:

```text
python experiments/pauli_fourth_moment_phase0/run_scf_separator_coverage.py --output results/pauli_fourth_moment_phase0/scf_separator_coverage.json
python experiments/pauli_fourth_moment_phase0/run_scf_coordinate_compatibility.py
```

Those commands regenerate the two named reference artifacts. Use a clean
archive for rediscovery to leave the working reference copies untouched.
Acceptance checks require only the standard library:

```text
python experiments/pauli_fourth_moment_phase0/verify_scf_separator_coverage.py
python experiments/pauli_fourth_moment_phase0/verify_scf_coordinate_compatibility.py
```

The combined exact/regression suite has 23 passing tests, including
deliberately corrupted minima, boundaries, distributions and dual bounds.

## Next proof gate

Do not assume that pairwise interval overlap proves simultaneous quantum
compatibility. A valid general route must establish full fiber intersection
or eliminate the boundary variables through a genuine operator theorem.
Before claiming even a one-pair closure rule, test it against known
hbar-imperfect graphs and inspect the exact graph-operation hypotheses in
the primary literature. Failure outside SCF would restrict such a rule;
it would not falsify H-SCF.
