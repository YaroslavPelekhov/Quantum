# Causal Certification Debt

Formal and numerical audit of

`sum_t a_t xi_t = sum_j Lambda_j delta_j`,

including the actual backward indexing, rank-two observable, explicit numerical
floor, capped operator enclosure, and executed sorted/spectral COT witnesses.

```powershell
python experiments/causal_certification_debt/analyze_debt.py
python -m unittest experiments.causal_certification_debt.test_debt -v
```

The frozen oracle-free controller uses causal price in a local cost-plus-debt
score. Rebuild its report and verify every choice with:

```powershell
python experiments/causal_certification_debt/analyze_controller.py
python -m unittest experiments.causal_certification_debt.test_controller -v
```

The central contribution and its nearest-work boundary are stated in
[`NOVELTY_POSITIONING.md`](NOVELTY_POSITIONING.md).
