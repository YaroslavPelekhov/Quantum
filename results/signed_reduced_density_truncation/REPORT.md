# Signed reduced-density truncation report

## Verdict

The signed reduced-density rule is a **supported local comparison primitive**.
It has an exact minimax trace-norm certificate, an explicit pure-state
rank separation, and it passes the frozen real-data transfer criterion.
Its decision-conditioned successor now preserves the global BKS gap as
a local operator trace, but neither result is yet a scalable simulator.

## Frozen real-data transfer slice

Equal retained subspace dimension `k=8`, cut 5:

| case | ordering | signed relative error | state-averaged relative error | improvement |
|---|---|---:|---:|---:|
| ibm32 | sorted | 8.7261% | 28.1747% | 3.23x |
| ibm32 | spectral | 6.0671% | 22.2474% | 3.67x |
| aves-sparrow-social | sorted | 10.3682% | 39.1344% | 3.77x |
| aves-sparrow-social | spectral | 0.6543% | 6.7720% | 10.35x |

All four prespecified rows exceed the 2x threshold. Across the complete
nonzero-tail ladder, observed improvement ranges from `1.49x`
to `75.53x`; no row violates signed optimality.

## Synthetic separation

The constructed pair consists of two pure states with a shared maximally
entangled component and branch-specific Schmidt modes. At 16 total qubits:

- rank required by either state for 0.99 fidelity: `253`;
- exact signed reduced-density rank: `2`;
- rank ratio: `126.5x`;
- norm-one witness contrast: `0.200`.

The state rank grows as `2^m`, while the signed rank remains two.
This separates local comparison from faithful representation of either
state; it does not by itself separate SRDT from every observable-specific
or multi-state algorithm.

## The certified object

For `Gamma_L = rho_L^B-rho_L^A`, retain the `k` eigenmodes with largest
absolute eigenvalues. The discarded sum `sum_{i>k}|lambda_i|` is both:

1. the exact trace-norm error of the rank-k approximation; and
2. a simultaneous error bound for every local observable with operator norm at most one.

This is a different optimization target from the positive state average
`(rho_A+rho_B)/2`, which minimizes state-representation loss.

## End-to-end successor result

The current result is terminal-state and cut-local. The QAOA BKS projector
is global, so this report does not claim an end-to-end BKS speedup.
A frozen rank-1 `karate` test of the forward-only contrast-augmented
successor failed: it was numerically indistinguishable from state averaging
on one ordering and therefore did not satisfy strict improvement on both.
Subsequent backward-environment Petrov--Galerkin experiments are reported
separately under `results/decision_balanced_truncation`; their held-out
schedule-pair transfer also fails the universal criterion (3/6).
The successful successor instead changes the compressed object itself:
`K_L=Tr_R({E,Gamma}/2)` combines the signed contrast with the BKS effect.
It reduces to SRDT for `E=I`, retains the exact global BKS gap in its trace,
and passes a frozen 4/4 development plus 4/4 held-out transfer benchmark.
See `results/decision_conditioned_srdt/REPORT.md`. It remains an exact-state
feasibility oracle rather than a finished simulator.

## Reproduction

```powershell
$py = 'C:\Users\psgpe\Downloads\Taiwan\.venv\Scripts\python.exe'
& $py -m unittest experiments.signed_reduced_density_truncation.test_srdt -v
& $py .\experiments\signed_reduced_density_truncation\run_srdt.py
& $py .\experiments\signed_reduced_density_truncation\run_end_to_end_heldout.py
& $py .\experiments\signed_reduced_density_truncation\analyze_srdt.py
```
