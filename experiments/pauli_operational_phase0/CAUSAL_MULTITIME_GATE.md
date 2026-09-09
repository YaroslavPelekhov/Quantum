# Nested-tail invariant for alternating causal filters

2026-09-09, preregistered before the sweep. Previous turn made progress:
proved the one-step invariant and saved all 90 diagnostic cases.

## Generalization and proof

Order L=2k+1 legs as o_k,i_k,...,o_0. Let Q_s be the marginal on the
last s legs, and q_s its rank. For even s=2,4,...,2k an elementary update
uses M=Q_s, R=Q_(s-1) and F=(I_d tensor sqrt(R)) M^(-1/2,+), extended
by identity to the earlier legs, then normalizes the global state.

Every q_t, t=1,...,L, is invariant under every such exact update:

* t=s and t=s-1 follow from the previous one-step proof. In fact the
  support of Q_(s-1), not only its rank, is unchanged.
* t<s-1: PSD operators with the same support have partial traces with
  the same support, so all these smaller-tail supports are unchanged.
* t>s: Q_t has support contained in the first t-s legs tensor supp(M).
  F is injective on supp(M); its identity extension is injective on that
  support, so congruence preserves the rank of Q_t.

This includes global rank and holds regardless of update order. Causality
requires q_s=d*q_(s-1) for every even s. If any initial equality fails,
NO finite sequence of these filters can give exact causality. Conversely,
if all these equalities hold, one sweep s=2k,2k-2,...,2 suffices: each
selected marginal has full support relative to its remaining marginal,
and subsequent filters on deeper tails preserve already-established
identity factors. The converse is not claimed for arbitrary sweep order.

For a complex Ginibre factor of size d^L by r, q_s=min(d^(L-s)*r,d^s)
almost surely. This follows by concatenating independent Gaussian blocks
before taking their Gram matrix. For d>=2, the top equality holds iff
r>=d^(2k-1). Indeed below that threshold q_(2k)=d*r, whereas either
d*q_(2k-1)=d^3*r or d^(2k), both strictly larger. At/above the threshold
all relevant tails are full rank, so all equalities hold.

Thus the generic exact finite-termination threshold is r=d^(2k-1).
For qubits k=2,r=2 and k=3,r=8 are below it. This is not a measure-zero
statement, but still does NOT refute approximate or asymptotic convergence.
Actual author code is unretrieved. The updates here follow the nested-leg
equation-50 construction, not an assertion that printed Algorithm-2 index
notation or the author's implementation has been independently reproduced.

## Diagnostic frozen before execution

d=2; (k,r)=(2,2),(2,8),(3,8),(3,32); five seeds 0,...,4 per setting.
Both descending and ascending even-tail orders; two full sweeps each.
Forty runs, 200 elementary updates, max dimension 128. Eigensolver support
cutoff 1e-12; report numerical tail ranks at 1e-9 without treating them
as exact ranks. Save all marginal spectra and causality residuals after
every update. Log rank mismatches rather than silently changing cutoffs.
One numerical thread, 60-second cap. Require full-support descending
controls to achieve all causal residuals <1e-9 after their first sweep.
No claim about low-rank asymptotic convergence from two sweeps.

No novelty is inferred from a rank argument by itself. A useful article
would additionally require prior-art separation and consequential results
about valid process sampling or experimentally accessible memory, not just
a criticism of an exact convergence sentence.

## Results and precision audit

The 40 runs / 200 updates completed in 0.312 seconds. All ten descending
full-support controls met all constraints after one sweep; largest residual
8.257e-14. There were 38 numerical rank mismatches at the registered 1e-9
threshold. These are retained in the raw JSON, not called a passing exact
rank check. In the first mismatching case (k=2,r=2,seed=0,descending), the
three-leg marginal's smallest eigenvalue was about 8.67e-16 after update 3,
while the predicted exact rank was eight rather than the reported seven.

Post-hoc follow-up was frozen to that first case, four updates, 80 decimal
digits and support threshold 1e-60. The same double Gaussian factor was
converted to mpmath BEFORE forming the Gram matrix, avoiding double Gram
roundoff. A separate eigensolver found a strictly positive smallest value
8.47856258708416611875e-16 after update 3 and 8.09053766830995738126e-16
after update 4. This supports threshold-induced numerical rank reporting
in this selected case; it is not an exact positivity certificate and does
not independently explain all 38 mismatches. No cutoff was retuned in the
original run. Precision run completed in 0.562 seconds.

Artifacts: check_causal_multitime.py, check_causal_multitime_precision.py,
and results/pauli_operational_phase0/causal_multitime{,_precision}_20260909.json.
The mathematical proof gives the exact invariant; the experiment documents
why a floating-point rank counter cannot be used as its verifier near a
rank boundary. The observed rapid approach to that boundary is not yet a
theorem about convergence rate or a result about sampling-distribution bias.
