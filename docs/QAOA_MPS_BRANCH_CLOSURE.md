# QAOA/MPS research branch closure

Status: **closed as a source of A*-level novelty** on 2026-08-28.

## Binding verdict

The QAOA/MPS symmetry branch must not be revived by renaming the same effect.
The final aggressive audit established that:

- full-symmetry Haar, orbit-phase, and twin-only Haar controls reproduce all 61
  previously interesting deficit cuts across five deterministic seeds;
- the amplitude-blind twin structural bound explains all 84 synthetic and 53
  real archived rank rows exactly, with zero violations and no ansatz residual;
- the optimized Qiskit Aer comparison reduces the reported `23.90x` speedup to
  `1.24x` median and `1.07x` conservative speedup; and
- compilation removes the first-use runtime advantage.

Exactness and `10.11x` memory compression remain valid engineering results.
They do not support either algorithmic-novelty or systems-performance novelty.
The authoritative report is
[`results/symmetry_claim_falsification/REPORT.md`](../results/symmetry_claim_falsification/REPORT.md).

## Archived research sequence

| stage | experiment directories | final role |
|---|---|---|
| Original QAOA/MPS study | `evoq_mis_full_qoblib`, `rankcert_mps`, `decisioncert_mps` | Reproducible baseline, exact references, ranking and certificate data |
| Observable/certificate line | `observable_telescope`, `compressed_observable_telescope`, `decision_certified_allocation`, `decision_certified_bond_allocation`, `causal_certification_debt`, `signed_decision_cot` | Valid identities and negative feasibility/performance evidence |
| Comparison-native truncation line | `contrastive_tensor_simulation`, `signed_reduced_density_truncation`, `decision_balanced_truncation`, `global_decision_balanced_contraction`, `decision_conditioned_srdt`, `sparse_mps_dcsrdt` | Successive candidates and frozen kill tests |
| Structural explanation | `dcsrdt_structural_audit`, `coherent_frontier_rank`, `ansatz_event_rank` | Event-support/matching theorem, phase controls, failed broad QAOA generalization |
| Symmetry candidate | `symmetry_quotient_decision_rank`, `symmetry_quotient_backend`, `symmetry_quotient_breadth` | Exact implementation and initially positive but now superseded interpretation |
| Final falsification | `symmetry_claim_falsification` | Binding negative verdict, optimized baseline, twin-aware structural theorem |

Every directory contains code and/or a frozen protocol.  Compact outputs are
under the matching `results/` directory.  SHA-256 manifests pin the principal
artifacts.  Dense 24-qubit reference statevectors are intentionally excluded
from ordinary Git because each is 256 MiB; their identities remain in the
existing exact-reference manifests.

## Results worth retaining

1. Exact twin-count quotient implementation and its correctness tests.
2. Dense and twin-aware capacity-two event-incidence bounds.
3. Exact small-core comparison identities.
4. Eight-case quotient/dense correctness validation.
5. The falsification suite and the methodological warning that ordinary
   symmetry can masquerade as decision-specific low-rank structure.
6. Frozen negative results from every abandoned candidate, to prevent repeated
   rediscovery of the same explanation.

These may support a technical appendix, benchmark note, software release, or a
broader methodological paper.  None is to be promoted as the main A* claim.

## Explicit no-reopen list

Do not start another primary novelty cycle based on:

- DCS rank or a renamed event-conditioned rank;
- symmetry/twin/orbit quotients of the same QAOA trajectories;
- R32/R64 or compression-memory effects;
- bond allocation, local truncation, observable backpropagation, or another
  certificate around the same two-state comparison;
- a slower dense baseline used to restore a large speedup number.

## Gate for the next research direction

The next candidate must change the research object and provide a new capability
or theorem.  Before any expensive experiment it must pass a short adversarial
screen:

1. primary-source prior-art search;
2. structural/optimality reduction attempt;
3. strongest symmetry, randomization, and trivial-baseline controls;
4. an explicit kill criterion frozen in advance;
5. a credible path to held-out or hardware evidence unavailable from another
   classical replay.

Preferred search spaces are a genuinely new simulation primitive with a
provable separation, simulator-to-hardware ranking failures with held-out
hardware validation, or a different AI/scientific-discovery formulation.

## Post-closure exact-event continuation

The 2026-09-02 continuation did not reopen the MPS/certificate novelty claim.
It changed the computational target to the exact probability of the complete
384-string BKS event.  A rational sparse-event compiler found fixed-order
minimal projector bond 152 for sorted order and 5 for spectral order, and two
independent cuTensorNet APIs reproduced the untruncated 55-qubit probability
through QAOA depth 2.  Depth 3 already exceeds the frozen local resource guard;
depths 8 and 15 fail path search, so the manuscript's depth-15 ideal winner is
still unresolved.

Prior-art falsification also closes “finite set to minimal MPO” as a broad
novelty claim.  The only live hypothesis is a genuinely different one: joint
circuit/event co-ordering with a general theorem and end-to-end advantage over
batched and sliced baselines.  See
[`results/exact_event_contraction/REPORT.md`](../results/exact_event_contraction/REPORT.md).
