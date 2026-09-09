# Next-capability adversarial gate, 2026-09-09

The completed campaign failed its registered gain threshold. Do not rerun
the same optimizer under a different name. This gate does not change the
frozen campaign or retrospectively relabel any family as development.

## Rejected generic contribution: two-copy quadratic measurement

For Q=sum_i w_i P_i tensor P_i and two independent identical copies rho,
E[Q]=sum_i w_i Tr(rho P_i)^2. All lifted terms commute, since the two
Pauli commutation signs cancel. Bell measurements can estimate these
squares simultaneously. This is an existing measurement primitive, not
a new contribution of this project. Xu et al. explicitly use this lift
and commutativity in Section IV.2, equations (10)-(14):
https://arxiv.org/html/2511.13531v1 .

Quantum expectation value estimation by doubling the number of qubits
explicitly assesses this existing approach:
https://arxiv.org/abs/2412.14466 .
The attempted v2 HTML URL was unavailable; do not claim a full theorem
audit of that paper from its abstract.

Noise resilience is not a blank prior-art space either. Cotler, Gong and
Kannan's Noisy quantum learning theory (2026) studies noise-dependent
limitations of purity testing and Pauli learning, including the fragility
of multi-copy primitives. Its oracle model must be matched before importing
any lower bound into our fixed-state experiment:
https://www.nature.com/articles/s41467-026-73693-x .

Two-copy baselines require two preparations, coherent copy access and
measurement-gate noise accounting. Their absence does not invalidate the
negative result against the frozen single-copy baseline, but prevents a
claim of optimality across quantum measurement architectures.

## Registered diagnostic: structural relationship of G8 and G9

Before execution: construct the two exact archived observable systems,
enumerate every induced G8 embedding in G9, and enumerate all copy/split
pairs of G9. For each embedding record whether the retained weights agree
and the omitted vertex/weight. Check the exhibited map directly by integer
symplectic products, separately from NetworkX's isomorphism search.
Budget: two graphs only, no optimizer, no new training or held-out tuning.

A matching induced subgraph means these fixed graph instances are
structurally related, NOT that their noisy four-/three-qubit tasks are
identical. Absence of an embedding does not prove broad family independence.
No numerical equality of beta is used as an isomorphism criterion.

Outcome: NetworkX finds two induced embeddings, both weight-preserving,
and no copy/split pair. A separate stdlib-only verifier checks the witness
G8 vertex i -> G9 vertex i+1 (zero-based); omit G9 vertex 0, word XIII,
weight 1. It compares local Pauli-character anticommutation with binary
symplectic products, and rejects altered weights and an altered observable.
The independent verification certifies this map, not completeness of
NetworkX's two-map enumeration.

Consequently G9 is a held-out graph instance with a development G8 induced
subgraph, not evidence of transfer to a structurally unrelated graph family.
Likewise antiC7 and antiC9 are sizes of the same anticycle family. The
original split was genuinely frozen, but its phrase "two held-out families"
overstates structural diversity. Retain the original protocol and report
this limitation explicitly. This makes the failed-gain verdict no less
negative; it further prevents interpreting this corpus as broad transfer.

Run: `python -S experiments/pauli_operational_phase0/check_holdout_structure.py`.
General A-star claim remains unconfirmed. No large campaign was launched.
