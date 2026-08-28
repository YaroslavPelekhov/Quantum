# RankCert-MPS local pilot

Isolated kill test for an exact-state-independent QAOA ranking certificate
derived from truncation information emitted by Qiskit Aer MPS.

The existing QAOA/QOBLIB protocols, QPY circuits, exact references, and result
files are immutable inputs.  This namespace does not optimize schedules,
retune reductions, alter decoding, use repair, submit cloud jobs, or overwrite
the frozen artifact.

Execution order and current status are recorded under
`../../results/rankcert_mps/`.

## Commands

Use the frozen Windows environment:

```powershell
$python = 'C:\Users\psgpe\Downloads\Taiwan\.venv\Scripts\python.exe'
& $python .\experiments\rankcert_mps\rankcert_inputs.py
& $python .\experiments\rankcert_mps\run_aer_semantics_audit.py audit
& $python .\experiments\rankcert_mps\run_rankcert_exact_cases.py --phase aves
& $python .\experiments\rankcert_mps\analyze_rankcert.py --phase aves
& $python .\experiments\rankcert_mps\run_rankcert_exact_cases.py --phase ibm32
& $python .\experiments\rankcert_mps\analyze_rankcert.py --phase ibm32
& $python .\experiments\rankcert_mps\run_rankcert_exact_cases.py --phase all
& $python .\experiments\rankcert_mps\analyze_rankcert.py --phase all
```

Every schedule run is a fresh child process because Aer 0.17.2 keeps its MPS
debug stream in static process state. The driver resumes completed JSON rows,
checks available physical RAM before each job, applies a two-hour per-job
timeout, and stops immediately on a BKS-error or TVD soundness violation.

The current safe pause and exact resume command are in
`../../results/rankcert_mps/FINAL_STATUS.md`.
