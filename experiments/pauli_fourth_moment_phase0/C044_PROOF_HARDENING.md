# C044: proof hardening of the SCF quasi-line theorem

Date: 2026-09-16

## Outcome

The C043 theorem survives its strongest internal proof audit:

> **Every simplicial claw-free quasi-line graph is rank-perfect and therefore
> hbar-perfect for all nonnegative Pauli weights.**

The main change is substantive rather than cosmetic.  The previous proof
sketch for nonlocal cliques used a circular three-arc statement whose short
justification was not sufficiently self-contained.  C044 replaces it by a
complete integer sumset proof.

## Autonomous nonlocal-clique lemma

Let `r=p-1`, `q=n-r`, and rotate a clique `K` of `C(n,p)` so that it contains
zero.  Write the other vertices as counterclockwise distances `A` and
clockwise distances `B`, both subsets of `[1,r]`.  A nonlocal clique has
`a=max(A)`, `b=max(B)` and `a+b>=q`; put `h=a+b-q`.

Compatibility with `b` partitions `A` into `[1,r-b]` and `[a-h,a]`.
Symmetrically, `B` lies in `[1,r-a]` or `[b-h,b]`.  Translate the high tails
to deficit sets `X,Y subseteq {0,...,h}`.  If `x+y=h+1`, the corresponding
cross-distance is `q-1`, which lies strictly in the forbidden interval
`(r,q)`.  Therefore `h+1` is not in `X+Y`.  The sets `X` and `h+1-Y` are
disjoint subsets of `{0,...,h+1}`, so `|X|+|Y|<=h+2`.  Hence

```text
|K| <= 1 + (r-b) + (r-a) + (h+2) = 3p-n.
```

This proof uses no circular-arc Helly lemma.  The boundary `n=2p+1` is also
handled internally: `C(n,p)` is an odd antihole, and a cyclic-gap argument
exhibits two nonadjacent external neighbors for a suitable vertex of every
candidate clique.

## Literal dependency audit

The external graph-polyhedral dependencies were checked against their primary
statements.

1. Eisenbrand--Oriolo--Stauffer--Ventura establish that quasi-line stable-set
   polytopes are described by nonnegativity, clique inequalities, and
   clique-family inequalities; the non-FCIG quasi-line case has only rank
   facets.
2. Oriolo--Stauffer Definition 8 states that an `(n,p)` clique-circulant
   contains an **induced** `(n,p)` circulant with one representative from each
   clique.
3. Their Theorem 26 proves the FCIG facet conjecture and strengthens it to
   coprime `n,p` with `n>2p>=4`.
4. SCF heredity therefore applies to the induced circulant.  The corrected
   obstruction lemma forces `p=2`.
5. For `p=2`, coprimality makes `n` odd and `r=n mod p=1`; the two CFI
   coefficients `p-r` and `p-r-1` are `1` and `0`.  The alleged nonrank facet
   is rank, giving the contradiction.

Primary sources:

- Eisenbrand, Oriolo, Stauffer, Ventura, *The stable set polytope of
  quasi-line graphs*, Combinatorica 28 (2008),
  https://doi.org/10.1007/s00493-008-2169-1.
- Oriolo, Stauffer, *On the facets of stable set polytopes of circular
  interval graphs*, Annals of Operations Research 315 (2022), Definition 8
  and Theorem 26, https://doi.org/10.1007/s10479-021-04449-7.
- Chudnovsky, Scott, Seymour, Spirkl, *A note on simplicial cliques*,
  Discrete Mathematics 344 (2021), 112470,
  https://doi.org/10.1016/j.disc.2021.112470.

Targeted searches for the exact statement and its natural equivalents
(`simplicial clique quasi-line rank-perfect`, `simplicial claw-free stable set
polytope`, `antiweb simplicial clique`, and `clique-circulant simplicial
clique`) found the separate ingredient literatures but no combined theorem.
Adjacent work on simplicial-edge compositions concerns claw-free graphs
outside the quasi-line class and does not state the result proved here.  This
is evidence for novelty, not a substitute for referee-level priority review.

## Reproduction and falsification controls

```text
python experiments/pauli_fourth_moment_phase0/run_c044_proof_hardening.py --overwrite
python -S experiments/pauli_fourth_moment_phase0/verify_c044_proof_hardening.py
cd experiments/pauli_fourth_moment_phase0
python -m unittest test_c044_proof_hardening.py -v
```

The frozen run records every one-vertex deletion of all 4,308 order-nine SCF
graphs, symbolic parameter checks through order 160, exhaustive deficit-set
checks through `h=20`, and every clique of every `C(n,p)` through order 30.

## Honest status

The internal mathematical case is materially stronger than in C043: the only
new combinatorial bound is now proved from first principles, and the imported
theorems have a literal assumption-to-conclusion map.  This remains an
unrefereed manuscript.  The result is a strong A/A* candidate, not an
externally certified venue outcome or priority claim.
