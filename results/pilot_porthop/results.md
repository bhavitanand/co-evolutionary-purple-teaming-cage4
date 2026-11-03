# Pilot results (frozen rules on TEST seeds 100-109)

Mean over test episodes per training run, then mean [95% bootstrap CI] over training runs. 'native' = events CAGE-4 really produced (plus seeded enrichment); 'synthetic' = events we invented (PrivilegeEscalate / Impact / DegradeServices): recall on those is easy by construction, never pool.

## seen Red strategies - all events

| condition | runs | precision | recall | FPR |
|---|---|---|---|---|
| Static hand-written rules | 1 | 0.974 | 0.970 | 0.193 |
| LLM co-evolved (ours) | 10 | 0.992 [0.984, 0.998] | 0.392 [0.291, 0.489] | 0.016 [0.007, 0.027] |

## seen Red strategies - native events

| condition | runs | precision | recall | FPR |
|---|---|---|---|---|
| Static hand-written rules | 1 | 0.962 | 0.958 | 0.193 |
| LLM co-evolved (ours) | 10 | 0.947 [0.876, 0.996] | 0.293 [0.162, 0.415] | 0.016 [0.007, 0.027] |

## seen Red strategies - synthetic events

| condition | runs | precision | recall | FPR |
|---|---|---|---|---|
| Static hand-written rules | 1 | 1.000 | 1.000 | n/a |
| LLM co-evolved (ours) | 10 | 1.000 [1.000, 1.000] | 0.625 [0.500, 0.745] | n/a |

## UNSEEN Red (hit_and_run) - all events

| condition | runs | precision | recall | FPR |
|---|---|---|---|---|
| Static hand-written rules | 1 | 0.969 | 0.958 | 0.169 |
| LLM co-evolved (ours) | 10 | 0.974 [0.942, 0.996] | 0.310 [0.193, 0.416] | 0.018 [0.008, 0.030] |

## UNSEEN Red (hit_and_run) - native events

| condition | runs | precision | recall | FPR |
|---|---|---|---|---|
| Static hand-written rules | 1 | 0.966 | 0.954 | 0.169 |
| LLM co-evolved (ours) | 10 | 0.942 [0.863, 0.995] | 0.293 [0.166, 0.410] | 0.018 [0.008, 0.030] |

## UNSEEN Red (hit_and_run) - synthetic events

| condition | runs | precision | recall | FPR |
|---|---|---|---|---|
| Static hand-written rules | 1 | 1.000 | 1.000 | n/a |
| LLM co-evolved (ours) | 10 | 1.000 [1.000, 1.000] | 0.486 [0.432, 0.542] | n/a |

## EVASIVE Red plan library - all events

| condition | runs | precision | recall | FPR |
|---|---|---|---|---|
| Static hand-written rules | 1 | 0.971 | 0.969 | 0.192 |
| LLM co-evolved (ours) | 10 | 0.989 [0.977, 0.997] | 0.365 [0.260, 0.466] | 0.016 [0.006, 0.027] |

## EVASIVE Red plan library - native events

| condition | runs | precision | recall | FPR |
|---|---|---|---|---|
| Static hand-written rules | 1 | 0.962 | 0.959 | 0.192 |
| LLM co-evolved (ours) | 10 | 0.944 [0.867, 0.996] | 0.293 [0.162, 0.416] | 0.016 [0.006, 0.027] |

## EVASIVE Red plan library - synthetic events

| condition | runs | precision | recall | FPR |
|---|---|---|---|---|
| Static hand-written rules | 1 | 1.000 | 1.000 | n/a |
| LLM co-evolved (ours) | 10 | 1.000 [1.000, 1.000] | 0.599 [0.494, 0.699] | n/a |
