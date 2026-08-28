# Sparse-MPS DCS-RDT

Direct construction of the decision-conditioned signed reduced operator from
Aer MPS tensors and a sparse BKS support. The algorithm never requests a full
statevector or a `2^n` event mask.

```powershell
$py = 'C:\Users\psgpe\Downloads\Taiwan\.venv\Scripts\python.exe'
& $py -m unittest experiments.sparse_mps_dcsrdt.test_sparse_mps -v
& $py .\experiments\sparse_mps_dcsrdt\run_sparse_mps.py development
& $py .\experiments\sparse_mps_dcsrdt\run_calibrated_replication.py
& $py .\experiments\sparse_mps_dcsrdt\run_snapshot_semantics.py
& $py .\experiments\sparse_mps_dcsrdt\analyze_sparse_mps.py
```

The development stage failed its deliberately strict cross-backend numerical
identity threshold, so the large transfer stage was not promoted. The report
separates that frozen negative verdict from the successful same-MPS algebraic
identity diagnostic.

A separately frozen calibrated replication also failed 0/4. The semantics audit
locates the large discrepancy in Aer's truncated-MPS terminal snapshot path.
