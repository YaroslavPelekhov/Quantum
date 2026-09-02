# Exploratory full-dynamics optimization provenance

## Disclosure

This search was run **post hoc**, after the gauge-resource Phase 0 result had
already failed its A-star gates. Its purpose was adversarial: try to break the
tempting extrapolation from the weak-drive single-response QTV bound to an
arbitrary nonlinear propagator.

The optimizer and the independent audit have deliberately separate roles:

- `optimize_full_dynamics.py` records how candidate pulses were found;
- `full_dynamics_audit.py` embeds the selected pulse and validates it using
  NumPy/SciPy only;
- PyTorch is optional and is not imported by the validator;
- the candidate was selected before its independent null, reversal,
  quantization, convergence, and robustness audits were read.

This provenance does not make the search preregistered and does not promote the
result to an A-star claim.

## Search space

The exact three-atom C6 model and static mask are the same as in the independent
audit. The laser phase is fixed to zero. The optimized controls are global Rabi
amplitude, global detuning, and the scalar waveform multiplying the one fixed
mask.

Unconstrained knot variables are mapped into restricted boxes chosen so that
every possible neighboring-knot pair obeys both the amplitude and slew limits.
The optimization uses a differentiable midpoint propagator; every retained
candidate is then reevaluated using a 16-substep midpoint calculation and
adaptive DOP853.

The deterministic search used:

- durations 0.4, 0.8, 1.2, and 2.0 microseconds;
- eight seeds per duration, numbered 99173 through 99180;
- 900 Adam steps, learning rate 0.035;
- two midpoint substeps per knot interval during optimization;
- the four best optimization-grid candidates retained per duration;
- CUDA complex64 for discovery and complex128 DOP853 for validation.

The objective was the clockwise mean population transfer plus a soft worst-leg
term, with a small penalty for inverse-cycle transfer. It did not use a matrix
logarithm or a quasienergy branch.

## Duration ladder and selection

The archive `full_dynamics_optimizer_search.json` retains all four durations,
the top four candidates at each duration, their complete pulses, constraint
checks, midpoint values, adaptive values, seed identifiers, and solver
metadata.

The best short-duration picture was:

| Duration (microseconds) | Best adaptive clockwise mean | Best candidate worst leg | Interpretation |
|---:|---:|---:|---|
| 0.4 | 0.5373 | about 0.13 | failed short-time control |
| 0.8 | 0.8678 | 0.7577 | oriented but incomplete cycle |
| 1.2 | 0.9839 | 0.9747 | first duration passing 0.98/0.97 |
| 2.0 | 0.9831 | 0.9772 | no useful fidelity gain over 1.2 |

The pulse sent to the independent audit was duration 1.2 microseconds, seed
index 1 (seed value 99174): the shortest searched duration with validated mean
clockwise probability above 0.98 and validated worst-leg probability above
0.97. This was a post-hoc selection rule, but it was applied before the
independent audit.

## Reproduction

The original search used a CUDA device and takes materially longer than the
validator:

```text
python -m experiments.aquila_gauge_resource_phase0.optimize_full_dynamics
```

For a quick pipeline check without overwriting the archived result:

```text
python -m experiments.aquila_gauge_resource_phase0.optimize_full_dynamics --durations-us 0.4 --seed-count 2 --adam-steps 2 --top-k 1 --device cpu --output temporary_optimizer_smoke.json
```

Floating-point trajectories can differ slightly between CPU and CUDA. The
seeded initialization and search specification are deterministic, while the
scientific claim depends only on the separately embedded pulse and adaptive
validator, not on reproducing identical optimizer iterates.
