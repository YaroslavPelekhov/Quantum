# Signed reduced-density truncation

Let two pure states be split as `L|R` and define the signed reduced density

`Gamma_L = Tr_R(|psi_B><psi_B| - |psi_A><psi_A|)`.

For every Hermitian observable supported on `L`,

`Delta(O_L) = Tr(O_L Gamma_L)`.

If `Gamma_L = sum_i lambda_i |u_i><u_i|`, with the eigenvalues ordered by
decreasing absolute value, define

`Gamma_L^(k) = sum_{i<=k} lambda_i |u_i><u_i|`.

## Theorem 1: minimax signed truncation

`Gamma_L^(k)` is a best rank-`k` approximation to `Gamma_L` in trace norm and

`||Gamma_L-Gamma_L^(k)||_1 = sum_{i>k} |lambda_i|`.

Consequently, simultaneously for every `||O_L||_infinity <= 1`,

`|Tr[O_L(Gamma_L-Gamma_L^(k))]| <= sum_{i>k}|lambda_i|`.

The bound is sharp: the sign of the residual is a norm-one observable that
attains equality.  This follows from the Eckart--Young--Mirsky theorem for
unitarily invariant norms and trace/operator-norm duality.

The formal distinction from state-averaged DMRG is that the basis is chosen
from an indefinite contrast operator and eigenmodes are ranked by `|lambda|`.
State averaging instead diagonalizes the positive operator
`(rho_A+rho_B)/2` and optimizes average state fidelity.  This distinction does
not imply a generic speedup: the positive average can select the same modes,
and any claimed advantage must be established empirically or under additional
assumptions.

## Theorem 2: exponential rank separation

Let each side have dimension `D=2^m`.  Use `D-2` Schmidt pairs for an identical
maximally entangled component of weight `1-epsilon`.  Put the remaining weight
`epsilon` on Schmidt pair `D-2` for state A and on pair `D-1` for state B.
Then both states require `Theta(D)=2^Theta(m)` Schmidt rank for any fixed
fidelity above `epsilon`, while

`Gamma_L = epsilon(|D-1><D-1| - |D-2><D-2|)`

has exact rank two.  The norm-one witness
`O=|D-1><D-1|-|D-2><D-2|` has constant contrast `2 epsilon`.

Thus local comparison complexity can be constant even when fidelity-based
representation of either state requires exponential bond dimension.  This is
a separation from representing both states faithfully, not automatically a
separation from every multi-state or observable-specific method.

## Scope

The theorem applies to all observables contained on one side of the selected
cut.  It does not by itself give a scalable algorithm for the global BKS
projector used in the QAOA ranking experiment.  Extending the signed minimax
principle to a sequence of target-aware environments is the remaining
algorithmic question.
