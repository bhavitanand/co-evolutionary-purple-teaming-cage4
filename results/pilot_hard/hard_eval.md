# Harder test: invented benign events that copy attacker signatures (frozen rules, seen test episodes, native events)

Level h = hard benign events added per native attacker event (invented by us, labelled benign). Mean [95% bootstrap CI over runs or groups; no CI under 4].

| rule set | runs/groups | h=0 recall | h=0 FPR | h=1 recall | h=1 FPR | h=4 recall | h=4 FPR |
|---|---|---|---|---|---|---|---|
| Static hand-written (10 rules) | 1 | 0.958 | 0.193 | 0.958 | 0.832 | 0.958 | 0.922 |
| Learned rules, no LLM (12) | 1 | 1.000 | 0.000 | 1.000 | 0.837 | 1.000 | 0.953 |
| LLM, fixed Red | 20 | 0.293 [0.226, 0.359] | 0.016 [0.009, 0.024] | 0.293 [0.226, 0.359] | 0.188 [0.142, 0.237] | 0.293 [0.226, 0.359] | 0.213 [0.161, 0.270] |
| LLM, no feedback | 10 | 0.671 [0.604, 0.740] | 0.027 [0.014, 0.040] | 0.671 [0.604, 0.740] | 0.449 [0.401, 0.508] | 0.671 [0.604, 0.740] | 0.510 [0.456, 0.578] |
| LLM, co-evolved | 20 | 0.368 [0.288, 0.454] | 0.009 [0.005, 0.014] | 0.368 [0.288, 0.454] | 0.260 [0.201, 0.322] | 0.368 [0.288, 0.454] | 0.297 [0.229, 0.367] |
| LLM co-evolved, 3 runs pooled | 6 | 0.687 [0.553, 0.824] | 0.024 [0.013, 0.036] | 0.687 [0.553, 0.824] | 0.537 [0.421, 0.654] | 0.687 [0.553, 0.824] | 0.609 [0.476, 0.745] |
| LLM co-evolved, 5 runs pooled | 4 | 0.820 [0.653, 0.923] | 0.045 [0.027, 0.066] | 0.820 [0.653, 0.923] | 0.661 [0.514, 0.767] | 0.820 [0.653, 0.923] | 0.748 [0.577, 0.868] |
