# Follow-up results after submission (3-Nov, all numbers from result files)

Pre-registration: results/PREREG_coevo_followup.md (written before looking at the GLM n=10 numbers).

1. GLM-4.7-Flash, 10 runs per condition (results/pilot_glm/results_n10.md, red_adapt_glm.md). Native seen recall / FPR: fixed Red 0.693 / 0.042, no feedback 0.781 / 0.066, co-evolved 0.652 / 0.033. Co-evolved minus fixed Red: -0.042 [-0.195, +0.114] recall, -0.009 [-0.031, +0.012] FPR. Pre-registered criterion (interval above zero) NOT met.
2. GLM Red planner adaptation: stealth_recon in 66 of 80 rounds; goal or scan style changed after 23 of 59 high-caught rounds and 6 of 11 low-caught rounds (no sign of responding to being caught).
3. Dev variant `broad` (simple-rule prompt), seeds 10-14: recall 0.545, FPR 0.030 vs base 0.516 / 0.016. FAIL (FPR limit). Not run on final seeds.
4. Pre-registered step 4 (GLM Red against 4B Blue) was not run: both models cannot be served together on the 6 GB GPU.
5. Measured replacements (results/pilot_baselines/extra_checks.md): scans to ports <1024 81.7% vs benign 0.0%; port 3390 0 benign / 674 attacker; silent rules 2.65 vs firing 2.34 constraints (co-evolved); first attacker event synthetic PrivilegeEscalate in 31 of 40 episodes.
Conclusion: across 4B and GLM, fixed vs adaptive Red, evasive Red, cap 20, recycling and four prompt variants, no setting shows a clear co-evolution benefit over a fixed attacker. Only recycling (+0.127 [+0.003, +0.246] vs 20 pooled baseline runs) comes near.
