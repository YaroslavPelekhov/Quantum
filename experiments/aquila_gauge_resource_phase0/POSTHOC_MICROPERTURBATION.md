# Post-hoc collision diagnosis

This analysis was specified **after** the frozen held-out geometry failed at
`n=5`.  It cannot change any preregistered gate or the Phase-0 verdict.

The collision is transparent: in geometry B, sites 2 and 4 are exactly
equidistant from site 1, so replacing either occupation produces identical
site-1 transition frequencies.  The diagnostic changes only the x coordinate
of site 4 from `30.000 um` to `30.001 um` and retains the frozen masks, target
tags, target identifiers, solver limits, and every other coordinate.

The purpose is to determine whether the gauge-quotient growth survives a
one-nanometre symmetry-breaking displacement.  Results are exploratory and
must be reported separately from `milp_instances.csv`.
