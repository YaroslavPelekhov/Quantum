# Quantum x Evolutionary Computing Research Artifact

Latest theorem-search continuation: the
[Pauli fourth-moment report](results/pauli_fourth_moment_phase0/REPORT.md)
proves `beta(G,1)=alpha(G)` for every simplicial claw-free frustration graph
and exhaustively screens all 261,080 connected order-nine graphs.  Of 128
non-rank SCF facet types, 115 now have an exact join reduction and 12 of the
13 residual alpha-three types close under a validated level-2 state-moment
relaxation.  The former last explicit atom, graph6 `HEhu|x|`, had a level-3
upper excess of `4.16e-5` before analytic reduction.  An exact four-hole
cancellation reduces that atom to one explicit scalar inequality.  That inequality is now proved on
all five primitive single-channel faces, and an exact Hessian-discriminant
argument excludes a maximum in the fully interior heavy simplex.  Exact KKT
elimination now also closes all four three-heavy relative interiors: two have
no positive stationary point, while the other two reduce to a complete
rational ridge with gap `48/2401` and a strict ascent direction into the
missing channel.  A further spectral reduction proves three of the six
two-heavy faces; exact KKT elimination closes the other three.  This proves
the whole positive-light stratum, and two explicit square-plus-monomial
certificates close the zero-light boundary.  The atom now satisfies the exact
equality `beta=alpha=3/2`.  A common one-hole spectral certificate now proves
four more residual types (`HCXmtiz`, `GQuvSw`, `HCZTmyz`, and `HQjRexz`).  Two
two-hole types then collapse to the same certificate by channel aggregation
or an equal-profile heavy rotation.  Thus 122 of 128 order-nine facet types
are exact and six residual types still
have only numerical SDP upper certificates.  The general weighted SCF claim
and A-star novelty are not yet confirmed.  No QPU run is justified for this
exact convex-geometric gate.

Latest hardware-transfer continuation: the preregistered
[CMRT offline Phase-0 report](results/cmrt_phase0/FINAL_REPORT.md) closes
simulator-disagreement scaling as a source of A-star novelty and as a reason to
spend QPU shots.  Approximate-representation spread does predict held-out
simulator-to-noise-surrogate residual magnitude (Spearman `0.780`), but the
conformal rule accepts only `27/108` signs, covers only `9/12` graph blocks,
has zero matched error reduction over exact-noiseless and nominal-noise
baselines, and drops to `7/9` accepted-sign accuracy under the frozen shifted
noise stress.  All 108 schedule comparisons required the preregistered fallback,
and a nonbinding 4,096-shot audit resolves only one contrast.  The complete
negative result, correction log, tests, hashes, and read-only legacy IBM archive
smoke audit are retained; zero QPU jobs were submitted.

Latest exact-event continuation: the
[event-conditioned-width Phase-0 report](results/event_conditioned_width_phase0/FALSIFICATION_REPORT.md)
closes the natural product proxy
`max_cut rank(E_cut) * 2^(2 p crossing_edges)` as a new width under K6.  A
single globally defined site-grouped tensor realizes that score exactly as an
ordinary linear TT-rank ordering objective.  Tie-aware exhaustive search over
48 small instances also leaves no joint-order headroom, and a 48-case dense
shape-only representation screen favors the best-order support MPO in every
case.  The full registered Phase 0 remains `INCOMPLETE_NO_PROMOTION`: the
reduction is for an artificial equality tensor, not the actual QAOA tensor, so
it does not kill every algebraic event-conditioned algorithm.  No QPU task was
submitted.  The only admissible continuation is now a non-factorizing,
cancellation-aware actual circuit/event algorithm with a proved separation;
another incidence-product score or relabeled co-ordering heuristic is closed.

The preceding [55-qubit sparse-event contraction study](results/exact_event_contraction/REPORT.md)
compiles all 384 decoded BKS solutions into a rank-5 spectral-order MPO and
computes their untruncated deterministic QAOA probability through depth 2,
with two cuTensorNet API paths agreeing within `8.49e-27`.  Depth 3 exceeds the
frozen workstation resource guard; depths 8 and 15 fail path search.  The
manuscript's ideal depth-15 winner is therefore still unresolved.

