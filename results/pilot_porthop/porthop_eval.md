# Port-hopping Red: robustness of rules trained against it (pre-registered, results/PREREG_porthop.md)

Frozen rules, seen test episodes, native events. Mean [95% bootstrap CI over runs].

| rule sets | runs | recall, original test | recall, ports re-drawn | FPR, original test |
|---|---|---|---|---|
| coevo trained vs port-hopping Red (seeds 35-44) | 10 | 0.293 [0.164, 0.416] | 0.011 [0.008, 0.014] | 0.016 [0.006, 0.027] |
| coevo, original Red (20 runs) | 20 | 0.368 [0.288, 0.454] | 0.012 [0.010, 0.014] | 0.009 [0.005, 0.014] |

Difference (port-hop trained minus original), recall with ports re-drawn: -0.001 [-0.005, +0.003]; recall, original test: -0.076 [-0.228, +0.074]; FPR, original test: +0.007 [-0.004, +0.019].

Pre-registered claim (robustness improves) is supported only if the first difference has an interval above zero and the FPR difference is at most +0.02.
