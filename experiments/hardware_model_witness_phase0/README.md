# Hardware noise-model witnesses: Phase 0

This directory contains the preregistered, simulator-only falsification screen
for the proposed matched-circuit-pair hardware noise-model witness.  It is not a
hardware result and it is not presented as a novelty claim.

The experiment enumerates one-qubit native-pulse sequences over
`Xp, Xm, Yp, Ym`.  Candidate pairs must have all of the following exactly in
common:

- ideal operation (identity, up to global phase);
- native gate multiset;
- width, sequential depth, and topology exposure; and
- the declared isolated-gate depolarizing prediction.

The hidden oracle contains coherent over-rotation and quasi-static detuning.
The declared model is calibrated to the isolated average fidelity of every
native gate, but discards coherent phase and temporal ordering.  Exhaustive
search finds the largest difference in measured `P(0)` inside each matched
equivalence class.  The same witness objective is compared with uniform random
matched pairs and simple cyclic-shift constructions.  Repeated short germs are
also tested as a standard characterization baseline for detecting model
residuals without the matching constraint.

Run:

```powershell
python experiments/hardware_model_witness_phase0/run_phase0.py
python -m unittest experiments.hardware_model_witness_phase0.test_witness_core
```

Outputs are written to `results/hardware_model_witness_phase0/`.
