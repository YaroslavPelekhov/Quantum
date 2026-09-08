# C016: exact baseline gap and direct-gear applicability audit

Registered 2026-09-08 after C015, before rationalization. SAME C014 graph
and weights; no new quantum optimization. The numerical first-moment
relaxation gives approximately 6.51255, while the exact stable bound is
six. Certify only that the standard relaxation cannot prove the proposed
quantum bound; do not infer a physical violation from a moment matrix.

Resolve the 25-dimensional first-moment SDP once. Mix its symmetric
matrix with the strictly interior feasible matrix having M00=1,
M0i=Mii=1/48 and all other entries zero, with interior weight 1/1000.
Round to denominator 100000000. Set M00=1, every edge entry zero and
M0i=Mi0=Mii from the same rounded diagonal. No adaptive denominator or
mixing search: if the resulting rational matrix is not positive definite,
record failure. Independent Fraction LDL without pivoting must have all
positive pivots, satisfy all affine equalities exactly and have weighted
objective strictly above six. Three-hundred-second local cap.

Also check the narrow applicability of ordinary gear composition from
Galluccio--Gentile--Ventura R.661 (2007), Definitions 2.2/2.4, printed
pp.5-6. In its eight-node gear, hubs h1,h2 each have degree five and get
no outside attachments. Compute the full degree histogram of C014.
If there is no degree-five vertex, the full graph cannot be the direct
output of that basic gear operation, regardless of a relabeling. This
does NOT rule out more general XX-strip, fuzzy, sequential-lifting or
iterated construction theorems. The author-hosted source definition and
proper-geared formula were read; the entire paper is not claimed audited.
https://www.iasi.cnr.it/~gentile/ClaudioGentileFiles/papers/MOR.pdf

Controls: corrupt an edge moment, a diagonal/pivot, the objective and
the proof scope. No general H-SCF, target quantum proof or novelty claim.

## Completed exact outcome

All 25 pivots of the rational LDL decomposition are strictly positive,
and exact multiplication reconstructs the 25-by-25 moment matrix.
All edge zeros and `M0i=Mii`, `M00=1` hold exactly. Its objective is
`325328979/50000000 = 6.50657958`, strictly above six by
`25328979/50000000`. Thus theta's inability to certify six is exact,
not solver tolerance. This is a feasible RELAXATION matrix, not a
density matrix or a physical violation of the proposed quantum bound.

The degree histogram is {4:2, 6:12, 7:4, 8:6}; no vertex has degree five.
The two published gear hubs each have exactly five neighbors inside the
gear and no external attachments in Definition 2.2. Therefore this full
graph is not a direct output of ordinary gear composition. This excludes
that one shortcut, not general striped/fuzzy/geared inequality theorems.

C014/C015/C016 now isolate a nontrivial full-support quantum obligation
with a verified weak-baseline gap. They still do not prove the obligation,
establish its priority, or certify A-star novelty. The next work must be
an exact quantum argument or exact physical counterexample for this row.
