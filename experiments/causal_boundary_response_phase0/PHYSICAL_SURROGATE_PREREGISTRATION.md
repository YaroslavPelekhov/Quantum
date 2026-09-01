# Physical-surrogate synthesis gate (frozen)

The structural and doubled-grid gates passed.  This next test asks whether the
low finite-horizon Hankel rank corresponds to a small *physical* Rydberg
system, rather than an unconstrained linear realization.

## Frozen target

- endpoint path `P_13`;
- both uniform and 3% perturbed detuning controls;
- `T in {5,10,20}`;
- the full complex conditional port-coherence response, not only its modulus;
- 129 equally spaced fitting times and 1023 held-out validation times.

## Optimistic physical model

Enumerate every non-isomorphic hard-blockade graph on `r=1,2,3` surrogate
atoms and every nonempty set of surrogate atoms blockaded by the port.  All
atoms start in the ground state and retain the hardware global transverse
drive `Omega=1`.

To make failure maximally informative, the optimizer is granted **more**
freedom than current Aquila:

- independent static onsite detunings in `[-3,3]` for every surrogate atom;
- one independent port phase-rate correction in `[-3,3]`.

Current Aquila exposes only one fixed spatial local-detuning pattern multiplied
by a shared time waveform.  Therefore failure of this optimistic envelope
rules out every static current-hardware realization; success must still be
retested in the real control algebra.

Each topology receives a deterministic differential-evolution screen.  The
two best candidates at each atom budget receive a longer independent refine.
No topology or bound will be added after viewing results.

## Promotion criteria

For a target case, an `r=3` realization passes only if, on the 1023-point grid:

1. maximum complex response error is at most 0.02;
2. relative L2 error is at most 0.01;
3. maximum-error improvement over the frozen three-atom prefix is at least
   fivefold.

Physical synthesis advances only if one horizon passes in both detuning
controls.  It is killed if no horizon does.

Passing this optimistic test is not yet a hardware result.  The next mandatory
gates are current-Aquila control projection, topology embedding, and frozen
transfer to held-out host graphs.

