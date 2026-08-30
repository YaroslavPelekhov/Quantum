# Dynamical kernel geometry: Phase-0 final report

## Verdict

**KILL the rooted-petal A* separation.**  The nearby scientific gap was real
enough to test: minimum-gap preservation does not imply preservation of
finite-time Rydberg-MIS performance.  However, neither two designed connected
families nor the exhaustive frozen rooted-petal grammar produced a nontrivial
scalable separation satisfying the preregistered gates.

No H200 or QPU run is authorised.

## Why this direction was tested

The preceding static-kernel experiment found a four-vertex graph whose exact
leaf reduction changes `T=10` success from `0.555419` to `0.950074`, while the
interior minimum-gap distortion is only `1.00236x`.  This suggested that
eigenpath geometry and phase-sensitive nonadiabatic transitions, rather than
the minimum gap, might support a genuinely dynamical kernel certificate.

The broad observation is not new: minimum gap is known not to determine
finite-time adiabatic success, counterdiabatic/subspace Rydberg MIS methods
exist, quantum-aware Rydberg embeddings exist, and recent local-control work
already targets low-degree vertices.  The only plausible new claim was a
graph-theoretic, endpoint-bijective, constant-deletion separation family.

## Family 1: shared-hub windmill

`W_k` contains one hub, one leaf, and `k` edge pairs, each forming a triangle
with the hub.  Removing the leaf and hub leaves `k` disjoint edges.  The lift is
endpoint-bijective, the original graph is connected, and only two vertices are
deleted.

The gap condition passed extremely strongly: the maximum interior distortion
over `k=1..5` was `1.002360`, tending toward one with k.  The desired dynamical
scaling failed:

| T | fitted log-ratio slope | R2 |
|---:|---:|---:|
| 5 | -0.01197 | 0.8659 |
| 10 | -0.10560 | 0.9261 |
| 20 | -0.01321 | 0.6383 |

At `T=10`, the success difference decreases from `0.394655` at `k=1` to
`0.088410` at `k=5`.  The sweep transition-action difference also decreases
from `0.61057` to `0.33818` over `k=1..4`.  The geometry diagnostic correctly
tracks the disappearance of the effect; it does not reveal a scalable
separation.

The structural reason is that selecting the hub loses one excitation per
petal.  Its competing sector moves away from the low-energy dynamics as k
grows.

## Family 2: constant-deficit hub

The follow-up attaches two forced leaves and connects the hub to only one
endpoint of every independent edge.  The best hub-selected classical sector
then remains exactly one below optimum for every k.  The leaf reduction remains
endpoint-bijective and removes two vertices.

This stronger construction also fails.  All fitted log-ratio slopes are
negative; the least negative is `-0.002817` with `R2=0.541`.  At its selected
time `T=20`, the `k=4` success difference is only `0.04220`.  Maximum interior
gap distortion is `1.000348x`.

Thus holding the classical trap deficit constant is insufficient.  Coherent
population transfer does not accumulate into the proposed family-level
distortion.

## Exhaustive rooted-petal grammar

The final search enumerated every connected rooted petal on two or three
vertices, every nonempty hub-neighbour subset, and one or two hub leaves.  It
constructed `k=1,2,3` shared-hub families, deduplicated them by graph6 sequence,
and retained only endpoint-bijective leaf reductions.

- 84 unique grammar families;
- 73 endpoint-bijective families;
- native-driver screening at `T in {5,10}`;
- 12 highest-slope families confirmed with 480 steps and exact/sparse interior
  gap controls;
- 0 candidates pass all frozen gates.

The closest candidate has:

- confirmed log-ratio slope `0.181664` and `R2=0.994407`;
- gap distortions `1.07016`, `1.00516`, and `1.00057` for `k=1,2,3`;
- 31.4% separation from the disconnected-product log ratio;
- but absolute success differences `0.17288`, `0.14935`, `0.10658`, decreasing
  rather than reaching the frozen `0.25` requirement.

This candidate is also structurally trivial: the petal has three mutually
independent vertices all adjacent to the hub, so the composed original is a
star and the reduction leaves independent vertices.  Its behavior is precisely
a high-degree/low-degree local-control effect, not a new kernel geometry.

## Scientific conclusion

The experiment establishes a useful negative boundary:

1. almost identical minimum gaps can coexist with material finite-time
   differences under exact classical kernelization;
2. ground-path metric/action differences diagnose the small motif but need not
   grow under graph composition;
3. preserving a competing sector's endpoint energy deficit does not force a
   scalable diabatic obstruction;
4. within the complete tested two-/three-vertex rooted-petal grammar, the only
   growing relative effect collapses to a star/independent-vertex construction.

This is not enough for an A* claim.  Replacing absolute success by relative
success or time-to-solution after seeing the star near miss would be a post-hoc
metric change and would amplify a textbook degree effect.  That route is closed.

## Reproduction

```powershell
python experiments/dynamical_kernel_geometry_phase0/run_family.py
python experiments/dynamical_kernel_geometry_phase0/run_constant_deficit.py
python experiments/dynamical_kernel_geometry_phase0/run_motif_search.py
python -m unittest experiments.dynamical_kernel_geometry_phase0.test_family
```

Frozen protocols, prior-art boundaries, family generators, exact dynamics,
geometry metrics, all motif-screen rows, and confirmed candidates are retained.

## Next legitimate gap

The next nearby question cannot be another static graph family or another
phase-blind scalar diagnostic.  It would need a hardware-realizable operation
that changes capability—for example a causal, phase-sensitive reduction
protocol whose correction is implementable with available Rydberg controls and
whose guarantee is stronger than standard counterdiabatic/local-control work.
That requires a fresh prior-art and hardware-control screen before experiments;
it is not claimed by this cycle.
