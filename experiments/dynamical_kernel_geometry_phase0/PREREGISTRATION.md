# Dynamical kernel geometry: frozen Phase 0

Frozen on 2026-08-30 before running the family experiment.

## Narrow hypothesis

There exists a connected, endpoint-bijective MIS leaf-reduction family for
which deleting only two vertices leaves the minimum interior spectral gap
nearly unchanged but produces a growing finite-time success distortion.  The
missing descriptor is eigenpath geometry/nonadiabatic coupling rather than the
minimum gap alone.

This is narrower than counterdiabatic Rydberg optimisation, subspace-reduced
counterdiabatic driving, and quantum-aware graph embedding, all of which are
prior art.  Phase 0 tests a separation family and a diagnostic, not a generic
claim that gauge potentials are new.

## Frozen family

For integer `k >= 1`, graph `W_k` contains a hub `u`, a leaf `v`, and `k`
disjoint pairs `(a_i,b_i)`.  Each pair and the hub form a triangle, and the leaf
is adjacent only to the hub.  Thus `W_1` is the four-vertex counterexample
`CN`.  Applying the exact leaf rule to `(v,u)` removes exactly two vertices and
leaves `k` disjoint edges.

Every maximum independent set of `W_k` contains `v` and one endpoint of every
pair.  The lift is therefore bijective on the `2^k` endpoint optima.  The
original graph is connected.  A geometry-only preflight before the physics run
found a direct unit-disk layout for `k <= 4` (at most 10 atoms).  The `k=5`
point is retained as a non-native family test, not as a hardware claim; packing
the five pair-clusters plus the separate leaf around one unit-disk hub creates
unwanted cross edges in the direct construction.

## Frozen physics and metrics

Use the same hard-blockade Hamiltonian and three-stage global schedule as the
closed static-kernelization Phase 0.

- exact dynamics at `T in {5,10,20}` with 480 midpoint steps;
- minimum gap on the preregistered full window and on `0.1 <= s <= 0.9`;
- final total probability on the entire MIS manifold;
- log success ratio between reduced and original systems;
- ground-path quantum metric and inverse-gap-weighted transition action,
  reported separately for ramp-up, sweep, and ramp-down where dense exact
  eigensystems are feasible;
- disconnected `k`-copy product of the `k=1` motif as a factorisation baseline.

## Success gates

The family survives Phase 0 only if:

1. interior gap distortion remains at most `1.25x` through `k=5`;
2. at one frozen time, `log(P_reduced/P_original)` has positive slope at least
   `0.15` per added petal with `R^2 >= 0.95` for `k=1..5`;
3. the connected shared-hub family is not explained by the disconnected-copy
   product baseline (at least 20% separation in log ratio at `k=5`);
4. a geometry/action statistic changes monotonically with the observed
   finite-time distortion for `k=1..4`, while minimum gap does not;
5. adversarial prior art does not contain this same family or an equivalent
   constant-deletion/min-gap-separated construction.

Failure of any gate kills the proposed A* separation.  No pulse optimisation,
H200 scaling, or QPU execution is authorised before these gates pass.
