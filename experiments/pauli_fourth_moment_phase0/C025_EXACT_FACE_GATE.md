# C025: exact saturated-stabilizer face

2026-09-09. Before another solver run, derive necessary equalities from
the 88 exactly saturated C014 stable sets. For each commuting binary
span enumerate every maximal isotropic extension L in 14 dimensions.
Deduplicate L. Cap at 10000 completed spaces and 120 seconds; if exceeded,
abort without a completeness claim. No optimization in this gate.

For each L, the identical-copy stabilizer Bell distribution is uniform
on the coset K={v: sp(v,p)=q(p) for all p in L}, q(x,z)=x.z mod 2.
Its partial transpose has uniform Bell coordinates on L. Compute and
check the aggregated relation by two exact integer transforms. Check
every K is even and each objective is exactly six.

If an exact-six dual u exists, complementary slackness forces u=0 on
the union of L and c+A*u=6 on the union of K. These are necessary, not
sufficient, conditions. Compare these exact sets with C021's numerical
support and C018 orbits. The stabilizer/Bell formalism and complementary
slackness are not claimed as new methods. Background: Montanaro,
[Learning stabilizer states by Bell sampling (2017)](https://arxiv.org/abs/1707.04012).

## Result and independently verified completeness

All 88 spans have binary rank five. Each has exactly
(2+1)(4+1)=15 Lagrangian extensions; 1320 distinct spaces were enumerated
in 10.125 seconds. The independent verifier reconstructs each space,
rejects duplicates, and counts all 15 extensions for each original span.
The count follows by quotienting S^perp/S and the incidence recurrence
N_k(2^k-1)=(2^(2k)-1)N_(k-1), hence N_k=product_j(2^j+1).

Summing the 1320 Bell distributions gives an exact feasible primal of
objective six and denominator 168960. Both integer PT implementations
agree in every coordinate. Its supports force 6540 dual zeros and 3784
tight primal-coordinate inequalities. In C018's verified symmetry
partitions, this leaves 3346 free dual orbits and forces 1030 affine-orbit
equalities. The remaining inequalities must still be checked.

For any nonnegative dual u whose bound is at most six, write
s_v=6-c_v-(Au)_v >=0 on even coordinates. For this primal lambda,

    0 = 6-c.lambda = s.lambda + u.(A lambda).

Both terms are sums of nonnegative numbers. This proves the forced zeros
and equalities from exact feasibility alone; the argument does not need
an assumption that the relaxation's optimum actually equals six.

## Consequence for C022/C024

Comparing the saved C021 dual at their fixed threshold 1e-8 shows that
C022/C024 selected 3283 of these 3346 free orbits and no forced-zero
orbits. They excluded another 63 orbits (126 coordinates) that the exact
face does NOT force to zero. This does not prove the excluded variables
are necessary, or explain the timeouts conclusively. It does remove the
justification for treating that heuristic support as exhaustive.

The next recovery should use all 3346 structurally permitted orbit
variables and the 1030 exact equalities, with acceptance over all original
coordinates. No solve on that new system has yet been run. Exact-six
upper bound and A-star novelty remain open. Four independent verifier
tests pass, including omitted space, corrupted probability and false
upper-bound claim. This is a structural reduction, not a new Bell method.