Latest research-cycle verdict: the
[Aquila gauge-quotiented resource screen](results/aquila_gauge_resource_phase0/FINAL_REPORT.md)
is **closed as an A-star direction**.  A new weak-drive theorem survives:
for any integrable scalar waveform with constant response margin, the physical
time-bandwidth product is lower-bounded by the minimum spectral total
variation over the complete vertex-gauge orbit.  A probabilistic argument
gives worst-case cost proportional to the `n 2^(n-1)` configuration edges.
The frozen held-out numerical gates nevertheless fail, the hard target has
exponential description length, no matching stronger-control compiler is
known, and the theorem does not cover finite-amplitude many-body dynamics.  A
post-hoc exact three-atom test makes that last boundary concrete: a `1.2 us`
one-mask pulse valid under the recorded provisional limits realizes an
oriented population cycle with `0.983860`
mean fidelity, while the time-reversed pulse realizes the inverse cycle.
Zero QPU tasks were submitted.  The retained result is therefore a scoped
technical theorem and falsification artifact, not a quantum-advantage claim.

The preceding
[Aquila configuration-curvature validation](results/aquila_configuration_curvature_phase0/FINAL_REPORT.md)
reproduces a strong branch-free interaction-by-mask directional response
(`chi=0.242291`) with exact zero-interaction, equal-mask, local-envelope-off,
and palindrome nulls, 100% sign retention across 256 perturbations, and
unretuned transfer to frozen three- and four-atom geometries.  A principal-log
Wilson diagnostic has flux `1.570506 rad`, but the effective flux is logarithm-
branch dependent.  The mechanism is density-dependent Peierls hopping with
direct prior art, so the A-star claim is closed and no QPU run is authorised.
The subsequent exact compiler audit also falsifies the tempting replacement
claim that one static mask enforces a globally low-rank curvature tensor:
generic ranks are already the full `5,17,49,129` for three through six atoms;
only the perturbative tangent is low rank.  The remaining exponential
time-bandwidth bound is conditional on fixing independent edge responses; a
curvature-only, gauge-quotiented hardware separation remains unproved.

The earlier
[Aquila one-static-mask control screen](results/aquila_one_mask_phase0/FINAL_REPORT.md)
found full small-system Lie rank but killed the practical claim.  Its frozen
optimizer reported near-unit fidelity on a coarse grid; an independent adaptive
ODE audit reduced the two hardware-facing target fidelities to `0.787188` and
`0.683809`, with robustness fifth percentiles near `0.11--0.13`.  This branch is
also closed as novelty because the algebraic mechanism is standard finite-
ensemble/frequency-selective control.

Latest research-cycle verdict: the
[causal boundary-response kernelization cycle](results/causal_boundary_response_phase0/FINAL_REPORT.md)
is **closed as an A* quantum-simulation primitive**.  A tuned four-atom path
does approximate a 13-atom path at `T=5` (maximum complex response errors
`0.005996` uniform and `0.000401` after a 3% perturbation) and transfers with
small absolute error to 30 held-out UDG hosts.  The robust separation fails:
uniform-host median gain over an inherited P4 is only `1.386x`, and the final
multi-switch process-Gram audit reduces the apparent `10.32x` one-slice gain to
`2.963x` at its adversarial two-bin split.  Closely related fitted bath
terminations, Rydberg boundary sinks, and interacting-spin-chain reduced models
already exist.  No QPU run is authorised.

The preceding research-cycle verdict: the
[dynamical kernel geometry Phase 0](results/dynamical_kernel_geometry_phase0/FINAL_REPORT.md)
is **closed as an A* separation family**.  Two connected constant-deletion
families and an exhaustive grammar of 84 rooted-petal families were tested; 73
were endpoint-bijective and the top 12 received high-accuracy dynamics and gap
confirmation.  Zero passed all frozen gates.  The closest near miss has
log-success slope `0.181664` with `R2=0.994407` and gap distortion at most
`1.07016x`, but its absolute effect falls to `0.10658` and the graph is only a
star reduced to independent vertices.  No H200 or QPU run is authorised.

