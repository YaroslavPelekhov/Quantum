# Frozen Phase-0 protocol: event-conditioned output-query falsification

Status: **pre-registered opportunity and falsification screen**.

Frozen on 2026-09-02, before any Phase-0 generator, planner, result table, or
candidate algorithm was implemented or run. The frozen repository base is
commit e6be309783a152e8594cb193efef9fd55f8a09c9 on branch
research/qaoa-exact-event-contraction.

This protocol is deliberately designed to kill a weak research direction
quickly. Passing it would justify a separate theorem/algorithm phase; it would
not itself establish A*-level novelty.

## 1. Binding research question

For a quantum circuit \(C\) on \(n\) measured qubits and a Boolean event
\(f:\{0,1\}^n\to\{0,1\}\), the target is

\[
q(C,f)=\Pr_{x\sim C}[f(x)=1]
      =\langle 0|C^\dagger \Pi_f C|0\rangle,\qquad
\Pi_f=\sum_x f(x)|x\rangle\langle x|.
\]

The Phase-0 question is not whether \(\Pi_f\) can be represented as an MPO.
That is established. The question is:

> After every representation is given an independent, equal-budget
> contraction-plan and slicing optimization, is there reproducible,
> growing, end-to-end headroom from choosing the event representation
> jointly with the circuit computation?

The object being screened is therefore a **pair** \((C,f)\), not a circuit
alone and not an event alone. A consistent relabeling of a circuit is a graph
isomorphism and cannot improve the exact optimum of a label-invariant generic
contraction planner. A qubit permutation matters here only when it selects a
different order-dependent factorization of \(\Pi_f\), or when a deliberately
restricted sweep algorithm is being measured.

No new width, compiler, approximation guarantee, or optimality result is
claimed in Phase 0.

## 2. Frozen legacy evidence

The following facts are inputs, not Phase-0 outcomes. Their source files are
results/exact_event_contraction/SUMMARY.json and
results/exact_event_contraction/event_support.json, whose SHA-256 hashes at
freeze time are respectively:

- 84c688975d35f067b61f9b046d3d209465f996cabb42cea0c24486bd80cf7ff5
- e3bf83ab3adda20e88119bd66afda214ae6d1001a74070b7679224f770c8c12b

| case | qubits | edges | \(\alpha\) | event size | max bond, sorted | max bond, spectral |
|---|---:|---:|---:|---:|---:|---:|
| es60fst03 | 12 | 16 | 4 | 48 | 16 | 6 |
| es60fst01 | 15 | 21 | 5 | 108 | 13 | 6 |
| es60fst02 | 55 | 91 | 23 | 384 | 152 | 5 |

For es60fst02, changing from sorted to spectral order reduced maximum exact
TT/MPO bond by 30.4 times and dense contraction-ready MPO storage by 837.05
times. The exact event representation accepts all 384 members and rejects all
4096 tested outsiders with zero observed error.

The existing validation comprises:

- eight selected-amplitude cohorts, maximum absolute error \(8.77\times10^{-15}\);
- eight high-level MPO cohorts, maximum error \(7.88\times10^{-15}\);
- eight low-level doubled-network cohorts, maximum error \(5.66\times10^{-15}\);
- forty depth-extraction cohorts, maximum error \(2.78\times10^{-15}\);
- sixty layer-extraction rows with exact topology agreement.

On 55 qubits, untruncated complex128 contraction completed only through
QAOA depth two:

| depth | published LR | matched random | ratio MR/LR |
|---:|---:|---:|---:|
| 1 | \(8.4434393208607\times10^{-14}\) | \(1.2280528559635\times10^{-12}\) | 14.5445 |
| 2 | \(7.3639125372524\times10^{-14}\) | \(1.0183370578131\times10^{-12}\) | 13.8288 |

At depth three, the recorded spectral plan had 12,288 slices and optimizer
cost \(1.441662504001535\times10^{15}\), above the frozen \(10^{13}\) guard.
At depth four it had \(2^{32}\) slices and cost
\(5.803719202481111\times10^{20}\). Depths eight and fifteen did not yield a
path. Sorted order was already resource-rejected at depth one.

The 55-qubit case motivated this protocol and is therefore **excluded from
all confirmatory promotion counts, effect estimates, and family-breadth
claims**. The two small QOBLIB cases are legacy face-validity controls and are
also excluded from the synthetic held-out primary test.

