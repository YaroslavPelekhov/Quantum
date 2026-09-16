# C042: rank-perfect boundary beyond line graphs

> Superseded by C043: the conjecture recorded below is now proved. See
> `C043_QUASILINE_SCF_THEOREM.md`. This file remains the frozen C042 record.

Date: 2026-09-16.

## Central result

Let `BETA(G)` be the downward body of squared Pauli expectation profiles and
`STAB(G)` the stable-set polytope. The earlier SCF rank theorem proves, for
every simplicial claw-free (SCF) graph `G` and every induced subgraph `G[U]`,

`sum_{v in U} y_v <= alpha(G[U])` for every `y in BETA(G)`.

A graph is rank-perfect when these induced-subgraph rank inequalities,
together with nonnegativity, describe `STAB(G)`. Therefore:

> **Theorem. Every rank-perfect SCF graph is hbar-perfect.**

Indeed, the SCF rank theorem gives `BETA(G) subseteq STAB(G)` under
rank-perfectness, while the universal stable-set construction gives the
reverse inclusion after downward closure. Hence `BETA(G)=STAB(G)` and
`beta(G,w)=alpha(G,w)` for every nonnegative weight vector.

The classical literature proves that semi-line graphs are rank-perfect.
Consequently every SCF semi-line graph is hbar-perfect. This is a class-level
extension of C038 that does not require a line-graph root or a Majorana
bilinear representation.

## Why the extension is strict

The smallest witness found automatically in the exact order-nine census has
graph6 code ``H?`adQY``. It has nine vertices and twelve edges. Independent
checks certify that it is connected, SCF, quasi-line, not a line graph, and
rank-perfect. Its stable-set polytope has 17 facets: nine nonnegativity facets
and eight rank facets, with no nonrank facets.

The witness is also not h-perfect. One facet is the rank inequality on the
eight-vertex support `[0,1,2,4,5,6,7,8]`, with graph6 code `GCXDcg`,
stability number three, ten edges, and twelve saturating stable sets. The
support is neither a clique nor an odd hole, so this facet is absent from the
h-perfect description. Thus the new theorem is strictly beyond both the
all-line-graph theorem and the h-perfect sufficient route.

## Exact order-nine boundary

The existing exact census contains every SCF graph of order nine considered
in C001/C002. C042 reclassifies all 4308 records with independent quasi-line
and line-graph tests and joins them to the exact facet census.

| Class | Graphs | Graphs with nonrank facets |
|---|---:|---:|
| Line graphs | 710 | 0 |
| Quasi-line, non-line | 3048 | 0 |
| SCF, not quasi-line | 550 | 550 |

Thus all 3758 quasi-line members of this exhaustive order-nine SCF census are
rank-perfect, while every detected nonrank case lies outside quasi-line. This
is strong finite evidence for a sharper boundary, not an arbitrary-size
proof.

## Larger falsification tests

### Web graphs

All 868 web graphs `W_n^k` for `5 <= n <= 60` were classified. Of the 112
SCF cases, every one is either the cycle regime `k=1` or has stability number
at most two. No known hard web obstruction survives the SCF condition in this
family. This eliminates one natural counterexample source but does not
classify all circular-arc graphs.

### Proper circular-arc stress

A separate seeded generator produced 60 connected equal-length circular-arc
graphs, twenty at each order 10, 11, and 12. Every retained graph is SCF,
quasi-line, non-line, has stability number at least three, and has at most 120
stable sets. Qhull was used only to discover candidate facets; every reported
rank facet was then checked with exact integer validity and exact affine rank.
No nonrank facet was discovered in the 60 retained graphs.

The conditioning on at most 120 stable sets and the finite sample are material
limitations. These rows are a falsification stress, not an exhaustive census
and not a proof of rank-perfectness for all proper circular-arc graphs.

## Stronger conjecture and failed overclaim

The data support the following sharper hypothesis:

> **Conjecture. Every SCF quasi-line graph is rank-perfect.**

If proved, it would combine with the central theorem to make every SCF
quasi-line graph hbar-perfect. C042 does **not** prove this conjecture.

The unrestricted quasi-line claim is false. Xu et al. identify the
anti-heptagon as the smallest hbar-imperfect graph, and it is quasi-line.
Therefore SCF is essential; `quasi-line => hbar-perfect` must not appear in the
paper. Likewise C042 does not prove the unrestricted SCF conjecture.

## Prior-art boundary

- Chapman, Elman, and Mann provide the SCF free-fermion/rank machinery used as
  an attributed input: <https://arxiv.org/abs/2305.15625>.
- Xu et al. define hbar-perfection and supply the anti-heptagon obstruction:
  <https://arxiv.org/abs/2511.13531>.
- Oriolo's semi-line class and the quasi-line stable-set literature supply the
  classical rank-perfect input; see
  <https://doi.org/10.1016/S0166-218X(03)00400-1> and
  <https://www.iasi.cnr.it/~ventura/PaoloVenturaFiles/papers/EOSV06.pdf>.

The logical bridge from the SCF rank theorem to rank-perfect graphs and the
strict Pauli witness are the priority-sensitive claims. A documented negative
search supports positioning but cannot establish publication priority.

## Reproduction

From the repository root:

```text
python experiments/pauli_fourth_moment_phase0/run_c042_rank_perfect_boundary.py
python -S experiments/pauli_fourth_moment_phase0/verify_c042_rank_perfect_boundary.py
python -m unittest discover -s experiments/pauli_fourth_moment_phase0 -p test_c042_rank_perfect_boundary.py -v
```

The frozen JSON contains the theorem statement, upstream hashes, exhaustive
counts, the strict witness, all 60 larger records, scope flags, source hash,
and hashes of three CSV tables plus the figure. The standard-library verifier
reconstructs the classifications and exact certificates without importing the
discovery code. Six tests include the reference run and five deliberately
corrupted controls.

## Honest verdict

C042 produces a genuine analytic extension beyond line graphs: the proved
object is the intersection of rank-perfectness with SCF, with semi-line SCF as
an immediate named corollary and an explicit strict witness. The attractive
quasi-line boundary is currently a well-falsified conjecture, not a theorem.
The combined C038+C042 result is a stronger A/A* candidate, but A* status and
priority still require external review; no hardware or quantum-advantage claim
is made.