The preceding research-cycle verdict: the
[quantum-safe Rydberg MIS kernelization Phase 0](results/quantum_safe_kernelization_phase0/FINAL_REPORT.md)
is **closed as an A* direction in its static graph-reduction form**.  Across 793
exact leaf reductions, an apparent `100.633x` gap effect vanished after removing
the final driver ramp-down: zero cases retained `5x`, and the strongest
endpoint-bijective case was `1.399x`.  A broad native-driver screen did find a
real `0.394655` finite-time success difference, but its strongest example is
already a four-vertex triangle-plus-leaf reduced to a single edge.  Static
forced-selection lifts also have exact initial projector distance one and
finite-drive leakage norm `|Omega|/2`.  No H200 or QPU run is authorised.

The preceding research-cycle verdict: the
[matched hardware noise-model witness Phase 0](results/hardware_model_witness_phase0/FINAL_REPORT.md)
is **closed as an A* direction**.  Exact enumeration found a valid matched
counterexample (`P(0)` gap `0.010490330501` under an exact declared-model tie),
but long-sequence GST/iterative RB already supply the core error-amplification
capability and random matched-pair search recovered at least 90% of the optimum
in 128/128 trials at 1,024 queries.  No QPU run is authorized from this branch.

Latest comparison-native result: [Signed reduced-density truncation](results/signed_reduced_density_truncation/REPORT.md) provides a sharp local-observable minimax certificate, a pure-state rank separation, and a frozen `ibm32`/`aves` transfer benchmark. Its global-BKS end-to-end extension remains open.

The subsequent [decision-balanced truncation](results/decision_balanced_truncation/REPORT.md) study found a 6/6 equal-work development result, but only 3/6 on a frozen held-out schedule pair; the universal end-to-end claim is therefore closed.

Reproducible research repository on evolutionary QAOA schedule transfer and
the reliability of approximate tensor-network benchmarking on real QOBLIB
Maximum Independent Set instances.

The final contribution is not a quantum-advantage claim. It is an
application-facing validation rule for approximate simulation: before declaring
one QAOA schedule better than another, the simulator error must be small relative
to the observed performance margin.

## Final headline result

The frozen exact replication contains:

- five real QOBLIB MIS cases reduced to 3, 7, 7, 18, and 24 qubits;
- five MPS bond/cutoff settings;
- the published linear ramp, a prior evolutionary schedule, and an
  equal-budget matched-random schedule;
- sorted and spectral qubit orderings; and
- Qiskit Aer MPS and NVIDIA cuTensorNet MPS.

This gives 300 dense backend rows: 240 newly executed after protocol freeze and
60 reused only after SHA-256 validation.

| Primary outcome | Result |
|---|---:|
| Correct matched-random-vs-LR effect signs | **91/100** |
| Aer/cuTensorNet sign agreement | **45/50** |
| Verified event-effect TVD inequalities | **100/100** |
| Exact-margin TVD certificates | **77/100** |
| Correct signs inside certificate | **77/77** |
| Correct signs outside certificate | **14/23** |
| Fidelity-only certificates | **58/100** |

For BKS event `A`, schedules `i,j`, exact distributions `p`, and approximate
distributions `q`,

```text
|(q_i(A)-q_j(A)) - (p_i(A)-p_j(A))|
    <= TVD(q_i,p_i) + TVD(q_j,p_j).
```

Therefore the approximate sign is certified whenever the exact effect magnitude
exceeds the summed TVD budget. Every certified cohort preserves the exact sign.
All nine observed failures occur on the 24-qubit case with the smallest exact
effect margin. The descriptive Fisher comparison across the certificate
threshold is `p=4.30e-7`; the guarantee itself is deterministic and does not
depend on that statistical test.

## Observable-Telescope RankCert follow-up

The latest follow-up replaces the globally accumulated MPS angle with a
BKS-observable-specific exact telescope. On the identical 7-qubit cohort it
strictly certifies **14/20** LR-vs-MR rankings, versus **4/20** for the original
accumulated-angle bound, with zero wrong certified signs. A memory-bounded 18q
pilot on the real `ibm32` circuit certifies the `confirm` (bond 128, cutoff
`1e-4`) and `cutoff1e-5` settings; the released low-resource setting correctly
remains uncertified.

