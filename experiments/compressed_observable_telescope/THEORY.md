# Certified Compressed Observable Telescope

For checkpoint transition `t`, let `Delta rho_t` be the difference between the
actual normalized MPS state after the transition and the exact unitary image of
the preceding approximate state. Let `O_t` be the exact backward BKS projector
and `O_t_tilde` its compressed approximation.

The exact observable telescope is

`p_MPS - p_exact = sum_t Tr(O_t Delta rho_t)`.

If `eta_t >= ||O_t-O_t_tilde||_infinity`, Holder duality gives

`|Tr(O_t Delta rho_t)| <= |Tr(O_t_tilde Delta rho_t)| + eta_t ||Delta rho_t||_1`.

For one normalized Schmidt truncation with discarded weight `w`, the trace norm
between pre- and post-truncation pure-state projectors is `2 sqrt(w)`. A logical
Aer gate can contain several internal swap/SVD truncations. Therefore this pilot
does **not** substitute one printed Aer value for the whole gate. It defines

`A_t = min(pi/2, sum_j asin(sqrt(w_tj_upper)))`,

`w_t_effective = sin(A_t)^2`,

so the accumulated-angle triangle inequality gives

`||Delta rho_t||_1 <= 2 sqrt(w_t_effective)`.

In the floating-point implementation, `1e-7` is added to each grouped trace-norm
radius, matching the independently calibrated RankCert numerical floor. The
reported effective `w_t` includes this explicit numerical inflation.

The backward BKS projector has rank `r`. Each exact backward basis vector is
approximated by a normalized TT-SVD MPS. If its accumulated compression angle is
`B_kt`, then

`|| |v_kt><v_kt| - |v_kt_tilde><v_kt_tilde| ||_infinity <= sin(B_kt)`.

Consequently a valid computable operator bound is

`eta_t = sum_k sin(B_kt)`.

Combining the inequalities proves the proposed certificate

`sum_t (|Tr(O_t_tilde Delta rho_t)| + 2 sqrt(w_t_effective) eta_t)`.

The dense 18q implementation is initially retained only as an oracle for
validating every local inequality. A later scalable implementation must apply
inverse gates and contract forward differences directly in MPS/MPO form.

## Residual-aware replacement for accumulated angles

Let `v_t` be an exact normalized backward basis vector and `z_t` its normalized
primary TT approximation. With `U_t` denoting the checkpoint segment, define

`c_t = U_t^dagger z_(t+1) - z_t`,

`r_t = v_t-z_t = U_t^dagger r_(t+1) + c_t`.

Rather than adding the norms of all `c_t`, retain a TT approximation `rhat_t`
to their coherently propagated sum. If

`rhat_t = TT_R(U_t^dagger rhat_(t+1) + c_t)`

and TT-SVD certifies local Euclidean error `delta_t`, set

`xi_t = xi_(t+1) + delta_t`.

Induction, unitarity, and the triangle inequality give

`||r_t-rhat_t||_2 <= xi_t`, hence

`||r_t||_2 <= ||rhat_t||_2 + xi_t`.

For phase-aligned normalized vectors,

`|| |v_t><v_t| - |z_t><z_t| ||_infinity <= min(1, ||v_t-z_t||_2)`.

For the rank-`r` BKS observable this yields the certified enclosure

`eta_t = sum_k min(1, ||rhat_(k,t)||_2 + xi_(k,t))`.

The unnormalized TT-SVD routine uses the standard bound
`delta_t = sqrt(sum_j discarded_singular_value_tail_j^2)`. This recurrence
retains cancellation among local errors instead of treating every compression
as adversarially aligned.

## Depth-adaptive ibm32 construction

The successful frozen schedule assigns primary backward bonds by checkpoint:

| Checkpoint positions | Primary bond |
|---:|---:|
| 512-555 | 64 |
| 448-511 | 128 |
| 384-447 | 256 |
| 320-383 | 384 |
| 1-319 | 512 (exact maximum central rank for 18 qubits) |

The residual witness is independently compressed. Bond 256 certifies the
paired comparison; bond 128 does not. Dense exact vectors are used only to
audit the inequalities, never to construct `eta_t`.

The identical schedule was then frozen before use on the spectral qubit
ordering. Its prespecified residual-bond-256 endpoint also certifies, and in
that held-out ordering bond 128 is already sufficient. This is ordering-level,
not graph-level, validation.

All statements above are exact-arithmetic inequalities. The implementation
adds a `1e-10` Euclidean-norm allowance per residual vector and checkpoint and
audits every selected depth against dense vectors. This is a documented
floating-point assumption, not an interval-arithmetic or formally verified
rounding proof.

## References

- I. V. Oseledets, “Tensor-Train Decomposition,” *SIAM Journal on Scientific
  Computing* 33(5), 2011. <https://doi.org/10.1137/090752286>
- U. Schollwöck, “The density-matrix renormalization group in the age of matrix
  product states,” *Annals of Physics* 326, 2011.
  <https://doi.org/10.1016/j.aop.2010.09.012>
