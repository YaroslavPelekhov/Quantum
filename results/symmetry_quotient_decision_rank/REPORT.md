# Symmetry-quotient decision-rank report

> **Superseded by the 2026-08-28 aggressive falsification audit.**
> Symmetry-preserving Haar and orbit-phase controls reproduce every reported
> QAOA rank.  An amplitude-blind twin-count structural bound equals all 84
> synthetic and 53 real archived ranks.  The ansatz-specific interpretation
> below is withdrawn; see `results/symmetry_claim_falsification/REPORT.md`.

## Verdict

**Supported new phenomenon and method-level novelty package.**  A
parameter-invariant comparison-rank signature below both the
event-incidence matching cap and the individual-state Schmidt ranks passes
frozen development **4/4** and untouched held-out transfer **2/2**.

| stage | case | ordering | event support | automorphisms | max matching cap | max QAOA rank | deficit cuts | pass |
|---|---|---|---:|---:|---:|---:|---:|:---:|
| dev | triangle chain 4 | natural | 60 | 32 | 28 | 12 | 7 | yes |
| dev | triangle chain 4 | spectral | 60 | 32 | 24 | 14 | 8 | yes |
| dev | triangle chain 5 | natural | 164 | 64 | 44 | 18 | 10 | yes |
| dev | triangle chain 5 | spectral | 164 | 64 | 44 | 16 | 11 | yes |
| held-out | triangle ring 6 | natural | 416 | 768 | 76 | 20 | 13 | yes |
| held-out | triangle ring 6 | spectral | 416 | 768 | 68 | 22 | 12 | yes |

The strongest observed rank/cap ratio is `0.2273`.  The held-out 18-qubit state
has Schmidt rank up to 216 while its comparison operator never exceeds rank 22.
Independent phase scrambling restores the matching cap on every eligible cut;
all three depth-15 QAOA schedule pairs share the same lower profile.

On the held-out spectral cut 9, the exact small-core construction took 0.0082 s
versus 0.1183 s for dense construction plus diagonalization (`14.37x`) and
matched trace/trace norm within `8.5e-15`.  This is a descriptive single-machine
benchmark.  At aves spectral cut 12, the exact factor has 14 columns (about
0.88 MiB) versus a 256 MiB dense operator, although both methods still require
the two exact 24-qubit statevectors.

## Exact structural result

For event mask `M`, amplitude matrices `Psi_A,Psi_B`, and the coordinate
embedding `P` of event-active left prefixes, define

`Z = Psi_B C_B^* - Psi_A C_A^*`, where `C_psi=M hadamard Psi` restricted to
active rows.  Then exactly

`K_L = (P Z^* + Z P^*)/2`.

Hence `rank(K_L) <= 2 rank(Z) <= 2 mu_2`.  The nonzero spectrum can be obtained
from a core no larger than the structural cap, without materializing the dense
`2^cut x 2^cut` operator.

For a fixed real-analytic parameterized ansatz, the maximum rank is attained
away from the common zero set of its maximal minors; therefore its rank
signature is constant for almost every parameter pair and can only drop on an
exceptional set.  This explains why three independent schedules have identical
profiles, but not why the MIS family lies below the unrestricted event cap.

## Novelty boundary

The ingredients are not new separately: structural/term rank and matching are
classical; variable ordering is central to OBDDs; tensor networks already use
observable-specific contraction; and graph automorphisms have been used to
reduce QAOA energy evaluation.  Relevant primary references include
[Shaydulin--Wild](https://arxiv.org/abs/2101.10296),
[qTorch](https://arxiv.org/abs/1709.03636), and
[OBDD variable ordering](https://arxiv.org/abs/1909.12658).

The candidate novelty is the combined object: a **paired event-matching cap plus
an ansatz-specific generic comparison-rank signature**, with a small-core exact
factorization and phase-scramble/frozen-transfer falsification.  A literature
claim remains conditional until a dedicated search finds no equivalent
event-conditioned comparison-rank construction.

## Backend status

The former statevector blocker is resolved by the twin-orbit quotient backend
in `results/symmetry_quotient_backend/REPORT.md`.  On the real 24-qubit aves
cohort it passes 2/2 orderings, gives `10.11x` state compression and a measured
`23.90x` steady-state evolution speedup while reproducing archived probabilities
to `4.49e-17`.  The remaining publication work is breadth against additional
symmetry-aware simulators, not absence of an executable algorithm.
