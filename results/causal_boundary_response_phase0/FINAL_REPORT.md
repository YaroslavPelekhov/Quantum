# Causal boundary-response kernelization: final report

## Verdict

**CLOSE CBRK as an A-star novelty branch.**

The cycle found a genuine and reproducible technical effect: at the frozen
constant-control horizon `T=5`, a detuning-tuned four-atom Rydberg path
approximates the conditional boundary response of a 13-atom path with maximum
complex error `0.005996` (uniform) and `0.000401` (perturbed).  This is `3.25x`
physical atom compression and it remains accurate on 30 held-out small
unit-disk hosts.

It is not a new universal simulation primitive.  The exact response complexity
is extensive, the apparent finite-time compression is a known type of fitted
boundary/bath termination, robust fivefold separation fails in the uniform
control, and the final multi-switch process-Gram test falsifies transfer from a
single fitted coherence curve to the full controlled boundary process.

No QPU run is authorised from this claim.

## Frozen research path

The experiment was deliberately staged so that each positive result authorised
only the next falsification:

1. adversarial prior-art and hardware-control tournament;
2. exact-frequency and finite-horizon Hankel rank gate;
3. doubled-grid numerical audit;
4. all one-to-three-atom physical topologies in an optimistic control envelope;
5. deeper restarts and all 79 four-atom colored topologies;
6. 30 frozen held-out unit-disk hosts;
7. all binary boundary histories through six time bins plus an exhaustive
   99-split two-bin scan.

All thresholds were written before their corresponding main run.  A baseline
implementation error discovered after the first host run is documented in
`CORRECTION_LOG.md`: the perturbed prefix now correctly inherits the first four
target detunings, and every affected artifact was regenerated without changing
criteria.

## Rank gate

For `g_k(t)=<empty|exp(+iH_0t)exp(-iH_1t)|empty>`, an `r`-atom surrogate has at
most `4^r` stationary frequency pairs.  The resolved-frequency results are:

| control | k=13 resolved rank | exact atom lower bound | fitted lower-bound slope | R2 |
|---|---:|---:|---:|---:|
| uniform | 61,155 | 8 | 0.61818 | 0.97966 |
| 3% perturbed | 218,525 | 9 | 0.70000 | 0.98162 |

Thus exact sublinear compression is not supported.  At finite horizon,
however, the 1% effective Hankel ranks at `T=5,10,20` are only `2,3,5` in both
controls.  Doubling the Hankel size to 512 leaves every 1% rank unchanged; at
`T=20` the `1e-6` ranks are 13 and 14.  The opening was finite-time and
numerically stable, so physical synthesis was justified.

## Physical synthesis

Three atoms fail the frozen 2% maximum/1% L2 gate at every horizon.  The closest
`T=5` fits have:

| control | maximum error | relative L2 | improvement over 3-atom prefix |
|---|---:|---:|---:|
| uniform | 0.02299 | 0.01663 | 8.89x |
| perturbed | 0.02735 | 0.02012 | 7.44x |

The expanded optimizer/capacity audit finds a four-atom solution.  In both
controls its colored topology is simply a path: internal edges
`(0,1),(0,3),(1,2)`, with the host port attached to atom 2.  The compiler has
learned a detuning-tuned path termination, not a new graph gadget.

| control | maximum error | relative L2 | improvement over inherited P4 |
|---|---:|---:|---:|
| uniform | 0.005996 | 0.002857 | 10.32x |
| perturbed | 0.000401 | 0.000375 | 154.36x |

The optimistic optimizer was allowed independent onsite detunings and a port
phase-rate correction in `[-6,6]`, more freedom than the current Aquila
control algebra.  Passing this gate was therefore a possibility result, not a
hardware demonstration.

## Held-out host transfer

The frozen four-atom profiles were attached without refitting to 30 distinct
connected port-colored UDG hosts with two to five vertices.  Full host reduced
density matrices were compared at 41 times.

| control | median max trace distance | p90 | worst | median prefix gain | win rate |
|---|---:|---:|---:|---:|---:|
| uniform | 0.01102 | 0.01315 | 0.01398 | 1.386x | 86.7% |
| perturbed | 0.002529 | 0.003181 | 0.003527 | 5.432x | 100% |

Absolute transfer is good, but the preregistered robust capability separation
fails in the uniform control.  This also shows why the isolated 10.32x number
cannot be used as the headline performance claim: on actual host marginals the
ordinary same-budget prefix is already competitive.

