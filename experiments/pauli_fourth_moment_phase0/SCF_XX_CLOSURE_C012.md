# C012: fixed XX closure with a three-edge external path

Registered 2026-09-08 before calculation. Take the full source XX graph of
C011 on original labels 1,...,13. Add vertices 14,15 and edges
(7,14),(14,15),(15,8), with no other new edges. This is ONE frozen graph,
not an assertion about all strip compositions or subdivisions.

Check claw-free and simplicial-clique properties independently; the
candidate simplicial clique {14,15} has one outside neighbor at each end.
Enumerate exact alpha and rational STAB facets. Route positive rows via
rank, alpha<=2, order<=9, then induced embedding in C011 full XX graph
(which already includes C009-supported obligations on that atom).
Any remaining facet is an open quantum obligation. A classical outside
point is not a physical counterexample. Five-minute per-script and
independent cube-clipping limits, dimension cap 15; no beta optimization,
paid compute or parameter search. Require missing-facet negative control.

This tests whether an explicit closed strip is actually harder than its
proved atom. If every row is covered, record a fixed-graph corollary,
not a new composition theorem. General quantum auxiliary compatibility,
unrestricted H-SCF and A-star novelty remain unproved.

Implementation note: the first independent run stopped at the old hard
dimension cap 14 before computing a hull. The explicit opt-in cap was
extended to the preregistered 15; default dimension and 300-second limits
are unchanged. This guard failure is not a mathematical counterexample.

The subsequent dense-first run completed the full 44-facet H/V check,
but the separate missing-facet control exceeded its 300-second clipping
limit. That run is NOT recorded as complete acceptance. The next verifier
run uses sparse cuts first, changing only intermediate polytope size.
It starts from the same full cube, uses the same exact edge/rank rules
and all the same inequalities, and retains the 300-second clipping limit.
No facet, graph, arithmetic precision or acceptance criterion is relaxed.

Sparse-first also exceeded the clipping limit, this time during the full
hull check. It was not accepted. The third implementation uses the original
dense-first ordering and an exact index for candidate edges. For an active
set A at a discarded vertex, enumerate all (n-1)-subsets of A and union
the retained vertices containing each subset. This is exactly the set with
at least n-1 common active constraints; the original exact rank n-1 test
is still applied. When there are more than 128 such subsets, fall back
to the full pair scan. Thus no possible edge is omitted. Compare complete
vertex sets AND clipping traces against the old implementation on P4,
C5, G1, and G1 with a deleted weighted facet, in both cut orders.

## Completed outcome

The indexed exact run passed BOTH complete cube clipping and the
missing-facet negative control. The fixed graph is `NhEM?rcNLhleuo?_?GG`,
with 15 vertices, alpha=4, 203 stable incidence vertices and 44 facets.
Routes: 15 nonnegativity, 26 SCF rank, two SCF alpha-two and one C011
induced row. The last row is exactly the same 11-vertex weighted support
as C011, with zero coefficients at original vertices 7,8,14,15.
The induced map checks edges AND nonedges. Componentwise simplicial
claw-free witnesses are independently checked for the other supports.

Consequently every squared Pauli expectation profile satisfies the full
STAB description. The known joint eigenstate lower bound gives
`beta(G,w)=alpha(G,w)` for all nonnegative weights on this ONE graph.
This is a corollary of C011 (and ultimately C009), not a new quantum
mechanism or a uniform path/strip-composition theorem. Deleting the
C011-supported facet admits non-stable rational vertices violating it;
these are geometric controls, not claimed quantum states.

The negative novelty conclusion is substantive: closing one XX atom by
this path adds rank inequalities but no new weighted operator obligation.
C013 therefore preregisters interaction of TWO atoms, rather than counting
longer paths as additional independent quantum discoveries.