This is an a posteriori exact-backward verifier and still scales exponentially;
it is evidence for an observable-aware certificate design, not yet the final
scalable algorithm. See the [combined research report](results/observable_telescope/REPORT.md)
and [reproduction commands](experiments/observable_telescope/README.md).

A subsequent [Certified Compressed Observable Telescope audit](results/compressed_observable_telescope/REPORT.md)
proved and tested the proposed compressed bound on `ibm32`. Fixed backward
bonds 8-64 fail, but the residual-aware depth-adaptive construction preserves
the ranking certificate with residual bond 256: full paired width `0.210617`
versus MPS gap `0.254904`, leaving margin `0.044287`. Residual bond 128 fails,
providing a measured compression threshold rather than a post-hoc success-only
claim. The primary backward bond rises from 64 on the easy suffix to the exact
18-qubit central rank 512 only where entanglement requires it. Without retuning,
the prespecified R256 endpoint also passes a frozen spectral-ordering held-out
test with width `0.060896` versus gap `0.253936`.

A subsequent frozen local test evaluated whether forward Schmidt modes should
instead be selected directly for BKS accuracy. On the diagnosed `ibm32`
checkpoint, the goal-aware subset improved BKS error by only `1.019x` at the
same rank, while Schmidt mass and decision importance had Spearman correlation
`0.99944`. Neighboring cuts gave at most `1.049x`. This negative kill-test does
not support building a decision-optimal MPS simulator from the current
single-observable subset objective; see the
[DOT report](results/dot_mps_kill_test/REPORT.md).

One tested engineering direction was joint decision-certified resource
allocation, rather than a new Schmidt truncation heuristic. On the complete
5 x 5 `ibm32/sorted`
portfolio, allowing different accuracy levels for the two competing trajectories
finds `released/confirm` as the minimum-cost certified pair: 20.024 s versus
22.451 s for the best symmetric `confirm/confirm` pair, a 10.81% measured
forward-simulation saving. The allocation was then frozen before a spectral
held-out run; it again certified the correct direction and used 12.742 s versus
13.759 s, a 7.39% saving. See the
[allocation report](results/decision_certified_allocation/REPORT.md),
[theorem and novelty boundary](experiments/decision_certified_allocation/NOVELTY_AND_THEOREM.md),
and [frozen held-out protocol](experiments/decision_certified_allocation/SPECTRAL_HELDOUT_PROTOCOL.md).
These savings remain valid within the measured portfolio, but a subsequent
adversarial novelty audit places the optimization in established
goal-oriented error allocation/KKT territory.  It is therefore not the current
A-star direction and is not evidence of an algorithmic separation.

The next refinement allocates the COT residual-witness bond jointly across
trajectory and checkpoint. A prespecified schedule built by independently
mixing fixed R128/R256 checkpoint diagnostics failed by `1.95e-4`, demonstrating
the irreversible residual-tail effect. A causal asymmetric rescue then used
R256/R128 only on the difficult LR witness and fixed R128 on matched-random. On
`ibm32/sorted` it retained a strict certificate (width `0.247714` versus gap
`0.254904`, margin `0.007191`) with **62.35% lower paired cubic bond-work** than
R256/R256. The schedule retained soundness on the frozen spectral transfer, but
used `3.012x` the work of the already sufficient spectral R128/R128 baseline;
resource optimality therefore did not transfer. See the
[causal allocation report](results/decision_certified_bond_allocation/REPORT.md),
[proof](experiments/decision_certified_bond_allocation/THEORY.md), and
[literature boundary](experiments/decision_certified_bond_allocation/LITERATURE_POSITIONING.md).

The subsequent methodological refinement was **causal certification debt**.
For local certified residual increments `e_kj`, checkpoint weights `a_t`, and
backward propagation `j -> {t:t<=j}`, the exact finite-sum identity

```text
sum_t,k a_t xi_kt = sum_j,k Lambda_j e_kj,
Lambda_j = sum_{t<=j} a_t
```

turns an irreversible future error burden into a price available at the moment
of compression. The proof includes the rank-two observable, explicit numerical
floor, capped enclosure, placement theorem, and KKT relaxation. An oracle-free
controller with one frozen shadow price then chooses residual bonds from
`{128,256,512}` without using dense errors or the exact answer.

