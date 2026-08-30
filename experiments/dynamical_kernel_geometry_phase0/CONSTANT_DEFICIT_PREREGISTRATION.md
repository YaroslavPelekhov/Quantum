# Constant-deficit connected family: frozen follow-up

Frozen after the shared-hub windmill family failed and before inspecting this
follow-up's numerical outcomes.

The windmill failure has a simple structural cause: occupying the hub loses one
selected vertex per petal, so the competing hub sector moves away from the
low-energy dynamics as `k` grows.  This follow-up keeps its classical deficit
equal to one.

Graph `C_k` has hub `u`, two leaf neighbours `v,w`, and `k` disjoint edges
`(a_i,b_i)`.  The hub is adjacent to every `a_i` but not to any `b_i`.  The
optimal sector selects both leaves and one endpoint of every edge, with size
`k+2`.  The best hub-selected sector selects the hub and all `b_i`, with size
`k+1`: its deficit is exactly one for all `k`.

Applying the leaf rule to `(v,u)` deletes exactly two vertices.  The reduced
graph is one isolated vertex plus `k` disjoint edges.  Every original optimum
contains both leaves, so the endpoint lift is bijective.

Frozen tests for `k=1..4` use the same Hamiltonian, schedule, times, 480-step
dynamics, gap windows, and geometry metrics.  The family survives only if:

1. interior gap distortion is at most `1.25x` for every `k`;
2. some frozen time has log-success-ratio slope at least `0.15` per petal with
   `R^2 >= 0.95`;
3. the absolute success difference reaches `0.25` at `k=4`;
4. transition-action distortion is monotone with the success distortion;
5. the effect is not reproduced by the disconnected `k=1` product baseline.

Failure closes this family.  Hardware geometry and pulse correction are tested
only after all five conditions survive.
