# C036: exact known-bound audit of the C035 sample

## Mathematical scope

For an anticommuting clique Q of Hermitian unitary observables,
sum_{i in Q} <P_i>^2 <= 1. Indeed, for real coefficients a,
(sum a_i P_i)^2=(sum a_i^2)I; taking a_i=<P_i> yields the bound.
Nonnegative linear combinations therefore prove weighted bounds.

For an induced odd cycle C_(2k+1), the quantum bound is k. This is
published, not new here: Xu, Schwonnek, Winter, *Bounding the joint
numerical range of Pauli strings by graph parameters*, Theorem 21,
https://arxiv.org/html/2308.00753v2 . The induced restriction is essential:
nonedges in the cycle must commute. We use that theorem as a premise,
not as something independently reproved by this finite computation.

For each of the 60 frozen C035 records, solve two outer-polytope LPs:
clique constraints only; clique plus every induced odd-cycle constraint.
Recover rational primal and dual solutions. An independent standard-library
verifier enumerates all nonempty subsets, tests all clique/cycle constraints,
validates every positive dual row, and checks exact primal=dual objective.
The numerical solver status alone is not acceptance evidence.

## Outcome

120 rational primal/dual pairs independently accepted; four tests pass,
including corrupted primal, negative dual coefficient, and invalid row bound.

* 40/60 rows are already implied by clique uncertainty alone, at exactly the
  proposed target. Their C035 quantum absence of violations is fully expected
  from a standard theorem, not independent support for a new transfer rule.
* 20/60 rows are not implied by the tested clique+odd-cycle inequalities.
  Their exact outer-polytope optima exceed the target by 1/3 or 2/3.
  The artifact `c036_independent_audit.json` identifies every case/variant
  and exact gap. Feasible LP profiles are NOT physical quantum states.
* Adding odd cycles explains no additional C035 row in this sample.

This is a classification relative to TWO specified relaxation systems only.
It does not establish independence from all known quantum inequalities,
including wheel/join rules, small-graph theorems, or other decompositions.
It is neither a counterexample nor a new quantum bound nor A-star novelty.
Next: audit stronger known induced-subgraph bounds on these 20 rows before
using them to motivate a general operator-transfer theorem.
