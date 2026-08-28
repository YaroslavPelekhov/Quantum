# Signed reduced-density truncation (SRDT)

This branch tests a comparison-native truncation primitive. Instead of choosing
a basis from either state or their positive average, it approximates the
indefinite local contrast `Gamma_L=rho_L^B-rho_L^A` and retains eigenmodes in
decreasing `|lambda|` order.

The result has a sharp trace-norm/worst-case-observable certificate and a
pure-state exponential separation from faithful state representation. The
frozen `ibm32`/`aves` transfer benchmark also beats the conventional
state-averaged subspace by more than 2x on all four prespecified cut-5/rank-8
rows. See `results/signed_reduced_density_truncation/REPORT.md`.

This is not yet a scalable end-to-end algorithm for the global BKS projector;
that boundary is explicit in the report.
