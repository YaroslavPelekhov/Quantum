# C022: fixed-right-hand-side dual recovery

2026-09-09. C021 gave an exact near-six bound, not equality. Freeze this
recovery before solving: use the C018 exact symmetry partitions, only
even affine constraint orbits, and dual linear orbits with mean -y>1e-8
in C021. This support restriction is a discovery heuristic; acceptance
will check the full original dual and does not rely on the heuristic.

Construct ALL even-orbit inequalities T*u <=128*(6-c), where T=128*A,
with each variable the common nonnegative dual value on a selected linear
orbit. Integer coefficients are direct character sums. At most 10 million
matrix entries, 60-second construction cap and one 60-second HiGHS dual
simplex feasibility solve, zero objective, one thread. No tolerance-based
claim of exact feasibility. Save any returned candidate and raw statuses.

Attempt rational recovery of returned coordinates using bounded denominators
1,2,4,8,16,32,64,128,256,512,1024 and limit_denominator(10000). These are
certificate-discovery options, not statistical trials. Exact acceptance
requires all 16384 dual coordinates nonnegative and all 8256 original
even-coordinate inequalities <=6 using integer/rational arithmetic and
regenerated objective. A failed rounded candidate is kept as a failed
attempt, not repaired by silently raising the asserted upper bound.
No new quantum-state search or broader graph theorem is claimed.

## Observed outcome

2596 constraints, 3283 selected orbit variables, 8522668 matrix entries.
The solver reached its 60-second limit; total runtime 63.953 seconds.
No candidate was returned, so no rational recovery attempts were made.
The raw status text includes `primal_status is Infeasible`, but the
terminal model status is **time limit**, NOT a proof of infeasibility.
No exact-six certificate was produced. The support restriction also
precludes drawing an impossibility conclusion about the full dual.
See `c022_exact_six.json` and `c022_recovery.json` in the results folder.
