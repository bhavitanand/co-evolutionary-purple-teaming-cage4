# Harder test: invented benign events that copy attacker signatures (frozen rules, seen test episodes, native events)

Level h = hard benign events added per native attacker event (invented by us, labelled benign); context copied from the attacker event in 100% of them. Mean [95% bootstrap CI over runs or groups; no CI under 4].

| rule set | runs/groups | h=1 recall | h=1 FPR |
|---|---|---|---|
| Static hand-written (10 rules) | 1 | 0.958 | 0.832 |
| Learned rules, no LLM (12) | 1 | 1.000 | 0.837 |
| LLM, fixed Red | 20 | 0.293 [0.226, 0.359] | 0.246 [0.191, 0.301] |
| LLM, co-evolved | 20 | 0.368 [0.288, 0.454] | 0.309 [0.241, 0.380] |
| LLM co-evolved, 3 runs pooled | 6 | 0.687 [0.553, 0.824] | 0.578 [0.466, 0.691] |