## 3. Claims already forbidden

The following statements may not be revived regardless of Phase-0 results:

1. first finite-set-to-TT/MPO compiler;
2. new fixed-order TT/MPO minimality theorem;
3. first one-network computation of an event probability;
4. globally optimal spectral ordering;
5. projector compression alone implies contraction speedup;
6. qubit relabeling alone improves a generic circuit contraction;
7. a prefix score consisting of circuit boundary plus event bond is a new
   width unless it is proved not to reduce to a known weighted
   pathwidth/cutwidth construction;
8. representation/schedule co-design, decision-diagram ordering, or
   query-aware variable elimination in general is new.

The current literature boundary is frozen separately in
PRIOR_ART_BOUNDARY.md.

## 4. Formal quantities and selection rules

### 4.1 Event ranks

For an event \(f\), qubit order \(\pi\), and prefix \(S_k\), define the exact
unfolding rank

\[
r_f(S_k)=
\operatorname{rank}_{\mathbb Q}
\left[f(x_{S_k},x_{\bar S_k})\right].
\]

For a fixed order this is the minimum exact TT bond and the operator-Schmidt
rank of the diagonal projector at the corresponding cut. Ranks are computed
over exact rationals or a finite-field/rational reconstruction procedure that
is independently certified; no floating rank threshold is allowed.

The event-only order \(\pi_E\) is the order that lexicographically minimizes:

1. maximum \(r_f(S_k)\);
2. sum of squared adjacent TT ranks, which fixes dense TT/MPO entries;
3. the tuple of vertex labels.

For \(n\leq9\), \(\pi_E\) is obtained by complete enumeration of all \(n!\)
orders. Calling an order event-optimal without this certificate is forbidden.

### 4.2 Restricted sweep diagnostic

For the doubled \(p\)-layer QAOA network on interaction graph \(G\), compute

\[
w_{\mathrm{sweep}}(G,f,p;\pi)=
\max_k\left[
  2p\,|\delta_G(S_k)|+\log_2 r_f(S_k)
\right].
\]

This is only a diagnostic upper-bound for a particular spatial sweep. It is
not a generic contraction complexity and not a candidate novelty claim.

For \(n\leq9\), all \(n!\) values are enumerated. The circuit-only order
\(\pi_C\) minimizes \(\max_k|\delta_G(S_k)|\), with total cut sum and then
vertex labels as tie-breakers. The restricted joint order \(\pi_J\) minimizes
\(w_{\mathrm{sweep}}\), then its cutwise sum, then vertex labels.

### 4.3 Full-network plan costs

For every event encoding \(R\), let \(N(C,R)\) be the complete scalar
bra-event-ket network. Every encoding receives a fresh contraction search;
a path found for another encoding may be reused only as an additional
baseline, never as that encoding's optimized result.

For a plan \(T\), record:

- exact dense arithmetic count \(F(T)\), separated into additions and
  multiplications where the engine exposes them;
- maximum live tensor elements \(M(T)\);
- peak estimated bytes in complex128;
- number of slices and total sliced arithmetic;
- path-search time;
- event-compilation time;
- contraction time;
- total end-to-end time, defined as compile + plan + execute;
- measured peak host and accelerator memory;
- whether \(T\) is exact-certified, heuristic, or only a lower/upper bound.

No single weighted scalar may be introduced after looking at results. Plan
frontiers are compared by Pareto dominance. Two fixed anchors are also
reported: the minimum-\(F\) plan and the minimum-\(M\) plan. On real execution,
the primary endpoint is end-to-end wall time subject to the same 12 GiB
accelerator-memory cap. If the available accelerator differs, the cap is the
smaller of 12 GiB and 75% of reported free memory and is frozen before the
first run.

The order-conditioned optimum \(K_R^\star(C,f)\) means an exact-certified
frontier over contraction plans for fixed \(R\). The outer envelope

\[
K^\star(C,f)=\operatorname{ParetoMin}_{R\in\mathcal R(f)}
             K_R^\star(C,f)
\]

may be called optimal only when every included representation and outer
choice is certified. Timed-out searches yield intervals and cannot support
an optimality claim.

### 4.4 Phase-0 opportunity measures

Let \(\mathcal B_{\mathrm{one}}\) contain sorted, spectral, \(\pi_E\),
\(\pi_C\), BDD-sifted, and each representation's native heuristic. Let
\(\widehat K_{\mathrm{outer}}\) be the best exhaustively selected TT/MPO order
under the same full-network planner, whether or not it can be selected
efficiently.

