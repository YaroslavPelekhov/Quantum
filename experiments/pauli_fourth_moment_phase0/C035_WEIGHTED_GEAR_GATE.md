# C035: nonuniform seed gear-transfer falsification

Protocol fixed in code before this run. Reuse the 30 C034 graph constructions,
but draw two seed weight vectors per graph: integers 1..3, endpoints fixed
to one. Seed RNG 20260911; weighting and start RNG share a deterministic
stream. This is not exhaustive and may include uniform draws or duplicate
weighted cases. For each draw, enumerate the exact seed stable bound and
the output stable bound. The proposed output has outside seed weights,
six unit gear weights, and hub weights two; its proposed bound is seed+2.
Record classical transfer failure separately; never count it as quantum
counterexample. These are valid-row candidates, not claimed seed facets.

For classically exact transfers run 16 starts (ones plus Gaussian), 256
iterations, one thread. Preserve every returned best state, expectations,
value, iteration convergence flag and the state stationarity residual
||sum_i w_i <P_i> P_i psi - f(psi) psi||. Independently recompute all saved
states by bitwise Pauli action using standard-library arithmetic, including
the residual. Stationarity is not local maximality or global optimality.
Convergence flags refer to the optimizer's terminal coefficient iterate;
saved best states have their own separately checked residual.

Threshold for a violation candidate: 1e-6. No-violation is not an upper-bound
proof. Positive-control behavior is covered by the existing C034 suite;
this campaign reuses the same optimizer, but does not replay a new positive
control. This does not cover g-lifting or XX additions and claims no new
optimizer, classical operation, quantum theorem, or A-star confirmation.

## Outcome

All 60 draws completed; 56 have nonuniform seed weights. Every classical
output bound equals seed+2. All 960 saved states independently accepted.
No excess above 1e-6; maximum recomputed excess 7.460698725481052e-14.
794/960 terminal coefficient iterations met the strict convergence test.
553/960 saved best states have stationarity residual below 1e-8; the largest
residual is 0.0012485871624572536. These are different diagnostics, not
interchangeable counts. Selecting the largest floating-point value can
retain an earlier state even when the terminal coefficient iterate converges.
The run body took 7.125 seconds, excluding startup. Five independent audit
tests cover the valid artifact and corrupt state, seed weight, residual,
and claimed bound. The prior C034 positive-control audit is rerun separately.

This strengthens bounded evidence for the necessary weighted transfer
condition, not its proof or novelty. No g-lift/XX or all-weight family
claim follows. Next useful step: an operator transfer lemma or an exact
obstruction to it; do not substitute further small random sampling for it.
