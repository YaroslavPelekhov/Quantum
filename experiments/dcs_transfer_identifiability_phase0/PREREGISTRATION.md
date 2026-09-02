# Preregistration: fidelity transfer in doped Clifford sampling

Frozen on 2026-09-03 before the confirmatory search and before inspecting any
held-out circuit family.  Exploratory observations made before this freeze are
listed explicitly below.

## Research object

We study whether the post-selected fidelity of a Clifford+T circuit can be
certified from classically verifiable Clifford companions when all circuits
share a stationary stochastic Pauli fault-path distribution.  Fault paths may
be spatially and temporally correlated.  The inserted phase gates are ideal,
commute with the measured checks, and therefore preserve the accepted set.

This is not a claim about QAOA, MPS compression, simulator rank reversal, or
learning a low-dimensional noise predictor.

## Claims frozen before confirmatory experiments

### Claim N1: asymptotic counterexample

The asymptotic statement

`Pr(harmless | accepted) = O(n^-c)`

does not follow from circuit independence plus arbitrary correlated Pauli
noise.  In the random-cycle architecture of arXiv:2607.25941v2, a fixed
correlated Pauli fault immediately after the first deterministic CZ layer can
be the forward image of an input `Z`.  A distribution concentrated on that
fault is circuit independent and harmless for every random continuation, so
the conditional probability is one.  This falsifies rarity as stated; it does
not by itself falsify the reported experiment because this early fault also
remains harmless after later doping.

### Claim N2: transfer non-identifiability

Reference fidelity, the complete syndrome distribution, and equality of
acceptance probabilities do not identify doped-state fidelity under arbitrary
correlated stationary Pauli noise.  The frozen two-qubit witness is:

- reference state `|Phi+>`;
- measured check `Z1 Z2`;
- target doping `T1 T2`;
- deterministic accepted fault `X1 X2` after doping.

The fault stabilizes the reference, while it maps the doped target to an
orthogonal state.  Hence the observable reference data can have fidelity one
and an all-zero syndrome while target fidelity is zero.

### Claim P: one of two genuinely new outcomes must survive

Let each T site be independently replaced by `I` or `S`, producing a random
Clifford companion `C_b`.  For a stationary stochastic Pauli fault-path model,
test the proposed distribution-free inequality

`1 - F_T <= C * E_b[1 - F_b]`.

Only either of the following counts as a surviving research result:

1. **Certificate outcome:** a dimension- and T-count-independent constant
   `C <= 4` is proved for the nondegenerate, DCS-pruned circuit class, together
   with a finite-sample lower confidence bound and validation on unseen
   circuits; or
2. **Barrier outcome:** an explicit nondegenerate DCS family proves
   `C_t >= exp(Omega(t))` (or rules out every finite companion-only bound), with
   a matching or near-matching upper bound that connects the obstruction to a
   quantum resource rather than to generic polynomial interpolation.

Anything between these outcomes is not an A-star-level result for this cycle.

## Exploratory disclosure

Before the freeze:

- the exact two-qubit non-identifiability witness was derived;
- a random search over 1,000 small circuits with up to seven phase sites found
  no companion-invisible target failure, but falsified `C=2` and observed a
  maximum ratio `8/3`;
- a second 1,000-case one-qubit search with 8--10 sites again observed `8/3`;
- an unconstrained construction with adjacent phase sites reached ratio four,
  but adjacent `T*T=S` is a degenerate Clifford collapse and is excluded by
  DCS pruning.

These observations define the confirmatory threshold; they are not evidence
for Claim P.

## Circuit class and exclusions

The confirmatory positive claim is restricted to circuits satisfying all of:

- Clifford skeleton with single-qubit `T` rotations on internal wires;
- every dopant commutes with every retained spacetime check;
- the same stochastic Pauli fault-path distribution is used for target and
  companions;
- dopants that act trivially, commute to measurement, or are mutually
  equivalent with only commuting intervening rotations are removed;
- no adjacent or otherwise algebraically collapsible group of dopants is
  counted as nondegenerate magic;
- target and companions use the same multi-qubit schedule and timing.

Coherent noise, circuit-dependent noise, drift, and imperfect inserted phase
gates are out of scope for the first theorem and become mandatory robustness
tests after any pass.

## Development and held-out split

Development:

- seeded random circuits with `n <= 4`, `t <= 10`;
- exhaustive one- and two-qubit canonical-state search where feasible;
- hand-derived Bell and boundary-fault witnesses.

Held out until the claim and constant are fixed:

- structured graph-state and ring families;
- new seeds with `n=5..7` and unseen depths;
- the public 64-qubit IBM payload QASM files, used only for structural and
  companion-generation checks because the released archive omits ancilla/check
  back-cumulants and the harmless-fault classifier;
- any real-device run.

No threshold may be tuned on held-out results.

## Baselines

- a single undoped reference;
- all-S and all-Z companions used in the source experiment;
- uniformly random single-qubit Cliffordization under the Pauli-twirling
  assumption of arXiv:2503.05943;
- exact enumeration of all `I/S` companions for small `t`;
- the source paper's model-based harmless-fault Monte Carlo when its missing
  inputs can be reconstructed or supplied.

## Confirmatory gates

The certificate outcome passes only if all gates hold:

1. no exact counterexample to `C <= 4` in the exhaustive development domain;
2. a written pointwise proof for every accepted deterministic Pauli fault path;
3. linearity extends the proof to every correlated stochastic mixture;
4. a finite-sample one-sided confidence procedure has verified coverage;
5. the bound remains non-vacuous on at least one unseen family at target
   fidelity below 0.9;
6. random companions strictly dominate the all-S/all-Z/reference baselines on
   a preregistered adversarial mixture;
7. the theorem does not reduce to the existing lowest-order process-fidelity
   Cliffordization result.

The barrier outcome passes only if all gates hold:

1. the lower-bound family obeys all nondegeneracy and check-commutation rules;
2. the family has growing T count and does not become Clifford after local gate
   cancellation;
3. the lower bound concerns state-fidelity transfer, not merely interpolation
   of an arbitrary scalar polynomial;
4. the upper bound is explicit and asymptotically comparable;
5. prior-art audit finds no equivalent robustness-of-magic or quasiprobability
   theorem already implying the result.

## Kill conditions

The A-star hypothesis is killed if any of the following occurs:

- a nondegenerate exact counterexample violates `C <= 4` and no barrier theorem
  with matching upper bound is obtained;
- the only result is the generic linear-program duality of partial
  identification;
- the positive result is already implied by Clifford proxy benchmarking,
  accreditation/trap verification, or the announced in-situ benchmarking Part
  II;
- the bound requires exponentially many measured companions without proving a
  new lower bound;
- public or real data cannot exercise the central observable because required
  check/fault metadata are unavailable, and no independent hardware instance
  can be run;
- robustness to small phase-gate error or schedule drift makes every bound
  vacuous.

## Reproducibility rules

- all random seeds are fixed in `protocol.json`;
- exact statevector arithmetic is cross-checked against stabilizer propagation
  on Clifford corners;
- every counterexample is serialized with its complete ordered gate and fault
  list;
- development and held-out manifests are hashed separately;
- post-hoc analyses are labeled and cannot change this decision rule.

