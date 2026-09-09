# C023: representation scope and closest-method audit

2026-09-09. Analytic audit, not a new optimization experiment.

## Fixed-instance corollary

Let G be the exact C014 graph, w_i=1 except w_6=w_7=2, and let
beta(G,w) be the maximum weighted sum of squared expectations over
self-adjoint unitary representations with anticommuting edges and
commuting nonedges. Then

**6 <= beta(G,w) <= 6 + 33/25600000000000.**

The upper bound applies to every such finite-dimensional representation
and every state, not just the archived seven-qubit realization.
It does NOT establish beta(G,w)=6, other weights, arbitrary SCF graphs,
approximate operator relations, or models with unconstrained nonedges.

## Attribution and transfer

[Xu, Schwonnek, Winter, PRX Quantum 5, 020318 (2024)](https://arxiv.org/html/2308.00753),
Theorems 10 and 12 and Appendix C Theorem 30, establish representation
invariance; the text explicitly includes nonnegative weights. Their
decomposition gives S_i equivalent to barS_i tensor commuting sign
operators D_i. In a common eigenbasis, expectations are mixtures
sum_k p_k s_ik a_ik. Jensen gives

    sum_i w_i (sum_k p_k s_ik a_ik)^2
      <= sum_k p_k sum_i w_i a_ik^2.

A fixed sign sector attains the standard-representation maximum.
Consequently the archived SAUR and every other SAUR of this same graph
have the same weighted maximum. This is an application of published
theory, NOT our new representation theorem.

## Our instance-specific evidence

The independent C014 verifier reconstructs the graph, checks every
operator pair against its edge set, and confirms a stable set of weighted
value six (88 such sets). Its Hermitian Pauli operators square to identity.
A simultaneous eigenstate of any such commuting stable set has squared
expectations one on that set; other nonnegative terms cannot reduce six.
This proves the lower bound without relying on the numerical state search.

The C021 certificate verifies the upper bound for the archived SAUR with
integer arithmetic. Published representation invariance transfers it to
G,w. The machine verifier deliberately retains its narrower scope label:
the transfer is an attributed mathematical argument, not a numerical test.

Both checks rerun successfully on 2026-09-09:

    python -S experiments/pauli_fourth_moment_phase0/verify_scf_two_xx_weight.py
    python -S experiments/pauli_fourth_moment_phase0/c021_exact_dual.py verify

## Method novelty gate

The same source, Appendix B.2, equations (42)-(45), already contains
the two-copy objective, PPT constraint and symmetric-support condition
F_12 gamma=gamma. Equation (46) also supplies a three-copy extension.
Thus C021's relaxation is not a new quantum-simulation primitive or a new
uncertainty framework. The rational certificate is instance-specific
evidence; its priority and significance remain unestablished.

## Consequence for further work

Do not spend another campaign on representation sectors or present a
three-copy extension as a new method. Exact-six recovery remains useful
only as a route to identifying a general proof mechanism. One exact
instance alone does not satisfy the A-star research objective.
