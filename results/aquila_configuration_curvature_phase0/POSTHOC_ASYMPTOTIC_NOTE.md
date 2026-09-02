# Post-hoc asymptotic diagnosis

This diagnostic was designed after the frozen `-6 +/- 0.25` distance gate
failed with slope `-6.662409`.  It cannot rescue or relabel the preregistered
verdict.

The frozen scan began at interaction `0.719832 rad/us`; the exact weak-response
formula is nonlinear at that scale even though it matches the numerical
continued-log derivative to `1.3e-11 rad`.  Extending only the analytic formula
to the explicitly post-hoc range 22--54 um gives log-log slope
`-6.023046369`.  This approaches the predicted `-6` as `V=C6/r^6` enters the
linear regime.

The appropriate primary scaling law is the already frozen mixed-term check
`chi = beta V delta_h + higher orders`, which passed with centered
`R2=0.998610`.  The raw finite-range power-law gate was over-restrictive; the
mechanism is not falsified by that miss, but the official Phase-0 status remains
`MECHANISM_PARTIAL_ASTAR_KILL`.
