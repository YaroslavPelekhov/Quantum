# C029: equality-only exposing functional

2026-09-09. C028 timed out even after exact equality deletion. Test one
specific facial-reduction hypothesis, not another LP. In C025's free
orbit coordinates, let r_j=1 for the 63 orbits excluded by C022/C024's
fixed C021 threshold, and zero otherwise. Seek y with A_eq^T y=r and
b_eq^T y=0 using one least-squares solve. If exact, u>=0 and A_eq u=b_eq
imply r.u=0 and force those coordinates to zero.

Numerical projection residual alone cannot prove membership or nonmembership.
If <=1e-9, attempt limit_denominator(4096) rational recovery and verify
every original equality coefficient and RHS using integer arithmetic.
Cap absolute integer products below 2^62; reject oversized denominators.
Failure only closes this particular exposing functional/recovery attempt,
not all facial reductions or exact-six certificates. Save diagnostics.

## Outcome

Maximum projection residual 0.8086500099076113, runtime 3.218 seconds.
No rational attempt was triggered and no exact exposing vector found.
The registered uniform sum of the 63 orbit variables is not numerically
consistent with this row-space construction. This is NOT an exact
nonmembership proof or a rejection of nonuniform exposing functionals,
inequality-assisted facial reduction, or the original conjecture.
