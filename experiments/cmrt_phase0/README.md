# CMRT Phase 0

This package contains the preregistered offline falsification of Conformal
Metamorphic Rank Transfer (CMRT): using disagreement across approximate,
exact-equivalent simulator representations as a split-conformal scale for the
hardware sign of a QAOA schedule-event gap.

The terminal result is **`KILL_CMRT_AS_ASTAR_SOURCE`**.  Representation spread
correlates with synthetic hardware residuals, but the rule abstains too often,
misses the simultaneous-coverage and shifted-device gates, does not improve on
strong baselines at matched coverage, and is built on shot-starved fallback
schedules.  No QPU run is authorized.

Run from the repository root:

```powershell
python -m pytest experiments/cmrt_phase0 -q
python -m experiments.cmrt_phase0.run_phase0
python -m experiments.cmrt_phase0.finalize_phase0
```

Key files:

- `PREREGISTRATION.md`: frozen claim, cohort, baselines, and kill gates;
- `PRIOR_ART_AUDIT.md`: occupied territory and the narrow candidate boundary;
- `CORRECTION_LOG.md`: conservative evaluator corrections made after the first
  negative run and before the recorded rerun;
- `cmrt_core.py`: deterministic conformal/selective statistics;
- `synthetic_qaoa.py`: pure-NumPy exact and TT-truncated QAOA-MIS simulator;
- `legacy_ibm_archive.py`: read-only validation of two historical
  `ibm_boston` jobs, explicitly excluded from inference;
- `../../results/cmrt_phase0/FINAL_REPORT.md`: binding outcome.
