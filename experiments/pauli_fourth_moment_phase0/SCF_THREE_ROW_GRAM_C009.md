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

The candidate passes. Independent acceptance recomputes the three even
coefficients (12,39,21 monomials), the constant, every odd coefficient and
all five central involutions. It computes e2 through squared 2-by-2 minors
of B and e3 as det(B)^2, instead of discovery's principal minors and det(M).
The graph is independently decoded from graph6. Both calculations retain
actual universal words, so no nonexistent independent sector assignments
are introduced. C008's complete 36-facet rational hull is rechecked.

## Analytic implication: a conditional Gram bound

The following sufficient condition is reusable, but is a repackaging of
the existing C005 envelope, not a claimed new free-fermion theorem.
Suppose an SCF Hamiltonian has alpha<=3 and in each sector its squared
single-particle energies have elementary coefficients e1,e2,e3 satisfying

`e1=L+H, e2<=e2(M)+H*lambda_max(M), e3=det(M)`,

where M is a real positive semidefinite 3-by-3 matrix with trace L, and
L,H are sums of squared light/heavy amplitudes. Zero modes may pad the
three slots. Then its Pauli uncertainty bound for weights one on lights
and two on heavies is at most three.

Proof: use half these weights and the standard variational identity
`beta(w)=sup_{sum a_i^2/w_i=1} ||sum a_i P_i||^2`.
Thus 2L+H=1, 0<=L<=1/2, e1=1-L. Write the eigenvalues of M as x,y,z>=0,
with y largest. For fixed L,y the expression

`xy+xz+yz+(1-2L)y+2 sqrt((3/2)xyz)`

is increasing in xz. Set x=z=(L-y)/2, y=s^2/6. Its difference from
`(1/4+L/2)^2` is the nonnegative polynomial
`(s-1)^2*(12L+s^2+6s+3)/48`.

For sector energies nu_i>=0 let S=sum nu_i and
`f(t)=((t^2-e1)/2)^2-e2-2t sqrt(e3)`.
The elementary symmetric identities imply f(S)=0. The envelope implies
f(sqrt(3/2))>=0. For t>=sqrt(3/2),
`f'(t)=t*(t^2-e1)-2sqrt(e3)>0`, since e1<=1 and
e3<= (L/3)^3<=1/216. Hence S<=sqrt(3/2). CEM's SCF sector spectrum
gives the Hamiltonian norm at most S, proving beta<=3/2 for the halved
weights and <=3 for the original weights. No equality between all
abstract sector assignments and physical sectors is needed for an upper
bound. Zero amplitudes and repeated roots follow by continuity; arbitrary
real amplitude signs are allowed throughout the polynomial identities.

## Application and all-weight closure of the fixed target

The five verified central Hermitian involutions can be simultaneously
diagonalized, and their values make B real in every physical sector.
M=B B^T is positive semidefinite with trace L. The r0,r1 term is a
Rayleigh form on a principal submatrix of M. The rc term is a column norm
of B, bounded by lambda_max(B^T B)=lambda_max(M). Their sum is at most
H lambda_max(M), so all conditions above hold.

Consequently the sole remaining full facet is quantum-valid:
`sum_(i=0)^8 <P_i>^2 + 2 sum_(i=9)^11 <P_i>^2 <=3`.
The commuting pair A0,H0 has total weight three. A joint eigenstate
attains at least three, and the upper bound therefore makes it exact.

C008 independently verifies that the target's complete STAB hull has
12 nonnegative-coordinate facets, 20 rank facets and three alpha<=2
support facets, besides this full facet. The prior SCF rank/alpha-two
theorems cover those 23 positive rows. Thus every squared expectation
profile is in STAB(G), giving beta(G,w)<=alpha(G,w) for ALL w>=0.
A simultaneous eigenstate for a maximum-weight commuting stable set
gives the reverse inequality. This proves all-weight perfection of this
fixed graph and, by known heredity, its induced subgraphs.

This does NOT establish the general weighted SCF conjecture, all-column
three-row closure, priority or A-star significance. External review is
pending. The C008 discovery artifact retains its historically correct
"unresolved" flags; C009 supplies the subsequent proof.

## Reproduction

`python -S run_scf_three_row_gram.py` regenerates the artifact from this
directory. `python -S verify_scf_three_row_gram.py` independently checks it
and the complete C008 hull. Run `python -S -m unittest discover -s . -p
test_scf_three_row_gram.py -v` for nine tests including corrupt phase,
coefficient, graph, odd-check and scope rejection.

Artifact: `results/pauli_fourth_moment_phase0/scf_three_row_gram_c009.json`.
Canonical LF SHA-256:
`34b89211fd99fbc77819c1ad68734425a3d96effae89d477d7289e55071ea2db`.

Clean-source reproduction of commit `cd89705` regenerated the same hash.
The independent standard-library verifier, all 57 bundle hashes and all
87 SCF tests passed in the fresh archive (27.980 seconds for the suite).
This is same-host reproduction, not external mathematical review.
