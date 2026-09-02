# Quantum A-star research decision, 2026-09-02

## Executive verdict

There is **no defensible A-star claim yet and no justified QPU spend**.  This is
not a stalled result: several tempting mechanisms have now been closed by exact
counterarguments or aggressive controls before hardware selection could turn
them into expensive false positives.

The strongest surviving mathematical object is now a gauge-invariant
weak-drive time-bandwidth theorem.  It repairs the previous closest-frequency
argument by minimizing over the complete vertex-gauge orbit and proves hard
worst-case curvature targets.  It still cannot support an A-star claim: those
targets have exponential descriptions, the frozen held-out screen fails, no
matching comparator compiler exists, and nonlinear finite-amplitude dynamics
lie outside the theorem.

## Decision ledger

| branch | strongest result | decisive falsifier | status |
|---|---|---|---|
| QAOA/MPS symmetry | exact quotient and useful memory compression | ordinary twin symmetry plus event incidence explains all audited rank rows; honest Aer speedup is modest | closed as A-star |
| drift-aware QAE | exact confounding and drift/noise information bounds | generator-aligned drift is nonidentifiable; fixed gate noise restores SQL scaling | closed as A-star |
| one-mask Aquila control | full small-system Lie rank | adaptive ODE reduces coarse-grid near-unit fidelities to `0.787188` and `0.683809`; ensemble-control prior art covers the algebraic mechanism | closed as A-star |
| configuration curvature | counts witness `chi=0.242291`, exact nulls, 100% sign retention in 256 perturbations | logarithmic flux is branch dependent and the branch-free mechanism is known density-dependent Peierls hopping | closed as A-star |
| one-mask curvature compiler | exact attainable space `image(d1 P)` and a conditional edge-response bound | generic one-mask rank is already full; the observed low rank is only a perturbative tangent | closed as A-star centerpiece |
| gauge-quotiented resource bound | exact QTV theorem for arbitrary integrable weak drives; worst-case `Omega(n 2^n/W)` existence bound | held-out numerical gates fail; hard target is not succinct; full finite-amplitude propagator admits nonlinear routes outside scalar response | closed as A-star; retain theorem |

## What the last theorem establishes

Order the distinct configuration-edge frequencies and let `W` be their total
width.  For a curvature target `Phi`, define `QTV_omega(Phi)` as the minimum
circular total variation, in that spectral order, over every edge-phase
representative with curvature `Phi`.  Contractibility of the full cube makes
this exactly a minimization over all vertex gauges.

For every integrable complex weak drive with response magnitude at least a
constant fraction `rho` of pulse area at every sampled frequency,

`T W >= (2 rho / pi) QTV_omega(Phi)`.

This holds for arbitrary pulse shapes inside the scalar first-order response
model, rather than for a polynomial ansatz or a fixed phase lift.  A Haar/net
argument further proves that, for every `n>=7`, some Bianchi-consistent target
on the full cube obeys

`QTV_omega(Phi) >= pi(E-1)/(8e)`, with `E=n 2^(n-1)`.

The exact circular MILP implements the quotient and uses only its dual bound as
a numerical certificate.  Development medians grow strongly, but the frozen
held-out geometry has exact transition-frequency collisions from `n=5`, one
development solve misses the registered gap, and a disclosed coordinate
microperturbation has poor scaling fit (`R2=0.621561`).

The theorem remains a scoped result, not an algorithmic separation.  The hard
Haar target contains `Theta(E)` data, so its lower bound is only linear in
explicit input length.  There is no succinct deterministic family, no matching
polynomial upper construction for a meaningful stronger resource, and no
extension to the nonlinear finite-amplitude propagator.

The last point was attacked directly in a disclosed post-hoc falsifier.  A
complete three-atom simulation found a provisional-hardware-valid `1.2 us`
one-mask pulse implementing the branch-free population cycle
`000 -> 001 -> 011 -> 010 -> 000` with mean probability `0.983860`, worst leg
`0.974694`, inverse-cycle probability `0.000809`, and leakage `0.003756`.
Time reversal implements the inverse cycle, interaction removal restores
reciprocity, and the fifth percentile over 128 perturbations remains
`0.874568`.  This does not disprove the conditional QTV theorem or an
asymptotic lower bound for a particular hard target.  It does falsify any
unrestricted step from a scalar response obstruction to all full propagators.

## Hardware decision

No real-server task was submitted.  The current hardware-facing curvature
packet would be suitable only as an engineering replication of known physics,
not as validation of a new A-star mechanism.  The gauge-resource theorem has
no direct constant-shot hardware observable and the frozen held-out gate
already fails, so running it on Aquila cannot repair the claim.  Any later
engineering replication must use interleaved forward, reverse,
zero-interaction/large-distance, equal-mask, and palindromic schedules; preserve
the counts-only estimator; and revalidate live device constraints immediately
before submission.  Ideal shot estimates do not include local-detuning
decoherence or device drift.

## Adjacent resource-bound screen: closed

The bounded screen proposed in the previous revision has now been run.  It
succeeds only at producing a new gauge-quotiented weak-drive bound.  It fails
the conditions needed for a resource separation:

1. the proof stops at first-order scalar response and does not constrain all
   finite-amplitude admissible propagators;
2. no succinct deterministic hard family was found;
3. no matching polynomial construction for an available stronger control
   resource was found;
4. the registered held-out numerical geometry fails without retuning;
5. the broad mechanism is covered by graph gauge, selective-control, and
   Fourier time-bandwidth prior art; and
6. known global-control universality and nonlinear optimal control supply a
   concrete bypass risk.

This closes the surrounding QAOA/MPS-to-one-mask-curvature lineage as a source
of A-star novelty.  The next cycle must change the research object.  The most
defensible quantum continuation is a hardware-native prediction problem with
held-out device validation—for example, predicting simulator-to-hardware
ranking reversals before spending shots—rather than another reformulation of
configuration-edge phases.  It requires a fresh preregistration and real
hardware data budget; it is not authorized by the present result.

## Repository entry points

- Gauge-resource final report: `results/aquila_gauge_resource_phase0/FINAL_REPORT.md`
- Gauge-resource theorem: `experiments/aquila_gauge_resource_phase0/THEORY_AND_SCOPE.md`
- Frozen quotient protocol: `experiments/aquila_gauge_resource_phase0/PREREGISTRATION.md`
- Full-dynamics scope falsifier: `experiments/aquila_gauge_resource_phase0/FULL_DYNAMICS_FALSIFICATION.md`
- Curvature result: `results/aquila_configuration_curvature_phase0/FINAL_REPORT.md`
- Exact compiler theorem: `experiments/aquila_configuration_curvature_phase0/COMPILER_THEOREM_AND_KILL.md`
- Machine-readable rank result: `results/aquila_configuration_curvature_phase0/compiler_rank_summary.json`
- One-mask control falsification: `results/aquila_one_mask_phase0/FINAL_REPORT.md`
- Drift-QAE falsification: `results/drift_qae_phase0/FINAL_REPORT.md`
- Sequential drift boundary: `results/interleaved_drift_boundary_phase0/FINAL_REPORT.md`

The binding research policy is simple: preserve the useful engineering
artifacts, state every negative result, and do not rename a falsified mechanism
into novelty.
