# Copy-correlation gate: target definition before experiments

2026-09-09. Status: generic proposed capability rejected before a large run.
This note is an assumption audit, not a new theorem claim or new main
contribution. Existing IID campaign results are not invalidated.

## Exact obstruction and distinction

Let F(rho)=Tr(rho X)^2+Tr(rho Z)^2 and Q=X tensor X+Z tensor Z.
For rho tensor rho, Tr(Q rho tensor rho)=F(rho). For a correlated pair
Omega this identity need not hold with either reduced state of Omega.

Consider three exact two-qubit states, all with marginal I/2:

1. Independent I/2 tensor I/2: E Q=0 and F(I/2)=0.
2. Classical mixture (|00><00|+|11><11|)/2: E Q=1, F(I/2)=0.
3. Bell projector |Phi+><Phi+|: E Q=2, F(I/2)=0.

The third value exceeds the one-qubit uncertainty bound one. This is
inter-copy entanglement, not an allowed one-copy state violating uncertainty.
The classical case biases the estimated marginal functional but does NOT
violate the bound. These two failure modes must not be conflated.

More generally, if sum w_i <P_i>_rho^2 <= B for every state, w_i>=0, then
for every inter-copy separable Omega=sum p_k rho_k tensor sigma_k,

|Tr(Q Omega)| <= sum p_k sqrt(F(rho_k) F(sigma_k)) <= B.

This is just weighted Cauchy-Schwarz and convexity. It is not a new
graph theorem or a general test of independence. Measurement of Q can
retain this separable bound without estimating the unconditional marginal F.

## Uniform unconditional-marginal estimation is impossible

For any N, take R0=|0><0|^tensorN, R1=|1><1|^tensorN and
Rmix=(R0+R1)/2. All are permutation invariant; random pairing cannot
remove the common latent bit. The single-system F values are 1,1,0.

Suppose one protocol, including arbitrary coherent/adaptive measurements,
estimates that unconditional marginal F with error epsilon<1/2 and
failure probability delta<1/2 for all three states. Let A be the event
that its estimate lies within epsilon of one. Correctness on R0 and R1
requires Pr(A|R0),Pr(A|R1)>=1-delta. Linearity of outcome probabilities
gives Pr(A|Rmix)>=1-delta. Correctness on Rmix requires Pr(A|Rmix)<=delta
because the error intervals around zero and one are disjoint. Contradiction.
The argument also covers randomized pairing as part of the protocol.

This does NOT preclude learning the conditional unmeasured state, imposing
a mixing assumption, or using independently reset batches. Those change
the estimand or access model and must be specified explicitly.

## Prior-art collision

Fawzi, Kueng, Markham and Oufkir, *Learning properties of quantum states
without the IID assumption* (2024), Results / Evaluating a learning
algorithm, explicitly use the conditional post-measurement test system.
They explain why the unconditional marginal alternative is unachievable
using the common-latent-state obstruction. Their Theorems 1 and 3 give
general non-IID transformations under their success criterion. Our simple
quadratic specialization is not new; it does not refute their result.
[Primary full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC11549401/).

Filip's 2002 work already distinguishes overlap/purity measurement on
uncorrelated inputs from an entanglement-witness interpretation for
correlated inputs. Only its primary abstract was checked here, not its
complete construction. [Primary source](https://arxiv.org/abs/quant-ph/0108119).

## Frozen verification and next admissible question

Before execution, freeze exactly the three 4x4 rational states above and
Q. Verify trace and reduced states, positive projectors/diagonal mixture,
and exact expectations using Fraction arithmetic. No random search, no
new optimizer, no large campaign; this is a reproducible control fixture.
The finite check illustrates, but does not prove, the arbitrary-N argument.

Executed `python -S experiments/pauli_operational_phase0/check_copy_correlation.py`:
all rational controls pass, with pair expectations 0,1,2 and marginal
functional zero in all cases. No floating-point tolerance is used.

No claim of novel "IID-free Bell estimation of unconditional squares" may
proceed. A later capability proposal must name its conditional target or
quantitative mixing/reset resource, then compare against the existing
non-IID transformations. Merely adding random pairing or a drift parameter
does not establish a new algorithm. Main article novelty remains open.