On `ibm32/sorted` it certifies width `0.211779 < 0.254904` while saving **54.55%**
paired cubic bond-work versus R256/R256. With no retuning, spectral certifies
`0.063044 < 0.253936` at **70.39%** saving. On the separate QOBLIB `chesapeake`
control it selects R128 at every checkpoint and certifies with 87.5% nominal
saving. Across 456 dense audit checkpoints there are zero enclosure violations,
and every selected bond is the argmin of the frozen score. These are feasible
upper bounds within the stated policy class, not proofs of globally minimal
decision-certification cost; spectral still uses `2.368x` the already sufficient
all-R128 baseline. See the [proof and identity audit](experiments/causal_certification_debt/THEOREMS.md),
[frozen protocol](experiments/causal_certification_debt/CONTROLLER_PROTOCOL.md), and
[controller report](results/causal_certification_debt/CONTROLLER_REPORT.md).

The latest follow-up retains the signed compressed telescope contributions
instead of replacing every local term by its absolute value. This gives a
rigorous interval centered at the MPS gap corrected by the paired signed
telescope residual, while the unknown compressed-observable remainder remains
fully adversarial. On `ibm32/sorted`, the frozen R32/R32 residual policy is
certified with interval `[-0.453426,-0.038820]`; the legacy absolute-sum COT
abstains at the same resource point. The policy uses **99.80% less nominal
paired cubic residual work** than R256/R256. After hash freeze it transfers to
spectral ordering with interval `[-0.265197,-0.227049]` and no retuning.

The low-bond ladder also reveals a certified residual-policy rank reversal:
R32 has a smaller integrated sorted LR remainder than R64, R96, and R128.
Spectral ordering retains a later-depth version of the reversal. Across 144
dense low-bond audit rows there are zero operator violations. This is a
path-dependent certificate result, not a claim that lower-bond MPS states are
generally more accurate or that total COT runtime falls by 99.80%. See the
[signed decision report](results/signed_decision_cot/RESEARCH_REPORT.md),
[proof](experiments/signed_decision_cot/THEORY.md), and
[frozen transfer protocol](experiments/signed_decision_cot/SPECTRAL_TRANSFER_PROTOCOL.md).

## Motivating 55-qubit result

On `es60fst02` (186 original vertices, 55-qubit depth-15 circuit), the released
Aer MPS setting gives 101 BKS hits for the transferred nonlinear schedule and
41 for the published ramp in 15,000 shots each. Tightening only the truncation
cutoff reverses the ranking. Independent cuTensorNet sampling also loses the
nonlinear advantage as accuracy is tightened.

Strong classical controls dominate both QAOA schedules. Evolutionary search
also fails to beat its matched random-search control. These negative results
are retained: the contribution is benchmark validity and resource-aware
simulation, not optimizer or solver superiority.

## Start here