For a common feasible memory cap, define the oracle headroom in FLOPs

\[
\Delta_F=
\log_2
\frac{\min_{b\in\mathcal B_{\mathrm{one}}}F_b}
     {F_{\widehat K_{\mathrm{outer}}}},
\]

and analogously \(\Delta_M\) for peak elements and
\(\Delta_t\) for median end-to-end time. Negative values are retained.
The numerator always uses the strongest completed baseline, not a preferred
baseline.

The oracle-selected order is an opportunity bound, not an algorithm. Its
search cost is included in end-to-end timings and is reported separately.

## 5. Frozen synthetic study

### 5.1 Randomness and data split

Every pseudo-random seed is the unsigned big-endian integer encoded by the
first eight bytes of

\[
\operatorname{SHA256}(
\text{ecoq-phase0-v1|family|n|replicate|purpose}).
\]

No seed may be replaced because an instance is slow, uninteresting,
disconnected, or unfavorable. Where rejection sampling is specified, the
same RNG stream continues until the stated predicate holds, and the number
of rejected proposals is recorded.

Random relation replicates 0 and 1 form the development set. Replicate 2 is
the locked holdout. Holdout event files are generated and hashed before
candidate tuning, but their plan and contraction results are not inspected
until the candidate objective, tie-breakers, and implementation hash are
frozen. Any change after opening the holdout creates a new exploratory
protocol version and invalidates confirmatory language.

### 5.2 Circuit family

For each \(n\in\{6,7,8,9\}\), use depths \(p\in\{1,2\}\) and

\[
C(G,p)=
\prod_{\ell=0}^{p-1}
\exp\!\left(-i\beta_\ell\sum_i X_i\right)
\exp\!\left(-i\gamma_\ell
  [\sum_i Z_i+\sum_{(i,j)\in E(G)} Z_iZ_j]\right)
H^{\otimes n},
\]

with angles in radians:

- \((\gamma_0,\beta_0)=(0.37,0.23)\);
- \((\gamma_1,\beta_1)=(0.61,0.41)\).

Gate order within a commuting layer is ascending vertex/edge lexicographic
order. No gate fusion, cancellation, transpiler rewrite, or precision change
may differ between methods. Any common preprocessing is run once and charged
equally.

The graph constructor \(R_{n,r}\) samples \(G(n,m)\) with
\(m=n+\lfloor n/2\rfloor\), without replacement, until connected. The edge
list is sorted after construction. \(P_n\) denotes the natural labeled path.

### 5.3 Query-graph relations

For every \(n\), instantiate these pair templates:

