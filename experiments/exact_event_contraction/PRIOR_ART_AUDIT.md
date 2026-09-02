# Adversarial prior-art audit: sparse event projectors

Audit date: 2026-09-02.

## Verdict

The broad claim is falsified.  Compiling a finite Boolean language to a
rank-minimal fixed-order TT/MPS, lifting it to a diagonal MPO, and contracting
one Born expectation is not a new general method.

The narrow live hypothesis is different: jointly choose a variable/elimination
order for a quantum circuit and a decision-event tensor so that the *combined*
network is cheaper than either circuit-only or event-only ordering.  The
observed `es60fst02` transition (event bond 152 to 5, with exact contraction
possible through depth 2 only in spectral order) is a motivating instance, not
evidence of a general algorithm or theorem.

## Structural reduction

For a finite event `A` and a fixed variable order, define

`M_k[p,s] = 1[p+s in A]`

for length-`k` prefixes and complementary suffixes.  This is exactly the
`k`-th unfolding of the Boolean indicator tensor.  Every TT factorization gives
`M_k = L_k R_k`, so its bond obeys `chi_k >= rank(M_k)`.  Standard exact
TT-SVD/rank factorization reaches equality at every cut.  This is a direct
specialization of tensor-train rank theory, not a new minimality theorem
([Oseledets, 2011](https://doi.org/10.1137/090752286)).

For `P_A = sum_x |x><x|`, the same `M_k` is the coefficient matrix across the
operator bipartition in the diagonal basis.  Its rank is therefore the
operator-Schmidt rank.  The diagonal TT-to-MPO lift reaches it, so the computed
bonds are fixed-order minimal even among unrestricted MPOs.  This is a useful
lemma for this artifact, but its ingredients are established.

## Closest prior art

| area | collision with the proposed claim | primary source |
|---|---|---|
| Tensor trains | unfolding ranks characterize fixed-order TT ranks | [Oseledets, 2011](https://doi.org/10.1137/090752286) |
| Weighted automata | minimal automaton dimension equals Hankel rank; prefix/suffix incidence is a finite Hankel slice | [Carlyle--Paz, 1971](https://doi.org/10.1016/S0022-0000(71)80005-3), [Kiefer, 2020](https://arxiv.org/abs/2009.01217) |
| WFA and TT | explicit equivalence/learning connection | [Li--Precup--Rabusseau](https://arxiv.org/abs/2010.10029) |
| Automata and MPS/MPO | automaton-to-matrix-product construction and expectation contraction | [Crosswhite--Bacon](https://doi.org/10.1103/PhysRevA.78.012356) |
| Finite quantum languages | finite bitstring DAG/DFA to MPS followed by exact Schmidt compression | [Bellante et al., 2026](https://arxiv.org/abs/2602.02698) |
| Boolean functions | exact truth-table/OBDD to TT constructions and order sensitivity | [Onaka et al., 2025](https://doi.org/10.1609/aaai.v39i14.33657), [Usturali et al., 2025](https://arxiv.org/abs/2505.01930) |
| Sparse exact QTT | removal of zeros and linear dependencies without materializing the full tensor | [Haubenwallner--Heller, 2026](https://arxiv.org/abs/2606.04506) |
| Generic circuit contraction | exact simulation cost governed by tensor-network width | [Markov--Shi](https://doi.org/10.1137/050644756) |
| Boolean counting as TN | Boolean solution sets/counting encoded as tensor networks | [Biamonte--Morton--Turner](https://doi.org/10.1007/s10955-015-1276-z) |

BDD/ZDD representations are also canonical finite-set baselines and highly
order-sensitive ([Bryant, 1986](https://doi.org/10.1109/TC.1986.1676819),
[Minato, 1993](https://doi.org/10.1145/157485.164890)).  Their width counts
distinct residual languages, whereas TT/Hankel rank measures the dimension of
their linear span; BDD minimization alone does not prove unrestricted TT/MPO
minimality.

## Claims ruled out

- first finite-set-to-MPO compiler;
- a new fixed-order TT/MPO minimality theorem;
- first event probability represented as one tensor-network expectation;
- spectral ordering is globally optimal;
- projector compression alone guarantees end-to-end speedup;
- raw storage compression (packed support is smaller than the dense MPO).

## Required baselines for a surviving claim

1. Separate selected-amplitude contractions.
2. One path reused while only basis projectors change.
3. Batched/open-output amplitude contraction
   ([Pan--Zhang](https://doi.org/10.1103/PhysRevLett.128.030501)).
4. Sliced contraction
   ([Huang et al.](https://doi.org/10.1038/s43588-021-00119-7),
   [Gray--Kourtis](https://doi.org/10.22331/q-2021-03-15-410)).
5. Trie, minimized DFA, BDD, and ZDD event operators.
6. Rank-minimal TT/MPO under the same order.
7. Circuit-only min-fill/treewidth and event-only rank-minimizing orders.

Each comparison must report path-search time, total contraction cost, slices,
wall time, and peak memory.  A single bra--MPO--ket network can be worse than
many amplitudes because it doubles the circuit and can increase contraction
width; the depth-3/4 failures in this artifact demonstrate that risk.

## Gate to an A*-level continuation

A credible next claim needs a clearly new combined objective, a theorem or
approximation guarantee for it, and broad held-out scaling across graph/event
families.  If an order is called optimal, it needs a certified lower bound such
as branch-and-bound over the relevant combined width.  Empirically it must beat
the baselines above end to end, not merely reduce event bond, and it must retain
the exact/certified error discipline used here.

Until those gates pass, the safe statement is:

> Applying known fixed-order Hankel/TT minimality produces a compact exact
> BKS-event projector, and problem-informed co-ordering changes both projector
> rank and practical circuit-contraction feasibility on one 55-qubit instance.
