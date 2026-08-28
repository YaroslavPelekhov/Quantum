# Decision-balanced truncation

Two-pass dense oracle for a comparison-native Petrov--Galerkin truncation.
Forward paired-state reachability is balanced against the backward BKS
decision subspace before every rank reduction.

The fixed-rank prospective protocol and adaptive schedule-pair transfer are
both complete. Fixed rank passes 3/6 rows; the adaptive development result is
6/6, but held-out schedule-pair transfer falls back to 3/6. The universal
end-to-end claim is therefore closed. See
`results/decision_balanced_truncation/REPORT.md`.

Run:

```powershell
$py = 'C:\Users\psgpe\Downloads\Taiwan\.venv\Scripts\python.exe'
& $py -m unittest experiments.decision_balanced_truncation.test_dbt -v
& $py .\experiments\decision_balanced_truncation\run_prospective.py
& $py .\experiments\decision_balanced_truncation\run_adaptive_exploratory.py
& $py .\experiments\decision_balanced_truncation\run_adaptive_transfer.py
& $py .\experiments\decision_balanced_truncation\analyze_dbt.py
```

This implementation deliberately uses dense state batches as a feasibility
oracle.  A positive result still requires an MPS/MPO implementation before any
scalability claim.
