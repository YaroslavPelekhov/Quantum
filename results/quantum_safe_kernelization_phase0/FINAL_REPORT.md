# Quantum-safe Rydberg MIS kernelization: Phase-0 final report

## Verdict

**KILL_ASTAR_DIRECTION for static graph kernelization under the standard global
Rydberg driver.**  The experiments contain real finite-time differences, but
the proposed whole-path quantum-safety contribution fails structurally and the
largest preregistered spectral effect fails aggressive falsification.

No H200 scaling or Aquila run is authorised from this formulation.

## Frozen experiment

- 411 connected non-isomorphic graph-atlas instances with 3--7 vertices;
- 120 seeded native unit-disk instances with 8--12 vertices, including saved
  coordinates;
- 793 oriented exact MIS leaf reductions;
- exact hard-blockade Hamiltonians in the independent-set basis;
- 49-point preregistered gap sweep, three driver normalisations, four annealing
  times, same-size deletion controls, and time-step convergence checks.

All 793 reductions satisfy `alpha(G)=alpha(G-{u,v})+1`.  However, 210/793 lifts
cover only a proper subset of the original endpoint optimum space.

## Apparent positive result and its falsification

The frozen metric initially produced a `100.633x` native gap distortion on the
7-vertex graph6 instance `F^NI?`, and 35 reductions exceeded `5x` under every
tested driver scaling.  This was not accepted at face value.

Every extreme minimum occurred at `s=0.98`, inside the final driver ramp-down.
For the top 12 cases the original gap scales as `Omega^2` (8 cases) or
`Omega^4` (4 cases): the large ratios compare different perturbative splitting
orders as classical degeneracy is restored.  When the ramp-down region is
removed (`0.1 <= s <= 0.9`):

| Check | Result |
|---|---:|
| Reductions with at least 5x gap distortion | **0 / 793** |
| Largest remaining distortion | **4.798x** |
| Largest distortion with a bijective endpoint lift | **1.399x** |
| Distortion for the strongest finite-time motif | **1.002x** |

The preregistered `100.633x` is therefore an endpoint-degeneracy artefact for
the intended claim, not evidence for a new avoided-crossing mechanism.

## Finite-time result

A post-hoc native-driver screen evaluated all 793 reductions at `T=5` and
`T=10` (1,586 rows).  Sixty screen rows exceeded an absolute MIS-success
difference of 0.25.  All top 12 remained above 0.25 when recomputed with 480
time steps.

The largest confirmed difference is `0.394655`:

- graph6 `CN`, four vertices: a triangle with one pendant leaf;
- exact leaf reduction to graph6 `A_`, a single edge;
- original success `0.555419`, reduced success `0.950074` at `T=10`;
- endpoint lift coverage `1.0`;
- mid-schedule gap distortion only `1.00236`.

This is a valid benchmark observation: deleting half of a four-atom system can
substantially change nonadiabatic finite-time population transfer even when the
minimum gaps are nearly equal.  It is not an A*-level mechanism or certificate.
The smallest textbook motifs already exhibit success differences up to about
0.249, and equivalent-encoding effects on annealing dynamics and gaps are
established prior art.

The earlier `0.44757` finite-time difference on an 8-vertex unit-disk graph is
also non-robust: it requires multiplying the reduced driver by `1.333x`.  With
the same native driver its difference is `0.0464` at `T=5` and `0.0708` at
`T=10`.  The 960-step convergence value for the rescaled comparison is
`0.447692`, so the number is numerically real but scientifically caused by the
chosen rescaling.

## Structural kill

Three exact facts rule out the naive whole-path certificate:

1. A static lift that forces any selected vertex is orthogonal to the standard
   empty initial ground state, so the initial projector distance is exactly 1.
2. A non-surjective classical lift has endpoint ground-projector distance 1;
   this occurs in 210/793 tested reductions.
3. At finite drive, the lifted leaf sector has exact leakage coupling
   `||(I-P)HP|| = |Omega|/2`; it is not an invariant subspace.

A neighbour with at least two leaf children is a locally checkable condition
that fixes endpoint surjectivity, but not the initial obstruction or finite
drive leakage.  No nontrivial whole-path safe rule beyond disconnected
factorisation or the vanishing-driver limit was found.

## Prior-art boundary

The direction is tightly surrounded by prior work:

- Aharonov and Zhou already formalise ground-space/gap simulation and general
  quantum sparsification obstructions;
- FastHare performs optimum-preserving Hamiltonian reduction for quantum
  annealing;
- Choi shows that equivalent MIS/Ising encodings and parameters can drastically
  alter anti-crossings and minimum gaps;
- Kombe and Pritchard study classical kernelisation of native unit-disk Rydberg
  MIS instances;
- Schuetz et al. combine Rydberg graph reductions, embeddings, and Aquila
  experiments.

The unoccupied niche would require a nontrivial, hardware-realizable,
finite-time-preserving transformation.  This cycle did not produce one.

## Hardware decision

The exact counterexamples need only 4--12 atoms and are already exactly
simulable.  Running them on Aquila would demonstrate ordinary device dynamics,
not distinguish the failed theorem or establish novelty.  Moreover this
workspace has no configured AWS Braket credentials.  Spending QPU budget is
therefore not justified.

## Reproducibility

Run:

```powershell
python experiments/quantum_safe_kernelization_phase0/run_phase0.py
python experiments/quantum_safe_kernelization_phase0/run_falsification.py
python experiments/quantum_safe_kernelization_phase0/run_broad_dynamics.py
python -m unittest experiments.quantum_safe_kernelization_phase0.test_qdk_core
```

The raw tables, frozen summary, falsification outputs, unit-disk coordinates,
and environment metadata are in this directory.  The preregistration,
prior-art boundary, exact structural arguments, and implementation are under
`experiments/quantum_safe_kernelization_phase0/`.

## Binding research decision

Retain this branch as a closed-hypothesis benchmark showing why
optimisation-preserving preprocessing is not automatically a dynamical
simulation.  Do not rebrand endpoint splitting, static P/Q leakage, or the
four-vertex finite-time motif as A* novelty.  The next search must change the
computational object or introduce a hardware-realizable capability that this
static graph-kernel formulation lacks.
