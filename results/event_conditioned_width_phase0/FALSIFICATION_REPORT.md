# Phase-0 falsification report

Audit date: 2026-09-02.

## Binding verdict

- **The full registered Phase-0 program:** **INCOMPLETE_NO_PROMOTION**.
- **The natural product proxy as a new width:** **KILLED_AS_ASTAR_SOURCE**
  by **K6 (known-width collapse)**.
- **The broader event-conditioned probability direction:** not decided by
  these files.

The natural candidate

\[
J_\pi=\max_S r_f(S)\,2^{2p|\delta_G(S)|}
\]

is exactly the maximum site-prefix unfolding rank of one globally defined
artificial tensor. It is therefore an ordinary linear TT-rank ordering
objective, not a new event-conditioned width. This conclusion is binding only
for this natural proxy/new-width claim. It does not identify the artificial
tensor with an actual QAOA tensor and does not falsify every possible
event-conditioned algorithm.

The audited input snapshots are:

- natural_proxy_falsification.json:
  SHA-256 f10a9a8e716d7f8105c669dcc21259ce55dff588ebbf734c991a695e6f11874b;
- real_qoblib_representation_paths.json:
  SHA-256 691a25dbfc16020bcc39e5cc83c3bbfbc5317effaeb88b3891e959e84fa1a029.

The frozen protocol predates both result files. Some supporting code existed
before the protocol timestamp, so this is result-blind, not
implementation-blind, preregistration.

## Structural reduction and development evidence

Let \(q=2p\). For every graph edge \(e=\{u,v\}\) and copy
\(c\in\{1,\ldots,q\}\), introduce distinct half-edge bits
\(z_{u,e,c}\) and \(z_{v,e,c}\), and define one tensor

\[
T=E(x)\otimes
\prod_{e=\{u,v\}}\prod_{c=1}^{2p}
\mathbf 1[z_{u,e,c}=z_{v,e,c}].
\]

Group \(x_v\) and all incident half-edge bits into site \(v\), and permit
only whole-site permutations. For every site cut \(S\), internal equality
factors have rank one and crossing equality factors have rank two. Because
their variables are distinct, the unfolding is a Kronecker product, so over
\(\mathbb Q\) or \(\mathbb C\), simultaneously for all \(S\),

\[
\operatorname{rank} T_{S\mid\bar S}
=r_f(S)\,2^{2p|\delta_G(S)|}.
\]

Thus \(J_\pi\) is exactly the linear TT-rank width of this single artificial
tensor. Four explicit full-tensor controls also reproduce the predicted ranks
2, 8, 16, and 2. This establishes K6 for the natural proxy/new-width claim.

Important scope limits are structural, not cosmetic. A site has local
dimension \(d_v=2^{1+2p\deg v}\); dense \(T\) is exponentially large, though
it has a succinct factor construction. Most importantly, \(T\) is **not** an
actual QAOA circuit tensor. No equality between its unfolding ranks and an
actual QAOA contraction width or runtime is established.

The structural file also contains 48 exhaustive development rows spanning
four synthetic families, \(n=4,\ldots,9\), and \(p=1,2\). The independent
audit evaluates 3,272,832 orders in total, while the three event/circuit/joint
searches evaluate 9,818,496 objective-order combinations. Across 264 cuts, 200 Kronecker ranks
are explicitly materialized; 64 oversized cases use the exact identity.

After tie-aware minimization over the complete event-optimal and
circuit-optimal order sets, the best-one-sided-over-joint ratio is exactly
1 in all 48/48 rows. This supplies additional negative development evidence,
but it is not the registered locked-holdout full-network \(\Delta_F\).

## Real 55-qubit representation screen

This is a development sentinel, not locked protocol evidence. The
real-QOBLIB file contains exactly 12 path-search rows:

- one case, es60fst02;
- one schedule, published_lr;
- spectral and sorted qubit layouts;
- depths 1--3;
- rank-minimal MPO and local MIS-plus-cardinality encodings;
- one cuTensorNet seed, eight optimizer samples;
- no contraction and no runtime measurement.

Dense optimizer costs and slices are:

| layout | depth | minimal MPO cost | local MIS cost | cost winner | MPO/local slices |
|---|---:|---:|---:|---|---:|
| spectral | 1 | \(9.32\times10^6\) | \(2.72\times10^{10}\) | MPO, 2919x | 1 / 1 |
| spectral | 2 | \(1.33\times10^{10}\) | \(7.63\times10^{13}\) | MPO, 5751x | 1 / 480 |
| spectral | 3 | \(3.42\times10^{15}\) | \(6.13\times10^{17}\) | MPO, 179x | 32,768 / 4,718,592 |
| sorted | 1 | \(4.65\times10^{15}\) | \(2.12\times10^{13}\) | local, 220x | 6,144 / 1,408 |
| sorted | 2 | \(2.80\times10^{21}\) | \(2.81\times10^{18}\) | local, 997x | 4,026,531,840 / 3,932,160 |
| sorted | 3 | \(1.82\times10^{26}\) | \(2.58\times10^{24}\) | local, 70.6x | \(2.29\times10^{14}\) / \(4.16\times10^{12}\) |