- [Main manuscript](experiments/evoq_mis_full_qoblib/paper/output/pdf/qaoa_mps_cross_backend_rank_reversal_manuscript.pdf)
- [Supplementary information](experiments/evoq_mis_full_qoblib/paper/output/pdf/qaoa_mps_cross_backend_rank_reversal_supplement.pdf)
- [One-page advisor brief](experiments/evoq_mis_full_qoblib/ADVISOR_BRIEF.md)
- [Aquila curvature terminal compiler theorem](experiments/aquila_configuration_curvature_phase0/COMPILER_THEOREM_AND_KILL.md)
- [Aquila curvature final report](results/aquila_configuration_curvature_phase0/FINAL_REPORT.md)
- [Aquila one-mask control final report](results/aquila_one_mask_phase0/FINAL_REPORT.md)
- [Current quantum A-star decision and next gates](docs/QUANTUM_ASTAR_DECISION_2026-09-02.md)
- [Frozen cross-case protocol](experiments/evoq_mis_full_qoblib/CROSS_CASE_REPLICATION_PROTOCOL.md)
- [Complete cross-case analysis](experiments/evoq_mis_full_qoblib/results/cross_case_replication/analysis.json)
- [Publication figure](experiments/evoq_mis_full_qoblib/results/figures/cross_case_replication.pdf)
- [Signed decision-COT research report](results/signed_decision_cot/RESEARCH_REPORT.md)
- [Equal-work reset-intervention report](results/signed_decision_cot/RESET_INTERVENTION_REPORT.md)
- [Frozen reset-intervention protocol](experiments/signed_decision_cot/RESET_INTERVENTION_PROTOCOL.md)
- [Contrastive tensor simulation kill-test](results/contrastive_tensor_simulation/REPORT.md)
- [Frozen contrastive protocol](experiments/contrastive_tensor_simulation/PROTOCOL.md)
- [Signed reduced-density truncation report](results/signed_reduced_density_truncation/REPORT.md)
- [Decision-balanced truncation report](results/decision_balanced_truncation/REPORT.md)
- [Global decision-balanced contraction report](results/global_decision_balanced_contraction/REPORT.md)
- [Decision-conditioned SRDT report](results/decision_conditioned_srdt/REPORT.md)
- [Sparse-MPS DCS-RDT constructibility kill test](results/sparse_mps_dcsrdt/REPORT.md)
- [Detailed reproduction guide](REPRODUCIBILITY.md)
- [Binding QAOA/MPS branch closure](docs/QAOA_MPS_BRANCH_CLOSURE.md)
- [Closed A* adversarial screen: hardware noise-model witnesses](docs/NEXT_ASTAR_ADVERSARIAL_SCREEN.md)
- [Hardware witness Phase-0 frozen protocol](experiments/hardware_model_witness_phase0/PREREGISTRATION.md)
- [Hardware witness Phase-0 final report](results/hardware_model_witness_phase0/FINAL_REPORT.md)

## Repository map

```text
experiments/evoq_mis_full_qoblib/
  run_cross_case_replication.py   export, self-tests, Aer/cuTN execution, analysis
  plot_cross_case_replication.py  paper statistics and final figure
  results/cross_case_replication/ 300 rows, 100 cohorts, hashes and summaries
  paper/                          LaTeX manuscript, supplement and stable PDFs
  test_*.py                       29 integrity/numerical tests
  *_PROTOCOL.md                   frozen decisions before target execution
  artifact_manifest.json         SHA-256 inventory of public artifacts
experiments/rankcert_mps/         accumulated-angle certificate and Aer audit
experiments/decisioncert_mps/     decision-aware bounds and held-out checks
experiments/observable_telescope/ exact-backward 7q/18q verifier
experiments/compressed_observable_telescope/ compressed-bound proof and 18q audit
experiments/decision_certified_allocation/ joint asymmetric decision allocation
experiments/decision_certified_bond_allocation/ causal per-witness bond allocation
experiments/causal_certification_debt/ proof, frozen controller, tests
experiments/signed_decision_cot/ signed interval, low-bond and reset protocols
experiments/contrastive_tensor_simulation/ comparison-native TT/M-D kill tests
experiments/hardware_model_witness_phase0/ matched-pair model-falsification kill test
experiments/signed_reduced_density_truncation/ signed local truncation and certificate
experiments/decision_balanced_truncation/ local Petrov--Galerkin transfer test
experiments/global_decision_balanced_contraction/ global linear contraction kill test
experiments/decision_conditioned_srdt/ target-conditioned SRDT theorem and transfer
experiments/sparse_mps_dcsrdt/ direct MPS construction and frozen kill test
experiments/dcsrdt_structural_audit/ event-support and Haar falsification
experiments/coherent_frontier_rank/ phase and schedule-pair controls
experiments/ansatz_event_rank/ broad synthetic QAOA kill test
experiments/symmetry_quotient_decision_rank/ symmetry-rich MIS rank transfer
experiments/symmetry_quotient_backend/ exact twin-orbit QAOA and decision core
experiments/symmetry_quotient_breadth/ all-case QOBLIB exact controls
experiments/symmetry_claim_falsification/ symmetry-preserving rank and optimized-baseline kill tests
experiments/aquila_one_mask_phase0/ exact one-mask control and adaptive-ODE falsification
experiments/aquila_configuration_curvature_phase0/ branch-free curvature and compiler-rank falsification
results/observable_telescope/     compact tables, raw contributions, report
results/compressed_observable_telescope/ bond ladder, oracle audits, verdict
results/decision_certified_allocation/ 5x5 grid and frozen held-out result
results/decision_certified_bond_allocation/ causal schedules, proofs, and audits
results/causal_certification_debt/ identity/controller audits and manifests
results/signed_decision_cot/ signed intervals, path/reset audits, hash manifests
results/contrastive_tensor_simulation/ equal-budget benchmark and full-M/D audit
results/signed_reduced_density_truncation/ local theorem and real/synthetic benchmarks
results/decision_balanced_truncation/ development and held-out transfer verdict
results/global_decision_balanced_contraction/ frozen development failure and manifest
results/decision_conditioned_srdt/ global-gap local operator benchmark and manifest
results/sparse_mps_dcsrdt/ constructibility identity failure and diagnosis
results/dcsrdt_structural_audit/ structural matching audit and corrected verdict
results/coherent_frontier_rank/ probability/phase/schedule controls
results/ansatz_event_rank/ failed broad generalization
results/symmetry_quotient_decision_rank/ 4/4 development and 2/2 transfer
results/symmetry_quotient_backend/ real 24q statevector-free 2/2 validation and completion audit
results/symmetry_quotient_breadth/ pre-existing cohort 7/7 breadth validation
results/symmetry_claim_falsification/ current verdict: prior symmetry/event claim rejected
results/aquila_one_mask_phase0/ pulse audit, robustness, diagnostics, terminal verdict
results/aquila_configuration_curvature_phase0/ exact controls, ranks, plots, terminal verdict
docs/QUANTUM_EVOLUTION_RESEARCH_MAP.md
prior_work/evolutionary_computing_portfolio/
QOBLIB, metriq-gym, baselines/    pinned upstream Git submodules
```

