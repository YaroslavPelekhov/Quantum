# Preregistration: fourth-power Pauli profiles and fractional colouring

Frozen on 2026-09-03 before adversarial alternating optimisation, the full
five-qubit held-out sweep, or any proof-guided instance selection.  Exploratory
observations available before the freeze are disclosed below.

## Research object

Let `S_1,...,S_m` be Hermitian Pauli observables, let `G` be their
anticommutation graph, and let `w >= 0`.  Define

`beta_p(G,w) = max_rho sum_i w_i |Tr(rho S_i)|^p`

and let `alpha(G,w)` be the maximum weight of a pairwise commuting subset.
The target is the finite-exponent question left open in Question 8 of
Stempin--Llorens--Huber, arXiv:2608.20113, rather than another QAOA/MPS or
fidelity-transfer reformulation.

## Frozen primary claim

For every finite family of qubit Pauli observables and every nonnegative
weight vector,

`beta_4(G,w) = alpha(G,w)`.                                    (T1)

Equivalently, for every state `rho`, the vector

`q_i = |Tr(rho S_i)|^4`

belongs to the stable-set polytope of `G`.  Equivalently again, it admits a
sub-probability decomposition into incidence vectors of commuting subsets.

The lower inequality in (T1) is attained by a common eigenstate of a
maximum-weight commuting subset.  The research content is the upper
inequality.

## Frozen consequence

For

`B_epsilon(rho) = {P : |Tr(rho P)| >= epsilon}`,

fractional-colouring LP duality and (T1) imply

`chi_f(G(B_epsilon)) <= epsilon^-4`.                            (C1)

Thus Question 8 of arXiv:2608.20113 has an affirmative answer with universal
exponent `kappa=4`.  The anti-`C_7` lexicographic-power construction in that
paper gives the current frozen lower exponent

`kappa >= -log(7/2) / log((1+2 sqrt(2))/7) = 2.07598...`.

No claim that `4` is optimal is preregistered.

## Exploratory disclosure

Before this freeze:

- the exact anti-`C_7` state reproduced violations at `p=2` and `p=2.05`,
  equality at `p=2.07598...`, and no violation at `p>=2.1`;
- iterative state optimisation on 18 published eight-vertex and 1,419
  published nine-vertex Pauli graphs found no `p=4` violation, including
  random log-normal weights;
- exact fractional-cover LPs over all Lagrangian Pauli subspaces passed 163
  three-qubit states and 62 four-qubit states at `p=4`;
- nine initial Haar states passed a full five-qubit LP containing all 1,023
  nonidentity Paulis and all 75,735 Lagrangian contexts;
- no proof of (T1) was known, and generic theta-body squaring was already
  recognized as an invalid proof route.

These observations motivate (T1); none counts as confirmation.

## Development and held-out split

Development instances:

- all source-paper graphs on at most nine vertices;
- seeded Erdos--Renyi and Mycielski graphs with standard SAURs;
- all Pauli contexts on at most four qubits;
- the anti-`C_7` exact algebraic anchor;
- weights drawn from uniform, log-normal, sparse, and facet-normal families.

Held out until the statement and numerical tolerances are frozen:

- the complete five-qubit Pauli graph and its 75,735 contexts, except for the
  nine disclosed Haar smoke tests;
- near-stabilizer paths with perturbation angles not used in development;
- alternating LP-dual/state adversaries from independently chosen seeds;
- lexicographic products whose seed is not anti-`C_7`;
- exact symbolic checks of every equality case proposed by a proof.

## Baselines and controls

- `p=2`, which must reproduce known beta-number violations;
- the exact anti-`C_7` critical exponent `2.07598...`;
- clique-only uncertainty constraints, which are insufficient in general;
- the Lovasz theta body, whose coordinatewise-square inclusion in `STAB` is
  false for general graphs and therefore cannot prove (T1);
- stabilizer states, product magic states, Haar states, and controlled
  near-stabilizer paths;
- dense and sparse weight vectors, including weights returned by the dual of
  the fractional-cover LP.

## Confirmatory gates

The primary claim survives only if every gate holds:

1. a complete written proof establishes (T1) for arbitrary weights, mixed
   states, redundant Paulis, signs, and reducible quasi-Clifford
   representations;
2. the proof does not silently replace the stable-set polytope by its clique
   or theta relaxation;
3. independent proof reconstruction finds no missing positivity,
   representation, or minimax assumption;
4. adversarial alternating optimisation finds no violation above numerical
   tolerance on the frozen held-out suite;
5. exact or interval arithmetic certifies every numerically marginal case;
6. an adversarial prior-art audit finds no theorem already implying (T1) or
   (C1);
7. the fractional-colouring implication is proved from the weighted LP dual,
   not inferred from unweighted tests;
8. algorithmic claims distinguish existence of a fractional colouring from
   efficient construction or sampling of one.

## A-star decision rule

This cycle may be labelled an A-star-level hypothesis only if gates 1--7 pass
and the resulting theorem still directly resolves the explicit 2026 open
question.  A stronger systems claim additionally requires either an
efficiently sampleable colouring construction or a proved separation showing
why existence alone changes sample complexity without claiming time
efficiency.

Numerical support alone, an unweighted theorem, a theorem for a restricted
graph class, or a proof conditional on the desired stable-set decomposition
does not pass.

## Kill conditions

The primary claim is killed immediately by any of:

- an exact Pauli/state/weight counterexample with `beta_4 > alpha`;
- a proof step that requires a doubly-nonnegative matrix to be completely
  positive without an additional Pauli-specific argument;
- dependence of the exponent on qubit count, graph size, or representation;
- a prior theorem equivalent to the weighted fourth-moment inequality;
- failure of the implication to fractional colouring under the correct LP
  dual;
- confirmation only for pure states if convexity does not extend it to mixed
  states.

If (T1) is killed, the next admissible question is whether some larger fixed
even exponent works.  The exponent may not be tuned on held-out instances;
each replacement must be separately frozen and audited.

## Reproducibility rules

- all seeds and tolerances live in `protocol.json`;
- development and held-out outputs are stored separately;
- Pauli commutation is checked independently from matrix multiplication;
- maximum-weight commuting sets and fractional covers use independently
  checked primal and dual objectives;
- every candidate violation is serialized before local refinement;
- all post-freeze changes to the claim are recorded as amendments, never
  overwritten.
