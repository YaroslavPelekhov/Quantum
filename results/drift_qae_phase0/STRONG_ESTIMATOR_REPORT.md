# Strong global-likelihood estimator control

This preregistered follow-up checks that the Phase-0 closure is not an artifact
of the minimal sequential alias resolver.

## Results

- Readout nuisance-oracle median tail RMSE slope: `-0.4716`
- Readout anchored median tail RMSE slope: `-0.4372`
- Equal-budget direct median tail RMSE slope: `-0.5051`
- Readout anchored maximum alias-failure rate: `3.320%`
- Gate nuisance-oracle median tail RMSE slope: `-0.1162`
- Gate anchored median tail RMSE slope: `-0.0872`
- Gate anchored maximum alias-failure rate: `50.195%`

Readout control verdict: **GLOBAL_ESTIMATOR_STILL_FAILS_FROZEN_GATE**.

Gate control verdict: **DEPTH_NOISE_SQL_KILL_UNCHANGED**.  Its analytic Fisher
ceiling is independent of this estimator.

## Interpretation

Even a successful post-circuit control is not a new A* drift result: its matched
anchors make the per-round visibility an ordinary calibrated nuisance.  The
physically depth-accumulating model remains limited to `Q^-1/2` for fixed
nonzero noise.  Therefore the broad Phase-0 verdict remains
**KILL_BROAD_DRIFT_ASTAR_UNCHANGED**, and no QPU run is authorised.
