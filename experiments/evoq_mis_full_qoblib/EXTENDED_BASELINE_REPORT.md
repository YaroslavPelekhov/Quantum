# Extended independent-backend and classical comparison

## Classical position

- HiGHS proves BKS 88 with zero MIP gap in
  0.036214 seconds.
- Randomized minimum residual degree on the full 186-vertex graph obtains
  1,133 BKS solutions in 15,000 starts
  (7.553%) in 19.954 seconds.
- The same heuristic on the released 55-variable QOBLIB kernel obtains
  6,063 BKS solutions
  (40.420%) in 2.209 seconds.
- The best QAOA schedule obtains 101 BKS samples
  (0.673%) in 15,000 shots. One-third of the measured
  three-method batch wall time is 183.039 seconds.

Thus full-graph greedy has 11.2x
the BKS rate and is 9.2x
faster by allocated wall time. Kernel greedy has
60.0x the BKS rate
and is 82.9x faster.
These are classical dominance results, not quantum advantage results.

## Independent backend

The machine-readable cuTensorNet sweep is `results/cutensornet_sweep.csv`.
Small 12/15-qubit exact contractions match Qiskit statevectors at unit fidelity.
The 55-qubit exact contraction sampler returned an internal backend error after
293 seconds. Completed 55-qubit results therefore use the independent
cuTensorNet MPS implementation and are explicitly labeled approximate.

At spectral ordering, bond 128, and 5,000 shots per method, cutoff `1e-3`
produces 15 nonlinear versus 6 LR BKS hits (two-sided Fisher p=0.0780). At
cutoff `1e-4`, the counts are 11 versus 12 (p=1.0). Thus the independent backend
supports loss of the BKS advantage as accuracy is tightened, while it does not
establish a significant advantage for either schedule at the tighter point.
