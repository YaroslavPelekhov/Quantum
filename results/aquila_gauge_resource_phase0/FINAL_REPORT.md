# Final report: gauge-quotiented curvature-resource Phase 0

## Verdict

**KILL_GAUGE_RESOURCE_ASTAR; RETAIN_WEAK_DRIVE_QTV_THEOREM**

- Frozen numerical gates passed: **False**
- Weak-drive curvature-only theorem: **Valid**
- Succinct asymptotic hard family: **Not established**
- Full-propagator separation: **Not established; naive extension falsified**
- A-star novelty: **False**
- QPU eligible: **False**
- QPU tasks submitted: **0**

## Exact theorem result

The corrected gauge-invariant quantity is the minimum circular total variation
of an edge-phase representative in transition-frequency order:

`QTV_omega(Phi)=min_(d1 A=Phi) TV_omega(A)`.

For every integrable weak drive whose sampled response magnitudes remain at
least a fraction `rho` of pulse area,

`T W >= (2 rho/pi) QTV_omega(Phi)`.

For the full `n`-cube and any ordering of distinct edge frequencies, a Haar/net
argument proves that for every `n>=7` there exists a Bianchi-consistent target
with

`QTV_omega(Phi) >= pi(E-1)/(8e)`, where `E=n 2^(n-1)`.

Thus a worst-case weak-drive target can require
`T >= rho(E-1)/(4eW)`.  This fixes the invalid closest-frequency-pair argument:
the bound now minimizes over the entire vertex gauge and is fully modulo
`2pi`.

The result is not an A-star separation.  Its Haar target contains `Theta(E)`
independent data, so the lower bound is only linear in explicit input length.
There is no succinct hard target, matching stronger-control construction, or
extension to the full finite-amplitude propagator.

## Frozen numerical result

The circular MILP optimized every vertex gauge and one integer phase lift per
adjacent spectral pair.  Development medians were:

| n | edges | certified median quotient cost | median raw cost |
|---:|---:|---:|---:|
| 3 | 12 | 4.210 | 17.623 |
| 4 | 32 | 100.195 | 198.175 |
| 5 | 80 | 308.440 | 3031.693 |
| 6 | 192 | 1087.276 | 5261.290 |
| 7 | 448 | 6166.862 | 85129.379 |

The registered `n=4..7` development fit has log2 slope `1.964861` per atom and
`R2=0.989423`.  At response margin `rho=0.2`, the corresponding conservative
median weak-drive time lower bounds rise from `0.768 us` at `n=4` to
`29.849 us` at `n=7` for the archived physical frequency widths.

This positive development screen does not pass the protocol.  One `n=7` solver ended
with a `27.50%` MILP gap, and the held-out geometry contains an exact equal-
distance transition collision beginning at `n=5`.  Consequently four of seven
registered numerical gates fail and no held-out slope exists.

## Disclosed post-hoc diagnosis

Moving one held-out x coordinate by `0.001 um` removes the collision without
changing masks or targets.  The certified median quotient costs are `603.525`,
`1386.414`, `11969.939`, and `4157.132` for `n=5..8`.  Eleven of 16 instances
reach exact optima; all four `n=8` instances time out.  The conservative log2
slope is `1.146229`, but `R2=0.621561`, far below the frozen held-out gate.

Gauge optimization is material: median feasible costs are roughly 0.6%--1.3%
of the raw nearest-gap costs in this diagnostic.  It eliminates the naive
minimum-gap blow-up while leaving hard finite-size targets.  The nonmonotone
certified sequence does not prove exponential asymptotic scaling.

## Novelty and full-dynamics boundary

Graph gauge quotients, Fourier/Vandermonde conditioning, and shared-pulse
selective control are established fields.  The exact frequency-weighted QTV
functional may be a narrow technical intersection, but existing global-control
universality and direct optimal-control results provide a concrete nonlinear
bypass risk.  The theorem must therefore be labelled `WEAK_DRIVE_ONLY`.

An explicitly post-hoc adversarial full-dynamics test confirms that this scope
boundary is operational, not semantic.  On the complete three-atom Rydberg
Hamiltonian, a bounded `1.2 us` pulse valid under the recorded provisional
hardware-shape limits and using global Rabi, global detuning, and one
static-mask detuning realizes the population cycle
`000 -> 001 -> 011 -> 010 -> 000`.  Independent adaptive integration gives
clockwise mean `0.983860`, worst leg `0.974694`, counter-clockwise mean
`0.000809`, and spectator leakage `0.003756`.  Reversing the waveform exchanges
the two orientations and satisfies `||U_reverse-U^T||_2=2.23e-10`.
The exploratory optimizer and all 16 retained, adaptively validated candidates
are archived separately from the independent frozen-pulse audit.

The effect vanishes as an oriented router when interactions are removed
(`2.0e-13` contrast), and is strongly degraded by an equal mask or by removing
the local waveform.  After quantizing positions to `0.1 um`, the clockwise
mean remains `0.982509`; across 128 frozen perturbations its fifth percentile
is `0.874568`.  These data kill only an unrestricted extrapolation from the
scalar Fourier response to the full propagator.  They do not refute the stated
weak-drive theorem or prove an efficient compiler for the asymptotic hard
targets.

The complete four-leg cycle requires non-native input preparation.  Only its
forward/reverse ground-state routing legs are immediately counts-measurable on
Aquila, so this CPU falsifier is not itself a hardware novelty claim and does
not authorize QPU spending.

Any future revival would need a succinct deterministic target, a lower bound
for every finite-amplitude hardware-admissible waveform, and a matching
polynomial compiler with one actually available additional control mode, all
at constant signal and polynomial shot cost.  This cycle supplies none of
those three requirements.  The next A-star search should therefore change the
research object rather than reformulate this configuration-edge branch again.

## Binding decision

Retain the QTV theorem, exact MILP formulation, all timeouts, the collision
diagnosis, and the full-dynamics bypass as a technical negative result.  Do not
represent the numerical finite-size trend as an asymptotic theorem, do not
extrapolate weak drive to the full propagator, and do not spend QPU budget on
this claim.
