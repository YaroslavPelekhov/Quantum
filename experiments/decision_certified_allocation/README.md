# Decision-certified allocation

This experiment minimizes the joint MPS simulation cost needed to certify which
of two QAOA schedules has the larger BKS probability. It consumes exact
Observable Telescope radii from `results/observable_telescope` and measured
single-thread costs from `results/rankcert_mps`.

Run the design analysis:

```powershell
python experiments/decision_certified_allocation/analyze_allocation.py
```

After the frozen spectral inputs exist, add `--include-spectral`.
