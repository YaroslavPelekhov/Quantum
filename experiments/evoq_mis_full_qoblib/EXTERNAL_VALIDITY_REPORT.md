# Cross-family external-validity report

- Completed MPS cohorts: `True`.
- Completed exact audit: `True`.
- MPS jobs currently available: 408 / 408.
- Matched-schedule aggregate BKS fidelity reversal: `False`.

## Aggregate paired effects versus published LR

| Candidate | Setting | Metric | Difference | 95% CI | p |
|---|---|---|---:|---:|---:|
| prior_evolutionary | released | bks_rate | -0.04573 | [-0.08093, -0.01117] | 0.01377 |
| prior_evolutionary | released | near_bks_rate | +0.02733 | [-0.01447, +0.06997] | 0.212865 |
| prior_evolutionary | released | feasible_rate | +0.11020 | [+0.08390, +0.13833] | 0 |
| prior_evolutionary | confirm | bks_rate | -0.03910 | [-0.07653, -0.00320] | 0.042655 |
| prior_evolutionary | confirm | near_bks_rate | +0.02143 | [-0.02510, +0.06837] | 0.379565 |
| prior_evolutionary | confirm | feasible_rate | +0.05933 | [+0.02587, +0.09563] | 0.001075 |
| prior_matched_random | released | bks_rate | -0.01161 | [-0.03747, +0.01389] | 0.386425 |
| prior_matched_random | released | near_bks_rate | +0.01453 | [-0.01844, +0.04847] | 0.403235 |
| prior_matched_random | released | feasible_rate | +0.11672 | [+0.08892, +0.14508] | 0 |
| prior_matched_random | confirm | bks_rate | -0.03836 | [-0.06378, -0.01475] | 0.00337 |
| prior_matched_random | confirm | near_bks_rate | -0.01917 | [-0.05250, +0.01283] | 0.259675 |
| prior_matched_random | confirm | feasible_rate | +0.04583 | [+0.01358, +0.07886] | 0.008055 |

Partial results are never interpreted as a completed cohort. Per-case and per-seed data remain in the checkpoint artifacts for independent re-analysis.
