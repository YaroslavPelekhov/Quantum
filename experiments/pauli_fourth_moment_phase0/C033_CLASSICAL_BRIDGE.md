# C033: the classical ancestry of the C014 row

2026-09-09. Targeted source audit and exact construction, not a new
quantum optimization. C031's fixed-instance quantum theorem stays valid.

## Source inspected

[Galluccio--Gentile--Ventura, R.661 (2007)](https://www.iasi.cnr.it/~gentile/ClaudioGentileFiles/papers/MOR.pdf),
printed pages 5--7 and 10, Definitions 2.2--2.4 and 2.7, Theorem 3.1.
Read text and visually checked PDF pages 7--9 and 12. Source SHA256:
`2ec9e7c4149f3e3662254dcd1f31ac47bbd839beafc9a134befb9111eec8f616`.
This is not an audit of the entire 35-page proof.

The source replaces a simplicial edge by an eight-node gear; only its
two designated port pairs attach outside. Proper geared rows double the
two hub coefficients and add 2 lambda to the RHS. Proper g-lifted rows
arise from the edge-subdivided input, use uniform gear coefficients and
add lambda. Theorem 3.1 is a CLASSICAL stable-set polytope description,
not a theorem about squared quantum expectations.

## Exact mapping found in our fixed instance

Delete C014 vertices 8,9,19,20 (zero-based): these are original XX vertices
11,12 in each of the two atoms. The remaining 20-vertex graph contains
two ordinary gears with precisely the required external attachments.
The retained original XX vertex 13 in each atom is NOT deleted.

Contract the left gear to edge (24,25), yielding a 14-vertex graph.
Contract its right gear to edge (26,27), yielding an 8-vertex base.
Subdivide that latter edge with vertex 28 to obtain the 9-vertex seed.
Both forward gear reconstructions match every original edge exactly.
The port sets and complete edge lists are archived.

For the weights relevant to C014, the classical chain is:

| Graph | Bound | Verified stable sets | Row transformation |
|---|---:|---:|---|
| Subdivided seed, 9 vertices | 3 | 40 | Uniform rank row |
| Intermediate, 14 vertices | 4 | 162 | Proper g-lift of the seed row |
| Core, 20 vertices | 6 | 1080 | Proper geared row, left hubs doubled |
| C014, 24 vertices | 6 | 2167 (C014 archive) | Four sequential vertex liftings |

For the fixed lifting order 8,9,19,20, exhaustive restricted stable-set
maxima are all five. Thus each maximal classical lifting coefficient
is exactly 6-5=1, agreeing with C014. No facet-preservation claim is
inferred for intermediates whose affine ranks were not computed here.
The final C014 facet was independently established in its earlier audit.

This explains why C016's no-degree-five test was correct yet insufficient
to rule out classical ancestry: the final four lifted vertices destroy
the direct-output degree signature. C032 likewise only excluded direct
last-step uses of different closure operations, not this chain.

## Quantum obligation and decision

No new classical facet, gear operation or sequential lifting rule is
claimed. The exact C031 quantum certificate is an instance-specific
validation of the final inequality, not a proof that quantum bounds
propagate through this chain. Such a conceptual proof would require
quantum-compatible g-lifting, geared lifting and the specified XX vertex
attachments, or another argument covering them jointly. A valid classical
inequality cannot simply be applied to squared expectation values.

Before a larger atom-chain campaign, formulate that restricted quantum
transfer lemma and test its hypotheses adversarially. Do not claim a
general quantum analogue of arbitrary classical sequential lifting.
Priority and A-star significance remain unconfirmed. Three construction
tests pass, including forbidden hub attachment and mismatched port.
Historical initial mapping and the subsequent lifting audit are retained
separately in c033_gear_bridge.json and c033_gear_bridge_with_lifting.json.
