# Structural statements and the final novelty boundary

## 1. Stationary conditional-coherence rank

Let a retained two-level port condition an eliminated motif Hamiltonian to
`H_0` or `H_1`, and let the motif start in `|e>`.  For time-independent
Hamiltonians,

```text
g(t) = <e| exp(+i H_0 t) exp(-i H_1 t) |e>
     = sum_(a,b) c_(a,b) exp(i (E^0_a-E^1_b)t).
```

After combining identical frequencies and removing zero coefficients, let `R`
be the number of active frequencies.  On a non-aliasing time grid the ordinary
Hankel rank of `g` is `R`.

An `r`-atom surrogate has Hilbert dimension at most `2^r`; the two-branch
coherence has at most `4^r` frequency pairs.  Therefore any exact surrogate
obeys

```text
r >= ceil(log_4 R).
```

This is deliberately optimistic: blockade and a restricted control algebra can
only decrease the physically realizable response set.

For the endpoint path family, the numerical resolved-rank lower bound grows
linearly: fitted slopes are `0.61818 atoms/motif atom` in the uniform control
and `0.70000` after a 3% symmetry-breaking perturbation.  At `k=13`, the
resolved ranks at relative coefficient threshold `1e-10` are 61,155 and
218,525, implying exact lower bounds of 8 and 9 atoms.  These numerical counts
are not presented as a symbolic generic-rank theorem.

## 2. Finite-horizon rank is only a possibility result

For a sampled Hankel matrix with singular values `sigma_1 >= ...`, the
Eckart--Young tail

```text
sqrt(sum_(j>q) sigma_j^2) / sqrt(sum_j sigma_j^2)
```

is the best unconstrained rank-`q` Frobenius residual.  A three-atom
conditional-coherence response has rank at most 64.  Consequently a large
rank-64 tail rules out three atoms, but a small tail does **not** construct a
physical three-atom Hamiltonian.

Here the finite-horizon 1% effective ranks for `k=13` are 2, 3, and 5 at
`T=5,10,20`, in both controls.  They remain identical when the Hankel grid is
doubled from 256 to 512.  This was a real finite-time low-rank opening, not a
discretization artifact.  The physical-realization gates were therefore
necessary.

## 3. Boundary-word Gram theorem

Fix an initial motif state and split the evolution into time bins.  For every
binary port history `w`, let `|psi_w>` be the motif vector obtained by applying
the corresponding conditional propagators and, in the hard-blockade model,
the required occupied-port projectors.  Define

```text
G[w,v] = <psi_w|psi_v>.
```

**Claim (within the frozen port-history model).**  Equality of all such Gram
kernels for target and surrogate is necessary and sufficient for equality of
the retained port process under arbitrary coherent controls built from these
histories.

Proof sketch:

1. Expanding any controlled retained-system trajectory over computational-port
   histories gives a joint state `sum_w a_w |host_w>|psi_w>`.
2. Tracing out the motif leaves coefficients
   `a_w conjugate(a_v) G[v,w]`.  Equal Gram kernels therefore give equal
   retained states for every set of history amplitudes; this proves
   sufficiency.
3. If one Gram entry differs, a coherent two-history interferometer supported
   on those histories has an off-diagonal retained matrix element proportional
   to that entry.  It distinguishes target and surrogate; this proves
   necessity.

The registered scalar response `g(t)` is only an off-diagonal element of the
one-bin, no-switch Gram kernel.  Matching it is necessary but cannot establish
host-universal process equivalence.

## 4. What the final experiment proves

The fitted four-atom model matches the one-bin uniform response 10.32 times
better than the inherited four-atom prefix.  Once the history switches, the
uniform improvements are only 3.24--4.05 times for equal-bin word lengths
`K=2,...,6`.  An exhaustive 99-split two-bin scan finds maximum Gram error
`0.0208879` at `tau=3.10` and only `2.963x` improvement.  This violates the
frozen 2%/5x process gate.

The perturbed control passes, but the claim required both controls and broad
prior art already covers fitted finite bath terminations and reduced-order
boundary models.  The result is therefore a useful schedule-specific physical
approximation, not a new host-universal quantum-simulation primitive.

