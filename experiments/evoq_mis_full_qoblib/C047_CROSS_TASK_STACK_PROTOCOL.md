# C047: frozen cross-task / cross-stack external validation

Frozen before execution on 1 October 2026. This protocol is a post-manuscript
external-validity extension and is not pooled with the five-case QOBLIB
replication.

## Question

Does the observable-level TVD certificate remain correct after simultaneously
changing the optimization task, benchmark generator, circuit-construction SDK,
exact simulator, graph family, and qubit representation?

## Frozen design

- Task shift: QOBLIB MIS to unweighted MaxCut.
- Four deterministic graph generators, never used for schedule selection:
  3-regular order 10 (seed 47010), Erdos--Renyi order 12 with `p=0.32`
  (seed 47012), Watts--Strogatz order 14 with `k=4,p=0.25` (seed 47014),
  and 3-regular order 16 (seed 47016).
- Schedules: the already frozen published linear ramp and prior matched-random
  nonlinear ramp; depth 15; no MaxCut tuning.
- Representations: identity placement and one seeded random logical-to-physical
  permutation per graph.
- Exact stack A: Qiskit `Statevector` from independently constructed MaxCut
  circuits.
- Exact stack B: Amazon Braket SDK `LocalSimulator("braket_sv")` from circuits
  constructed directly in Braket, not converted from Qiskit.
- Approximate stack: Qiskit Aer MPS at five pre-specified settings:
  `(bond,cutoff)=(4,1e-2),(8,1e-3),(16,1e-4),(32,1e-6),(128,1e-12)`.
- Primary observable: exact maximum-cut probability.
- Primary pair: matched-random minus linear-ramp maximum-cut probability.

This gives 16 Qiskit exact rows, 16 Braket exact rows, 80 Aer/MPS rows, and 40
paired effect cohorts.

## Gates and analysis

1. The two independently constructed exact stacks must agree to TVD `<=1e-10`
   after the documented endian conversion.
2. Exact maximum-cut probabilities and schedule effects must be invariant to
   the two logical-to-physical placements to `1e-10`.
3. For each approximate cohort, verify
   `|Delta_MPS-Delta_exact| <= TVD_LR+TVD_NLR`.
4. A sign is certified only when
   `|Delta_exact| > TVD_LR+TVD_NLR`.
5. Report all sign failures, but do not tune settings, schedules, graph seeds,
   or placements after observing them.

The extension tests transport of the validation rule, not MaxCut performance,
quantum advantage, hardware behavior, or prevalence in a graph population.
Metamorphic and differential testing are prior paradigms; the contribution
here is the application-specific task-and-stack triangulation of a ranking
certificate, not a claim to have invented those paradigms.
