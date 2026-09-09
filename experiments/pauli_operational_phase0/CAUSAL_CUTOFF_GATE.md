# Practical cutoff-sensitivity falsification

2026-09-09. Frozen before execution. The previous cycle established an
exact finite-termination obstruction; that alone says nothing about the
quality of numerical approximations. Test this gap rather than promoting
the obstruction into a practical sampling claim.

Primary setting: two-step qubit processes, rank-two Ginibre factors,
seeds 0,...,19. Positive controls: same dimension rank eight, seeds 0,...,4.
Use SeedSequence([2,rank,seed]), as in the previous diagnostic, so the first
five seeds overlap openly; this is not a held-out novelty validation.
Each input receives cutoffs 1e-8,1e-12,1e-14, applied to BOTH square roots
and pseudoinverse roots as in our previous numerical transcription.
Descending tail order 4,2. Stop after a full sweep with maximum normalized
Frobenius causal residual <=1e-9, or 200 sweeps. Seventy-five runs, one
thread, 60-second overall cap. Preserve failures and do not silently
relax tolerances. The cap is a diagnostic budget, not the paper's bound.

Measure negativity across (o2,i2)|(o1,i1,o0), purity, and paired trace
distance of terminal states. Primary endpoint: median absolute negativity
difference between 1e-8 and 1e-14 on the twenty rank-two inputs. Require
all forty endpoints to meet the same 1e-9 causal tolerance and physical
PSD/trace checks, and median negativity difference >=0.01 for the proposed
practical-instability gate to pass. This is a predeclared screening scale,
not a power calculation or an established universal relevance threshold.
If endpoints fail to converge, record an inconclusive comparison rather
than treating invalid outputs as different valid processes.

Secondary endpoints: maximum/median paired trace distance, all intermediate
cutoff comparisons, iterations, rank/purity changes. These cannot replace
the primary gate after seeing results. Different samplers define different
measures; no distributional bias is defined without an intended measure.
These experiments do not audit the actual author's code or hardware data.

If the gate fails, close cutoff-sensitive temporal negativity at these
settings as a source of a major contribution. Retain the exact theorem as
a limited correction; do not enlarge claims by relabeling convergence
technicalities as a new quantum capability.

## Outcome: practical-instability gate FAILED

All 75 runs reached the common causal tolerance, in 1 to 11 sweeps;
largest terminal residual 9.0873e-10. The primary twenty paired inputs
had median absolute negativity change 2.3852e-12, far below 0.01.
Median paired trace distance was 2.4339e-10; maximum was 1.5558e-9.
Runtime 0.234 seconds. These small paired differences are descriptive,
not a universal stability guarantee or an estimate of an intended measure.

All 75 terminal matrices were saved in a compressed NPZ with a SHA256
recorded in causal_cutoff_20260909.json. A separate read-only verifier
imports no sampling code, uses explicit index partial transposition and
SVD nuclear norms rather than eigenspectrum negativity/trace distance,
and checks all 75 states and 75 pairwise records, including positivity,
trace, Hermiticity, marginal constraints and purity. It reproduced the
negative gate. Shared NumPy/BLAS and the same machine remain limitations;
this is not external validation or trajectory replay.

Decision: close cutoff-sensitive temporal negativity in this registered
regime as an A-star route. The exact finite-termination theorem remains
valid, but numerical outputs can be accurate and stable despite violating
the written finite iteration guarantee. Do not claim the original paper's
physical conclusions fail, or keep stretching this correction into a
major contribution without independently motivated new evidence.

No acceptance criterion was changed after observing the result. The gate
does not establish stability for other dimensions, near-degenerate inputs,
other precision formats or different control tasks. Those possibilities
are not by themselves a reason to reopen this candidate.
