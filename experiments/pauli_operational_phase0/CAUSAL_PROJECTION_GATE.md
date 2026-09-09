# Causal-projection falsification registration

2026-09-09. Source: White et al., arXiv:2107.13934v7, Section 5.1,
equations (40), (46), (50), (51) and Algorithm 2.
https://arxiv.org/html/2107.13934v7

The source proposes pseudoinverse filtering to preserve positivity/rank
while imposing causality, and states a finite iteration bound d^(2k)-r.
Check this step before using it as a random-process generator. This is
not an audit of the authors' unretrieved implementation or published data.

Freeze d=2, k=1, order A=final output, B=input, C=initial output; rho is
trace one. The normalized causality condition is
Tr_A rho = I_B/2 tensor Tr_AB rho. Normalization is explicit so a missing
global d factor in unnormalized notation cannot manufacture a failure.

One iteration transcribes equation (50): M=Tr_A rho, R=Tr_AB rho,
T=(I_AB tensor sqrt(R))(I_A tensor sqrt(M)^+),
rho' = T rho T^dag / Tr(T rho T^dag).

Exact input: GHZ projector (|000>+|111>)(<000|+<111|)/2. Hypothesis to
falsify: every positive input of the selected rank is causal after at
most 3 iterations. Check a symbolic fixed-point argument separately from
floating-point eigenfilter iteration. Positive controls: I/8 and Bell_AB
projector tensor |0><0|_C, which already satisfy normalized causality.

Finite generic-input diagnostic: ten rank-one complex Ginibre vectors,
seeds 0,...,9, dimension eight. Record Frobenius causality residuals at
0,3,30,300 iterations; tolerance 1e-9, eigenvalue support cutoff 1e-12.
No parameter tuning, no large ensemble, no claim of exact floating-point
rank preservation. Wall cap 30 seconds, one numerical thread. Random
cases are diagnostic only; a singular fixed point alone does not refute
an almost-sure claim for a continuous input ensemble.

Stop and record failure if the exact fixed point is noncausal. Do not
claim that all results of the source paper fail, that its actual code
matches this transcription, or that this alone supplies A-star novelty.

## Outcome and exact argument

The transcribed normalized map fixes GHZ, with Frobenius causal residual
1/2. Both already-causal controls pass. All ten random seeds have residual
above 1e-9 after three steps (range 0.0003059482 to 0.38724994), but below
1e-9 at 30 and 300 steps. The latter observations use a support cutoff and
are not exact finite-convergence proofs. Run time: 0.156 seconds.

For an exact generalization at one time step, take d>=2 and p_j>0 summing
to one, |psi>=sum_j sqrt(p_j)|j,j,j>. Then

M_BC=sum_j p_j |jj><jj|, R_C=sum_j p_j |j><j|,
T=I_A tensor sum_j |jj><jj|.

Consequently T|psi>=|psi>: normalization changes nothing at any iteration.
However M_BC differs from I_B/d tensor R_C, with squared Frobenius defect
(1-1/d) sum_j p_j^2 > 0. Positivity, trace one and rank one hold exactly.
This is an entire structured fixed-point family, not floating-point error.
It is lower-dimensional than the continuous Ginibre ensemble, so it does
not by itself disprove almost-sure asymptotic convergence.

`verify_causal_fixed_point.py` checks the rational d=2 projectors with
amplitude ratios 1:1 and 1:2. It does not use the numerical eigensolver;
it verifies the derived diagonal filter, idempotence, trace, marginals and
exact squared residuals 1/4 and 17/50. The second ratio was selected AFTER
the initial diagnostic to illustrate the derived family, not as a new
preregistered stochastic test.

The safe conclusion is narrow: the written pseudoinverse map has noncausal
fixed points, and its claimed worst-case finite guarantee cannot be used
as our acceptance criterion. This does not invalidate the process-tensor
framework, unitary-restricted witnesses or the authors' hardware results.
No source implementation or raw experimental archive has been examined.

## Next proof/experiment obligation

Before treating this as a research contribution, check the publisher PDF,
author implementation/updates, and operator-scaling/Sinkhorn convergence
literature. Separate a correction to this stated guarantee from a genuinely
new rank-constrained causal-sampling method. Any new generator must enforce
all normalized causal constraints independently and declare its sampling
measure; merely using a known sequential Stinespring construction is not
new. A-star novelty is NOT confirmed by this counterexample.
