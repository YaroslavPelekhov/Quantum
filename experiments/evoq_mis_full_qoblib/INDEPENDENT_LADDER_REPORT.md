# Independent cuTensorNet MPS audit

All 30 frozen jobs completed before this report was generated.

| Setting | Ordering | Matched effect | Exact effect | Aer effect | Exact sign | Aer sign | Min fidelity | Max TVD | Max BKS error | Cross-backend BKS delta |
|---|---|---:|---:|---:|---|---|---:|---:|---:|---:|
| released | sorted | -0.00828657 | -0.01213885 | +0.13847902 | True | False | 0.79808758 | 0.24000490 | 0.01300014 | 0.25959428 |
| released | spectral | +0.01684902 | -0.01213885 | +0.10527256 | False | True | 0.69803211 | 0.28289948 | 0.11585877 | 0.10456694 |
| confirm | sorted | -0.00781145 | -0.01213885 | +0.00134460 | True | False | 0.94267665 | 0.09908438 | 0.00492455 | 0.04451493 |
| confirm | spectral | +0.00429307 | -0.01213885 | +0.00181663 | False | True | 0.81256912 | 0.18159869 | 0.04760753 | 0.01836037 |
| bond128 | sorted | -0.00995499 | -0.01213885 | -0.00371651 | True | True | 0.94433415 | 0.08974136 | 0.00453683 | 0.00820178 |
| bond128 | spectral | +0.01669905 | -0.01213885 | -0.01190733 | False | False | 0.80727810 | 0.19723943 | 0.06007862 | 0.05982467 |
| cutoff1e-4 | sorted | -0.01203058 | -0.01213885 | +0.00085570 | True | False | 0.99727625 | 0.01052629 | 0.00012774 | 0.04049003 |
| cutoff1e-4 | spectral | -0.01220715 | -0.01213885 | +0.00181663 | True | False | 0.99721037 | 0.01073121 | 0.00015022 | 0.02931652 |
| cutoff1e-5 | sorted | -0.01215620 | -0.01213885 | -0.01223477 | True | True | 0.99999707 | 0.00045278 | 0.00001921 | 0.00440239 |
| cutoff1e-5 | spectral | -0.01232364 | -0.01213885 | -0.01283092 | True | True | 0.99998207 | 0.00124044 | 0.00022919 | 0.00330221 |

Primary interpretation is the exact-sign column. Cross-backend differences are
reported as diagnostics and do not replace exact adjudication.
