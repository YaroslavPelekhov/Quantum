# Exact sparse-event contraction: final continuation report

Status: **completed negative/partial result** on 2026-09-02.

## Binding verdict

This continuation does **not** resolve the manuscript's ideal depth-15 winner
and does **not** establish A*-level novelty.  It does establish a narrower new
capability in this codebase: an untruncated deterministic contraction of the
probability of *all* 384 BKS bitstrings on the 55-qubit `es60fst02` circuit,
without constructing the full statevector, through QAOA depth `p=2`.

The main new structural observation is real but not a standalone novelty claim:
the same 384-string event has fixed-order minimal TT/MPO bond 152 in sorted
order and only 5 in the existing spectral order.  Nevertheless, full-depth
contraction fails.  A small event projector is therefore not sufficient; the
circuit and event must admit a good **joint** contraction order.

## What was computed

The reduced graph has 55 vertices and 91 edges.  Exact maximum-independent-set
enumeration gives independence number 23 and exactly 384 maximum sets.  Every
set passes the frozen decoder and maps to BKS 88.  The target for schedule `s`
is

`p_s(A) = <psi_s|P_A|psi_s>`, with
`P_A = sum_{z in A} |z><z|`.

For each prefix/suffix cut, an exact rational rank factorization of the sparse
incidence matrix `M_k[p,s] = 1[p+s in A]` constructs the indicator TT.  The TT
is lifted diagonally to an MPO and attached to the doubled circuit network.
There is no support pruning, MPS bond truncation, or Monte Carlo sampling.
The final numerical contraction is complex128.

| ordering | max TT/MPO bond | TT entries (nonzero) | dense MPO bytes |
|---|---:|---:|---:|
| sorted | 152 | 827,008 (4,250) | 26,464,256 |
| spectral | 5 | 988 (183) | 31,616 |

The spectral ordering reduces maximum bond by 30.4x and dense
contraction-ready MPO storage by 837.05x.  This is not raw-data compression:
the packed list of 384 strings itself needs only about 2.64 KB.  The value of
the MPO is algebraic compatibility with tensor-network contraction.  All
compiled TT coefficients in both orderings are exactly in `{-1,0,1}`, so their
conversion from rational arithmetic to complex128 introduces no coefficient
rounding.

## Validation

All pre-registered validation gates passed:

| validation | cohorts/checks | maximum absolute error |
|---|---:|---:|
| selected-amplitude event sum vs dense state | 8 cohorts | 8.77e-15 |
| high-level event MPO vs dense state | 8 cohorts | 7.88e-15 |
| low-level density+MPO vs dense state | 8 cohorts | 5.66e-15 |
| truncated-depth density+MPO vs fresh dense state | 40 cohorts | 2.78e-15 |
| layer extraction invariants | 60 rows / 30 LR-MR topology pairs | exact pass |

The exact event representation accepts all 384 support strings and rejects
4,096 deterministic outsiders in both orderings with zero observed error.
Layer extraction verifies one `h` per qubit, 15 `rz` and `rx` gates per qubit,
15 `rzz` gates per edge, complete cost layers before every mixer, and identical
LR/MR circuit topology at every tested depth.

## 55-qubit completed results

The following values were independently reproduced by the experimental
`NetworkState.compute_expectation` API and by an explicit low-level scalar
density-network contraction.  The two APIs disagree by at most `8.49e-27`;
the high-level state norm is exactly 1 to reported precision.

| depth | published LR | matched random | MR - LR | MR/LR |
|---:|---:|---:|---:|---:|
| 1 | 8.4434393208607e-14 | 1.2280528559635e-12 | +1.1436184627549e-12 | 14.5445x |
| 2 | 7.3639125372524e-14 | 1.0183370578131e-12 | +9.4469793244062e-13 | 13.8288x |

These are shallow-prefix results only.  They cannot be substituted for the
depth-15 experiment in the manuscript.  Their probabilities also make direct
hardware sampling impractical: even the larger value is around `1e-12`, so a
single expected event would require order `10^12` shots before hardware noise.

## Exact feasibility boundary

The resource guard was fixed after the first `p=4` path exposed billions of
slices and before the `p=3` bisection.  A path is recorded but not executed
above 65,536 slices or optimizer cost `1e13`.

