# C010: uniform three-row closure gate

Registered 2026-09-08 before computations, starting from C009 commit 4ede4e0.
Question: does every claw-free F(E) of C008 have BETA=STAB for all weights?
This is strictly a subclass of SCF, not unrestricted H-SCF.

Two-column covers embed in the full 3-by-3 C009 target. For a mixed
row/column cover, collapse all outside-column true twins; the remaining
core also embeds in that target. Restore twins by known vertex splitting.
Two-row covers {0,1} use C007. It remains to analyze D_m: full central
column, m noncentral columns occupied by rows 0 and 2, then H0,H1,Hc,
in sorted cell order. Covers {1,2} follow by exchanging rows 0,1 and H0,H1.

Freeze m=0,1,2,3 for structural and rational facet discovery, not as an
all-m proof. Max order 12; five minutes per script. No beta optimization,
randomness, QPU or paid computation. Test known line/induced embeddings
before introducing a quantum mechanism. Classify facets by support alpha
and rank; if all proper rows use known bounds, isolate exactly the rest.

If a bounded-core/twin or uniform refinement description is suggested,
prove it analytically for arbitrary m and independently verify the finite
certificates. A failed inequality or missing facet stops that proposed
description. A classical outside point is not a physical counterexample.
Controls: m=0 heavy/central core, m=1 alpha test, complete positive facet
support classification, induced maps preserving every edge and nonedge.

Sources: C008/C009 proofs and Xu et al. Section III, known induced-subgraph
and vertex-splitting closure. These operations are not novelty. Existing
Hall transport is not a new algorithm. A-star and priority remain open.

## Adaptive registration after the frozen four hulls, before core computation

D_0,...,D_3 have 11,17,23,27 facets, all using rank or alpha-two support
bounds. Test ONE new fixed core with sorted cells
[(0,0),(0,1),(1,0),(2,0),(2,2)], then heavies; the noncentral vertices U,V
are private and nonadjacent. Lift its stable vertices by z=1_{U,V selected}.
Candidate endpoint: z_min=max(0,U+V+H1+Hc-1,
U+V+A0+B0+C0+H0+H1+Hc-2). Enumerate its exact rational 9D hull and check
independently by full-cube Fraction clipping. No alternate core is selected
if this fails without another explicit registration.

If this holds, substitute U=sum Aj, V=sum Cj, and append pair rows
Aj+Cj+H1+Hc<=1, Aj+Cj+A0+B0+C0+H0+H1+Hc<=2.
Prove completeness by the existing Hall refinement with private marginals
set to zero. Check implied cube and completeness on the four frozen D_m.
Show uniformly that each lifted positive row has alpha<=2 support, or
is a rank inequality; missing graph cases or failed support argument block
the all-m claim. The C008 cover classification, not a bigger census,
will then determine the full F(E) scope.
