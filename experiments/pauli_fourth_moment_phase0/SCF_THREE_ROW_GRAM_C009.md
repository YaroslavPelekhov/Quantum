# C009: fixed three-row operator gate

Registered 2026-09-08, before calculation. Source target: C008 graph6
`K{S{aSfF~Fln`, row-major cells (r,c), 0<=r,c<=2, then H0,H1,Hc.
Only this target is frozen; no enlarged census or numerical optimization.

Candidate: K_j=-H0 H1 A_j B_j, Lambda_0=I,
Lambda_j=-A_0 C_0 A_j C_j (j=1,2). Set B rows to
(a_j), (K_j b_j), (Lambda_j c_j), and M=B B^T.
Test centrality against ALL 12 generators, Hermiticity, involution and
mutual commutation before treating signs as sector scalars.

With independent-set charges Q_k=sum_{|S|=k} product_{i in S}(a_i P_i),
expand T(u)T(-u) in the universal algebra. Require constant 1, zero
coefficients in degrees 1,3,5, and alternating even coefficients
e1=tr(M)+r0^2+r1^2+rc^2,
e2=e2(M)+(r0,r1)M[0:2,0:2](r0,r1)^T+rc^2 sum_i B[i,0]^2,
e3=det(M).

Discovery uses inversion parity; acceptance uses adjacent-letter rewriting
and exact integer amplitude polynomials. No sector signs are assumed
independent. Freeze five-minute CPU-scale wall limit per script and no
randomness. Stop the candidate on any failed centrality or coefficient,
retaining a canonical monomial witness; this refutes the identity only,
not weighted SCF. Positive acceptance additionally needs the C005 scalar
envelope, correct spectral branch, attainment and C008 facet completeness.
Controls: generator anticommutation, altered sign/coefficient rejection,
and the already accepted C005 bridge. No finite audit implies general SCF.

Prior art: [Chapman--Elman--Mann, Theorem 2 and Lemma 11](https://arxiv.org/html/2305.15625)
give the SCF sector spectrum and transfer framework. They do not by
themselves supply this candidate weighted Gram estimate. The known C005
envelope, Rayleigh principle and determinant identities are reused tools.
The separate [novelty audit](NOVELTY_AUDIT_20260907.md) remains provisional.
No new free-fermion construction or confirmed A-star claim is intended.

## Outcome

Pending.
