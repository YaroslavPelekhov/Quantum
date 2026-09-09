# C034: small-seed falsification of proper quantum gear transfer

2026-09-09. Test the specific candidate implication: for an hbar-perfect
seed H and simplicial edge e, the proper geared weighting (unit outside
and on six gear vertices, weight two on its hubs) has beta<=alpha(H)+2.
This is a conjectural transfer, not inferred from classical validity.

Seeds: connected NetworkX atlas graphs of orders 3..6, all simplicial
edges with both external neighborhoods nonempty cliques. Published
Xu et al. 2511.13531v1 reports hbar-perfectness through six vertices.
For each order retain the first 12 nonisomorphic weighted outputs in
atlas/lexicographic edge order (or all if fewer); no result-based selection.
Record whether each output is claw-free; that condition is not imposed
on this broader candidate implication. Canonical Pauli labels checked
pairwise. Exact stable bounds independently enumerated.

Eight starts per output (all ones then seven fixed-seed Gaussian starts),
32 alternating eigenvector iterations each, one thread, 120-second cap
checked between cases. Save coverage, convergence and best physical state.
Published G8 positive control must exceed 3.01 using the same search.
Flag values >classical bound+1e-6 for a separate independent/exact witness
audit. No violations found is NOT an upper-bound or generalization proof.
No QPU or paid runs. No new gear or optimizer method is claimed.

## Outcome and limitations

Completed 30 selected cases: seed orders 3/4/5/6 contributed 1/5/12/12.
Outputs included 16 claw-free and 14 non-claw-free graphs. All 240 starts
reached the 32-step limit; **zero met the strict iteration convergence
criterion**. Therefore this is a shallow falsification screen, not an
estimated global optimum or strong evidence for the proposed theorem.
No violation above 1e-6; maximum independently recomputed excess was
1.51e-14 (roundoff scale). Positive control achieved 3.0445923942>3.
Measured campaign body time 0.687 sec excludes Python/library startup.

Independent stdlib audit checked 31 saved best states including control,
normalization, bitwise Pauli expectations, source/output graph construction,
weights and seed bounds. It did not replay all optimization trajectories.
Three tests pass. This screen covers unit-weight seed rank inequalities
and proper geared lifting only, NOT arbitrary seed facets, g-lifting,
the four XX vertex additions, or C014 as a whole. No general transfer or
A-star claim follows. The next test should address those missing weights
or derive a candidate operator transfer lemma before scaling campaigns.