## Final controlled-process falsification

For every binary port history of length `K`, the environment produces a word
vector.  Their Gram kernel is the object that determines interference between
host histories.  Equality of the scalar no-switch coherence checks only one
Gram entry; equality of all word-Gram kernels is necessary and sufficient for
the frozen host-universal port-process model.  The proof and scope are in
`THEOREMS_AND_BOUNDARY.md`.

Uniform-control results:

| K | maximum Gram error | improvement over inherited P4 |
|---:|---:|---:|
| 1 | 0.005996 | 10.32x |
| 2 | 0.019117 | 3.24x |
| 3 | 0.020691 | 3.55x |
| 4 | 0.019180 | 4.05x |
| 5 | 0.020825 | 3.72x |
| 6 | 0.020691 | 3.78x |

The exhaustive two-bin timing scan is even more decisive: at `tau=3.10`, the
maximum error is `0.0208879` and the prefix improvement is only `2.963x`.
The perturbed control passes every process test, with worst split error
`0.007748` and `8.978x` improvement, but the frozen claim required both
controls.  Selecting only the positive perturbation after seeing these results
would be post-hoc restriction.

## Prior-art boundary

The exact platform-specific instantiation may be uncommon, but the proposed
principle is not new:

- short bath-chain terminations optimized for finite-time correlation and
  reduced dynamics: [Sanchez-Barquilla and Feist (2021)](https://doi.org/10.3390/nano11082104);
- finite Rydberg spin-waveguides with matched boundary sinks suppressing
  reflections: [Vermersch et al. (2016)](https://doi.org/10.1103/PhysRevA.93.063830);
- finite TLS surrogates for short-time environment dynamics:
  [Baer and Kosloff (1997)](https://doi.org/10.1063/1.473950);
- optimized real-time bath discretization:
  [de Vega, Schollwock, and Wolf (2015)](https://doi.org/10.1103/PhysRevB.92.155126);
- controlled low-dimensional digital twins of interacting spin-chain
  boundaries: [Luchnikov, Gavreev, and Fedorov (2024)](https://doi.org/10.1103/PhysRevResearch.6.013161);
- exact observable-specific quantum model reduction:
  [Grigoletto et al. (2025)](https://doi.org/10.22331/q-2025-07-29-1814);
- conditional central-spin coherence and finite-cluster convergence:
  [Yang and Liu (2008)](https://doi.org/10.1103/PhysRevB.78.085315).

The remaining narrow description—closed, detuning-only, hardware-native
termination for an interacting blockade bath—is a platform-specific method,
not an A-star capability after the process-separation failure.

## Hardware status

Official Aquila controls provide fixed geometry, global `Omega(t)`, phase and
detuning, plus an experimental local-detuning time waveform multiplying one
static spatial pattern.  They do not provide arbitrary changing masks or
mid-shot feedback.  The fitted static profile can be affinely embedded in one
spatial pattern on a plateau in principle, but this workspace has no active AWS
or IBM hardware credentials and the A-star claim is already falsified before
noise, `C6/r^6` tails, loss, waveform constraints, or measurement overhead.

Spending QPU budget would validate a narrow curve fit, not rescue novelty.

## Reproduction

```powershell
python -m experiments.causal_boundary_response_phase0.run_phase0
python -m experiments.causal_boundary_response_phase0.run_rank_audit
python -m experiments.causal_boundary_response_phase0.run_physical_surrogate
python -m experiments.causal_boundary_response_phase0.run_capacity_audit
python -m experiments.causal_boundary_response_phase0.run_host_transfer
python -m experiments.causal_boundary_response_phase0.run_process_gram
python -m unittest experiments.causal_boundary_response_phase0.test_phase0 -v
python -m experiments.causal_boundary_response_phase0.build_manifest
```

## Final scientific classification

- **Valid engineering result:** a tuned P4 reproduces a P13 finite-time
  conditional response and achieves small absolute held-out-host error.
- **Invalid broad claim:** new causal quantum-simulation primitive.
- **Invalid A-star claim:** robust host-universal physical compression with a
  nontrivial separation from same-budget truncation.
- **Branch decision:** do not rebrand CBRK, kernelization, or this fitted
  boundary layer.  Preserve the artifact as a falsified hypothesis and move to
  a genuinely different quantum object.

