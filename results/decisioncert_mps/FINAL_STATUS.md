# Decision-aware follow-up status

The exploratory follow-up is complete.

- Rigorous probability-aware event-angle interval: 14 / 50 rankings, 0 wrong;
  it is tighter pointwise but does not improve global-angle coverage.
- `sqrt(sum w)`-family incoherent-loss heuristics: 21 / 50 rankings and no
  empirical BKS/TVD violation on 100 exact runs; not a theorem.
- Aggressive `sum(w)` heuristic: 31 / 50 rankings but falsified by 3 BKS and
  33 TVD schedule checks.
- MR-vs-LR multi-setting stability: 4 / 5 case decisions and 8 / 10
  case-ordering decisions, 0 wrong; approximation-sensitive aves rejected.
- Independent frozen ES-vs-LR validation: 5 / 5 case decisions and 10 / 10
  case-ordering decisions, 0 wrong.
- Frozen 55q MR-vs-LR point signs are unstable; confidence-aware Wilson
  intervals also force abstention. No new 55q simulation was run.

The theoretical audit shows why discarded weights alone cannot universally
improve on the coherent angle sum. A truly rigorous next method must add BKS
observable information, such as backward observable environments or validated
tensor-network probability bounds.

All new stability/surrogate results remain explicitly labelled exploratory.
