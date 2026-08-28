# Equal-work residual reset intervention

Four policies use R32 in one 64-checkpoint window and R128 elsewhere.
All policies have identical cubic residual work.

## sorted

| policy | LR correction | MR correction | paired remainder | margin | certified |
|---|---:|---:|---:|---:|:---:|
| reset_129_192 | 0.215661718 | 0.000111119 | 0.215772877 | 0.030350062 | yes |
| reset_193_256 | 0.205445628 | 0.000100050 | 0.205545719 | 0.040577220 | yes |
| reset_257_320 | 0.175676261 | 0.000072603 | 0.175748904 | 0.070374035 | yes |
| reset_321_384 | 0.203036936 | 0.000116823 | 0.203153799 | 0.042969140 | yes |

Frozen expected policy: `reset_193_256`. LR minimum: `reset_257_320`; pair minimum: `reset_257_320`. Mechanism prediction: **fail**.

Dense violations: `0/72`.

## spectral

| policy | LR correction | MR correction | paired remainder | margin | certified |
|---|---:|---:|---:|---:|:---:|
| reset_129_192 | 0.017697322 | 0.000007806 | 0.017705168 | 0.228417835 | yes |
| reset_193_256 | 0.016760545 | 0.000007297 | 0.016767882 | 0.229355122 | yes |
| reset_257_320 | 0.015195213 | 0.000006504 | 0.015201757 | 0.230921247 | yes |
| reset_321_384 | 0.015362793 | 0.000006938 | 0.015369771 | 0.230753233 | yes |

Frozen expected policy: `reset_129_192`. LR minimum: `reset_257_320`; pair minimum: `reset_257_320`. Mechanism prediction: **fail**.

Dense violations: `0/72`.
