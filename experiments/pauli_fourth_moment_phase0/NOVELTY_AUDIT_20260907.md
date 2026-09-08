# Novelty gate, 2026-09-07

Scope: adversarial priority audit of C007/C008, not C009 or a new quantum
experiment. Starting source: 1c3aa654d650f0dc138b22aa3a330b11157e65af.
A-star novelty is NOT CONFIRMED. Internal proof acceptance, priority and
publication significance are separate questions.

## Frozen structural diagnostic (registered before execution)

Enumerate every proper nontrivial vertex subset of G_m for m=0,...,4 and
the fixed C008 12-vertex target. A module requires every outside vertex to
be adjacent to either all or none of its vertices. Also enumerate induced
four-cycles. Use only integer graph adjacency, without quantum optimization.

A module is a possible known substitution route, not automatically a
refutation. Absence excludes nontrivial direct lexicographic decomposition
of that tested graph, NOT induced embeddings in larger known graphs, every
sequence of graph operations, or a uniform statement for all m.
An induced C4 excludes direct application of the ECF mode theorem below.

## Primary-source comparison

[Xu et al., arXiv:2511.13531v1](https://arxiv.org/html/2511.13531v1):
Definition 3 already formulates all-weight equality BETA=STAB. Section III
provides join, disjoint union, lexicographic product, copying and splitting
closures, plus h-perfect sufficiency. Section IV already reduces equality
to facet weights. None of these formulations or generic procedures is ours.
Section IX.1 explicitly anticipates a connection to the solvable claw-free
class, but its broad inclusion wording cannot be read as a valid theorem
for all claw-free graphs: the paper itself reports the anti-heptagon as
hbar-imperfect. Section III does not supply the precise weighted SCF
statement we need. This ambiguity is a priority risk, not evidence that
we originated the concept. Whether C007 follows from their operations
through a larger embedding remains unresolved.

[Fukai, Pozsgay and Vona, arXiv:2605.31453v2](https://arxiv.org/html/2605.31453v2):
Theorem 3.2 requires connected even-hole-free claw-free (ECF) graphs and
constructs fermion modes; Section 3 derives them via path products and a
Krylov generating function. Theorems 5.5 and 5.11 construct conserved
charges for claw-free graphs within explicit even-bubble-wand range
conditions. They assert conservation, not the all-weight Pauli uncertainty
inequality of C007. These particular theorem statements do not directly
establish C007. This is not an exhaustive non-derivability result. Generic
hidden-mode, induced-path or Krylov constructions cannot be claimed new.

## Candidate contribution and acceptance criteria

- C007: candidate precise contribution is all-weight uncertainty for the
  specified unbounded G_m family, using its signed-Gram bound and uniform
  closure proof. Exact family/inequality priority is still unestablished.
- Classical Hall transport, clique refinement and facet reduction are
  tools, not new algorithms.
- C008: structural target selection, not a proved quantum upper bound.
- C009, if successful on just the fixed graph, would extend coverage;
  that alone would not demonstrate A-star significance.

Next novelty gate: resolve known-closure/embedding routes and extract an
operator lemma valid beyond the one fixed target, with explicit hypotheses
and failure examples. Then establish a quantum consequence not already
implied by the cited framework. External mathematical/priority review is
still needed; no reviewer contact is authorized or performed by this audit.

## Diagnostic outcome

All six frozen graphs have zero proper nontrivial modules. Induced C4
counts for G_0,...,G_4 and C008 are respectively 1,3,6,10,15,12.
The initial exhaustive bitmask run was followed by a set-based diagnostic
with P4, C4 and K3 controls:

`python -S experiments/pauli_fourth_moment_phase0/check_novelty_modules_20260907.py`

Thus direct nontrivial lexicographic decomposition is excluded for these
six graphs. Direct ECF Theorem 3.2 application is also excluded. General
embeddings and other derivations remain open. This bounded diagnostic is
not part of the existing 56-artifact proof bundle and does not increase
its accepted quantum theorem scope. No new quantum claim is accepted here.
