# Causal boundary-response kernelization: frozen Phase 0

Status: frozen before inspecting any result produced by `run_phase0.py`.

## Capability claim under test

Let a pendant Rydberg motif of `k` atoms meet an arbitrary host at one blockade
port.  The proposed capability is to replace the motif by `r = o(k)` physical
Rydberg atoms while preserving the finite-time reduced channel seen at the
port, uniformly over host graphs and without host-specific fitting.

The first necessary test is deliberately stronger than fitting a convenient
host.  Put the port in a coherent superposition and condition the motif
Hamiltonian on the port being empty or occupied.  Its port-coherence response
is

```text
g_k(t) = <empty| exp(+i H_0 t) exp(-i H_1 t) |empty>.
```

Any surrogate that preserves the boundary channel for every host and input
must preserve this scalar response.  Failure here falsifies the full claim.

## Frozen family and controls

- Motifs: endpoint-attached paths `P_k`, `k = 3,...,13`.  They are native unit
  disk graphs, pendant trees, classically reducible by boundary-conditioned
  dynamic programming, and have no twin vertices.
- Hamiltonian: hard-blockade Rydberg MIS Hamiltonian with `Omega = 1` and
  mean detuning `Delta = 0.37`.
- Two controls: uniform detuning and a frozen 3% deterministic onsite
  perturbation.  The latter removes accidental reflection/spectral
  degeneracies and tests whether a low rank is symmetry-only.
- Finite horizons: `T in {2, 5, 10, 20}` in units of `Omega^{-1}`.
- The sampled response uses 511 equally spaced points and a `256 x 256`
  Hankel matrix.
- Robust approximation tolerances: 1% and 5% relative Frobenius error of the
  response Hankel matrix.

## Structural lower bound

A time-independent surrogate with internal Hilbert dimension `D` can produce
at most `D^2` distinct frequencies in this two-branch coherence experiment.
For `r` two-level atoms, `D <= 2^r`; hence a response Hankel rank `R` implies

```text
r >= ceil(log_4 R).
```

This is an optimistic lower bound: blockade and the Aquila control algebra can
only reduce the responses available to the physical surrogate.  We report
both the resolved continuous-frequency rank and finite-horizon effective
Hankel ranks.  The numerical resolved-rank thresholds are frozen at
`1e-8`, `1e-10`, and `1e-12` relative coefficient magnitude.

## Baseline and the only promotion window

The decisive baseline is a same-budget spatial buffer: retain only the first
`r = 1,2,3` path atoms next to the port.  Locality can make this trivial
truncation sufficient at short time, in which case a learned causal surrogate
is not a new capability.

Phase 0 advances to physical-surrogate optimization only if at least one
`T in {5,10,20}` satisfies **all** of the following for `k = 13`, in both the
uniform and perturbed controls:

1. the best-rank-64 Hankel residual is at most 1% (so an arbitrary three-atom
   realization is not already ruled out by response complexity);
2. every `r <= 3` prefix buffer has at least 5% maximum time-domain error;
3. the best prefix-buffer Hankel error is at least five times the best-rank-64
   residual;
4. the window is not created by a resolved-frequency degeneracy that vanishes
   under the 3% perturbation.

The factor 64 is `4^3`, the largest scalar Hankel rank available to three
unconstrained two-level atoms in this diagnostic.

## Kill criteria

The frozen CBRK claim is rejected at Phase 0 if there is no promotion window.
We distinguish the two possible failure mechanisms:

- **locality regime:** a three-atom prefix already reaches 5% error;
- **complexity regime:** rank 64 cannot reach 1% Hankel error.

If the data cover every tested horizon by the union of those two regimes,
there is no observed interval in which a compact nonlocal response compiler is
both necessary and information-theoretically possible.  We will not rescue a
failure by changing tolerances, choosing a symmetric motif, allowing
host-specific refits, or rebranding exact linear rank as an approximate
surrogate result.

## Scope boundary

Passing this gate would not establish A-star novelty.  It would authorize the
next experiments: constrained physical-surrogate fitting, 100 held-out UDG
hosts, full low-energy distributions, `C6/r^6` tails, waveform discretization,
and an Aquila-compatible open-loop schedule.  Failing it closes the adjacent
kernelization/causal-response branch.

