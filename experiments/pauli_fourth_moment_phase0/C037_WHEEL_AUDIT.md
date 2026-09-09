# C037: stronger known odd-wheel bound audit

## Known mathematical input and explicit derivation

For an induced cycle on 2k+1 vertices with unit weights, beta=k by
Xu--Schwonnek--Winter (2024), Theorem 21:
https://arxiv.org/html/2308.00753v2 . Add one universal hub h, anticommuting
with every rim observable. Then

    sum_{i in rim} <P_i>^2 + k <P_h>^2 <= k.

For completeness, for real coefficients a of Euclidean norm one let
R=sum_{rim} a_i P_i and H=R+sqrt(k) a_h P_h. The cycle bound implies
||R||^2<=k sum_{rim} a_i^2 by Cauchy--Schwarz applied to every state's
expectations. Since {R,P_h}=0 and P_h^2=I, H^2=R^2+k a_h^2 I<=k I.
Taking the supremum over a gives the displayed squared-expectation bound.
This is an instance of the published weighted join rule, NOT a new lemma:
Xu et al. (2025), Property 1 and its Appendix A.1 proof,
https://arxiv.org/html/2511.13531v1 .

## Computation and acceptance

On all 60 frozen C035 rows, add every induced odd wheel (one hub only)
to all clique and induced odd-cycle constraints. Numerical LP solutions
are converted to fractions. The independent standard-library verifier
enumerates all subsets for primal feasibility, verifies every dual row's
induced edges/nonedges, hub coefficient k, nonnegative multiplier, covering
of the requested weights, and exact equality of primal/dual objectives.

60 exact primal/dual pairs accepted, including 47 used wheel terms.
Four tests pass: valid artifact; corrupt hub coefficient; corrupt primal;
corrupt target. This is exact acceptance of the specified relaxation,
not an exact quantum-state search.

## Outcome and remaining scope

53/60 cases now have their target proved by known inequalities, compared
with 40/60 using cliques alone. Thus 13 more finite numerical successes
need no new transfer theorem. Seven cases remain outside this relaxation,
each with exact gap 1/2. The full case/variant list is saved in
`c037_independent_audit.json`. Their LP profiles are not physical states.

The smallest remaining case (0,1) has nine vertices and weights seven ones
and two twos, superficially matching the published narrow-basin G9 example.
A read-only exact comparison excluded graph isomorphism: the degree multisets
are [4,4,4,4,4,4,4,5,5] and [3,3,4,4,4,5,5,6,6], respectively. The latter
was reconstructed from the nine Pauli strings in the paper's equation 94.
This does not exclude an induced smaller counterexample, other published
graphs, or a different narrow optimization basin.

The seven residual cases must still be checked against stronger known
small-graph bounds and representations. No general gear theorem, priority,
or A-star novelty follows from surviving this restricted baseline.
