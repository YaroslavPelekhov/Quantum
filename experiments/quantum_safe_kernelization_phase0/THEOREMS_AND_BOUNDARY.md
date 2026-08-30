# Structural results and claim boundary

Let `G` contain a leaf `v` with unique neighbour `u`.  The standard exact MIS
leaf reduction removes `{u,v}`, adds one to the optimum, and lifts a reduced
independent set `S` to `S union {v}`.  Let `L` denote this static lift and
`P = LL*` its image in the hard-blockade Hilbert space.

## Proposition 1: initial-state obstruction

For the standard negative-detuning start, `Omega(0)=0` and `Delta(0)<0`, the
unique ground state of the original Hamiltonian is the empty set.  Every vector
in `range(P)` has `v` occupied.  Therefore the original initial ground-state
projector and every projector supported in `range(P)` have operator-norm
distance one.

Consequently no static forced-selection lift can preserve the full standard
Rydberg annealing path with projector error below one.  This statement is
independent of graph size and numerical precision.

## Proposition 2: endpoint ground-space obstruction

The leaf rule guarantees that every reduced optimum lifts to an original
optimum, but it need not be surjective onto all original optima.  If an original
maximum independent set outside `range(P)` exists, the full original endpoint
ground projector contains a vector orthogonal to the lifted endpoint ground
space.  Their operator-norm distance is again one.

In the exhaustive screen this obstruction occurs in 210 of 793 oriented leaf
reductions.  Optimisation-value preservation is therefore strictly weaker than
ground-space simulation even at the classical endpoint.

## Proposition 3: exact finite-driver leakage

For any basis state `|S union {v}>` in `range(P)`, the transverse driver has the
allowed transition

```text
|S union {v}> -> |S>
```

with amplitude `-Omega/2`.  These target states are distinct and lie in the
orthogonal complement of `range(P)`.  All other single flips from a lifted
basis state either remain in `range(P)` or are blockade-forbidden.  Hence

```text
|| (I-P) H P || = |Omega| / 2.
```

Thus the static lifted sector is never invariant at finite nonzero drive.  A
P/Q or Feshbach argument can only make the reduction approximate by comparing
this fixed coupling with an energetic separation; it cannot certify exact
whole-path equivalence.

## Local endpoint condition and why it is insufficient

If `u` has at least two leaf neighbours, selecting `u` can be improved by
replacing it with all those leaves.  Every such leaf is therefore present in
every maximum independent set.  The experiment exhaustively confirms that
this local condition removes the endpoint-surjectivity obstruction.

It does not remove Proposition 1 or Proposition 3.  The only exact dynamical
rules found are disconnected-factorisation cases, which the preregistration
declared trivial.  A late-schedule condition `|Omega| << Delta` is ordinary
adiabatic elimination and also fails the frozen requirement for a nontrivial
whole-path rule.

## Novelty boundary

These propositions are useful diagnostics, but they are elementary
specialisations of established low-energy simulation and block-perturbation
ideas.  They are not presented as new A*-level theorems.  A future positive
claim would need a nontrivial hardware-realizable transformation that preserves
a precisely stated finite-time task, not merely a classical optimum, endpoint
energy, or asymptotically vanishing-driver limit.
