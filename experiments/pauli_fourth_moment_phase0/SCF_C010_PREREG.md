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
