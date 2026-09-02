# Frozen protocol: exact event-selective contraction

Frozen on 2026-09-02 before any 55-qubit exact-amplitude result was
computed.

## Question

The existing QAOA/MPS study cannot identify the exact winner on the
55-qubit `es60fst02` kernel because a full exact statevector and exact
cuTensorNet sampling both failed.  This experiment asks a narrower question:
can the exact BKS probability be obtained without representing or sampling the
full state, by contracting only the amplitudes in the BKS event?

For a circuit state `psi_s` and the frozen BKS support `A`, the target is

`p_s(A) = sum_{z in A} |<z|psi_s>|^2`.

The result is an event probability, not a state-simulation or quantum-advantage
claim.

## Immutable inputs

- The four 55-qubit QPY circuits and their hashes come from
  `experiments/evoq_mis_full_qoblib/results/cutensornet/export_manifest.json`.
- The graph reduction, decoder, schedules, depth, and Hamiltonian are unchanged
  from `experiments/evoq_mis_full_qoblib`.
- The tested schedules are `published_lr` and `matched_random_search`.
- The tested qubit orderings are `sorted` and `spectral`.
- Exact contractions use cuQuantum/cuTensorNet 26.6.0, complex128, and
  `TNConfig`; no MPS approximation is allowed.

## Event construction

Enumerate every maximal clique of the complement of the reduced graph, retain
all maximum cliques, and convert them back to independent sets.  The support is
accepted only if all of the following checks pass:

1. the reduced kernel has 55 vertices and 91 edges;
2. the maximum independent-set size is 23;
3. the support contains exactly 384 distinct strings;
4. every string is feasible under the frozen decoder and decodes to BKS 88;
5. the sorted and spectral supports describe the same 384 node sets.

The count 384 was established before the contraction feasibility pilot and is
therefore a structural input, not a simulation outcome.

## Validation sequence

1. **Support audit.** Generate a hash-stable support file for the 12-, 15-, and
   55-qubit QOBLIB kernels.
2. **Small exact self-test.** For both schedules and both orderings on the
   12- and 15-qubit kernels, sum cuTensorNet amplitudes over the BKS support and
   compare against the existing dense exact state.  Absolute error must be at
   most `1e-10`.
3. **55-qubit feasibility pilot.** Contract the lexicographically first BKS
   amplitude for sorted LR.  Escalate only if it finishes without approximation,
   out-of-memory failure, or an internal preparation error.
4. **Primary exact target.** Sum all 384 probabilities for sorted LR and sorted
   matched-random.  Checkpoint every completed amplitude.
5. **Semantic replication.** Repeat both schedules under spectral ordering.
   Since ordering is an exact relabeling, each schedule probability must agree
   between orderings to absolute `1e-9` or relative `1e-7`.

## Decision rules

- If the pilot fails, report the exact failure and close this implementation
  path without substituting an MPS result.
- If the small self-test fails, no 55-qubit number is admissible.
- If both 55-qubit orderings agree within tolerance and the schedule gap exceeds
  accumulated numerical tolerance, the sign adjudicates the exact BKS ranking
  for the frozen circuits.
- If only one ordering finishes, its value is evidence from an exact contraction
  but the central ranking remains provisional until an independent semantic
  replication succeeds.
- Wall time and peak GPU memory are reported; no speedup claim is made without
  a matched baseline.

## A*-novelty boundary

Computing selected amplitudes with tensor networks is established prior art.
This phase is valuable if it resolves the manuscript's central 55-qubit unknown
or exposes a reusable event-sparse regime.  It is not, by itself, an A*-level
algorithmic contribution.  A broader claim would require a new event-contraction
algorithm, complexity separation, and transfer beyond this one instance.
