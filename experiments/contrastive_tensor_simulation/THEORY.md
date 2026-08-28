# Contrastive channel identities and certified error recurrence

Let `UA(X)=U_A X U_A^dagger` and `UB(X)=U_B X U_B^dagger`. With

`M=(rho_A+rho_B)/2`, `D=(rho_B-rho_A)/2`,

`Ubar=(UA+UB)/2`, and `deltaU=(UB-UA)/2`, direct expansion gives

`M' = Ubar(M)+deltaU(D)` and `D' = deltaU(M)+Ubar(D)`.

If compression produces local trace-norm residuals `r_M,r_D`, average channels
are trace-norm contractions and

`epsilon = ||deltaU||_(1->1) <= min(1,||U_A-U_B||_infinity)`.

Therefore

`e_M' <= e_M + epsilon e_D + r_M`,

`e_D' <= e_D + epsilon e_M + r_D`.

For an observable `O`,

`|Delta_tilde-Delta| <= 2 ||O||_infinity e_D`.

The implementation audits these inequalities against exact dense evolution on
the frozen 7q pair. The bound is sufficient and may be loose. A vacuous bound
is recorded as a negative result rather than tightened after inspection.

For the final-state operator-Schmidt diagnostic, if a pure-state amplitude
matrix across a spatial cut is `X`, the reshuffled projector is
`R_rho = X kron X*`. Thus its left Gram matrix is

`(X X^dagger) kron (X X^dagger)*`.

For `M` or `D`, the corresponding Gram matrix is the signed sum of the two
self terms and the two cross terms. This permits leading operator-Schmidt
coefficients without materializing a `4^n` density matrix.
