# Exact event contraction reproduction

This directory continues the QAOA/MPS manuscript with one narrower question:
can the full BKS-event probability be contracted without constructing or
sampling the 55-qubit state?  Read the protocols before rerunning expensive
jobs and the final report at `results/exact_event_contraction/REPORT.md`.

## Environments

The CPU preparation/audit requires the packages in `requirements.txt`, now
including SymPy for exact rational rank factorization.  GPU contractions require
`requirements-cutensornet.txt`, CUDA 12, and a supported NVIDIA GPU.

All commands below are run from the repository root.  Replace `python` with the
Python executable of the corresponding environment.

## Deterministic preparation

```text
python experiments/exact_event_contraction/build_event_support.py
python experiments/exact_event_contraction/run_event_projector.py audit
python experiments/exact_event_contraction/run_event_projector.py validate-layers
```

Expected 55-qubit invariants are 55 vertices, 91 edges, independence number 23,
384 BKS strings, sorted max bond 152, and spectral max bond 5.

## Required small exact validation

Run these in the cuTensorNet environment:

```text
python experiments/exact_event_contraction/run_exact_event_contraction.py self-test --hyper-samples 32
python experiments/exact_event_contraction/run_event_projector.py self-test --hyper-samples 32
python experiments/exact_event_contraction/run_event_projector.py lowlevel-self-test --hyper-samples 8
python experiments/exact_event_contraction/run_event_projector.py depth-self-test --hyper-samples 8
```

The four summaries must contain 8, 8, 8, and 40 passing cohorts,
respectively, each at absolute error at most `1e-10`.

## Completed 55-qubit jobs

For each `p` in `1,2` and each method in
`published_lr,matched_random_search`, run both API paths in spectral order:

```text
python experiments/exact_event_contraction/run_event_projector.py run --case es60fst02 --method METHOD --ordering spectral --layers P --hyper-samples 8
python experiments/exact_event_contraction/run_event_projector.py lowlevel-run --case es60fst02 --method METHOD --ordering spectral --layers P --hyper-samples 8
```

The high-level and low-level values must agree to absolute `1e-24`; the
high-level norm must agree with one to `1e-10`.

## Resource-bound/failure jobs

The following commands are reproducible negative tests.  The low-level runner
records a path but refuses to execute it above the frozen 65,536-slice or
`1e13` optimizer-cost guard.

```text
python experiments/exact_event_contraction/run_event_projector.py lowlevel-run --case es60fst02 --method published_lr --ordering spectral --layers 3 --hyper-samples 8
python experiments/exact_event_contraction/run_event_projector.py lowlevel-run --case es60fst02 --method published_lr --ordering spectral --layers 4 --hyper-samples 8
python experiments/exact_event_contraction/run_event_projector.py lowlevel-run --case es60fst02 --method published_lr --ordering spectral --layers 8 --hyper-samples 8
python experiments/exact_event_contraction/run_event_projector.py lowlevel-pilot --case es60fst02 --method published_lr --ordering spectral --hyper-samples 32
```

The full-depth path search can take about 20 minutes on the recorded RTX 4070
Ti SUPER before returning `ALL_HYPER_SAMPLES_FAILED`.  It performs no QPU task
and incurs no cloud charge.

## Final checks

```text
python experiments/exact_event_contraction/summarize_results.py
python -m unittest experiments/exact_event_contraction/test_exact_event_contraction.py -v
```

`summarize_results.py` verifies the two-API replications, writes `SUMMARY.json`,
synchronizes embedded representation metadata, and hashes the complete compact
artifact into `MANIFEST.json`.
