# C026: exact-face recovery with all permitted variables

2026-09-09. Verify C025 independently before constructing a dual problem.
Keep all 3346 linear orbits not forced to zero; unlike C022/C024, no
C021 numerical threshold is used. Split the 2596 even-affine orbit rows
into 1030 proved equalities and 1566 inequalities. Exact RHS remains six.
Minimize sum of orbit coefficients using one-thread HiGHS interior point,
one 60-second solve, construction cap 60 seconds / 10 million entries.
No restarts. Save raw candidate/status and apply the existing registered
dyadic/bounded-fraction recovery grid with all-coordinate exact acceptance.

This retains every variable permitted by the exact C025 face. Equality
and symmetry reductions only guide discovery: final acceptance uses the
original 16384 dual coordinates and all 8256 even inequalities. A timeout
is not infeasibility; a numerical optimum is not an exact certificate.
No graph-family or novelty claim follows solely from this instance.

## Outcome

8686216 matrix entries, 35.703 seconds. HiGHS returned status 4 / model
status Unknown (15), without a candidate. This is NOT an infeasibility
proof and NOT a timeout. No rational recovery attempts were possible.
Four C025 and five C021 tests passed. Subsequent C027 examines exact row
redundancy before attempting another solve; C026 does not improve C021.
