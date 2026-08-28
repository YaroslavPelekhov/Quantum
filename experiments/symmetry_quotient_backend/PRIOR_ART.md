# Prior-art boundary for the symmetry/event comparison backend

> **Superseded claim boundary.**  The later aggressive falsification in
> `results/symmetry_claim_falsification/REPORT.md` showed that the rank profile
> is generic twin-count structural rank and that optimized Aer removes the
> reported large runtime advantage.  The conjunctive novelty claim below is no
> longer promoted.

Search updated 2026-08-28.  The novelty claim is intentionally conjunctive;
none of the following ingredients is claimed alone.

## Explicitly old ingredients

- Difference operators for two-state discrimination are standard Helstrom
  machinery.
- The anticommutator is a Jordan product.  Jordan-product states/observables
  over time and their partial traces predate this work; see
  [Fullwood--Parzygnat](https://arxiv.org/abs/2202.03607) and the later
  [quantum-observable-over-time construction](https://arxiv.org/abs/2412.11659).
- Best rank-k approximation in unitarily invariant norms is classical
  Eckart--Young--Mirsky theory.
- Generic/term rank from a zero pattern is classical structural-matrix theory;
  maximum bipartite matching is its standard graph characterization.
- Variable-order dependence for sparse Boolean events is central to OBDDs; see
  [Tani](https://arxiv.org/abs/1909.12658).
- Symmetry-confined evolution on an orbit quotient is established for quantum
  walks by [Krovi--Brun](https://arxiv.org/abs/quant-ph/0701173).
- Classical objective symmetries, invariant QAOA probabilities, and reduced
  QAOA energy evaluation are established by
  [Shaydulin et al.](https://arxiv.org/abs/2012.04713) and
  [Shaydulin--Wild](https://arxiv.org/abs/2101.10296).
- Spatially equivariant parameterized circuits are studied by
  [Sauvage et al.](https://arxiv.org/abs/2207.14413).
- General tensor-network QAOA/circuit simulation is established, e.g.
  [qTorch](https://arxiv.org/abs/1709.03636).

## Claim retained after the audit

The candidate contribution is the first located combination of:

1. a paired, event-conditioned comparison operator whose trace is the exact
   difference of decision probabilities;
2. an exact `2 mu_2` capacity-two event-incidence matching bound;
3. a parameter-generic ansatz/event rank signature used as a reusable compiled
   comparison budget;
4. exact orbit-amplitude assembly of only the small comparison core;
5. a direct twin-count QAOA quotient backend with measured real 24-qubit
   speedup; and
6. explicit Haar, phase, dense-event, broad-QAOA, schedule-pair, Schmidt-rank,
   synthetic-transfer, and all-case breadth controls.

The claim is not “symmetry speeds up QAOA” and not “sparse events are low rank.”
It is that circuit symmetry reduction and paired-event structural rank can be
compiled independently and composed into an exact comparison-native simulator
with a cutwise rank certificate.

## Scope that must remain in every abstract

- Exact and noiseless.
- Requires a diagonal sparse/structured event.
- Runtime gain requires nontrivial automorphism/twin sectors; asymmetric graphs
  can fall back to the full Hilbert space.
- Current real large-scale evidence is one 24-qubit QOBLIB kernel in two
  orderings, supplemented by a pre-existing eight-case census, seven exact
  breadth controls, and frozen synthetic topology transfer.