| ID | circuit graph \(G\) | query graph \(H\) | role |
|---|---|---|---|
| A | \(P_n\) | \(P_n\) | aligned easy/easy control |
| B | \(P_n\) | \(\rho_n(P_n)\) | deliberately anti-aligned control |
| C-r | \(P_n\) | \(R_{n,r}\) | circuit-easy/event-irregular |
| D-r | \(R_{n,r}\) | \(P_n\) | circuit-irregular/event-easy |
| E-r | \(R_{n,r}\) | independently seeded \(R'_{n,r}\) | both irregular |
| F-r | \(R_{n,r}\) | \(R_{n,r}\) | aligned irregular |

Let \(b=\lceil\log_2 n\rceil\), and let
\((a_0,\ldots,a_{n-1})\) be the vertex labels \(0,\ldots,n-1\) sorted by the
integer obtained after reversing their \(b\)-bit encodings. Then
\(\rho_n(P_n)\) has edges \((a_j,a_{j+1})\) for \(0\leq j<n-1\). This is a
valid deterministic permutation for non-powers of two as well.

Templates A and B are deterministic controls. Templates C--F are generated
for replicates \(r=0,1,2\). This gives 56 circuit/query-graph pairs before
event and depth expansion.

### 5.4 Query events

Each query graph \(H\) produces two primary events:

\[
f_{\mathrm{OPT}}^H(x)=
\mathbf 1[
 x_i+x_j\leq1\ \forall(i,j)\in E(H),\
 \sum_i x_i=\alpha(H)],
\]

\[
f_{\mathrm{TOP2}}^H(x)=
\mathbf 1[
 x_i+x_j\leq1\ \forall(i,j)\in E(H),\
 \sum_i x_i\geq\max(0,\alpha(H)-1)].
\]

\(\alpha(H)\) and the complete support are obtained by exhaustive enumeration
of all \(2^n\) strings and independently checked with an exact maximum
independent-set routine. OPT preserves the legacy scientific object. TOP2
tests a less sparse, decision-relevant tail rather than selecting events
post hoc by observed probability.

The 56 graph pairs, two events, and two depths give 224 primary scalar
networks. The locked holdout comprises the 64 networks from C--F, replicate
2, both events, both depths, and all four sizes. A and B are structural
controls and do not count toward holdout breadth.

### 5.5 Negative and algebraic controls

For \(G=P_n\) and \(G=R_{n,0}\), both depths, add:

1. identity event \(f(x)=1\);
2. singleton event containing the SHA-derived bitstring;
3. permutation-invariant exact-weight event
   \(\sum_i x_i=\lfloor n/2\rfloor\);
4. linear-code event \(A x=0\pmod2\), where \(A\) has
   \(\max(1,\lfloor n/3\rfloor)\) independent SHA-generated rows of Hamming
   weight three.

All code matrices are regenerated until full row rank, continuing the same
RNG stream. For the linear-code event, the measured TT-rank profile must equal
the known trellis/matroid connectivity formula. These controls detect
label-sensitive planners, broken rank calculations, and rediscovery of known
matroid pathwidth. They are excluded from the primary effect median.

### 5.6 Legacy face-validity controls

Without changing their QPY circuits or event support, reproduce es60fst03
(12 qubits, 48 strings) and es60fst01 (15 qubits, 108 strings) for both
published_lr and matched_random_search, sorted and spectral orders, at
depths \(1,2,4,8,15\). Existing dense results are the references.

These runs validate transfer to the motivating QOBLIB construction. They
cannot promote the hypothesis because their outcomes and order sensitivity
were already observed.

## 6. Exhaustive and bounded search sequence

The sequence is binding. Later stages are not run after a kill gate.

### Stage 0A: semantic and rank audit

For every synthetic event:

1. enumerate the full truth table;
2. compile every representation in Section 7;
3. test membership on all \(2^n\) strings;
4. enumerate all \(n!\) qubit orders for exact TT ranks;
5. compute \(\pi_E,\pi_C,\pi_J\) with frozen tie-breakers;
6. record OBDD residual width, TT rank, support size, and factor-graph
   structure for every relevant order;
7. evaluate \(w_{\mathrm{sweep}}\) for all orders.

The full permutation enumeration is mandatory through \(n=9\). Symmetry may
cache equal subproblems but may not remove labeled orders from the audit log.

### Stage 0B: exact probability validation

For every synthetic network, compute a complex128 dense statevector reference
and sum its probabilities under the full truth mask. Each alternative route
must agree with this reference before its costs are admissible.

For \(n\leq7\), attempt an exact branch-and-bound or dynamic-programming
certificate for each representation's minimum-F and minimum-M contraction
plans. The per-network certification cap is 30 CPU minutes. A timeout stores
the best upper bound, proven lower bound, and gap; it is not converted into an
optimum.

For \(n=8,9\), exact plan certification has the same 30-minute cap for the
outer incumbent and strongest baseline only. In addition, every encoding and
selected order receives the equal-budget heuristic searches in Stage 0C.
Phase 0 may be killed with incomplete certificates, but it may not be
promoted on an alleged exact separation that lacks them.

### Stage 0C: unrestricted planner comparison

For each representation/order, run:

1. a deterministic min-fill/treewidth-style plan;
2. cotengra/HyperOptimizer or the closest version-pinned equivalent with
   128 repeats and 60 CPU seconds;
3. cuTensorNet hyperoptimization with 128 samples where available;
4. joint path-and-slicing optimization under the common memory cap.

Use five independent planner seeds derived from the frozen seed rule. Report
the best structural plan found and the distribution of planning times. Every
method, including an eventual candidate, receives the same number of seeds,
repeats, wall-time cap, memory cap, and preprocessing.

At \(n\leq7\), run all event orders. At \(n=8,9\), the mandatory order set is
the union of:

- sorted, spectral, \(\pi_E,\pi_C,\pi_J\);
- BDD sifting order and each representation-native order;
- 128 SHA-seeded uniform permutations;
- the ten lowest and ten highest
  \(w_{\mathrm{sweep}}\) orders;
- the ten lowest maximum-event-rank orders;
- the incumbent orders produced by the exact outer search.

Duplicate orders are evaluated once. The larger-size search is not called
exhaustive.

### Stage 0D: execution

Execute every nondominated plan that fits the common memory cap for
\(n\leq9\). Use one untimed warm-up and five timed repetitions in an otherwise
idle process. Synchronize the accelerator before and after timing. Report the
median and full range; never report the best timing alone.

Planning, event compilation, and execution are timed separately. The primary
end-to-end number includes all three. An amortized execution-only number may
also be reported for a declared repeat count, but cannot replace the primary
endpoint.

No approximation, tensor truncation, Monte Carlo sampling, reduced precision,
or event-support pruning is permitted.

### Stage 0E: locked holdout

After all development decisions and code hashes are frozen, execute the 64
locked networks exactly once through the complete pipeline. All failures,
timeouts, negative effects, and outliers remain in the denominator.

No candidate change, additional heuristic, new threshold, or new exclusion is
allowed after opening the holdout. Such a change starts a labeled exploratory
v2 and the present protocol's result remains final.

### Stage 0F: optional 55-qubit sentinel

This stage runs only after all promotion gates pass. Apply the frozen
candidate to es60fst02 at depth three, published LR, without changing the
circuit, event, complex128 precision, 65,536-slice guard, or \(10^{13}\)
optimizer-cost guard. First compare plan estimates against every legacy and
generic-planner baseline; execute only if the frozen guard passes.

Success would be a capability demonstration, not confirmatory evidence for
the hypothesis. Failure remains a reported negative result.

## 7. Mandatory baselines

Phase 0 cannot be promoted while a mandatory baseline is missing.

### 7.1 Probability-computation baselines

1. dense statevector plus exact truth-mask sum;
2. one selected-amplitude contraction per supported string;
3. one contraction path reused across basis projectors;
4. batched/open-output selected amplitudes;
5. optimally sliced versions of 2--4;
6. one scalar bra-event-ket contraction.

All methods compute the identical \(q(C,f)\); a method that computes an
energy expectation or a different event is not a baseline.

### 7.2 Event encodings

1. explicit sparse support list;
2. prefix trie and minimized acyclic DFA;
3. reduced ordered BDD;
4. ZDD for sparse supports;
5. ADD where weighted leaves are useful;
6. exact rank-minimal TT and diagonal MPO for every tested order;
7. local CSP/factor-network encoding of independence and cardinality
   constraints;
8. dense diagonal mask for small-reference timing only.

If an engine cannot consume one encoding directly, the adapter and its
conversion time are charged. Translating all representations into the same
MPO and then claiming a representation comparison is forbidden.

### 7.3 Ordering and scheduling baselines

1. input/sorted order;
2. Fiedler/spectral order;
3. reverse Cuthill--McKee;
4. circuit-only min-fill and minimum-cut-prefix orders;
5. exact event-only \(\pi_E\);
6. restricted joint \(\pi_J\);
7. 128 uniform random orders;
8. adjacent-swap/sifting refinement;
9. a generic hypergraph contraction optimizer on the actual augmented network;
10. an exact-certified planner where Stage 0B requires it.

For a generic tensor network, a "circuit-only qubit order" is labeled as a
restricted linear-layout baseline, not as a distinct generic contraction
problem.

### 7.4 Structural explanations to test

Every effect is compared against:

- support cardinality;
- maximum and full profile of exact TT ranks;
- OBDD/ZDD layer widths;
- circuit cutwidth/pathwidth diagnostics;
- weighted treewidth/pathwidth of the augmented factor graph;
- treewidth of the augmented tensor-network line graph;
- vertex/edge congestion or carving-width bounds;
- rank-width and linear rank-width when computable;
- matroid connectivity/pathwidth for linear-code controls;
- dense and sparsity/rank-aware contraction cost models.

Correlation alone neither proves nor disproves equivalence. A collapse is
binding only when an explicit reduction/equality is supplied or a known
algorithm reproduces the proposed object exactly. Empirical prediction is
reported separately.

## 8. Correctness, determinism, and reporting gates

All of the following must pass before cost comparisons:

1. Every event encoding agrees with the truth table on all \(2^n\) strings.
2. Every computed probability has absolute error at most \(10^{-10}\) versus
   dense reference and relative error at most \(10^{-8}\) when the reference
   exceeds \(10^{-8}\).
3. The imaginary magnitude is at most \(10^{-10}\), and the real result lies
   in \([-10^{-10},1+10^{-10}]\).
4. Consistent relabelings agree semantically to the same tolerance.
5. Exact TT ranks agree across two independent rank implementations on all
   primary events through \(n=8\), and on a 20% SHA-selected audit subset at
   \(n=9\).
6. Repeated deterministic planners produce identical paths and costs.
7. Linear-code ranks match their matroid/trellis formula at every cut.
8. All source instances, encodings, circuits, paths, results, environment
   metadata, and failures are hash-manifested.

A failed correctness gate invalidates the affected method. If the candidate or
dense reference fails, the phase stops. A baseline implementation failure is
not grounds to omit the baseline; it blocks promotion until fixed.

## 9. Binding promote/kill decision

### 9.1 Development lock

At the end of development, one candidate selection rule may be frozen. It
must map only \((C,f)\) and the allowed development-time structural features
to an event encoding/order and contraction-search initialization. It cannot
use the exact oracle choice, actual holdout runtimes, or holdout plan costs.

The candidate source hash, feature list, hyperparameters, tie-breakers, and
planner budget are written before Stage 0E. More than one candidate on the
holdout makes the holdout exploratory and automatically fails promotion.

### 9.2 Required promotion gates

All gates P0--P5 are required to proceed to a theorem/algorithm Phase 1.

**P0 — correctness and completeness.** Section 8 passes, all 64 locked
networks are retained, and every mandatory baseline is operational.

**P1 — oracle headroom survives full replanning.** On the 64 locked networks,
the exhaustively/outer-selected representation has:

- median \(\Delta_F\geq3\) bits (at least 8 times fewer FLOPs);
- \(\Delta_F\geq1\) bit on at least 75% of networks;
- no more than 2 times peak memory on the median network;
- positive median \(\Delta_F\) separately for OPT and TOP2 and in at least
  three of C--F.

The same conclusions must hold after generic path and slicing reoptimization.

**P2 — growing rather than constant-only signal.** Across \(n=6,7,8,9\), the
Theil--Sen slope of family-median \(\Delta_F\) is at least 0.25 bits per added
qubit, medians are nondecreasing from \(n=7\) onward, and the \(n=9\) median
is at least 4 bits. This is only a scaling signal; it is not an asymptotic
theorem.

**P3 — an efficient rule recovers useful headroom.** The single frozen
candidate recovers at least 60% of the oracle \(\Delta_F\) on the median
locked network, has median end-to-end speedup \(\exp_2(\Delta_t)\geq3\),
and is slower than the strongest baseline on no more than 20% of locked
networks. Search overhead is included.

**P4 — query contraction beats enumeration.** Against the strongest of direct
amplitudes, reused paths, batched outputs, and their sliced variants, the
candidate has at least 3 times median end-to-end speedup on both OPT and TOP2
and at least 8 times speedup at \(n=9\). A win only over naive independent
amplitudes does not pass.

**P5 — non-collapse prospect.** Before Phase 1 begins, a written lemma target
and an explicit infinite pair family must be stated for which the proposed
pair-dependent mechanism is conjectured to remain bounded while each of the
following grows: event-only TT/OBDD width, circuit-only generic contraction
width, and augmented-network topology-only width. The family must survive
direct checks through at least four increasing sizes and the reductions in
PRIOR_ART_BOUNDARY.md. A new name for weighted pathwidth, line-graph
treewidth, carving width, linear rank-width, or known semantic-rank scheduling
fails this gate.

Passing P0--P5 authorizes work on a proof and scalable implementation. It does
not authorize an A* claim.

### 9.3 Immediate kill gates

Any one of K0--K7 closes this direction as a source of A*-level novelty:

**K0 — invalid computation.** The candidate fails a correctness or semantic
relabeling check.

**K1 — no material oracle headroom.** Locked median \(\Delta_F<2\) bits, or
fewer than half of locked networks have positive \(\Delta_F\).

**K2 — generic replanning erases the effect.** A generic optimizer on the same
augmented network reduces the locked median advantage below 2 times, or the
effect exists only when event and circuit are forced into one spatial sweep.

**K3 — bond-only result.** Initial event bond/entries improve, but neither
optimized FLOPs, peak memory, nor end-to-end time improves by 2 times on the
locked median.

**K4 — no growth.** Family-median \(\Delta_F\) decreases at both \(n=8\) and
\(n=9\), or the fitted slope is nonpositive.

**K5 — existing representation wins.** A mandatory BDD/ZDD/ADD, CSP/WMC,
batched-amplitude, MPE-like temporal, or generic TN baseline matches the
candidate within 2 times median end-to-end time and memory, with no separate
family on which the gap grows.

**K6 — known-width collapse.** The candidate object is explicitly reducible
to an existing weighted pathwidth/treewidth, line-graph contraction width,
rank-width/linear-rank-width, matroid pathwidth, project-join tree, or known
representation-aware schedule objective.

**K7 — evidence cannot be completed.** Any mandatory baseline, locked family,
full failure log, or required certificate is omitted after the fixed resource
budget. "Promising but incomplete" is reported as incomplete, not promoted.

If a kill gate fires, all completed artifacts are retained and a short
falsification report identifies the first gate and any later gates that also
fail. No rebranding of the same score or ordering under a new name is allowed.

### 9.4 A*-level gate beyond Phase 0

Even after promotion, an A*-level submission requires all of:

1. a non-collapsing pair-dependent characterization or matching upper/lower
   bounds;
2. a proved infinite separation from state simulation, selected-amplitude
   enumeration, standard augmented-TN contraction, and the closest DD/WMC
   method;
3. an efficient exact/FPT or certified approximation algorithm;
4. a new frozen held-out study on substantially larger, independent
   circuit/event families;
5. at least 10 times median end-to-end gain against the strongest baselines
   and instances solved within the same resource cap that those baselines
   cannot solve;
6. exact or rigorously bounded numerical error.

The 55-qubit depth-three sentinel would be useful evidence but does not replace
these requirements.

## 10. Analysis discipline

- The unit of analysis is one frozen \((G,H,f,p)\) network.
- Report paired log2 ratios and all individual rows; do not average raw
  runtimes across sizes.
- Primary summaries are medians. Also report geometric means, quartiles,
  minima, maxima, and a paired bootstrap 95% interval with 10,000 SHA-seeded
  resamples.
- The bootstrap interval is descriptive because the generator distribution
  is artificial; promotion is determined by the fixed thresholds above, not
  by a p-value.
- Timeouts and out-of-memory outcomes remain as censored failures and in
  coverage counts. They are never silently imputed as favorable speedups.
- Planner variance, compilation, warm-up, and cache state are reported.
- No favorable subset, alternative event threshold, depth, precision, or
  memory cap may replace the registered primary analysis.
- Exploratory observations are clearly labeled and cannot change the binding
  verdict.

## 11. Resource policy

Phase 0 uses local classical resources only. It launches no QPU task and
incurs no cloud charge.

- complex128 throughout;
- no tensor truncation or approximate decision diagram;
- at most 30 CPU minutes for each exact-plan certificate;
- at most 60 CPU seconds and 128 repeats per heuristic planner seed;
- five planner seeds;
- common accelerator-memory cap from Section 4.3;
- retain the legacy guards of 65,536 slices and optimizer cost \(10^{13}\)
  for the optional 55-qubit sentinel;
- stop an individual job at 60 wall-clock minutes unless it is a declared
  exact-certificate job;
- record rather than retry resource failures.

A hardware upgrade after the phase starts requires rerunning every timed method
on the same device. Structural cost comparisons remain portable.

## 12. Required artifacts

Execution of this protocol must eventually produce, without overwriting the
legacy exact_event_contraction artifact:

- a machine-readable frozen instance registry and split;
- truth tables/support hashes and every event encoding;
- exhaustive order/rank rows for \(n\leq9\);
- certified plan bounds and heuristic paths;
- complete timing/memory rows;
- candidate pre-holdout lock file and source hash;
- holdout results with every failure;
- a machine-readable summary implementing P0--P5 and K0--K7;
- a human-readable report with a binding verdict;
- a SHA-256 manifest covering code, inputs, plans, and results.

The final verdict must be exactly one of:

- KILLED_AS_ASTAR_SOURCE;
- INCOMPLETE_NO_PROMOTION;
- PROMOTE_TO_THEOREM_PHASE;
- PROMOTE_WITH_55Q_SENTINEL_SUCCESS.

No result from this protocol can directly use the label A*-novel.
