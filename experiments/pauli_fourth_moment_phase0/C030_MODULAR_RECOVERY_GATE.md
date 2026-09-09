# C030: exact modular correction of the near-six dual

2026-09-09. Use C021 orbit means >1e-8 and even constraints within 1e-8
of six solely as discovery heuristics. Pivoted QR selects independent
rows/columns numerically. Round orbit means at denominator 2^20; correct
only pivot coordinates by solving the integer square residual system.
Use modular elimination and CRT/rational reconstruction, at most eight
descending primes starting at 65521 and 120 seconds checked between
prime solves. Exact substitution, not numerical rank, accepts a solve.
At most ten million matrix entries. One rounded starting vector, no LP.

Acceptance requires full original-coordinate nonnegativity and exact
upper bound six via the independent C021 verifier. Missing active rows,
heuristic support, singular primes, or reconstruction failure cannot
silently relax acceptance. Report all failed recovery stages. Modular
linear algebra is a known computational technique, not claimed novelty.

Outcome: 1046 discovered active orbit rows, 3283 variables, numerical
pivot rank 906. Eight nonsingular primes, 16.172 seconds; not all rational
coordinates reconstructed. No certificate in C030. Four modular tests
pass. C031 reuses one factorization to reach higher precision efficiently.
