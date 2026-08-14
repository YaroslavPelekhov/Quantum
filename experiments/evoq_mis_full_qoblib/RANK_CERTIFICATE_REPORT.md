# Observable-rank certificate audit

For a BKS event and two schedules, the absolute error of their probability
difference is bounded by the sum of their two total-variation distances.
This is a sufficient, observable-level rank certificate; it is deliberately
more conservative than checking the realized sign against exact.

| Backend | Setting | Order | Approx effect | Actual error | TVD bound | Exact-margin certified | Sign correct |
|---|---|---|---:|---:|---:|---|---|
| Aer | released | sorted | +0.13847902 | 0.15061787 | 0.69884572 | False | False |
| Aer | released | spectral | +0.10527256 | 0.11741141 | 0.61485685 | False | False |
| Aer | confirm | sorted | +0.00134460 | 0.01348345 | 0.21640975 | False | False |
| Aer | confirm | spectral | +0.00181663 | 0.01395549 | 0.18416871 | False | False |
| Aer | bond128 | sorted | -0.00371651 | 0.00842234 | 0.06027424 | False | True |
| Aer | bond128 | spectral | -0.01190733 | 0.00023152 | 0.00404346 | True | True |
| Aer | cutoff1e-4 | sorted | +0.00085570 | 0.01299455 | 0.21537676 | False | False |
| Aer | cutoff1e-4 | spectral | +0.00181663 | 0.01395549 | 0.18416871 | False | False |
| Aer | cutoff1e-5 | sorted | -0.01223477 | 0.00009592 | 0.04255430 | False | True |
| Aer | cutoff1e-5 | spectral | -0.01283092 | 0.00069207 | 0.04791179 | False | True |
| cuTensorNet | released | sorted | -0.00828657 | 0.00385228 | 0.40306014 | False | True |
| cuTensorNet | released | spectral | +0.01684902 | 0.02898787 | 0.50795800 | False | False |
| cuTensorNet | confirm | sorted | -0.00781145 | 0.00432740 | 0.15295035 | False | True |
| cuTensorNet | confirm | spectral | +0.00429307 | 0.01643192 | 0.29130821 | False | False |
| cuTensorNet | bond128 | sorted | -0.00995499 | 0.00218386 | 0.14197866 | False | True |
| cuTensorNet | bond128 | spectral | +0.01669905 | 0.02883790 | 0.30522435 | False | False |
| cuTensorNet | cutoff1e-4 | sorted | -0.01203058 | 0.00010827 | 0.00602870 | True | True |
| cuTensorNet | cutoff1e-4 | spectral | -0.01220715 | 0.00006830 | 0.00617640 | True | True |
| cuTensorNet | cutoff1e-5 | sorted | -0.01215620 | 0.00001735 | 0.00078098 | True | True |
| cuTensorNet | cutoff1e-5 | spectral | -0.01232364 | 0.00018478 | 0.00167859 | True | True |

Summary: `{"approximate_margin_tvd_certified": 5, "cohorts": 20, "exact_margin_fidelity_certified": 2, "exact_margin_tvd_certified": 5, "sign_correct": 11}`
