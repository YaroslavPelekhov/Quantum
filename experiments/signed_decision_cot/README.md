# Signed Decision-Gap COT

This experiment replaces the absolute-sum ranking radius by a signed,
recentered interval for the decision gap while retaining the full certified COT
remainder.  See `THEORY.md` for the proof and `PROTOCOL.md` for the frozen
low-bond ladder.

Retrospective archived-artifact analysis:

```bash
python experiments/signed_decision_cot/analyze_signed_decision.py
python experiments/signed_decision_cot/test_signed_decision.py
```

Frozen low-bond witnesses:

```bash
python experiments/compressed_observable_telescope/run_residual_cot.py \
  --primary-schedule "1-319:512,320-383:384,384-447:256,448-511:128,512-555:64" \
  --residual-bonds "32,64,96,128" --ordering sorted --output-tag signed-gap-lowbond

python experiments/compressed_observable_telescope/run_residual_cot.py \
  --primary-schedule "1-319:512,320-383:384,384-447:256,448-511:128,512-555:64" \
  --residual-bonds "32,64,96,128" --ordering spectral --output-tag signed-gap-lowbond
```

Then pass the two new JSON files to `analyze_signed_decision.py` through
`--sorted-extra` and `--spectral-extra`.

