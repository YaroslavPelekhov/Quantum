# Frozen held-out host-transfer gate

The four-atom capacity audit found a `13 -> 4` static surrogate at `T=5` for
both detuning controls.  Its parameters and topology are frozen in
`capacity_audit_summary.json`.  This experiment tests the central missing
condition: does an isolated-port response fit transfer to hosts without
refitting?

## Held-out hosts

- 30 distinct port-colored connected unit-disk graphs: 1 with two vertices, 3
  with three, 8 with four, and 18 with five;
- deterministic seed `20260903`;
- the port is fixed at the left geometric boundary; the 13-atom motif extends
  in the opposite half-plane, so the only host--motif edge is the registered
  port edge;
- no host appears in surrogate fitting.

## Dynamics and comparators

- hard-blockade constant-control evolution, `Omega=1`, `Delta_host=0.37`, from
  the all-ground state to `T=5` on 41 time points;
- target: the full host plus the 13-atom path motif;
- frozen surrogate: the best four-atom topology, onsite detunings, and port
  phase-rate correction from the capacity audit;
- same-budget baseline: the first four unmodified path atoms;
- both uniform and 3% perturbed target-motif controls;
- absolutely no host-specific optimization.

At every time, trace out the motif/surrogate and compare the full host reduced
density matrices.  Report trace distance, computational-basis TV distance, and
port-occupation error.

## Promotion criteria

Each detuning control passes only if all conditions hold across the 30 hosts:

1. median maximum-in-time host trace distance <= 0.02;
2. 90th percentile <= 0.05 and worst case <= 0.10;
3. median trace-distance improvement over the four-atom prefix >= 5x;
4. surrogate beats the prefix on at least 90% of hosts;
5. 90th-percentile maximum port-population error <= 0.02.

CBRK advances only if both controls pass.  Failure means the low-rank
conditional Loschmidt slice was not a transferable boundary process and cannot
support the A-star claim.  Thresholds will not be weakened after the run.

