# DCS-RDT structural-rank falsification audit

## Verdict

The audit invalidates the broad low-rank interpretation of DCS-RDT.

For diagonal event support `S`, let `s_L`, `s_R` be distinct prefixes/suffixes
at a cut and let `mu_2` be maximum matching size in the event-incidence graph
after duplicating every suffix vertex.  The exact factorization gives

`rank(K_L) <= min(2 s_L, 4 s_R, 2 mu_2, 2^cut)`.

The capacity-two matching bound predicts the Haar numerical rank on **104/104
cuts**, with zero violations.  It also predicts all 12 exact/near/feasible and
random-support controls on ibm32.

## Consequences

- ibm32: QAOA and Haar ranks are identical (`2` or `4`) on all 17 cuts.
- chesapeake: both are rank `2` on all cuts.
- football: both profiles are identical (`2`, `4`, or `8`).
- Random event supports of 10, 100, and 1000 grow to ranks 20, 180--186, and
  the full cut dimension 512, respectively.
- The earlier rank-4/rank-8 exactness on those cases is event algebra, not a
  QAOA discovery.

The sole non-generic case is aves: QAOA is below the matching/Haar cap on 34 of
46 ordering/cut rows, with the frozen 25% deficit gate met on 29.  That residual
was isolated in the next audit rather than attributed to DCS-RDT.

Raw artifact: `results/dcsrdt_structural_audit/audit.json`.

