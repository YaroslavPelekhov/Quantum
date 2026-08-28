# Decision-conditioned signed reduced-density truncation report

## Verdict

**Superseded by the 2026-08-28 structural-rank audit.**  The algebraic
identities and frozen numerical rows below remain correct, but their original
novelty interpretation does not.  The machine-precision ranks for ibm32,
chesapeake, and football are completely predicted by sparse-event structural
rank, and Haar states attain the same ranks on every cut.  DCS-RDT by itself is
therefore not promoted as a novel truncation method.

The surviving result is narrower: on the 24-qubit aves MIS instance, QAOA has a
parameter-invariant ansatz/event rank deficit below the event-matching generic
cap.  That phenomenon and its held-out symmetry-rich transfer are reported in
`results/symmetry_quotient_decision_rank/REPORT.md`.

This remains an exact-state feasibility construction, not a scalable simulator.

## Construction and theorem

For `Gamma=|B><B|-|A><A|`, decision effect `E`, and split `L|R`, define

`K_L = Tr_R((E Gamma + Gamma E)/2)`.

Then `K_L` is Hermitian and `Tr(K_L)=Tr(E Gamma)`, the exact global
decision gap. For `E=I`, it reduces to the original signed reduced density
`rho_L^B-rho_L^A`. Keeping the `k` eigenmodes with largest absolute
eigenvalues gives the optimal rank-k approximation in every Schatten norm.
For discarded eigenvalues `lambda_i`, the actual gap error is
`|sum_i lambda_i|` and is certified by `sum_i |lambda_i|`.

## Frozen fixed-rank results

| stage | case | ordering | rank | exact gap | DCS bound | vs SRDT | vs state avg | pass |
|---|---|---|---:|---:|---:|---:|---:|:---:|
| development | ibm32 | sorted | 8 | -0.246123 | <1e-15 | >5.50e+13x | >2.77e+13x | yes |
| development | ibm32 | spectral | 8 | -0.246123 | <1e-15 | >3.90e+13x | >2.37e+13x | yes |
| development | aves-sparrow-social | sorted | 8 | -0.012139 | 0.007024 | 5.12x | 8.65x | yes |
| development | aves-sparrow-social | spectral | 8 | -0.012139 | <1e-15 | >1.64e+13x | >2.27e+13x | yes |
| transfer | chesapeake | sorted | 4 | -0.134214 | <1e-15 | >6.18e+13x | >9.21e+13x | yes |
| transfer | chesapeake | spectral | 4 | -0.134214 | <1e-15 | >3.27e+13x | >6.96e+13x | yes |
| transfer | football | sorted | 4 | +0.019269 | <1e-15 | >2.37e+13x | >4.30e+13x | yes |
| transfer | football | spectral | 4 | +0.019269 | <1e-15 | >2.62e+13x | >4.53e+13x | yes |

Factors marked `>` are conservative lower bounds obtained by replacing a
machine-zero denominator with `1e-15`; they should be read as exact-at-rank,
not as meaningful fourteen-digit speedup estimates.

## Certification and numerical rank

| case | ordering | first sign-certified rank | numerical DCS rank |
|---|---|---:|---:|
| ibm32 | sorted | 1 | 2 |
| ibm32 | spectral | 1 | 2 |
| aves-sparrow-social | sorted | 8 | 16 |
| aves-sparrow-social | spectral | 4 | 4 |
| chesapeake | sorted | 1 | 2 |
| chesapeake | spectral | 1 | 2 |
| football | sorted | 1 | 4 |
| football | spectral | 1 | 4 |

DCS-RDT certifies the decision sign within the tested ladder on all eight
rows. The hardest row is `aves-sparrow-social/sorted`: rank 8 certifies
the small negative gap and rank 16 makes the contribution operator exact.
At rank 8 its finite residual improvement is 5.12x over SRDT and 8.65x
over the state-averaged basis.

## Novelty boundary

The Jordan product, difference densities, observable-focused tensor-network
methods, and spectral low-rank truncation all predate this experiment. The
candidate novelty is their specific combination into a spatially reduced
paired-decision contribution operator with an exact gap trace, signed spectral
certificate, and frozen equal-rank transfer benchmark. A targeted search found
no exact match, but absence from search is not proof of priority. See
`experiments/decision_conditioned_srdt/PRIOR_ART.md`.

## Limitations and next step

The current oracle constructs `K_L` from exact terminal states and the full
BKS effect. It proves comparison compressibility, not cheap constructibility.
The next real algorithmic question is whether `K_L` or its dominant signed
modes can be accumulated directly as a tensor network with a propagated tail
certificate, without first materializing either exact state.
