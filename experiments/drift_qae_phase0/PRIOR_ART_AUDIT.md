# Prior-art boundary for drift-aware amplitude estimation

Audit date: 2026-09-02.  This is an adversarial positioning note, not a claim
that absence from the searched sources proves novelty.

## Established neighboring results

- The canonical amplitude-estimation/query formulation originates with
  [Brassard et al.](https://doi.org/10.1090/conm/305/05215).
- Iterative and low-depth variants already trade coherent circuit depth for
  sampling cost: [Iterative QAE](https://doi.org/10.1038/s41534-021-00379-1)
  and [Low-depth QAE](https://quantum-journal.org/papers/q-2022-06-27-745/).
- Stationary noisy-likelihood models, schedule optimization, and error
  saturation are treated by
  [Brown, Goktas and Tham](https://arxiv.org/abs/2006.14145) and
  [Tanaka et al.](https://arxiv.org/abs/2006.16223).
- Noise-aware Bayesian experiment design already learns nuisance behavior
  during amplitude estimation:
  [Ramôa and Santos](https://quantum-journal.org/papers/q-2025-09-11-1856/).
- A general noise-resilient construction explicitly permits noise that differs
  across circuit depths: [Ding and Yang](https://arxiv.org/abs/2312.01084).
- Hardware robust-amplitude-estimation experiments already expose coherent
  error and device-stability limitations:
  [Kunitsa et al.](https://arxiv.org/abs/2410.00686).
- General noisy quantum-metrology bounds show why uncorrected Markovian noise
  usually removes Heisenberg scaling:
  [Escher, de Matos Filho and Davidovich](https://arxiv.org/abs/1201.1693) and
  [Kolodynski and Demkowicz-Dobrzanski](https://arxiv.org/abs/1303.7271).
- Temporal instability of real quantum processors and the failure of a static
  error model are established experimentally by
  [Proctor et al.](https://arxiv.org/abs/1907.13608).

## What the audit did not locate

The searched primary sources did not provide the exact combination of:

- a fixed ideal amplitude;
- wall-clock nonstationarity during an adaptive experiment;
- fully charged, time-interleaved matched references;
- anytime or finite-sample validity;
- and matching minimax upper/lower rates under a stated local drift class.

That combination was the original opportunity.  Phase 0 nevertheless closes
the broad version because natural subclasses already produce exact
nonidentifiability or the standard depth-noise information ceiling.

## Positioning constraint

None of the following is sufficient novelty:

- adding a Bayesian tracker to QAE;
- estimating one stationary or depth-dependent depolarizing parameter;
- observing that longer circuits lose visibility;
- showing a post-circuit readout model retains amplified scaling;
- treating reference circuits as free;
- reporting hardware drift without a theorem or prospective discriminant.

A defensible future claim would have to concern a sharp wall-clock
interpolation/identifiability boundary that survives this literature and is
not merely a classical calibration lemma attached to QAE.

