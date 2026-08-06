# Frozen resource-aware protocol

Frozen on 2026-08-06 before any new resource-controller evaluation on the blind
instance `es60fst02`. Existing blind artifacts from the earlier schedule study
are baselines only and may not influence candidate promotion in this cycle.

## Question

Can an automated multi-fidelity controller reduce QAOA resources while
remaining statistically non-inferior to the published depth-15 linear ramp on
BKS, BKS-1, and raw feasible probability, with conclusions stable across two
MPS accuracy settings?

## Split and leakage control

- Exact training: `es60fst01`, `es60fst03`.
- MPS validation: `es60fst04`.
- One final blind confirmation: `es60fst02`.
- Blind outcomes never change the controller, margins, shortlist, or champion.
- Previously published `es60fst02` outcomes are used only as named baselines;
  the resource champion is selected exclusively from training and validation.

## Search space

- Schedule family:
  `beta_k = delta_beta*((p-k+1)/p)^beta_power`,
  `gamma_k = delta_gamma*(k/p)^gamma_power`.
- Schedule genomes: 32 deterministic scrambled-Sobol candidates plus the
  published LR, prior evolutionary, and prior matched-random schedules.
- Depths: `p in {3, 5, 8, 10, 12, 15}`.
- Qubit orderings: sorted and Fiedler/spectral.
- Reduction caps certified before search: `max_degree in {2,3,4,5,6}`.
- Released MPS setting: bond 64, discarded-weight cutoff `1e-3`.
- Confirmation setting: bond 128, cutoff `1e-4`.
- QUBO penalty 1.5; native RZ/RZZ/RX circuits; no basis transpilation.

## Reachability gate

For every reduction cap and instance, an exact HiGHS solve of the reduced
kernel is decoded to the full graph. A configuration is eligible for a BKS
claim only if the decoded optimum is raw-feasible and reaches the recorded full
instance BKS on training, validation, and blind graphs. The smallest eligible
cap is frozen for quantum evaluation. Empty kernels and lower-qubit reductions
that destroy BKS reachability are reported, not silently discarded.

## Multi-fidelity promotion

1. Exact statevectors on both training kernels evaluate all genome-depth pairs.
   Exact probabilities eliminate finite-shot selection noise.
2. A candidate is training-eligible only if, on each donor, its BKS probability
   is at least 75% of published LR at depth 15, its BKS-1 probability is at
   least 90%, and feasible probability is no more than 0.02 lower.
3. The nondominated set maximizes worst-donor BKS/BKS-1/feasible mass and
   minimizes depth and RZZ count. At most eight diverse schedule-depth points
   are promoted. Published LR and prior nonlinear depth-15 controls are always
   retained as controls, not as automatically eligible champions.
4. Both qubit orderings are screened on validation at bond 64/cutoff `1e-3`
   with four seeds and 250 shots per configuration and seed.
5. At most four resource candidates, plus controls, enter confirmation on
   validation at both accuracy settings with ten seeds and 500 shots.

All promotion decisions and input hashes are written before the next fidelity
stage runs.

## Validation target and champion rule

The published sorted-order LR schedule at depth 15 is the fixed reference at
each accuracy setting. For each candidate, paired job-level differences use a
50,000-resample bootstrap. At both settings the candidate must satisfy:

- BKS difference lower 95% bound greater than `-0.005`;
- BKS-1 difference lower 95% bound greater than `-0.02`;
- feasible difference lower 95% bound greater than `-0.02`;
- no raw-feasibility repair or archived-solution fallback;
- either depth below 15 or measured median runtime at least 10% lower.

Among eligible candidates, selection is lexicographic: minimum qubit count,
minimum RZZ count, minimum median wall time, minimum estimated shots for a 95%
chance of at least one BKS, then maximum worst-setting BKS lower bound. The
champion JSON and its SHA-256 digest are frozen before blind execution.

## Blind confirmation

The frozen champion, published LR, and the prior matched-random nonlinear
schedule are evaluated with 15 paired seeds and 1,000 shots per method at both
MPS accuracy settings. We report paired bootstrap intervals, exact sign-flip
tests, raw counts, Wilson bounds, runtime, gates, and required shots for 95%
BKS success. A failure of non-inferiority or accuracy stability is a negative
result and does not trigger retuning.

## Classical context

The existing zero-gap HiGHS solve and 15,000-start randomized minimum-degree
controls remain mandatory. A resource saving relative to fixed QAOA is not a
quantum-advantage claim.

