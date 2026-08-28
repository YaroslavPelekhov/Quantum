# Frozen coherent-frontier-rank diagnostic protocol

Frozen before executing the diagnostic: 2026-08-28.

## Motivation

The structural audit found that a capacity-two maximum matching of the event
incidence graph predicts the Haar DCS rank on every tested cut.  The 24-qubit
QAOA pair is nevertheless below that generic bound on many cuts.  This stage
tests whether that deficit is a coherent property of the state/event pair or a
remaining artifact of event support, probabilities, or qubit-local gauge.

For cut `c`, define the generic predicate cap

`B_E(c) = min(2 mu_2(c), 2^c)`

and the rank deficit `1 - rank(K_L)/B_E(c)`.

## Frozen data and transformations

- Case: `aves-sparrow-social` (24 qubits).
- Orderings: sorted and spectral.
- Primary pair: published LR versus prior matched-random.
- Additional schedule pairs: published LR versus prior evolutionary, and
  matched-random versus prior evolutionary.
- All 23 nontrivial cuts.
- Absolute numerical-rank tolerance: `1e-12`.

For the primary pair compare:

1. original states;
2. magnitudes only, preserving every computational-basis probability;
3. independent random phases, preserving every probability but destroying
   coherent phase structure independently in the two states;
4. one common arbitrary diagonal random phase applied to both states;
5. one common product of single-qubit phase gates applied to both states.

All randomness is deterministically seeded from the transformation and
ordering names.

## Go/no-go

Call the deficit a supported coherent phenomenon only if:

- the local-product phase control preserves every original numerical rank;
- independent phase scrambling reaches the generic predicate cap on at least
  90% of cuts where the cap is not the full left Hilbert dimension;
- at least two of the three original QAOA schedule pairs show a rank at most
  75% of the generic cap on at least five common cuts.

This is a phenomenon-level gate only.  It does not establish algorithmic or
literature novelty, and it does not rescue the original DCS-RDT claim by itself.

