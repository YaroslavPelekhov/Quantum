# Frozen low-bond Signed Decision-COT protocol

Locked on 2026-08-21 before executing any new residual witness at bond 32, 64,
or 96.

## Design/held-out boundary

The signed recentering was derived after inspecting the already completed
adaptive-primary R128/R256/R512 `ibm32` artifacts.  The R128 result is therefore
a retrospective design result.  The new low-bond ladder `{32,64,96}` is frozen
before execution, and all failures must be retained.

The adaptive primary schedule and forward `confirm` trajectories remain fixed:

`1-319:512, 320-383:384, 384-447:256, 448-511:128, 512-555:64`.

For each ordering and both `published_lr` and `prior_matched_random`, run fixed
residual bonds `{32,64,96,128}`.  R128 is repeated only as a regression anchor.
The signed first-term centers are reused from the frozen COT artifacts.

## Prespecified tests

1. Primary low-bond test: determine whether any bond below 128 gives a strict
   signed decision-gap interval on `ibm32/sorted`.
2. Transfer test: apply the same ladder without retuning to spectral ordering.
3. Regression: repeated R128 corrections must match the archived R128 values to
   `1e-10` absolute error.
4. Soundness audit: the exact gap, excluded from construction, must lie inside
   every reported interval; all dense residual/operator audits must pass.
5. Comparison: report the old absolute-sum COT verdict beside the signed verdict
   for every bond.
6. Asymmetric allocation: after the sorted ladder is complete, enumerate the
   Cartesian product of LR and matched-random bonds and select the strict
   certificate with minimum paired cubic work.  Ties are broken by smaller
   maximum bond, then smaller bond sum, then lexicographically `(LR,MR)`.
   Transfer that selected pair unchanged to spectral ordering.  Spectral rows
   cannot influence the sorted selection.

Resource cost is the paired fixed-bond cubic proxy `(R/256)^3`, normalized so
R256/R256 equals one.  Success at R96, R64, or R32 corresponds respectively to
94.73%, 98.44%, or 99.80% nominal savings.  Failure at all three bonds is a
valid measured threshold result.

## Leakage controls

Exact BKS values and dense exact backward vectors are audit-only.  They cannot
select a bond, alter an interval, or change the frozen ladder.  The certificate
uses only the MPS gap, compressed signed centers, certified forward radii,
residual enclosures, and explicit numerical allowances.
