# C024: low-mass dual discovery

2026-09-09. C023 resolved representation scope by existing theory; the
exact-six certificate remains absent. C022 dual simplex with zero
objective timed out without a candidate. This bounded attempt instead
minimizes the sum of orbit coefficients using HiGHS interior point and
crossover. Low coefficient mass is a discovery heuristic for a simpler
certificate, not a guarantee of sparsity or novelty.

Keep C022's identical selected support, all even-orbit constraints,
integer coefficient construction, exact target six, 10-million-entry
cap, 60-second construction cap, one thread and 60-second solve limit.
No additional restarts. Use the unchanged C022 rational recovery grid
and independent C021 exact verification over every original coordinate.
Save timeout or rejection too. A numerical feasible point alone does
not prove exact six. If accepted, inspect certificate structure before
launching a graph-family campaign; one instance is not A-star novelty.

## Result

The interior-point run also timed out without a returned candidate:
61.937 seconds total, 2596 rows and 3283 variables. No rational recovery
attempts were possible. The timeout's `primal_status is Infeasible` is
not an infeasibility certificate. No improvement to C021 is claimed.

Together C022/C024 show that neither of these bounded dense-orbit LP
configurations supplies a candidate. They do not show the full dual is
infeasible. Do not repeat these same configurations with new labels.
Further recovery should exploit exact active-face structure or a
different analytic certificate, with full-coordinate acceptance retained.
The original C021 verifier's five tests passed after parameterizing the
discovery code; the 127-test historical suite was not rerun here.
