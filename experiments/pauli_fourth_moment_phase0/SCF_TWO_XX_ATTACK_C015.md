# C015: adversarial quantum test of the C014 full facet

Registered 2026-09-08 before any numerical evaluation of the target.
Freeze C014's 24 operators, seven-qubit binary labels and target weights
one except zero-based vertices 6,7 of weight two. Exact stable bound six.
The operator obligation is universal; this finite numerical test cannot
prove it, even if all starts return six.

Construct Hermitian Pauli matrices and verify normalization, involution
and every pair's prescribed commutation sign. Use a first state-moment
SDP only to propose nonnegative initial magnitudes `sqrt(w_i*profile_i)`.
It is a relaxation, not a proof certificate. Alternate a top-absolute
eigenvector of `sum sqrt(w_i)*a_i*P_i` and normalized
`sqrt(w_i)*<P_i>` for at most 64 steps, tolerance 1e-10.

Freeze sign representatives modulo the 14-dimensional binary row space
of the adjacency matrix: reduce that space by exact XOR elimination,
then flip subsets of the ten nonpivot coordinates in binary order
0,...,1023. These are 1024 starting sign classes, NOT an exhaustive search
of continuous amplitudes or quantum states. Pauli conjugations generate
the removed row-space signs. Independent binary rank already checked.
Any central-sector representation differs by operator signs, which leave
the squared-expectation objective unchanged; this does not make numerical
local maximization globally exact.

Positive control: published C003 G8 Pauli words and weights, all 128
sign starts with first sign fixed and uniform magnitudes, up to 160
iterations. It must recover a value above 3.03 against exact bound three.
This tests a genuine known violation, not a fabricated lower threshold.
Additional checks: the target's first tight stable set produces a joint
eigenstate attaining six; the double-weighted-atom control must not exceed
its proved bound seven under 16 frozen sign starts.

One BLAS thread. Up to two 300-second local batches to cover the 1024
starts, with deterministic resumable checkpoints. Stop between starts
at 275 seconds. Retain every completed-start value, convergence flag,
best state and expectations; a partial prefix is labeled incomplete.
Any value above 6+1e-7 triggers independent state reevaluation and an
exact/rational follow-up before any counterexample claim. No QPU, paid
compute, random sampling or automatic graph/weight mutation.

Acceptance requires independent bitwise Pauli action on the saved state,
not only reuse of dense-matrix expectations. The positive control must
pass; otherwise the run is not evidence about the target. If no violation
is found, the next gate is an exact signed operator/gear-composition
lemma, not a novelty announcement or another numerical census.

Quantum target, unrestricted H-SCF and A-star novelty remain OPEN.
