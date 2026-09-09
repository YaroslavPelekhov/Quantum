# C028: solve the exactly reduced equality system

2026-09-09. Revalidate C025 and C027 with their independent verifiers.
Use all 3346 permitted dual orbit variables, 898 retained equality rows
and all 1566 remaining inequalities. C027 proves the 132 deleted equality
rows are redundant, including their right-hand sides. No numerical rank
assumption is needed. One-thread HiGHS interior point, minimize sum of
orbit coefficients, 60-second solve cap, no restart. Keep the ten-million
entry construction cap. This changes the actual system supplied to the
solver, not the mathematical feasibility problem.

Save raw output and any candidate. Rational recovery uses the unchanged
C022 dyadic/bounded-fraction grid and full C021 integer checks over all
16384 coordinates and all 8256 even inequalities. Verify original equality
residuals numerically for diagnostics too. Numerical feasibility alone is
not proof. Timeout or Unknown is not infeasibility. Exact six, general
graph theorem and publication novelty are separate gates.

## Outcome

The supplied solver system had 898 equalities, 1566 inequalities and
3346 variables, with C025/C027 reverified before solving. Time limit
reached, 64.547 seconds total, no candidate. No rational recovery attempts.
This does not prove infeasibility. Removing exact redundancy alone did
not produce a candidate within this budget. Three C027 and five C021
tests passed; no new exact upper bound or novelty claim.
