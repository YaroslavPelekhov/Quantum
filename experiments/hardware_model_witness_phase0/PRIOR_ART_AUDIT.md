# Adversarial prior-art audit

Audit date: 2026-08-28.  Scope: primary papers and the canonical GST technical
review, searched specifically for experiment selection, model violation,
coherent-error amplification, context dependence, and circuit-dependent model
accuracy.

## Closest established capabilities

- Nielsen et al., *Gate Set Tomography*, Quantum 5, 557 (2021),
  <https://doi.org/10.22331/q-2021-10-05-557>.  Long-sequence GST selects short
  germs so that every estimable gate-set error direction is amplified by at
  least one germ.  This is already designed circuit synthesis for exposing
  error components hidden by per-gate summaries.
- Sheldon et al., *Characterizing errors on qubit operations via iterative
  randomized benchmarking* (2015), <https://arxiv.org/abs/1504.06597>.
  Repetition of a target gate within RB distinguishes coherent from incoherent
  error scaling and deliberately amplifies coherent error.
- Rudinger et al., *Probing context-dependent errors in quantum processors*
  (2018), <https://arxiv.org/abs/1810.05651>.  The paper gives statistically
  rigorous tests that reject context-independent circuit models and
  demonstrates crosstalk and drift detection on IBM hardware.
- Moueddene et al., *A context-aware gate set tomography characterization of
  superconducting qubits* (2021), <https://arxiv.org/abs/2103.09922>.  Its
  experiment-selection objective explicitly quantifies error accumulation and
  infers crosstalk and memory effects on cloud hardware.
- Dahlhauser and Humble, *Benchmarking Characterization Methods for Noisy
  Quantum Circuits* (2022), <https://arxiv.org/abs/2201.02243>.  The agreement
  between predicted and measured circuit fidelity is shown to depend strongly
  on circuit structure; direct empirical characterization is most accurate in
  their study.
- Gazit et al., *Quantum process tomography via optimal design of experiments*
  (2019), <https://arxiv.org/abs/1904.11849>.  Optimal experiment design for
  quantum process identification is therefore prior art at the broader level.

## What was not located

The audit did not locate the exact packaging constraint used here: return a
minimal pair with identical ideal operation and native-gate multiset, for which
a declared scalar calibration model predicts a tie but hardware rejects it.
That narrow output format is not enough for A* novelty by itself.  Its physical
mechanism and experimental-design purpose are already covered by GST germs,
iterative RB, model-violation tests, and context-aware GST.

## Adversarial verdict before experiments

The broad capability claim is already occupied.  A surviving contribution
would need a theorem or algorithm showing a nontrivial separation caused by the
matching constraint -- for example, substantially greater falsification power
under a fixed query/shot budget than random circuits and standard germs.  The
exact experiment is retained to test that possibility rather than to rescue
the broad claim by wording.
