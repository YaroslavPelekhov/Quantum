# Observable telescope pilot

Exact-backward feasibility oracle for a future BKS-aware MPS certificate. It
uses only frozen native QPY circuits and writes to `results/observable_telescope`.

```powershell
& 'C:\Users\psgpe\Downloads\Taiwan\.venv\Scripts\python.exe' `
  .\experiments\observable_telescope\run_observable_telescope.py
```

The memory-bounded 18q pilot replays exact prefixes in blocks. For example:

```powershell
$py = 'C:\Users\psgpe\Downloads\Taiwan\.venv\Scripts\python.exe'
& $py .\experiments\observable_telescope\run_observable_telescope_18q.py `
  --setting confirm --ordering sorted --block-checkpoints 64
& $py .\experiments\observable_telescope\build_report.py
& $py -m unittest experiments.observable_telescope.test_observable_telescope -v
```

The exact-backward method is a strict a posteriori feasibility oracle with
exponential cost, not yet a scalable internal certificate.
