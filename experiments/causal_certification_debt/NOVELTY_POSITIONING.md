# Novelty positioning: causal certification debt

## Central claim

The paper should not claim a new tensor-network compressor. Its central object
is the **causal price of certified approximation error** in a backward
observable-verification trajectory. A local discarded residual at checkpoint
`j` is charged by

`Lambda_j = sum_{t<=j} a_t`,

because it irreversibly contributes to every earlier certified observable
checkpoint. The finite identity in `THEOREMS.md` makes this price exact for the
uncapped tail, rather than a heuristic importance score. The capped theorem
preserves a rigorous conservative enclosure.

The algorithmic claim is narrower: within a frozen policy class, an oracle-free
cost-plus-debt controller can allocate different residual bonds across time and
across the two competing trajectories while retaining the decision certificate.
Dense simulation is used only after selection to audit soundness.

## Nearest-work boundary

- Standard MPS simulation and truncation explain how discarded Schmidt weight
  controls approximation, but do not price a local truncation by all downstream
  decision-certificate weights: [Vidal, 2005](https://arxiv.org/abs/quant-ph/0503174).
- Entanglement-adaptive MPS methods allocate resources from entanglement
  structure; our price is instead induced by a target observable certificate and
  causal reuse of a residual witness: [EA-MPS](https://arxiv.org/abs/2307.16870).
- Observable backpropagation focuses simulation on measured observables, but the
  audited formulation does not identify this finite causal-debt identity or the
  paired decision-cost allocation: [observable backpropagation](https://arxiv.org/abs/2502.01897).
- Recent work relates tensor-network simulation cost to noise and entanglement;
  that is complementary to, not equivalent to, a decision-certificate shadow
  price: [noisy tensor-network complexity](https://arxiv.org/abs/2606.00474).

Within this nearest-work audit, we did not identify the combination of (i) an
observable-telescope certificate, (ii) an exact causal debt decomposition for
local residual errors, and (iii) oracle-free asymmetric allocation for a paired
ranking decision. This is a literature-audit statement, not a proof that no
equivalent construction exists under different terminology.

## What the data establish

The frozen controller passes ibm32 sorted and spectral, and a separate real
QOBLIB graph. Every bond choice recomputes as the argmin of the frozen score;
all 456 dense audit checkpoints satisfy both residual and operator enclosures.
This establishes sound feasible allocations, not global optimality. In
particular, spectral is still 2.368x more expensive than an all-R128 allocation
that happens to suffice, so the current controller is a rigorous first policy,
not the final optimizer.

## Submission-safe wording

“We introduce causal certification debt, an exact decomposition of accumulated
certified residual error into local compression increments weighted by their
downstream observable exposure. We instantiate it as a frozen oracle-free bond
controller and demonstrate sound asymmetric resource allocation on real QOBLIB
QAOA circuits. We claim certified feasibility and transfer, not quantum
advantage or globally optimal resource allocation.”
