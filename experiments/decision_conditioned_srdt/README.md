# Decision-conditioned signed reduced-density truncation

This experiment extends SRDT from the decision-blind local contrast
`Tr_R(Gamma)` to the target-conditioned contribution operator
`Tr_R({E,Gamma}/2)`. Its trace is the exact global decision gap.

```powershell
$py = 'C:\Users\psgpe\Downloads\Taiwan\.venv\Scripts\python.exe'
& $py -m unittest experiments.decision_conditioned_srdt.test_dcsrdt -v
& $py .\experiments\decision_conditioned_srdt\run_dcsrdt.py development
& $py .\experiments\decision_conditioned_srdt\run_dcsrdt.py transfer
& $py .\experiments\decision_conditioned_srdt\analyze_dcsrdt.py
```

The frozen development criterion passed, so the held-out transfer stage was
promoted and also passed. See the result report and `PRIOR_ART.md` for the
scoped novelty claim.
