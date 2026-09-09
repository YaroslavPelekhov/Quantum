# Finite-iteration obstruction beyond diagonal states

2026-09-09. Candidate elementary theorem about the normalized one-step
equation-50 map. Not a novelty claim. This file is registered before the
new dimension/rank sweep; the proof was derived from the earlier results.

## Statement

For a nonzero PSD state rho_ABC define M=Tr_A rho, R=Tr_B M, and
S=supp(R). Write b=dim(B), K=I_B tensor sqrt(R), Pi=supp(M), and
T=I_A tensor (K M^(-1/2,+)). The normalized update is T rho T*/Z.
For every finite exact iteration:

1. rank(rho), rank(M), and supp(R) are preserved.
2. The updated state is causal, M'=I_B/b tensor R', if and only if
   rank(M)=b rank(R). If this equality holds, one update suffices.
3. Therefore an initial strict deficit rank(M)<b rank(R) prevents exact
   causality at EVERY finite iteration, not only the proposed finite bound.

This applies to arbitrary noncommuting states. It makes no assertion of
asymptotic convergence, rates, or the numerical cutoff implementation.
It concerns repeated one-step filtering, not a proof about all alternating
multi-time passes in Algorithm 2.

## Proof

Positivity gives supp(M) contained in B tensor S and supp(rho) contained
in A tensor supp(M). Moreover D=Tr_B Pi has support exactly S: positive
operators M and Pi have the same kernel, and their partial traces have
the same kernel by the sum-of-positive-quadratic-forms identity.

Taking the output trace after filtering gives M'=K Pi K/Z and
R'=sqrt(R) D sqrt(R)/Z. Both R and D are positive definite on S, so R'
has support S. K is invertible on B tensor S, so rank(M')=rank(M).
M^(-1/2,+) is injective on supp(M), and K is injective there as well;
hence T is injective on supp(rho), proving preservation of rank(rho).

Necessity in (2) follows immediately from rank(M')=rank(M) and
rank(I_B/b tensor R')=b rank(R). For sufficiency, equality and the support
inclusion imply Pi=I_B tensor P_S. Thus K Pi K=I_B tensor R, Z=b, and
R'=R. Induction proves the finite-iteration statement.

## Generic one-step inputs and interpretation

For A,B,C each dimension d, a rank-r Ginibre state has almost surely
rank(M)=min(d*r,d^2) and rank(R)=d. One can see this by concatenating the
d output blocks of the Ginibre factor for M, and all d^2 blocks for R;
these are rectangular Gaussian matrices with maximal rank almost surely.
Thus for r<d there is almost surely no exact finite convergence; for
r>=d one update satisfies the single causal constraint almost surely.

In particular, d=2,r=2 (one of the publisher's one-step sampling settings)
is generically in the successful regime. Our special diagonal rank-two
failure does NOT imply generic failure there. The earlier rank-one
three-step failures are not merely a rare fixed-point phenomenon.

For any causal rho with dim(A)=dim(B)=d, the standard partial-trace rank
inequality also gives rank(R)<=rank(rho). Hence a rank-one causal rho
has pure R and factors as a maximally entangled pure AB state tensor a
pure C state. A generic rank-one input starts with rank(R)=d, so a
convergent causal limit must approach a marginal-rank boundary. This
explains why numerical near-causality is not evidence of exact finite
termination. No contradiction with approximate convergence is claimed.

## Frozen diagnostic

Before running: d=2,3,4; r=1,...,d; ten independent complex Ginibre seeds
0,...,9 per (d,r), one update per input. Record ranks and spectra of rho,
M,R and residual before/after. Check the proof predictions with cutoff
1e-10; mathematical claims rely on the proof, not numerical ranks.
Use independent marginal contractions for the residual cross-check.
Ninety inputs, at most dimension 64, one thread, 60-second cap. No tuning
or ensemble inference from numerical near-zero residuals. Include one
already-causal rank-one positive control. Preserve all rows in a new JSON.

## Remaining gate

Priority is not established. The proof uses standard PSD support facts;
generic rank obstructions alone should not be marketed as A-star novelty.
Need to audit the actual sampler and determine consequences for its
multi-time sampling distribution. Do not infer invalid hardware data.

## Observed outcome

The frozen 90-input diagnostic passed, with one additional causal control.
All three ranks matched the predicted values before and after the update.
The 30 r=d cases had maximum causal residual 1.8936e-14. All 60 r<d cases
remained noncausal, with residuals from 0.125311 to 0.516817. Runtime was
0.047 seconds. Full spectra and all inputs' identifiers are stored in
`results/pauli_operational_phase0/causal_rank_invariant_20260909.json`.
No optimization, parameter change, or rerun selection was used.

The general proof, rather than these one-step numerical checks, rules out
finite repair in the deficient case. Importantly, the earlier observation
of near-zero residual by 30 cutoff-based iterations does not contradict
this theorem and must not be described as exact finite convergence.
No distributional bias magnitude or failure of the actual author code
has yet been measured. Targeted public searches for the title/author and
sampler with GitHub/code did not locate a verified implementation; search
absence is not a statement that no implementation exists.
