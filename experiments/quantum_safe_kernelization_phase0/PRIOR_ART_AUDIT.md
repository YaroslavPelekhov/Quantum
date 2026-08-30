# Adversarial prior-art audit

Audit date: 2026-08-30.  This is a claim-boundary document, not a complete
literature review.

## Closest work

- Aharonov and Zhou, *Hamiltonian sparsification and gap-simulations*
  (arXiv:1804.11084), already define simulation that preserves ground spaces
  and spectral gaps and prove general quantum degree-reduction obstructions.
  Therefore neither "preserve the low-energy space" nor a generic no-go for
  Hamiltonian reduction is new here.
- Thai et al., *FastHare* (arXiv:2205.05004), reduce Ising Hamiltonians for
  quantum annealing by merging variables constrained in optimal solutions.
  It establishes that optimisation-preserving QA preprocessing is prior art;
  its advertised guarantee is about optima, not the annealing path.
- Choi, *The Effects of the Problem Hamiltonian Parameters on the Minimum
  Spectral Gap* (arXiv:1910.02985), demonstrates that equivalent MIS/Ising
  encodings can drastically alter anti-crossings and minimum gaps.  A gap
  change under an equivalent formulation is therefore not novel by itself.
- Kombe and Pritchard, *Reducibility of native weighted graphs on Rydberg
  Arrays* (arXiv:2605.07952), directly studies classical MIS/MWIS kernelisation
  for native unit-disk Rydberg instances.  It is the closest application
  neighbour, but its stated scope is classical reducibility and embedding
  overhead rather than preservation of the Rydberg annealing path.
- Schuetz et al., *Quantum Compilation Toolkit for Rydberg Atom Arrays*
  (arXiv:2412.14976), combines graph reductions, compatibility checks,
  embeddings, and Aquila experiments.  It prevents claiming that reduction
  plus Rydberg hardware validation is itself new.
- Jeong and Kim, *Enhanced Maximum Independent Set Preparation with Rydberg
  Atoms Guided by the Spectral Gap* (arXiv:2602.17991), uses the spectral gap
  to design detuning schedules and validates them on hardware.  Gap-aware
  Rydberg control is prior art, though not kernel certification.

## Remaining narrow claim candidate

The only plausible claim after this screen is a Rydberg-MIS-specific theory
and algorithm that certifies when a particular classical kernel rule preserves
a stated finite-time annealing task, together with a separation from ordinary
MIS exactness and a nontrivial safe rule.  Merely showing different gaps,
different success probabilities, or restating a P/Q perturbation bound is
insufficient.

## Immediate structural warning

An optimisation-preserving lift usually maps *some* reduced optima to original
optima.  A low-energy projector claim instead needs a near-isometry onto the
entire target subspace.  The leaf rule fails this whenever an optimal solution
containing the leaf's neighbour exists.  It also fails at the initial endpoint
because its static lift forces the leaf to one while the standard Rydberg
initial ground state is the empty set.  These are theorem-level obstructions to
the naive whole-path formulation, but too direct and too close to the general
gap-simulation literature to count as an A* contribution alone.
