# C027: equality conditioning diagnostic

2026-09-09. C026 returned solver status Unknown, not infeasibility.
Before another LP, build its exact integer equality matrix (1030 x 3346)
and run one pivoted QR of its transpose, one thread. Inspect diagonal
rank thresholds 1e-8, 1e-10, 1e-12 relative to maximum diagonal. Save matrix,
RHS, pivot order and QR diagonal. This is a numerical discovery diagnostic,
NOT proof of rational rank, equivalence, feasibility or bound six.
At most ten million entries. No LP, state search, or novelty claim.

## Follow-up exact redundancy gate (before recovery)

The QR diagnostic returned rank 898 at all three thresholds, with a
clear gap (14.85 versus 1.15e-12). Use its proposed 898 retained rows to
express the other 132 rows. Recover coefficients on the dyadic grid
1,2,...,1024 and verify both FULL integer matrix equality and RHS equality.
If successful, this proves deletion of those rows preserves the system,
not that the remaining rows are independent. Require coefficients <=1e6
in magnitude so all integer matrix products are safely below int64 range.
No optimizer will be run in this follow-up. Save accepted relations.

Dyadic recovery failed all 11 checks. Before a second recovery, register
one bounded-fraction attempt: per-entry limit_denominator(4096), common
LCM denominator, rejecting coefficient numerators above 1e6 or unsafe
int64 products. Save separately; do not overwrite dyadic failures.

## Exact result

Bounded-fraction recovery succeeds with common denominator 48:
132 rows are exact rational combinations of the selected 898 rows,
with matching right-hand sides. 9851 nonzero relation numerators,
maximum absolute numerator 72. All 3346 columns are checked.

The independent stdlib verifier regenerates the original matrix from
direct integer character sums (not the stored matrix or NumPy bincount)
and verifies every identity using arbitrary-precision Python integers.
Three tests pass: valid relations, corrupted coefficient, omitted row.
Thus dropping these 132 equalities preserves the system EXACTLY. We have
not separately proved independence of the remaining 898 rows. Neither
the QR diagnostic nor this reduction establishes feasibility or upper six.

Next solve may use 898 equality rows, 1566 inequality rows and all 3346
permitted variables. It has not been run in this gate. Dependence is a
possible numerical difficulty, not a proven cause of C026's Unknown status.
