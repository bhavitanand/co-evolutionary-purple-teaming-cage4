# Pilot results (frozen rules on TEST seeds 100-109)

Mean over test episodes per training run, then mean [95% bootstrap CI] over training runs. 'native' = events CAGE-4 really produced (plus seeded enrichment); 'synthetic' = events we invented (PrivilegeEscalate / Impact / DegradeServices): recall on those is easy by construction, never pool.

## seen Red strategies - all events

| condition | runs | precision | recall | FPR |
|---|---|---|---|---|
| Static hand-written rules | 1 | 0.974 | 0.970 | 0.193 |
| LLM co-evolved (ours) | 10 | 0.994 [0.990, 0.997] | 0.416 [0.330, 0.503] | 0.017 [0.008, 0.027] |

## seen Red strategies - native events

| condition | runs | precision | recall | FPR |
|---|---|---|---|---|
| Static hand-written rules | 1 | 0.962 | 0.958 | 0.193 |
| LLM co-evolved (ours) | 10 | 0.983 [0.973, 0.992] | 0.330 [0.218, 0.438] | 0.017 [0.008, 0.027] |

## seen Red strategies - synthetic events

| condition | runs | precision | recall | FPR |
|---|---|---|---|---|
| Static hand-written rules | 1 | 1.000 | 1.000 | n/a |
| LLM co-evolved (ours) | 10 | 1.000 [1.000, 1.000] | 0.622 [0.547, 0.704] | n/a |

## UNSEEN Red (hit_and_run) - all events

| condition | runs | precision | recall | FPR |
|---|---|---|---|---|
| Static hand-written rules | 1 | 0.969 | 0.958 | 0.169 |
| LLM co-evolved (ours) | 10 | 0.985 [0.975, 0.993] | 0.366 [0.248, 0.484] | 0.019 [0.009, 0.031] |

## UNSEEN Red (hit_and_run) - native events

| condition | runs | precision | recall | FPR |
|---|---|---|---|---|
| Static hand-written rules | 1 | 0.966 | 0.954 | 0.169 |
| LLM co-evolved (ours) | 10 | 0.977 [0.960, 0.991] | 0.347 [0.217, 0.477] | 0.019 [0.009, 0.031] |

## UNSEEN Red (hit_and_run) - synthetic events

| condition | runs | precision | recall | FPR |
|---|---|---|---|---|
| Static hand-written rules | 1 | 1.000 | 1.000 | n/a |
| LLM co-evolved (ours) | 10 | 1.000 [1.000, 1.000] | 0.563 [0.506, 0.624] | n/a |

## EVASIVE Red plan library - all events

| condition | runs | precision | recall | FPR |
|---|---|---|---|---|
| Static hand-written rules | 1 | 0.971 | 0.969 | 0.192 |
| LLM co-evolved (ours) | 10 | 0.992 [0.987, 0.996] | 0.398 [0.306, 0.489] | 0.017 [0.008, 0.027] |

## EVASIVE Red plan library - native events

| condition | runs | precision | recall | FPR |
|---|---|---|---|---|
| Static hand-written rules | 1 | 0.962 | 0.959 | 0.192 |
| LLM co-evolved (ours) | 10 | 0.982 [0.971, 0.992] | 0.333 [0.219, 0.444] | 0.017 [0.008, 0.027] |

## EVASIVE Red plan library - synthetic events

| condition | runs | precision | recall | FPR |
|---|---|---|---|---|
| Static hand-written rules | 1 | 1.000 | 1.000 | n/a |
| LLM co-evolved (ours) | 10 | 1.000 [1.000, 1.000] | 0.610 [0.543, 0.684] | n/a |
