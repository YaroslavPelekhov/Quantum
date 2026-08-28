# Primary-source positioning audit

This note bounds the novelty claim; it is not evidence for a priority claim.

## Nearest established directions

- DMRG and multi-state targeting already allocate a shared truncated basis to
  represent one or more target states. See D'Azevedo et al.,
  [Targeting Multiple States in the Density Matrix Renormalization Group with
  the Singular Value Decomposition](https://arxiv.org/abs/1902.09621).
- EA-MPS already adapts bond dimensions to meet a requested global state-fidelity
  target. See Oliva,
  [An entanglement-aware quantum computer simulation algorithm](https://arxiv.org/abs/2307.16870).
- Operator Backpropagation already shifts part of observable estimation into a
  classical Heisenberg-picture computation and studies approximation/error
  budgets. See Fuller et al.,
  [Improved Quantum Computation using Operator Backpropagation](https://arxiv.org/abs/2502.01897).
- Entropy-feedback controllers already adapt bond dimensions at per-bond
  granularity. See Kumaresan et al.,
  [Adaptive Tensor Network Simulation via Entropy-Feedback PID Control and
  GPU-Accelerated SVD](https://arxiv.org/abs/2604.03960).

## Defensible gap tested here

None of those descriptions makes the resource-allocation target the minimum
joint cost needed to certify the ordering of two competing trajectories, with
different accuracy levels allowed on the two sides. Our proposed contribution
is therefore the combination of:

1. sound observable intervals per trajectory;
2. a comparative stopping condition based on interval separation;
3. joint asymmetric cost minimization across the two simulations; and
4. a frozen transfer test showing that a design-selected asymmetric allocation
   retains its certificate on a held-out qubit ordering.

The wording must remain “we did not identify this exact formulation in the
audited nearest work,” not “the first,” until a broader systematic search covers
decision-focused tensor-network simulation, ranking-and-selection, multi-fidelity
optimization, and goal-oriented error control.
