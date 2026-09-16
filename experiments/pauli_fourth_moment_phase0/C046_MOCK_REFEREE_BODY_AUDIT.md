# C046: adversarial mock-referee and beta-body audit

Audit date: 2026-09-17. Scope: the central line-graph theorem and every
logical dependency between the definition of the beta number and the claimed
matching-polytope identity. The secondary SCF quasi-line theorem was checked
only for isolation from the headline result; its classical facet theorem
remains an external cited dependency.

## Referee verdict before revision

The skew-contraction lemma, weighted matrix inequality, Majorana norm
reduction, and matching lower bound form a valid proof chain. No counterexample
or normalization failure was found. However, the manuscript used the phrase
"complete beta body" before formally defining the representation-independent
convex corner. That made the strongest formulation look broader than the
proved all-weight identity. A second exposition gap was the odd-order
Clifford case in the equality between the Majorana Hamiltonian norm and half
the skew nuclear norm.

Both issues are repaired in the revised manuscript.

## Finding ledger

| ID | Severity | Adversarial objection | Resolution |
|---|---|---|---|
| F1 | Major | `BETA(L(R))=MATCH(R)` was used without defining `BETA`; the raw squared joint range is realization-dependent and need not be convex. | Added the Xu-et-al. convex-corner definition `BETA(G)=conv(down Q(S))`, stated its representation invariance, and distinguished it from the raw range. |
| F2 | Major | Equality of all nonnegative weighted optima does not by itself identify an arbitrary nonconvex profile set. | The theorem now identifies two compact convex corners. Equality of all nonnegative support functions then proves body equality. |
| F3 | Moderate | The definition of `beta` appeared to optimize simultaneously over realizations and states, obscuring where representation invariance is used. | Defined `beta` for any fixed realization and cited representation invariance before selecting the Majorana realization. |
| F4 | Moderate | The norm formula could be questioned for an odd number of root Majoranas. | Added the `2q`/`2q+1` block count, the zero direction, and the joint-sign-pattern argument for the commuting bilinear involutions. |
| F5 | Minor | The corollary mixed raw attainability with membership in a downward convex body. | Replaced it by a realization-level statement: every raw squared profile satisfies every blossom inequality, while matching incidence vectors belong to `BETA`. |
| F6 | Minor | The secondary quasi-line theorem could be mistaken for a dependency of the line-graph result. | The contribution hierarchy now treats it as removable and secondary; the headline proof uses only Edmonds, nuclear duality, Majorana algebra, and beta representation invariance. |

## Central proof dependency audit

1. **Variational identity.** For fixed observables, Euclidean duality and the
   spectral variational principle give the maximum Hamiltonian norm. Compact
   state and coefficient spheres justify maxima and interchange.
2. **Skew-contraction lemma.** Row norms give the degree inequalities. Every
   odd principal skew matrix loses one rank, so its Frobenius norm gives the
   full odd-set inequality. Entries outside the root support can only make
   these bounds stronger.
3. **Weighted matrix inequality.** A real operator-norm dual optimizer may be
   skew-symmetrized without increasing its norm or changing its pairing with
   the skew matrix. Weighted Cauchy--Schwarz then uses the matching-polytope
   membership from step 2. A maximum-weight matching saturates the constant.
4. **Majorana reduction.** Root edges map to bilinears that anticommute exactly
   on incident pairs. Skew normal form gives one commuting involution per
   singular-value pair and therefore norm `||A||_*/2`, including odd root
   order.
5. **Upper and lower support functions.** The matrix inequality proves the
   upper bound for the Majorana realization; representation invariance
   transfers it to the graph parameter. A maximum-weight matching supplies
   the common-eigenstate lower bound.
6. **Body equality.** The beta body and matching polytope are compact convex
   corners with identical support functions for every nonnegative weight, so
   they coincide.

No step uses the finite atlas, random ablations, the SCF quasi-line theorem,
QPU data, or a complexity assumption.

## Remaining external dependencies and honest risk

- Edmonds' matching-polytope theorem.
- Representation invariance and the convex-corner definition of `BETA` from
  the beta-number literature.
- Standard real nuclear/operator-norm duality and finite Clifford algebra.
- Only for the secondary extension: the published quasi-line facet
  classification and the cited SCF free-fermion rank theorem.

The remaining headline risk is bibliographic priority, not an observed gap in
the proof. The secondary theorem carries a larger citation-interpretation risk
and can be split off without changing any line-graph result. This internal
mock review is not a substitute for an independent referee.

## Submission recommendation

The revised manuscript is ready for an external mathematical review of the
central theorem. The recommended submission claim is exactly:

> For every finite simple root graph, the representation-independent Pauli
> beta body of its line graph equals the root matching polytope; equivalently,
> every nonnegative weighted beta number equals maximum matching weight.

Do not claim novelty for line-graph free-fermion solvability, beta bodies,
matching algorithms, or skew-energy bounds individually.
