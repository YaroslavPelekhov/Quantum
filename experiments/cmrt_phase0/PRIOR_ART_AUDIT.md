# CMRT adversarial prior-art boundary

Audit date: 2026-09-02.  This file defines what cannot be claimed even if the
offline screen and a later hardware study are positive.

## Occupied territory

The following components are established independently and are not novelty
claims here.

- Hardware-trained learning to rank logically equivalent circuit layouts and
  comparison to Mapomatic: Hartnett et al., *Quantum* 8, 1542 (2024),
  <https://quantum-journal.org/papers/q-2024-11-27-1542/>.
- Predictive quantum-computer capability models from circuit and device
  features: Hothem et al., <https://arxiv.org/abs/2304.10650>.
- Few-shot transfer of noise models between devices:
  <https://arxiv.org/abs/2604.24397>.
- Physics-informed circuit-fidelity prediction from calibration data:
  <https://arxiv.org/abs/2503.06693>.
- Machine-learning error mitigation on unseen circuits and observables:
  <https://www.nature.com/articles/s42256-024-00927-2>.
- Metamorphic testing of variational quantum programs (MetaMorphQ):
  <https://arxiv.org/abs/2606.28742>.
- Calibration-snapshot dependence in hardware diagnostics:
  <https://arxiv.org/abs/2608.26010>.
- Broad multi-method QAOA hardware benchmarking:
  <https://arxiv.org/abs/2607.11637>.
- Split conformal prediction, normalized/nonconformity scores, group/block
  conformalization, and abstaining/selective prediction are standard tools.

The local matched noise-model witness branch is also closed: standard random
sampling recovered at least 90% of its optimum in all 128 registered trials,
while gate-set tomography, randomized benchmarking, and context-aware model
violation tests already occupy the broad diagnostic capability.

## Narrow candidate not located in this audit

The only unoccupied conjunction found is:

> use disagreement across approximate but exact-equivalent quantum-simulation
> representations as a heteroscedastic nonconformity scale for a
> split-conformal interval on the *hardware sign of an application-event gap
> between two non-equivalent algorithmic schedules*, with abstention and
> whole-instance held-out validation.

This is a conjunction, not proof of novelty.  The burden is therefore higher
than showing correlation or a positive hardware example.  The spread must add
material selective value beyond ordinary margin, calibrated noise,
gate-count/error-product, and existing ranker baselines.  Otherwise CMRT is an
incremental assembly of occupied ideas and must be killed.

## Claims explicitly prohibited

- first hardware performance predictor;
- first quantum circuit ranker;
- first use of metamorphic testing in quantum software;
- first application of conformal prediction to quantum data;
- generic uncertainty quantification from simulator ensembles;
- hardware validation based on a calibrated simulator;
- independent evidence from pairwise contrasts that share one circuit job;
- an A* result based on one backend, one calibration snapshot, or a
  post-selected schedule cohort.

## Search result that would terminate the branch

Any primary work predating this freeze that directly predicts the sign of an
application-observable difference between non-equivalent quantum schedules,
uses exact-equivalent simulator/representation disagreement as its calibrated
selective scale, and validates on held-out hardware blocks terminates the
novelty claim even if our implementation performs well.