| depth/order | outcome | slices | optimizer cost |
|---|---|---:|---:|
| p=1 spectral | completed | 1 | 9.32e6 |
| p=2 spectral | completed | 1 | 1.33e10 |
| p=3 spectral | resource-rejected | 12,288 | 1.44e15 |
| p=4 spectral | resource-rejected | 4,294,967,296 | 5.80e20 |
| p=8 spectral | no path | — | `ALL_HYPER_SAMPLES_FAILED` |
| p=15 spectral/sorted | no path | — | `ALL_HYPER_SAMPLES_FAILED` |

Sorted-order semantic replication is already impractical at `p=1`: its path
has 6,144 slices and cost `4.65e15`.  At `p=2` it rises to 306,016,419,840
slices and cost `9.49e22`.  Thus the order affects both the event representation
and the circuit network, and the completed spectral values currently have
two-API rather than two-ordering replication.

At full depth, three honest routes were tried and failed:

1. `NetworkState.compute_amplitude` failed in exact preparation.
2. Low-level single-amplitude path search failed for sorted and spectral order.
3. Both high-level event-MPO expectation and the explicit doubled circuit+MPO
   path failed (`INTERNAL_ERROR` and `ALL_HYPER_SAMPLES_FAILED`, respectively).

The ideal depth-15 LR-vs-matched-random BKS ranking therefore remains unknown.

## Novelty falsification

The broad formulation “finite set to minimal TT/MPO and one expectation
contraction” is prior art, not the A* contribution:

- prefix/suffix unfolding ranks and rank-minimal tensor trains follow standard
  TT theory ([Oseledets, 2011](https://doi.org/10.1137/090752286));
- Hankel-rank minimality is classical weighted-automata theory
  ([Carlyle--Paz, 1971](https://doi.org/10.1016/S0022-0000(71)80005-3)) and the
  WFA--TT connection is explicit
  ([Li, Precup, Rabusseau](https://arxiv.org/abs/2010.10029));
- automata-to-MPS/MPO constructions are established
  ([Crosswhite--Bacon](https://doi.org/10.1103/PhysRevA.78.012356));
- recent work is very close to finite-language-to-MPS compilation
  ([Bellante et al., 2026](https://arxiv.org/abs/2602.02698)) and sparse exact
  Boolean/QTT factorization
  ([Haubenwallner--Heller, 2026](https://arxiv.org/abs/2606.04506)); and
- generic exact circuit contraction is longstanding
  ([Markov--Shi](https://doi.org/10.1137/050644756)).

Consequently, the following claims are closed: first finite-set MPO compiler,
new fixed-order minimality theorem, first one-network event probability, and
global optimality of spectral ordering.

## The live A* gap

The only defensible continuation is **joint circuit/event co-ordering**: choose
one variable/elimination order that minimizes the end-to-end contraction cost
of the circuit together with a decision event, rather than minimizing circuit
width or event-MPO rank separately.

That is still a hypothesis, not a result.  To reach A* level it needs all of:

1. a theorem or approximation guarantee for a combined width/cost objective,
   beyond the known fixed-order Hankel/TT lemma;
2. a certified lower bound if any ordering is called optimal;
3. a broad graph/event sweep with spectral, min-fill, random, BDD/ZDD, and
   circuit-only baselines;
4. end-to-end comparison against 384 amplitudes with path reuse, batched/open
   amplitudes, and sliced contraction; and
5. held-out scaling or hardware-relevant evidence, not one favorable instance.

The present result is the right seed for that study because it exhibits a
large projector-rank change and an equally decisive contraction-feasibility
change.  It is not yet the study itself.

## Reproducibility map

- Frozen protocols: `experiments/exact_event_contraction/PROTOCOL.md`,
  `MPO_PROTOCOL.md`, and `DEPTH_SWEEP_PROTOCOL.md`.
- Adversarial literature screen:
  `experiments/exact_event_contraction/PRIOR_ART_AUDIT.md`.
- Event enumeration: `build_event_support.py`.
- Exact amplitude and failure pilots: `run_exact_event_contraction.py`.
- Exact TT/MPO compiler, validation, and contractions:
  `run_event_projector.py`.
- Machine-readable verdict: `results/exact_event_contraction/SUMMARY.json`.
- Full artifact hashes: `results/exact_event_contraction/MANIFEST.json`.

The manuscript was also corrected in two places without changing data: the
first 80 cohorts contain eight (not three) conservative certificate false
negatives, and ten setting/ordering locations are explicitly identified as 20
backend cohorts.  Both PDFs rebuild cleanly.