The representation winner reverses with layout: the minimal MPO dominates
the tested dense path cost in spectral order, whereas the local constraint
network dominates in sorted order. At spectral depth three the local
encoding has a smaller largest intermediate
(\(2.68\times10^8\) versus \(4.03\times10^8\) elements), despite its much
larger FLOP and slice estimates. Thus there is no scalar
"best representation" independent of layout and resource objective.

No depth-three route passes the frozen optimizer-cost guard of \(10^{13}\).
The spectral MPO path has only 32,768 slices, but its cost is still about
342 times the guard. The file therefore establishes no new executable
55-qubit capability.

## Gate audit

| gate | status | reason |
|---|---|---|
| K0 | not fired | no contradictory value is present, but the real file performs no probability validation |
| K1 | **do not claim** | the 48-row quantity is a rank proxy, not locked-holdout full-network \(\Delta_F\) |
| K2 | **do not claim** | only two encodings, one case, one seed, eight samples, and no full registered replanning study |
| K3 | **do not claim** | depth-three infeasibility is a warning, but there is no locked median or executed end-to-end comparison |
| K4 | **do not claim** | proxy headroom is flat, but it is not the registered family-median \(\Delta_F\) |
| K5 | **do not claim** | BDD/ZDD/ADD, batched amplitudes, MPE-like, WMC and other mandatory baselines are absent |
| K6 | **fired for the natural proxy/new-width claim** | one global site-grouped artificial tensor realizes the proxy exactly as ordinary linear TT-rank width; actual-QAOA equivalence is not established |
| K7 | not fired yet | the registered resource budget and mandatory study have not been exhausted; the work is presently incomplete |

None of P0--P5 is established. In particular, the registered 64-network
holdout, exact probability execution, five planner seeds, 128-sample budget,
mandatory representation set, end-to-end timings, and candidate lock have
not been run. The four synthetic families in the structural file are a
targeted proxy screen, not the registered A--F OPT/TOP2 holdout.

## Claims that these data do not support

- the whole event-conditioned output-query direction is impossible;
- a joint compiler or pair-dependent algorithm has been falsified;
- minimal MPO or local MIS is generally superior;
- path-estimated FLOPs are measured speedups;
- depth-three exact contraction is now feasible;
- any positive generalization, scaling, hardware, or actual-QAOA A*-novelty
  claim;
- a separation from generic TN, DD, WMC, rank-width, or MPE methods.

## Next admissible hypothesis class

The natural separable proxy is now mathematically classified and closed as a
source of A* novelty. The next candidate cannot be another product of event
rank and circuit cut size. The admissible hypothesis class is a
**non-factorizing, cancellation-aware residual-space algorithm** for the
actual fused circuit-event computation.

For a partial elimination cut \(S\), let \(d_{C,f}(S)\) be the dimension of
the span of the actual amplitude-weighted event residual boundary maps. The
product proxy assumes the generic upper bound

\[
d_{C,f}(S)\leq d_C(S)\,r_f(S)
\]

is effectively tight. A surviving hypothesis must instead exploit a strict,
growing defect

\[
d_{C,f}(S)\ll d_C(S)\,r_f(S)
\]

without constructing the full state or truth table.

The dimension itself is not claimed new: it is still a rank of a fused
object. A potentially new contribution would have to be a constructive
compiler or dynamic program that updates this joint residual basis
implicitly, with:

1. an infinite separation from the product proxy, augmented-network
   treewidth/rank-width, and existing DD/WMC algorithms;
2. exact or certified arithmetic;
3. a broad held-out end-to-end advantage;
4. a capability beyond the existing 55-qubit depth-two result.

The first test should compute exact fused residual maps at \(n\leq10\), measure
the defect against the product bound at every cut, and repeat with Haar,
random-phase, and event-permuted controls. If the defect is absent, constant,
or explained by ordinary zeros/symmetry/known rank compression, this
hypothesis class must also be closed immediately.

Separately, the observed layout-dependent representation reversal justifies
an engineering study of adaptive MPO-versus-CSP representation selection.
Without the residual-space theorem and separation above, that is a systems
heuristic, not an A* contribution.
