# Post-hoc full-dynamics falsification

## Status and disclosure

This is an explicitly **post-hoc adversarial test** of the nearest attempted
extension of the weak-drive gauge-resource result. It is not part of the
preregistered Phase 0 validation and cannot turn that Phase 0 into a positive
A-star claim.

The question is deliberately narrow: may the weak-drive, single-Fourier-
response QTV cost be extrapolated to an arbitrary finite-time propagator driven
by the complete Rydberg Hamiltonian? The answer is no.

## Exact test

The test uses the complete three-atom, eight-dimensional C6 Hamiltonian, not a
blockade projection. Available controls are global Rabi amplitude, global
detuning, and one time-independent spatial mask multiplied by a scalar local-
detuning waveform. The laser phase is fixed to zero, so a complex drive phase
cannot manufacture the orientation. Every waveform knot obeys the provisional
Aquila amplitude, endpoint, time-grid, and slew limits.

The fixed population target is the oriented configuration-space face

`|000> -> |001> -> |011> -> |010> -> |000>`.

Its score is the mean of the four indicated transition probabilities. The
inverse-cycle score, the worst directed transition, leakage into configurations
with the spectator atom excited, and the phase of the product of the four
directed amplitudes are reported separately. No matrix logarithm or branch
choice enters this observable.

The exploratory optimizer is intentionally absent from the reproducer. The
selected 1.2 microsecond pulse was frozen verbatim in `full_dynamics_audit.py`.
All primary values are independently recomputed with adaptive DOP853 at
`rtol=5e-12`, `atol=5e-14`. A midpoint convergence ladder is diagnostic only.

## Results

| Quantity | Adaptive result |
|---|---:|
| Clockwise mean probability | 0.9838600 |
| Worst clockwise transition | 0.9746938 |
| Counter-clockwise mean probability | 0.0008090 |
| Orientation contrast | 0.9830510 |
| Spectator leakage mean | 0.0037563 |
| Cycle Wilson phase | 2.4069903 rad |
| Unitarity error | 1.34e-11 |

Because every instantaneous Hamiltonian is real symmetric, reversing the
piecewise-linear schedule must produce the transpose propagator. Numerically,
`||U_reverse-U^T||_2=2.23e-10`; the reversed schedule has clockwise score
0.0008090 and counter-clockwise score 0.9838600.

The mechanism controls are destructive:

| Control | Clockwise mean | Orientation contrast |
|---|---:|---:|
| Nominal | 0.983860 | 0.983051 |
| Interaction off | 0.248394 | 2.0e-13 |
| Equal mask | 0.061672 | 0.032221 |
| Interaction off and equal mask | 0.129412 | -5.6e-17 |
| Local waveform off | 0.126059 | -0.021489 |

Quantizing both the waveform and the geometry to the recorded hardware grids
leaves a clockwise mean of 0.982509, worst transition 0.972952,
counter-clockwise mean 0.000742, and leakage 0.003710.

In the frozen 128-draw perturbation audit (position sigma 0.03 micrometers,
mask sigma 0.01, and independent 1% control-scale errors), the clockwise mean
has p05 0.87457 and median 0.95634. The worst-transition p05 is 0.81342 and the
orientation-contrast p05 is 0.86541. Adaptive spot checks at the worst, p05,
median, and best selected draws agree with the 24-substep audit to at most
3.6e-4 in mean clockwise probability.

## What is and is not falsified

The finite-time cycle uses strong, noncommuting time ordering and a
time-dependent detuning. It therefore does not admit the fixed-frequency,
single-response representation used by the weak-drive QTV derivation. This
counterexample kills an **unrestricted full-propagator extrapolation** of that
bound.

It does not falsify either of the following:

- the original perturbative Fourier-response theorem;
- a conditional theorem requiring a nonzero response margin on every edge of
  a scalable target family.

Those restrictions must remain explicit in any surviving theorem statement.

## Hardware interpretation

The complete four-leg cycle is an exact simulator observable but requires
preparing three non-ground computational-basis inputs. Those preparations are
not native to a single Aquila program. Only two legs give an immediate
counts-only hardware test from the native all-ground input:

- forward schedule: target site 0 probability 0.972952 versus wrong site 1
  probability 0.001584;
- reversed schedule: target site 1 probability 0.988111 versus wrong site 0
  probability 0.000145.

Thus the two-schedule router is hardware-testable, while the four-input cycle
claim remains a simulator-level diagnostic unless a separately validated
state-preparation protocol is added. No QPU task is justified by this post-hoc
falsifier alone.

## Reproduction

Compact committed result:

```text
python -m experiments.aquila_gauge_resource_phase0.full_dynamics_audit
```

To additionally retain all 128 individual perturbation rows:

```text
python -m experiments.aquila_gauge_resource_phase0.full_dynamics_audit --full-output results/aquila_gauge_resource_phase0/full_dynamics_audit_full.json
```

Focused regression tests:

```text
python -m unittest experiments.aquila_gauge_resource_phase0.test_full_dynamics
```
