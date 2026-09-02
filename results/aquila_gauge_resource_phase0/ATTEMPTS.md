# Execution attempts

## Direct-script import failure

The first command invoked `run_phase0.py` by file path.  It exited before any
target evaluation because the repository package was not on Python's import
path.  The documented module invocation was then used.  No result row was
created by the failed command.

## Frozen run interruption and resume

The first module run completed all 20 development rows and four held-out
`n=4` rows, then stopped on the preregistered held-out `n=5` frequency
collision.  The runner was hardened to record collisions as failed instances
and to support atomic resume.  The resumed run preserved the 24 completed rows
and recorded all 16 collided `n=5..8` instances.

## Solver limits

One development `n=7` target reached the registered 120-second limit with
primal objective `7774.360530`, certified dual lower bound `5636.528515`, and
relative gap `0.274985`.  It is a failed numerical gate, not an exact optimum.

In the disclosed post-hoc run, one `n=7` and all four `n=8` targets reached the
same limit.  Both incumbents and dual bounds are retained.  Scaling statements
that use lower bounds are labelled separately from feasible upper values.

## Post-hoc full-dynamics search and audit

An exploratory deterministic multistart search optimized `0.4`, `0.8`, `1.2`,
and `2.0 us` pulses with a differentiable midpoint propagator.  The selected
`1.2 us` pulse was then frozen before a separate adaptive DOP853 audit,
time-reversal/null controls, hardware-grid quantization, and 128 perturbations.
The optimizer archive is provenance, not a registered validation result; all
reported headline values are recomputed from the frozen pulse without Torch.
