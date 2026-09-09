# Deterministic-only hidden memory: reject the generic novelty claim

2026-09-09. Previous cycle made progress by falsifying practical cutoff
instability, rather than just repeating status. This cycle checked a
different observable-control question before a large experiment.

Proposed generic question: can quantum correlations be completely hidden
from deterministic system operations followed by final-state tomography,
yet exposed by retaining a selective intermediate outcome?

## Primary-source coverage

Milz, Pollock and Modi, Physical Review A 98, 012108 (2018),
[Reconstructing non-Markovian quantum dynamics with limited control](https://arxiv.org/html/1610.02152),
arXiv:1610.02152v2, Sections IV.1–IV.2 and V.1 were inspected.
V.1 equations 26–27 explicitly use a SWAP evolution and an initial
correlation term to show invisibility under unitary control and detection
by a selective causal break. IV.1 formulates the information accessible
from the span of allowed operations. These are not merely related titles.
The HTML carries an unrelated 2026 rendering date; the version metadata
and journal publication identify the work as 2018, not a new 2026 result.

## Why replacing unitary by CPTP is insufficient novelty

Our proposed generalization is immediate from trace preservation:
for any traceless system operator X, Tr E(X)=0 for every CPTP E, not only
unitary E. More generally start with any joint state rho_SE and apply E
on S followed by SWAP. The final S state is rho_E for every E. Thus all
initial joint states with the same environment marginal give identical
data under these allowed experiments. Resetting S without keeping an
outcome does not remove this indistinguishability.

Choosing a maximally entangled initial state or its product of marginals
gives quantum-correlated and uncorrelated realizations with identical
deterministic outputs. A selective measurement on S can steer the former
environment state. This extension is a no-signalling/trace-preservation
corollary of the known construction, not a new learning capability or
new experimental discovery. Retained ancillas or intermediate classical
records change the access model and are excluded from this statement.

Decision: do not launch a large campaign to rediscover generic hidden
memory or claim that adding a reset solves it. Any future control-resource
claim needs a specific task, access model and resource lower bound beyond
this known null space. No broad assertion that all memory questions are
solved is made. No new quantum-memory novelty is confirmed here.

## Return to the actual open theorem in the manuscript

The fixed C014 inequality is still a concrete unresolved operator problem,
not the closed QAOA/symmetry or causal-cutoff branches. Re-ran its exact
stdlib verifier and the C016 theta witness verifier on the current tree:
2167 stable sets, 88 tight sets, full facet rank 24, classical bound 6;
the exact theta witness is 325328979/50000000=6.50657958. Both pass.
Neither proves the quantum upper bound. No new optimization was run.

The next useful proof effort must impose genuinely quantum constraints
beyond the theta relaxation and account for all central/sign sectors.
Simply repeating the 1024-start physical search is not progress toward a
global upper bound. A promising candidate bound must be checked against
the existing positive G8 violation before interpreting a value of six.
The larger all-weight SCF claim and publication priority remain open.
