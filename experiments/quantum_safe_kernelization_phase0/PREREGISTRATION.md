# Quantum-safe MIS kernelization: frozen Phase 0

Frozen before inspecting numerical outcomes on 2026-08-30.

## Question

Can an exact classical MIS reduction change the closed-system Rydberg annealing
dynamics enough to require a genuinely quantum-aware reduction criterion?

This phase is a falsification screen, not a novelty claim.  The older QAOA/MPS
and hardware-witness branches remain closed.

## Hamiltonian and schedule

We use the ideal hard-blockade Hamiltonian in the independent-set basis,

\[
H_G(s)=-\frac{\Omega(s)}2\sum_i P_G X_i P_G
       -\Delta(s)\sum_i n_i.
\]

The frozen piecewise-linear schedule ramps `Omega` from 0 to 1 during the first
10% at `Delta=-2`, sweeps `Delta` from -2 to 2 with `Omega=1`, and ramps
`Omega` to 0 during the final 10%.  Spectral minima are measured on
`s = 0.02, ..., 0.98`, avoiding the intentionally degenerate classical end
point.  Dynamics start in the empty independent set and report total final
probability on maximum independent sets.

## Reduction under test

For every degree-one vertex `v` with neighbour `u`, the classical leaf rule
selects `v`, removes `{u,v}`, and adds one to the reduced optimum.  The lift is
fixed: add `v` and leave `u` empty.  This rule is exact for MIS value, but is
not parsimonious and need not preserve all optimal states.

The isolated-vertex rule is retained only as a factorising sanity check.  It
cannot satisfy the nontrivial-safe-rule success condition.

## Data

1. Every connected, non-isomorphic graph in NetworkX's graph atlas with 3--7
   vertices and at least one leaf.
2. A seeded set of native random unit-disk graphs with 8--12 vertices and at
   least one leaf.

All oriented leaf reductions are tested.  Graphs and reductions are identified
by canonical graph6 strings and vertex labels.

## Metrics and controls

- exact check `alpha(G) = alpha(G-{u,v}) + 1`;
- original and lifted optimum degeneracy and lifted coverage;
- minimum interior gap for original and reduced systems;
- symmetric gap distortion `max(g'/g, g/g')`;
- finite-time MIS probability at `T in {5,10,20,40}` for the strongest
  spectral candidates;
- reduced-driver controls `Omega' / Omega in {1, sqrt(n/n'), n/n'}`;
- same-size induced-deletion controls for the strongest candidates.

The static-lift endpoint obstruction is evaluated analytically, not counted as
an empirical discovery: at the standard negative-detuning start the original
ground state is empty and orthogonal to any lift that forces a selected vertex.

## Success and kill criteria

Phase 0 survives only if all of the following hold:

1. a leaf-rule family reaches at least 5x gap distortion or 0.25 absolute
   finite-time success difference;
2. the effect survives at least one driver-normalisation control and is not
   explained by generic deletion of the same number of vertices;
3. a nontrivial, locally checkable sufficient quantum-safety rule (strictly
   beyond isolated factorisation and "wait until Omega is zero") is derived and
   exhaustively verified;
4. adversarial prior art does not already contain the same Rydberg-MIS claim,
   criterion, and construction.

Failure of any item closes this formulation before H200 or QPU work.  Aquila
validation is authorised only after Phase 0 survives and credentials/cost are
separately available.
