# Operational Pauli campaign: current results

Complete paired cells: 1/720.

Local quantum-channel and Bernoulli-measurement simulations only. No QPU data.
No top-novelty claim. Generic significance optimization is established prior art.

## Per-family descriptive results

Incomplete-prefix averages are not final comparisons; channel strengths and frames are pooled here.
Use the per-cell JSON for all disaggregated results and confidence intervals.

| Graph | Channel | Shots | Method | Cells | Mean simulated detection power |
|---|---|---:|---|---:|---:|
| G8 | none | 10000 | ideal_beta | 1 | 0.0000 |
| G8 | none | 10000 | noisy_beta | 1 | 0.0000 |
| G8 | none | 10000 | noisy_score | 1 | 0.0000 |
| G8 | none | 1000000 | ideal_beta | 1 | 0.0000 |
| G8 | none | 1000000 | noisy_beta | 1 | 0.0000 |
| G8 | none | 1000000 | noisy_score | 1 | 0.0000 |
| G8 | none | 10000000 | ideal_beta | 1 | 0.9375 |
| G8 | none | 10000000 | noisy_beta | 1 | 0.9688 |
| G8 | none | 10000000 | noisy_score | 1 | 0.9688 |

## Interpretation boundary

A higher smoothed optimization score is not a detection result. All methods use the same oracle
allocation rule, and selected states are frozen before independently simulated measurements.
Only G9 and antiC9 are held-out families. C009 is a proved negative control; C014 is open.
No exact counterexample, general quantum theorem, noise-robust deployment or publication priority
is inferred automatically. Inspect PROTOCOL.md and status.json before interpreting partial output.

## Sources

- Xu et al., beta framework and observable systems: https://arxiv.org/html/2511.13531v1
- Jungnitsch et al., existing significance-optimization principle: https://arxiv.org/abs/0912.0645
- Dirkse et al., correlated-noise inference outside this IID model: https://arxiv.org/abs/2002.12400
