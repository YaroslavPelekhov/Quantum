# Adversarial prior-art audit and novelty verdict

Audit date: 2026-09-02.  Primary sources were checked for the mechanism and the
stronger open problem.  Failure to locate an exact paper is not proof of
novelty.

## Direct pressure on the simple claim

- Symmetric ABBA ordering and removal of polynomial drift are established by
  [Swanson and Schlamminger](https://arxiv.org/abs/1009.1894).
- Phase-congruent short/long Ramsey cycles and active common-mode balancing are
  used in [auto-balanced Ramsey spectroscopy](https://arxiv.org/abs/1707.02630)
  and its [generalized form](https://arxiv.org/abs/1712.03365).
- Quantum-processor drift characterization already uses time-resolved
  estimates and proposes interleaving characterization circuits with
  applications: [Proctor et al.](https://arxiv.org/abs/1907.13608).
- Past and future observations for phase estimation appear in
  [time-symmetric quantum smoothing](https://arxiv.org/abs/0912.1162).
- Quantum limits for time-changing signals are developed in
  [Tsang, Wiseman and Caves](https://arxiv.org/abs/1006.5407) and the
  [Bell-Ziv-Zakai waveform bounds](https://arxiv.org/abs/1409.7877).
- Fundamental clock/interrogation-time optimization under oscillator noise is
  treated by [Fraas](https://arxiv.org/abs/1303.6083).
- Simultaneous interleaved ensembles can remove dead-time local-oscillator
  noise, showing that the sequential limitation is architectural rather than
  universal: [Schioppo et al.](https://arxiv.org/abs/1607.06867).
- Nuisance-tangent projection is already formalized in quantum semiparametric
  estimation: [Tsang, Albarelli and Datta](https://arxiv.org/abs/1906.09871).

The exact equal-duration `C^2` constant plus QAE notation was not found as a
single prior result.  Nevertheless, affine cancellation is established, the
sharp `C^2` remainder is classical interpolation/optimal recovery, and the
cube-root follows from an elementary balance with `1/D`.  This is insufficient
for A* novelty.

## Stronger gap not solved here

The audit did not locate a result combining all of:

```text
wrapped Bernoulli QAE likelihood
+ adaptive multi-depth scheduling
+ noisy duration-matched references
+ wall-clock Holder drift
+ joint query and elapsed-time budget
+ matching minimax upper and lower bounds.
```

The relevant object would be a schedule-dependent modulus of continuity

```text
omega_S(epsilon) = sup |theta-theta'|
  subject to KL(P_(theta,d)^S || P_(theta',d')^S) <= epsilon
  and d,d' in a stated smoothness ball.
```

Solving that optimization for every adaptive schedule, then constructing a
matching protocol with global alias control, could be publishable.  The local
RTR result is only one lemma toward it and is not represented as the missing
theorem.

## Binding verdict

`PASSES_MATHEMATICAL_PHASE0` and `KILL_SIMPLE_CURVATURE_AS_ASTAR` are both true.
No QPU experiment is justified by this branch.

