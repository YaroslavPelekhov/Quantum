# Protocol deviations and audit trail

## 2026-08-03: simulator circuit semantics

The first validation and held-out MPS pass used `qiskit.transpile(...,
optimization_level=0)` before simulation. Inspection against the released
QOBLIB notebook showed that the published baseline sends native RZ/RZZ/RX
circuits directly to Aer MPS. At finite bond dimension, a basis decomposition
can change the MPS truncation sequence, so the first pass is retained only as a
transpilation-sensitivity audit:

- `results/validation_transpiled_audit.json`
- `results/blind_test_transpiled_audit.json`

The runner was corrected to match the published execution semantics. To avoid
outcome-driven reselection after the held-out result had been inspected, the
three champions frozen by the original validation pass remain unchanged. The
corrected confirmatory pass only re-evaluates those already frozen schedules.
Training used an exact statevector backend, so transpilation changed the gate
representation but not the simulated unitary and was not repeated.

