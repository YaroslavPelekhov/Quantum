# C047 independent-runtime oracle report

## Verdict

The weighted skew-matrix inequality survives an independently implemented,
cross-language falsification suite. The oracle uses the legacy standard C#
compiler and .NET Framework runtime only. It shares no Python, NumPy, SciPy,
NetworkX, LP solver, or eigensolver with the research pipeline.

## Frozen results

| Quantity | Result |
|---|---:|
| Root graphs | 119 |
| Positive weight vectors | 952 |
| Gaussian skew directions | 3808 |
| Inequality violations | 0 |
| Largest random ratio | `1.0000000000000002` |
| Matching-supported equality directions | 952 |
| Maximum equality residual | `7.771561172376096e-16` |

Maximum-weight matching is implemented by subset dynamic programming. The
nuclear norm is obtained from a handwritten Jacobi diagonalization of `-A^2`.
Both source and frozen protocol hashes are recorded in the JSON result.

## Reproduce

```powershell
& C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe `
  /nologo /optimize+ `
  /out:experiments\pauli_fourth_moment_phase0\external_oracle_c047\ExternalOracle.exe `
  experiments\pauli_fourth_moment_phase0\external_oracle_c047\Program.cs
& experiments\pauli_fourth_moment_phase0\external_oracle_c047\ExternalOracle.exe
python -m unittest experiments.pauli_fourth_moment_phase0.test_c047_external_oracle -v
```

## Interpretation

This materially reduces the risk that the headline inequality is an artifact
of one implementation or numerical library. It cannot establish mathematical
priority and is not a substitute for an independent proof referee. The ideal
next external step is therefore a compact proof-challenge packet asking a
specialist to attack exactly three transitions: skew contraction to all
odd-set inequalities, nuclear duality to the weighted bound, and equality of
nonnegative support functions to equality of convex corners.
