# Frozen spectral held-out protocol

Locked before any spectral Observable Telescope run for this experiment on
2026-08-20 (Europe/Moscow).

## Design information

The complete ibm32/sorted 5 x 5 portfolio selected:

- published LR trajectory: `released` (`bond=64`, `cutoff=1e-3`);
- prior-matched-random trajectory: `confirm` (`bond=128`, `cutoff=1e-4`).

The frozen symmetric comparator is `confirm` for both trajectories.

## Held-out execution

Run only `released` and `confirm` on the ibm32/spectral ordering. The transferred
allocation is evaluated without changing either fidelity level. Exact BKS values
must not enter selection; they are used only after the certificate is formed to
audit its direction.

Primary success requires the transferred asymmetric pair to produce disjoint
sound intervals and the certified direction to agree with the exact audit.
Secondary success requires lower measured forward-simulation time than the
frozen symmetric comparator. A failure is retained and reported; no replacement
pair may be selected from the held-out results.
