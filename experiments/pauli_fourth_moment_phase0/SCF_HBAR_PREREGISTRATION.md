# Preregistration: hidden free fermions versus hbar-perfectness

Frozen before the systematic experiment on 2026-09-03.

## Object change

The proved line-graph result uses a generator-to-generator Majorana map.  The
next target is the strictly larger hereditary class `SCF`: every connected
component is claw-free and contains a simplicial clique.  Hamiltonians with
SCF frustration graphs have a hidden, symmetry-resolved free-fermion solution
(Chapman--Elman--Mann), even when their Pauli generators do not form a line
graph.

## Claims tested

`H1-weighted`: every SCF graph is hbar-perfect,

`beta(G,w) = alpha(G,w)` for every nonnegative weight `w`.

This is the high-risk claim.  It is false if one reproducible Pauli
realization, state, and nonnegative weight give a ratio greater than one by
more than `1e-7`.

`H1-rank`: for every SCF graph and every induced subgraph `F`,

`beta(F,1) = alpha(F)`.

This weaker statement would place the beta body in the rank relaxation of the
stable-set polytope.  It does not imply `H1-weighted` when non-rank facets are
present.

## Analytic route fixed in advance

For `H1-rank`, use the symmetry-resolved free-fermion decomposition of an SCF
Hamiltonian `A=sum_i a_i P_i`.  Each sector has at most `alpha(G)` positive
single-particle energies.  The coefficient of the quadratic term of the
generalized characteristic polynomial gives

`sum_j epsilon_j^2 = sum_i a_i^2`.

Therefore Cauchy--Schwarz gives

`||A||^2 <= alpha(G) sum_i a_i^2`.

The variational characterization of beta and the commuting independent-set
lower construction then give `beta(G,1)=alpha(G)`.  Heredity of SCF supplies
the statement for every induced subgraph.  The proof must be rejected if the
sector normalization or coefficient identity fails under direct spectral
audit.

No analytic route is assumed for `H1-weighted`.  Unweighted equality, even on
all induced subgraphs, must not be presented as weighted equality.

## Adversarial experiment gates

1. Reproduce the published anti-heptagon weighted violation as a positive
   control and verify that it has no simplicial clique.
2. Audit every connected SCF graph in the NetworkX graph atlas through seven
   vertices, separating line graphs from genuinely non-line SCF graphs.
3. Audit the explicit eight-vertex non-line SCF Hamiltonian in the 2023
   free-fermion paper.
4. Complete closed neighborhoods in claw-free seeds, including odd
   anticycles, to force a simplicial vertex while retaining a deliberately
   adversarial ancestry.
5. Test random connected SCF non-line graphs on eight through ten vertices.
6. Use uniform, lognormal, sparse, and integer weights with multi-start
   see-saw optimization.  Any lower-bound violation kills `H1-weighted`;
   absence of one is evidence only.

## Novelty gate

The weighted claim is not A-star-ready without a proof and a direct literature
audit across hbar-perfect graphs, hidden free fermions, independence
polynomials, and claw-free stable-set polytopes.  The rank claim is retained as
a theorem only if its proof audit passes, but it is explicitly a smaller
contribution.

## Post-run outcome

The `H1-rank` coefficient and sector-normalization audit passed, yielding the
theorem recorded in `POSTFREEZE_THEORY_NOTE.md`.  The stronger `H1-weighted`
claim survived the broad random suite and a separate attack on 32 non-rank
facet directions obtained from complete stable-set vertex enumeration, but
remains unproved.  A post-preregistered strengthening seeded those same
directions from their first state-moment SDP profiles and again found no
violation.  The SDP upper ratios remained loose at about `1.118034`, so this
is a falsification attack, not a certificate.  Both the anti-heptagon and the
published narrow-basin `G9` violation were reproduced as positive controls.
The pinned published imperfect-graph sets through nine vertices contain no
SCF member.  These outcomes strengthen the conjecture but do not change its
preregistered proof requirement.

A further post-preregistered exhaustive gate screened all 261,080 connected
graphs of order nine from McKay's hash-pinned census.  It found 4,308 SCF
graphs and reduced 701 non-rank facet occurrences to 128 weighted-support
isomorphism classes.  All 29,664 sign orthants of their first-moment
SDP-guided profiles survived.  This closes the selected seeded search at
order nine, not the continuous global optimization problem.

The next structural pass proved 115 of the 128 order-nine types: their
coefficient-one vertices form a clique completely joined to the
coefficient-half induced subgraph, so join preservation and the proved SCF
rank theorem apply.  Of the 13 residual alpha-three types, a validated
second state-moment relaxation closes 12 to tolerance `2e-5`.  One explicit
graph6 atom, `HEhu|x|`, remains open; its upper-bound excess decreases from
`1.3569e-4` at level 2 to `4.1579e-5` at level 3.  This is localization of
the obstruction, not a proof by numerical tolerance.  An exact follow-up
uses cancellation among the atom's eight four-hole operators to reduce the
remaining quantum statement to one explicit homogeneous scalar inequality.
That scalar inequality survived one million interior samples but remains the
unproved decisive gate.
