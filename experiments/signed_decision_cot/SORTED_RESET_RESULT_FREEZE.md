# Sorted reset-intervention result freeze

Frozen after both sorted methods completed and while the independently
pre-registered spectral `published_lr` run was still in progress.

- Artifact: `results/signed_decision_cot/reset_intervention_sorted.json`
- SHA-256: `831E26A82A88E13B7FC82B3F611F98FD923E4C52D6A3454F18C1768B22FA1EFC`
- Complete rows: 2 (`published_lr`, `prior_matched_random`)

The pre-registered sorted prediction (`reset_193_256`) failed. Both methods
selected `reset_257_320`:

| method | `reset_129_192` | `reset_193_256` | `reset_257_320` | `reset_321_384` |
|---|---:|---:|---:|---:|
| `published_lr` | 0.21566171818008673 | 0.20544562812347520 | **0.17567626105625228** | 0.20303693597210820 |
| `prior_matched_random` | 0.00011111876312645824 | 0.00010005046660774961 | **0.00007260251598859825** | 0.00011682304949749547 |

No spectral result was inspected or used to choose its intervention window;
the spectral prediction remains the one in `RESET_INTERVENTION_PROTOCOL.md`.
