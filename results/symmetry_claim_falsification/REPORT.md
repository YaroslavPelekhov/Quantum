# Aggressive falsification of the symmetry/event comparison claim

## Verdict

**The previous novelty claim is rejected.**  Both of its distinguishing parts
failed stronger controls:

1. the reported ansatz/event rank signature is exactly the generic structural
   rank in a cut-local twin-count basis; and
2. the reported `23.90x` runtime speedup falls to `1.24x` against an optimized
   Qiskit Aer statevector baseline and fails the frozen `2x` gate.

Exact correctness and `10.11x` state-representation compression survive.  They
are useful engineering results, but the current evidence does not support an
A*-level novelty claim.

## Rank falsification

The original independent phase control broke graph symmetry.  The new controls
preserve it.  On all 61 previously selected deficit cuts, for five deterministic
seeds each:

- Haar-random states in the full automorphism-invariant subspace exactly match
  every archived QAOA rank;
- independent phase randomization by full graph orbit, preserving QAOA
  magnitudes, also matches exactly; and
- Haar-random states in the larger twin-only quotient still match exactly.

Thus neither the depth-15 ansatz nor the nonlocal chain/ring automorphisms are
needed to produce the profile.

The amplitude-blind replacement bound is

`B_twin(c) = min(2 s_L_bar, 4 s_R_bar, 2 mu_2_bar, d_L,twin)`.

Here the event incidence graph is collapsed by the counts of selected vertices
inside each twin class on both sides of the cut, `mu_2_bar` duplicates every
right quotient vertex, and

`d_L,twin = product_g (|C_g intersect L| + 1)`.

This bound has zero violations.  Generic twin-Haar states saturate it on all 78
eligible synthetic cuts across five seeds; QAOA equals it on all 84 synthetic
nontrivial cuts.  Transfer to the pre-existing QOBLIB cohort gives another
53/53 exact rank equalities: seven balanced breadth cuts and every cut in both
24-qubit aves orderings.  There is no residual ansatz-dependent cut.

## Performance falsification

The same sorted 24-qubit, depth-15 MIS trajectory was benchmarked with three
Qiskit Aer statevector repetitions and seven twin-quotient repetitions.

| metric | result |
|---|---:|
| Aer raw times | 5.43, 4.64, 5.28 s |
| Aer median | 5.285 s |
| Quotient raw range | 4.17--4.33 s |
| Quotient median | 4.254 s |
| Median steady-state speedup | 1.242x |
| Conservative fastest-Aer / slowest-quotient | 1.071x |
| Quotient compile | 2.264 s |
| Three-cut decision median | 0.117 s |
| Representation compression | 10.114x |

The old `23.90x` number used a single NumPy dense trajectory taking 101.96 s.
It is not robust to an optimized baseline and is withdrawn.  Including quotient
compilation makes the first state slower than the Aer median on this machine.
The sampled probability errors remain `1.53e-17` for Aer and `1.30e-18` for the
quotient backend, so the timing reversal is not caused by mismatched circuits.

## Prior-art consequence

Once the rank profile is reduced to twin-invariant structural rank, the main
ingredients sit directly inside established symmetry-adapted simulation:
graph symmetries constrain QAOA probabilities, orbit/Dicke bases reduce
permutation-equivariant dynamics, and group symmetry has long been used in
quantum hypothesis testing.  Particularly close context includes
[Shaydulin et al.](https://arxiv.org/abs/2012.04713), the 2026
[permutation-equivariant circuit simulator](https://arxiv.org/abs/2603.13072),
and [quantum hypothesis testing with group symmetry](https://arxiv.org/abs/0904.0704).

The capacity-two bound and exact small-core identity remain correct.  Their
composition with a standard twin/Dicke quotient may be publishable as a narrow
technical note or reproducible software contribution, but the present audit
does not justify calling that composition a major standalone algorithmic
novelty.

## What remains valid

- exact twin-count QAOA evolution;
- exact event-conditioned comparison spectra without a full `2^24` state;
- the dense and twin-aware capacity-two structural theorems;
- exact validation on the eight-case frozen cohort;
- `10.11x` memory reduction on aves;
- an unusually complete negative-result and falsification record.

The correct research decision is to stop promoting this claim in its previous
form.  Any future A*-level direction must introduce a new capability or
complexity result, not another interpretation of the same rank profile.
