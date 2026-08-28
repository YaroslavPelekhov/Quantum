# Twin-orbit quotient backend report

> **Performance claim superseded on 2026-08-28.**  Against an optimized Qiskit
> Aer statevector baseline, the median steady-state speedup is `1.24x`, not
> `23.90x`, and the frozen `2x` robustness gate fails.  Exactness and `10.11x`
> representation compression survive.  See
> `results/symmetry_claim_falsification/REPORT.md`.

## Verdict

The missing algorithmic bridge is now implemented and passes the frozen real
24-qubit validation **2/2**.  For the symmetry-rich aves MIS kernel, QAOA is
evolved exactly in count sectors of graph-twin orbits.  The primary path builds
neither a `2^24` complex statevector nor a dense DCS operator.

| ordering | full dimension | quotient dimension | compression | compile | two states | three decision cuts | pass |
|---|---:|---:|---:|---:|---:|---:|:---:|
| sorted | 16,777,216 | 1,658,880 | 10.11x | 2.58 s | 8.53 s | 0.118 s | yes |
| spectral | 16,777,216 | 1,658,880 | 10.11x | 2.57 s | 8.65 s | 0.097 s | yes |

Across 20,000 deterministic validation amplitudes per state/order, the maximum
probability error is `4.49e-17`.  At cuts 5, 9, and 12, every quotient DCS rank
equals the prior exact audit and every global-gap trace error is below `1e-10`.

## Measured dense comparison

One sorted 24-qubit dense trajectory of the same normalized MIS Hamiltonian took
`101.96 s` and occupied 256 MiB.  Quotient evolution takes an estimated `4.27 s`
per state and 25.31 MiB of coefficients:

- steady-state evolution speedup: `23.90x`;
- first-state speedup including compilation: `14.88x`;
- state-representation compression: `10.11x`;
- reference probability error: `7.32e-19`.

The compile result is reusable across every parameter schedule for the same
graph/order/ansatz.

## Breadth and failure surface

The cohort was not selected for twins: it was frozen by an earlier independent
QOBLIB screen.  Nontrivial twin sectors occur in 5/8 cases and yield 2.0--10.11x
state compression.  Exact quotient/dense validation passes all 7/7 non-aves
cases in addition to aves.  Mammalia-kangaroo gives 3.20x compression and 3.08x
evolution speedup; es60fst01 gives 2.37x and 2.12x.  Chesapeake and football
have no twins and correctly expose small-instance overhead rather than a false
speedup claim.  Full details are in
`results/symmetry_quotient_breadth/REPORT.md`.

## Algorithm

Vertices with identical external neighborhoods form true/false-twin classes.
For a class of size `m`, permutation invariance reduces its `2^m` basis states
to `m+1` normalized count sectors.  The cost Hamiltonian is diagonal in the
joint count basis.  The mixer `sum X_i` becomes a spin tridiagonal with coupling
`sqrt((k+1)(m-k))`; its exponential is applied along one quotient tensor axis.

Decision-conditioned factors query amplitudes by orbit label and assemble the
exact small core

`K_L = (P Z* + Z P*)/2`, with `rank(K_L) <= 2 mu_2`.

Thus symmetry reduction is applied to the variational circuit, while paired
event matching controls the comparison operator.  They are independent
reductions and multiply rather than substitute for one another.

## Novelty boundary

Orbit/quotient evolution itself is established in quantum-walk theory
([Krovi--Brun](https://arxiv.org/abs/quant-ph/0701173)); spatial symmetries in
parameterized circuits and symmetry-reduced QAOA objectives are also known
([Sauvage et al.](https://arxiv.org/abs/2207.14413),
[Shaydulin--Wild](https://arxiv.org/abs/2101.10296)).

The defensible new contribution is the **composition and certificate**:

1. capacity-two matching bound for a paired event-conditioned operator;
2. parameter-generic ansatz/event comparison-rank signature;
3. exact orbit-amplitude decision-core construction;
4. phase/Haar/broad-QAOA falsification controls;
5. frozen synthetic transfer and real 24-qubit statevector-free speedup.

No individual classical ingredient is claimed as new.  The current boundary is
symmetry-rich graph kernels; arbitrary asymmetric graphs can have quotient
dimension `2^n`.
