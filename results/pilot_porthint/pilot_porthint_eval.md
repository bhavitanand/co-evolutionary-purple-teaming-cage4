# Port-hopping Red (pilot_porthint): robustness of rules trained against it (pre-registered, see results/PREREG_*.md)

Frozen rules, seen test episodes, native events. Mean [95% bootstrap CI over runs].

| rule sets | runs | recall, original test | recall, ports re-drawn | FPR, original test |
|---|---|---|---|---|
| coevo trained vs port-hopping Red, pilot_porthint (seeds 35-44) | 10 | 0.330 [0.221, 0.444] | 0.029 [0.011, 0.061] | 0.017 [0.008, 0.027] |
| coevo, original Red (20 runs) | 20 | 0.368 [0.288, 0.454] | 0.012 [0.010, 0.014] | 0.009 [0.005, 0.014] |

Difference (port-hop trained minus original), recall with ports re-drawn: +0.017 [-0.001, +0.049]; recall, original test: -0.038 [-0.177, +0.098]; FPR, original test: +0.008 [-0.003, +0.019].

Pre-registered claim (robustness improves) is supported only if the first difference has an interval above zero and the FPR difference is at most +0.02.
