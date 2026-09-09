# C019: constraint generation after C018's size-cap stop

2026-09-09, frozen before execution. C018 found 5184 affine and 5184
linear orbits with exhaustive weight-preserving automorphism enumeration;
its 10-million-entry matrix cap stopped construction. Do not change that
record. Reuse the verified orbit partitions but solve by adding constraints.

At most 20 LP solves and 60 seconds overall. Start with probability mass
normalization and necessary PPT Bell bounds lambda_v<=1/D (hence orbit
mass<=orbit_size/D). After each solve compute ALL 16384 PT probabilities.
If minimum >=-1e-9, save the candidate. Otherwise add up to 32 most
violated unused linear-orbit constraints, using exact integer character
sums for each row. No bound accepted as exact; a feasible rational PPT
repair above six will falsify only this relaxation's ability to prove six.
At most 640 dense rows, within the original matrix-entry budget. Save
iteration history and all returned candidate probabilities, including
infeasible ones marked as such. No new state search or changed C014 weights.

Outcome: reached the registered 20-iteration limit in 40.875 seconds.
All 20 truncated LPs solved numerically; final LP had 608 PPT orbit cuts,
objective 9.546589668255269 and minimum FULL PT probability
-0.001207693838967796. No candidate passed full PPT, including all earlier
iterates. These values are not feasible PPT witnesses or physical states;
no rigorous upper bound is certified by these numerical optima either.

verify_c019_saved.py reloaded all 20 saved candidates, reconstructed the
objective from original C014 labels/weights, and used a Walsh-Hadamard
convolution rather than the staged four-by-four transpose implementation
to recompute all full PT spectra. All minima and objectives matched, and
every candidate was independently confirmed non-PPT. Same NumPy machine
arithmetic remains a limitation. The ordinary theta certificate 6.50658
is still tighter than these partial-constraint numerical objectives.

Thus this cycle supplies a validated reduced formulation but not progress
on the actual numerical upper bound. Do not inflate implementation work
into mathematical novelty. Further work must justify a more effective
certificate/constraint strategy, not accept the non-PPT candidates.
