# C031: reuse one modular factorization for exact lifting

2026-09-09. C030's eight CRT primes did not reconstruct all rationals.
Use the SAME frozen starting vector, discovered active rows and pivot
selection. Replace repeated elimination by Dixon lifting with p=65521:
factor once; B d_k=r_k (mod p); r_(k+1)=(r_k-B d_k)/p. Accumulate digits.
At most 128 lifts and 120 seconds checked between lifts, rational recovery
every eight lifts, exact square-system substitution before original dual
checks. Save a checkpoint if incomplete. No LP or new objective. Exact
full-coordinate nonnegativity and upper six remain the sole acceptance.
The lifting algorithm is standard arithmetic, not a research novelty.

## Result: exact six, independently checked

At 40 lifts / 640 modulus bits, all rational correction coordinates were
reconstructed and substituted exactly into the 906-row square system.
The resulting FULL dual has nonnegative numerators and exact upper six.
Common denominator has 332 bits. Total discovery runtime 3.703 seconds.
The portable certificate is `results/pauli_fourth_moment_phase0/c031_exact_six_certificate.json`.
The original `c031_candidate.json` is retained as a raw-hash discovery artifact.

`verify_c031_exact_six.py` runs with Python -S and checks the frozen source
graph/Pauli relations and the saved full certificate. The existing C021
verifier checks all 16384 dual coordinates and 8256 even inequalities,
with two agreeing integer transforms and regenerated objective. Eight new
tests pass, including negative coefficient, wrong denominator, missing
symmetric support and wrong source. No floating point is used by this
standalone certificate verifier. Discovery QR support/rank is not trusted
by acceptance. The 127-test historical suite was not rerun in this turn.

## Fixed-instance theorem and proof chain

For the fixed C014 graph G and weights w_i=1 except w_6=w_7=2,

    beta(G,w) = 6.

For the archived representation, convexity of the weighted squared
expectations permits restriction to pure states. The identical two-copy
state has symmetric support; Pauli twirling preserves objective and
support and produces a Bell distribution lambda>=0, sum lambda=1,
lambda_odd=0, A lambda>=0. Here A is the Bell-coordinate partial transpose.
The exact saved certificate u satisfies u>=0 and c+A u<=6 on every even
coordinate. Consequently

    c.lambda <= (c+A u).lambda <= 6.

An independently verified stable set of weighted value six consists of
commuting Hermitian unitaries. A common eigenstate contributes six from
that set and nonnegative terms elsewhere, proving the matching lower
bound. Published weighted representation invariance transfers the result
to every finite-dimensional SAUR of G, as attributed in C023. The
commuting nonedge relations are essential to the stated scope.

## What this does not establish

This closes the fixed C014 inequality, not all weights on G, a general SCF
composition theorem, a new relaxation or quantum-simulation algorithm,
practical hardware advantage, or A-star novelty. The certificate's large
rationals are exact but not yet a conceptual general proof. Priority and
generalization remain research requirements. The manuscript/PDF predates
this result and must be updated and checked separately.

## Archive portability audit

The first clean Git archive failed the RAW source hash because Git
normalized CRLF to LF. No coefficient or mathematical inequality failed.
The portable certificate retains identical numbers and explicitly uses
LF-normalized source bytes for its SHA256; no other whitespace or content
is ignored. Legacy raw-hash mode remains unchanged. Tests cover both line
endings, altered source and unknown normalization mode. Use the portable
certificate for clean checkouts; the discovery artifact is historical.
