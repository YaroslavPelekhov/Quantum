# Literature positioning for causal asymmetric bond allocation

Audit updated 2026-08-20. This is a nearest-work search, not a proof of priority.

## Established components

- MPS quantum-circuit simulation and truncation control are longstanding; see
  Banuls et al., [Simulation of many-qubit quantum computation with matrix
  product states](https://arxiv.org/abs/quant-ph/0503174).
- EA-MPS adapts bond dimensions to a requested global final-state fidelity; see
  Oliva, [An entanglement-aware quantum computer simulation
  algorithm](https://arxiv.org/abs/2307.16870).
- Entropy-feedback PID control adapts per-bond dimensions using entanglement
  signals; see Kumaresan et al., [Adaptive Tensor Network Simulation via
  Entropy-Feedback PID Control and GPU-Accelerated
  SVD](https://arxiv.org/abs/2604.03960).
- Operator Backpropagation moves observable evolution into a classical
  Heisenberg-picture computation with approximation/error budgets; see Fuller
  et al., [Improved Quantum Computation using Operator
  Backpropagation](https://arxiv.org/abs/2502.01897).
- Recent noisy-circuit theory proves bond-dimension sufficiency for particular
  global Hilbert-Schmidt error targets and noise models; see Shao et al.,
  [Complexity of tensor network simulation for noisy quantum
  circuits](https://arxiv.org/abs/2606.00474).

## Narrow gap supported by the audit

The searched nearest work does not describe the exact combination tested here:

1. a backward observable residual witness with an explicit irreversible scalar
   tail;
2. different witness-bond schedules for two competing forward trajectories;
3. allocation over `(trajectory, checkpoint, witness bond)` to minimize total
   cost subject to a strict ranking certificate; and
4. a retained failure showing why independently mixing fixed-bond checkpoint
   diagnostics is not a sound resource model.

The manuscript-safe claim is therefore that this is a new formulation relative
to the audited nearest work. It must not be called the first method until a
systematic review also covers goal-oriented tensor approximation, adaptive
error control, ranking-and-selection, and multi-fidelity verification outside
the quantum-circuit literature.
