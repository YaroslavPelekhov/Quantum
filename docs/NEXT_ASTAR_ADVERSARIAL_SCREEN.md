# Next A* adversarial screen: hardware noise-model witnesses

Status: **provisional direction, not a novelty claim**.  This replaces the old
EvoQBench/QAOA-schedule recommendation for the next primary research cycle.

## Research object

Generate small pairs of logically matched quantum circuits that act as
counterexamples to a specified hardware calibration or noise model.  A witness
pair should be indistinguishable under the model's declared features -- width,
depth, native gate multiset, topology exposure, isolated gate error summaries,
and noiseless task score -- yet exhibit a statistically significant reversal of
their predicted ranking on held-out hardware.

The intended contribution is not another fidelity predictor or compiler cost
function.  It is a **model-falsification primitive** that returns minimal,
reproducible circuits explaining where a hardware model loses ordering
information.

## Why broader formulations are already too crowded

- Calibration-aware remapping and device selection already recover fidelity by
  scoring candidate layouts from hardware calibration data.
- Graph/transformer models already predict noisy circuit fidelity.
- Few-shot cross-device noise-model transfer already uses circuit and
  calibration features.
- Active Hamiltonian/noise learning already selects informative experiments.
- Randomized, cycle, and application-level benchmarking already expose errors
  invisible to isolated gate summaries.

Therefore the project must not claim novelty for prediction, hardware-aware
placement, active characterization, or circuit benchmarking in general.

## Candidate capability

Given:

1. a declared calibration/noise model `M`;
2. an allowed native gate grammar and hardware topology;
3. a matching relation over circuit pairs; and
4. a QPU query budget,

return a Pareto set of minimal witness pairs maximizing posterior evidence that
`M` predicts the wrong ordering, while controlling shot uncertainty and
multiple testing.  The output includes an executable replay record and an
explicit model assumption that the witness rejects.

## Phase 0: kill it before hardware

Time-box the first adversarial screen before large experiments.

1. Search primary literature specifically for adversarial/optimal experiment
   design whose objective is *ranking-model falsification by matched circuit
   pairs*, not parameter estimation.
2. Test whether the proposed theorem is merely a standard channel
   discrimination or coherent-error echo construction in new language.
3. Construct the smallest exact examples under coherent, stochastic Pauli,
   crosstalk, and temporally correlated noise.
4. Compare exhaustive search, uniform random circuits, standard RB/cycle
   sequences, and the proposed witness search under the same circuit budget.
5. Require witnesses to remain matched after transpilation; reject examples
   explained by gate count, depth, layout, or noiseless-score differences.

## Frozen pre-hardware kill criteria

Stop the direction if any of the following occurs:

- an equivalent matched-pair model-falsification method is located in prior art;
- the theoretical statement reduces without additional content to standard
  process/channel discrimination;
- random or standard benchmarking circuits find equally strong witnesses at
  the same query budget;
- ranking reversals disappear under exact shot-noise intervals and multiplicity
  correction;
- witnesses depend on a feature omitted accidentally rather than on a genuine
  insufficiency of the declared model; or
- the witness does not transfer across simulated noise draws held out from
  search.

No QPU budget is authorized until these gates pass.

## Hardware validation if Phase 0 survives

- Freeze circuits and analysis before dispatch.
- Use at least two providers or one provider at multiple calibration dates.
- Train/search on one device/date only; keep the others untouched.
- Record calibration snapshot, transpiled circuit, shots, queue/QPU/wall time,
  monetary cost, and all raw counts.
- Compare against the provider noise model, independent gate-product scores,
  Aer/device emulators, and learned fidelity predictors.
- Treat abstention as valid: the method should refuse to declare a reversal
  when shot uncertainty is too large.

The local machine currently has AWS CLI but no configured AWS profile and no
Braket Python SDK.  This is an explicit external dependency, not something to
silently bypass with simulator-only evidence.

## Current recommendation

Run only the Phase-0 prior-art and exact-small-instance screen next.  If it
survives, obtain explicit QPU credentials/budget and register the held-out
hardware protocol.  If it fails, close it immediately and move to a different
scientific object rather than weakening the claim.
