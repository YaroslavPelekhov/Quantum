# Frozen twin-orbit quotient backend protocol

Frozen after deriving and unit-checking the orbit equations, before executing
the two-ordering 24-qubit backend validation: 2026-08-28.

## Claim under test

For MIS graphs whose automorphism group contains full permutations of
true/false-twin vertex classes, compile the QAOA circuit into tensor-product
count sectors of dimensions `m_i+1`.  Evolve one complex coefficient per orbit,
not one per bitstring, and assemble the DCS small core through orbit-amplitude
queries.  Neither a dense statevector nor a dense DCS operator is constructed
on the primary path.

## Frozen cohort

- Real 24-qubit `aves-sparrow-social` references.
- Sorted and spectral orderings.
- Published-LR versus prior matched-random, depth 15.
- Original MIS penalty `lambda=1.5` and the archived normalized Ising phase
  convention.
- Decision cuts 5, 9, and 12.
- Dense references are opened only after quotient construction for validation
  samples and frozen-metric comparison.

## Gates

Every ordering must satisfy:

1. quotient dimension at most 10% of `2^24`;
2. maximum probability error on 20,000 deterministic reference samples below
   `1e-12` for both states;
3. DCS rank equals the prior exact structural-audit rank on every selected cut;
4. DCS trace differs from the frozen exact BKS gap by at most `1e-10`;
5. quotient state norm differs from one by at most `1e-10`.

Runtime is descriptive.  Promotion requires 2/2 orderings and establishes a
real statevector-free backend for the symmetry-rich cohort, not polynomial
scaling on arbitrary graphs.

