# Frozen contrastive tensor simulation protocol

Frozen before running any contrastive compression outcomes.

## Question

Can a comparison-native representation certify or estimate

`Delta = p_B - p_A`

more efficiently than two independently compressed state trajectories?

Here `A = published_lr`, `B = prior_matched_random`, and `O` is the frozen BKS
projector. The immutable sorted and spectral QPY circuits, exact statevectors,
scorers, and hashes are inherited from the RankCert manifests.

## Exact object

For density operators `rho_A,rho_B`, define

`M=(rho_A+rho_B)/2`, `D=(rho_B-rho_A)/2`.

For paired channels `U_A,U_B`, define their average and half-difference. The
runner must verify gate by gate that

`M' = Ubar(M) + deltaU(D)` and `D' = deltaU(M) + Ubar(D)`,

and that `Delta = 2 Tr(O D_T)`.

## Frozen experiment tiers

1. **Full operator prototype.** Use the real 7-qubit `chesapeake` LR/MR pair
   on both orderings. Verify exact M/D dynamics. Compress the operator tensors
   after every paired gate with `(M bond,D bond)` in
   `(4,4),(2,8),(4,8),(4,16)`. Propagate a trace-norm certificate using the
   exact local compression residual and
   `epsilon_t <= min(1, ||U_A-U_B||_infinity)`.
2. **Structural diagnostics.** On `ibm32` (18q) and
   `aves-sparrow-social` (24q), compare state, diagonal probability, mean, and
   signed-contrast Schmidt spectra at cuts `3,5,7,floor(n/2)`. Compare the full
   operator spectra of `rho_A,rho_B,M,D` at cuts `3,5,7`; only the leading 32
   coefficients are required for the full operators.
3. **Equal-budget target benchmark.** TT-SVD-compress the two exact statevectors
   independently at bonds `4,8,16,32,64`. Compress the exact signed diagonal
   contrast `q(z)=|psi_B(z)|^2-|psi_A(z)|^2` at the largest integer bond whose
   canonical TT parameter count does not exceed the combined parameter count
   of the two state MPS representations. Compare absolute error in Delta and
   ranking sign on both orderings.

The diagonal contrast is an observable-specific surrogate for the diagonal of
`2D`; it is not presented as a completed full-density contrastive simulator.

## Resource accounting

- Primary equal-budget measure: complex/scalar TT parameter count.
- Secondary measures: maximum TT bond, wall time, retained norm/fidelity for
  the separate states, and captured Frobenius energy for spectra.
- Exact values are used for audit and compression evaluation, never to alter
  the frozen bond ladder or success thresholds.

## Kill criteria

The strong branch survives only if all of the following hold:

1. On `aves`, contrastive Delta error is at least `2x` smaller than separate
   MPS at one or more equal budgets on **both** orderings.
2. At a budget where separate MPS gives the wrong sign on `aves`, the
   contrastive representation gives the correct sign on both orderings. If no
   frozen tested separate budget has the wrong sign, this condition is marked
   `not_testable`, not passed.
3. Full-operator `D` has lower 99%-energy effective rank than both individual
   projectors at a majority of the frozen operator cuts across ibm32 and aves.
4. At least one full 7q M/D run has a non-vacuous certified interval for Delta.

Failure of any required, testable item closes the claim of a general
contrastive density-operator simulator. A diagonal-only improvement may be
reported as a narrower observable-specific result, but cannot rescue the full
claim.

## No post-hoc changes

Cases, methods, orderings, cuts, bonds, budgets, and thresholds above are
frozen. Failures and resource disadvantages are retained.