## Quick verification

```bash
git clone --recurse-submodules https://github.com/YaroslavPelekhov/Quantum.git
cd Quantum
python -m venv .venv
# Windows: .venv\Scripts\python -m pip install -r requirements.txt
# Linux:   .venv/bin/python -m pip install -r requirements.txt
cd experiments/evoq_mis_full_qoblib
python -m unittest discover -v -p "test_*.py"
python run_cross_case_replication.py analyze
python plot_cross_case_replication.py
```

The completed JSON checkpoints allow the final analysis and paper figure to be
regenerated without rerunning expensive backend simulations. Full Windows/WSL
commands and safety assumptions are in [REPRODUCIBILITY.md](REPRODUCIBILITY.md).

## Large exact states

Six dense 24-qubit reference states are 256 MiB each and exceed GitHub's normal
100 MB object limit. They are intentionally omitted from ordinary Git history.
Their filenames, byte sizes, and SHA-256 identities remain recorded in
`results/mps_ladder/exact_references.json` and the export manifests. Publish
them through Git LFS or a versioned release/archive when independent
state-by-state recomputation is required. The paper, compact results, circuits,
metrics, and certificate analysis are reviewable without them.

## Reproducibility status

- 300/300 dense backend rows complete.
- 29/29 integrity and numerical tests pass in the archived environment.
- Both backend axis-convention self-tests pass at near-machine precision.
- All long jobs use atomic checkpoints and hash-bound frozen manifests.
- Manuscript and supplement were rendered and visually checked page by page.
- Structured event records, errors, runtimes, software versions, and failed
  attempts are retained. Verbose ignored `.mps.log` streams can be regenerated
  from the frozen inputs and are not part of the portable artifact.

## Scope and limitations

This is an exact-calibrated noiseless simulator study, not quantum hardware
evidence. The 55-qubit target remains approximate. The five-case replication
uses one MIS reduction family, three frozen schedules, two simulator
implementations, and one GPU platform. Setting cohorts share circuits and are
not independent population samples, so the Fisher test is descriptive. The TVD
certificate is sufficient rather than necessary and currently requires an
exact reference distribution.

## Citation

Citation metadata are provided in [CITATION.cff](CITATION.cff). Author,
affiliation, venue, and DOI fields can be updated before submission without
changing the frozen experimental artifacts.
