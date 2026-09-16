# C043: SCF quasi-line rank-perfect theorem

Date: 2026-09-16

## Result

> **Theorem. Every simplicial claw-free quasi-line graph is rank-perfect.**

Together with the previously proved rank-perfect SCF bridge, this gives:

> **Corollary. Every simplicial claw-free quasi-line frustration graph is
> hbar-perfect for all nonnegative weights.**

This closes the conjecture left open in C042. It is an analytic theorem, not
an extrapolation from the finite census.

## Proof architecture

1. **SCF heredity.** If a simplicial clique survives a vertex deletion, it
   remains simplicial. If the deleted vertex was the whole simplicial clique,
   its neighborhood is a simplicial clique in every remaining component. For
   any additional component, claw-freeness makes the deleted vertex's
   neighborhood inside that component a simplicial clique. Repeated deletion
   proves that every induced subgraph is componentwise SCF.
2. **Known quasi-line facet structure.** Eisenbrand--Oriolo--Stauffer--Ventura
   prove that quasi-line stable-set polytopes have only nonnegativity, clique,
   and clique-family facets. Quasi-line graphs outside the fuzzy circular
   interval class have only rank facets.
3. **Clique-circulant core.** Oriolo--Stauffer (2022, Theorem 26) prove that a
   remaining FCIG facet is associated with a maximal `(n,p)`
   clique-circulant, with `gcd(n,p)=1` and `n>2p>=4`. This structure contains
   an induced circulant `C(n,p)` whose vertices at circular distance at most
   `p-1` are adjacent.
4. **New obstruction lemma.** For `n>2p`, `C(n,p)` has a simplicial clique if
   and only if `p=2`. For `p>=3`, local cliques (those fitting inside `p`
   consecutive vertices) are excluded by three explicit witness families.
   Every nonlocal clique satisfies the three-arc bound `|K| <= 3p-n`.
   Simpliciality would require `|K| >= p-1`, which is impossible for
   `n>=2p+2`; at `n=2p+1` the graph is an odd antihole, known to have no
   simplicial clique.
5. **Facet collapses to rank.** Heredity forces the induced `C(n,p)` to be
   SCF, hence `p=2`. Coprimality makes `n` odd, so the clique-family
   coefficients `p-r` and `p-r-1` are `1` and `0`. The facet is rank, a
   contradiction to any proposed nonrank facet.

Therefore every nontrivial facet is a rank inequality. The C042 bridge then
turns rank-perfectness into exact weighted Pauli uncertainty.

## Adversarial controls

The frozen run
`results/pauli_fourth_moment_phase0/c043_quasiline_scf_falsification.json`
contains:

| control | result |
|---|---:|
| frozen order-nine SCF graphs, one deterministic deletion each | 4,308 / 4,308 pass |
| circulant parameter pairs `n>2p`, through `n=160` | 6,162 / 6,162 match the lemma |
| all cliques in small circulants through order 18 | 18,149 checked |
| nonlocal cliques (the case missed by the first proof draft) | all satisfy `|K| <= 3p-n` |
| published nonrank web `W_25^5` exact CFI positive controls | 1 / 1 detected |
| positive controls that are SCF | 0 |
| seeded SCF proper circular-arc exact-CFI stress graphs, orders 10--14 | 250 |
| discovered counterexamples | 0 |

The `W_25^5` control is not merely recognized heuristically. Its specified
clique-family inequality is checked against all stable sets and has exact
affine rank 25. The independent verifier redoes this calculation using only
the Python standard library.

## Reproduction

```text
python experiments/pauli_fourth_moment_phase0/run_c043_quasiline_scf_falsification.py --random-per-order 50 --max-order 14 --circulant-max-order 160 --overwrite
python -S experiments/pauli_fourth_moment_phase0/verify_c043_quasiline_scf_theorem.py
cd experiments/pauli_fourth_moment_phase0
python -m unittest test_c043_quasiline_scf_theorem.py -v
```

The five mutation tests reject a false circulant boundary, erasure of the
nonlocal-clique countercontrol, a corrupted positive-control right-hand side,
a downgraded theorem flag, and a corrupted source hash.

## Prior-art boundary

The proof uses, but does not claim as new, the Ben Rebea theorem and the
clique-circulant facet characterization:

- Eisenbrand, Oriolo, Stauffer, Ventura, *The stable set polytope of
  quasi-line graphs*, Combinatorica 28 (2008),
  https://doi.org/10.1007/s00493-008-2169-1.
- Oriolo, Stauffer, *On the facets of stable set polytopes of circular
  interval graphs*, Annals of Operations Research 315 (2022),
  https://doi.org/10.1007/s10479-021-04449-7.
- Chapman, Elman, Mann, *A Unified Graph-Theoretic Framework for Free-Fermion
  Solvability*, arXiv:2305.15625.
- Chudnovsky, Scott, Seymour, Spirkl, *A note on simplicial cliques*,
  Discrete Mathematics 344 (2021), 112470,
  https://doi.org/10.1016/j.disc.2021.112470.

Targeted searches for the combined statement, for a simplicial-clique versus
clique-circulant obstruction, and for an SCF quasi-line rank-perfect theorem
did not locate the result. That is meaningful novelty evidence, not proof of
priority. Independent expert or referee review is still required before an
A* claim can be presented as externally confirmed.

## Honest scope

- Proved: all SCF quasi-line graphs are rank-perfect and hbar-perfect.
- Not proved: all SCF graphs are hbar-perfect.
- False: all quasi-line graphs are hbar-perfect; the anti-heptagon is the
  boundary control and has no simplicial clique.
- No QPU data are required: this is a graph-polyhedral and quantum-uncertainty
  theorem, not a hardware-performance claim.
