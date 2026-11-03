# Pre-registration: follow-up tests of the co-evolution claim (written 3-Nov 09:30, before the GLM n=10 results were looked at)

Fixed in advance, to be reported whichever way it comes out:

1. GLM-4.7-Flash runs use the same model as Red planner and Blue writer, so the GLM co-evolved runs are already a test with a larger planner. After the 7 extra seeds finish (10 runs per condition), score all 30 rule sets on test seeds 100-109 (seen strategies, native events).
2. Claim "co-evolution helps with the larger model" is supported only if co-evolved recall minus fixed-Red recall has a 95% bootstrap interval above zero and FPR does not rise by more than 0.01. Otherwise it is reported as not supported.
3. Red adaptation with GLM is measured with scripts/pilot/red_adapt.py on the GLM co-evolved training logs: share of rounds in which the plan changes after a high-caught round, and whether goals depend on round number alone (same measures as the 4B analysis).
4. If 2 fails, one further variant may be screened on dev seeds 10-14 only (GLM Red planner against 4B Blue), under the existing dev rule (native recall >= base + 0.05, FPR <= base + 0.01, base 0.516/0.016). A passing variant gets one final run on seeds 35-44 and one scoring on the test seeds. Failing variants are listed in Appendix B with their dev numbers. No tuning on test seeds.
5. Everything tried goes into the paper, including failures.
