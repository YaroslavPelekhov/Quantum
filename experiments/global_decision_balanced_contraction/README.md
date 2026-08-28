# Global decision-balanced contraction

Linear two-pass Petrov--Galerkin contraction of a paired quantum-circuit
comparison. Unlike the earlier DBT experiment, the reduced coordinates are
never renormalized or used to rebuild later bases.

```powershell
$py = 'C:\Users\psgpe\Downloads\Taiwan\.venv\Scripts\python.exe'
& $py -m unittest experiments.global_decision_balanced_contraction.test_gdbc -v
& $py .\experiments\global_decision_balanced_contraction\run_gdbc.py development
& $py .\experiments\global_decision_balanced_contraction\analyze_gdbc.py
```

The development test failed its frozen 6/6 promotion criterion, so the
held-out transfer command was deliberately not run. See `PROTOCOL.md` for the
claim boundary and `../../results/global_decision_balanced_contraction/REPORT.md`
for the final negative result.
