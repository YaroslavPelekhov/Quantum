# Final controlled-process Gram falsification (frozen)

The isolated response and all-ground host tests probe only a small slice of the
boundary process.  For piecewise-constant binary port histories, let

```text
|psi_w> = U_{w_K}(dt) P_{w_K} ... U_{w_1}(dt) P_{w_1} |empty>
```

with the hard-blockade projection applied whenever the port is occupied.  The
Gram matrix `G_K[w,v] = <psi_w|psi_v>` is the influence matrix seen by a
coherent superposition of port histories.  Equality of all such Gram matrices
is necessary for universal host/control transfer; the registered scalar
Loschmidt response is only a no-switch entry.

## Frozen test

- target `P_13`, frozen optimized `P_4`, and inherited-field `P_4` prefix;
- `T=5`, equal bins, every binary history for `K=1,...,6`;
- uniform and 3% perturbed controls;
- frozen capacity-audit parameters, with no refitting;
- metrics: maximum complex Gram-entry error, relative Frobenius error, and
  improvement over the same-budget prefix.

The process gate passes only if every `K=2,...,6` has maximum Gram error at
most 0.02 and at least fivefold improvement over the prefix in **both**
controls.  A failure closes CBRK as an A-star branch.  No alternate word subset,
threshold, or one-control claim will replace this gate.

An independent red-team also specified an exhaustive two-bin timing audit:
scan the 99 splits `tau=0.05,0.10,...,4.95` before the main implementation was
run.  This is reported separately and must meet the same 0.02/fivefold gate at
every split; it can only falsify, not rescue, the equal-bin result.
