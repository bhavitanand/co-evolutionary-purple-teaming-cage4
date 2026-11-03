# Evasion stress test: attacker changes one detail of its native events (frozen rules, seen test episodes, native recall)

Perturbations are invented by us. Mean recall [95% bootstrap CI over runs or groups; no CI under 4]. FPR is unchanged (benign events untouched).

| rule set | runs/groups | none | port | process | parent | privilege | all |
|---|---|---|---|---|---|---|---|
| Static hand-written (10 rules) | 1 | 0.958 | 0.459 | 0.958 | 0.887 | 0.958 | 0.388 |
| Learned rules, no LLM (12) | 1 | 1.000 | 0.071 | 1.000 | 0.964 | 1.000 | 0.000 |
| LLM, fixed Red | 20 | 0.293 [0.226, 0.359] | 0.008 [0.006, 0.010] | 0.289 [0.222, 0.355] | 0.290 [0.222, 0.358] | 0.293 [0.226, 0.359] | 0.003 [0.002, 0.004] |
| LLM, no feedback | 10 | 0.671 [0.604, 0.740] | 0.028 [0.009, 0.064] | 0.665 [0.600, 0.733] | 0.668 [0.601, 0.737] | 0.671 [0.604, 0.740] | 0.023 [0.003, 0.059] |
| LLM, co-evolved | 20 | 0.368 [0.288, 0.454] | 0.012 [0.010, 0.014] | 0.362 [0.281, 0.447] | 0.360 [0.280, 0.444] | 0.368 [0.288, 0.454] | 0.002 [0.001, 0.003] |
| LLM co-evolved, 3 runs pooled | 6 | 0.687 [0.553, 0.824] | 0.030 [0.026, 0.033] | 0.672 [0.538, 0.805] | 0.668 [0.535, 0.798] | 0.687 [0.553, 0.824] | 0.005 [0.003, 0.008] |
| LLM co-evolved, 5 runs pooled | 4 | 0.820 [0.653, 0.923] | 0.039 [0.038, 0.040] | 0.800 [0.630, 0.904] | 0.799 [0.628, 0.899] | 0.820 [0.653, 0.923] | 0.009 [0.006, 0.012] |
| LLM co-evolved, 10 runs pooled | 2 | 0.958 | 0.049 | 0.934 | 0.940 | 0.958 | 0.016 |
