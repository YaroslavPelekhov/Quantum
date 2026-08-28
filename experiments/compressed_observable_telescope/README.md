# Certified Compressed Observable Telescope

This experiment audits the proposed rigorous bound

`sum_t (|Tr(O_t_tilde Delta rho_t)| + 2 sqrt(w_t) eta_t)`

on the frozen 18q `ibm32/confirm/sorted` LR and MR trajectories.

## Reproduce the completed analysis

```powershell
$py = 'C:\Users\psgpe\Downloads\Taiwan\.venv\Scripts\python.exe'
& $py .\experiments\compressed_observable_telescope\analyze_cot.py
& $py -m unittest experiments.compressed_observable_telescope.test_cot_core -v
```

The expensive constituent audits are:

```powershell
& $py .\experiments\compressed_observable_telescope\audit_forward_groups.py
& $py .\experiments\compressed_observable_telescope\run_backward_feasibility.py `
  --bonds 8,16,32,64 --setting confirm --ordering sorted
& $py .\experiments\compressed_observable_telescope\audit_backward_oracle.py
& $py .\experiments\compressed_observable_telescope\audit_recursive_eta.py
& $py .\experiments\compressed_observable_telescope\run_residual_cot.py `
  --primary-schedule '1-319:512,320-383:384,384-447:256,448-511:128,512-555:64' `
  --residual-bonds 128,256,512
& $py .\experiments\compressed_observable_telescope\run_compressed_first_term.py
```

## Verdict

The inequality is valid under the documented conditions, and every audited
local forward inequality holds. Fixed backward bonds 8-64 fail. The
residual-aware depth-adaptive successor succeeds on `ibm32/confirm/sorted` with
residual bond 256: full paired width `0.210617` versus MPS gap `0.254904`, for a
positive certificate margin `0.044287`. Residual bond 128 is a strict negative
control (`0.286767 > 0.254904`). The same schedule was frozen before a spectral
ordering held-out test; its prespecified R256 endpoint passes with width
`0.060896` versus gap `0.253936` (margin `0.193039`). See
`results/compressed_observable_telescope/REPORT.md`.
