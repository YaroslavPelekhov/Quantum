# Event-conditioned width: Phase-0 representation screen

## Binding status

The full registered program is `INCOMPLETE_NO_PROMOTION`. The natural product
proxy is separately `KILLED_AS_ASTAR_SOURCE` by K6: it is exactly the maximum
prefix unfolding rank of one artificial site-grouped tensor and therefore an
ordinary linear TT-rank ordering objective. This does not establish a width
formula for the actual QAOA tensor and does not kill every pair-dependent
algebraic algorithm. See the
[falsification report](../../results/event_conditioned_width_phase0/FALSIFICATION_REPORT.md)
and machine-readable
[decision](../../results/event_conditioned_width_phase0/PHASE0_DECISION.json).

This is a deliberately cheap falsification screen. It asks whether an apparent
advantage from a low-rank event MPO survives when a generic contraction-path
optimizer is allowed to optimize the complete circuit-plus-event network.

For a small graph and an exact target cardinality, the script builds the same
Boolean event in two forms:

1. a rank-minimal fixed-order support TT, lifted structurally to a diagonal MPO;
2. local independent-set edge factors plus an exact cardinality automaton.

Each representation is attached to identical bra and ket copies of a structural
QAOA circuit. The optimizer receives only tensor shapes and index incidences. It
does not see coefficients, MIS semantics, or the requested qubit order, and it
does not execute the contraction. The reported path cost is therefore a dense,
semantic-blind baseline rather than a runtime prediction for sparse execution.

`opt_einsum` is used automatically when installed. The repository's default
environment does not require it: a deterministic, multi-start shape-greedy
fallback is included.

Run the unit tests:

```powershell
python -m unittest experiments/event_conditioned_width_phase0/test_representation_screen.py
```

Run a small depth-one cycle screen:

```powershell
python experiments/event_conditioned_width_phase0/representation_screen.py `
  --graph cycle --qubits 5 --depth 1 --backend auto --trials 24
```

Run the fixed aggregate development sweep (48 cases: path/cycle/star and three
seeded random graphs, `n=5..8`, `p=1..2`):

```powershell
python experiments/event_conditioned_width_phase0/run_representation_sweep.py
```

The runner checkpoints a unified report at
`results/event_conditioned_width_phase0/development_representation_sweep.json`.
Its default six-trial shape-greedy search is deterministic. Use `--resume` to
continue a compatible partial report.

Run the exact structural proxy audit, including full order enumeration through
`n=9`, tie-aware argmin checks, and explicit global-tensor controls:

```powershell
python experiments/event_conditioned_width_phase0/run_structural_falsification.py
```

After the report and result files are stable, validate the package and rebuild
the frozen decision and SHA-256 manifest:

```powershell
python experiments/event_conditioned_width_phase0/finalize_phase0.py
```

The JSON report includes exhaustive semantic equivalence checks, event bond
ranks, tensor counts, dense input sizes, unrestricted pairwise paths, estimated
arithmetic cost, and peak intermediate elements. Phase 0 should be considered a
kill test: if the local factor network plus generic path search consistently
matches or beats the support MPO, event-MPO rank alone is not an adequate theorem
object.

The aggregate report makes two additional asymmetries explicit. Dense path cost
penalizes sparse COPY tensors, diagonal gates, and diagonal MPO legs as though
they were dense; conversely, support enumeration and TT compilation are excluded
from the MPO cost even though the local factor representation does not require
an enumerated support. The sweep is therefore a representation/path-cost screen,
not a systems benchmark or an asymptotic separation result.
