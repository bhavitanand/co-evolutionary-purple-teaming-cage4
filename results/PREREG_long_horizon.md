# Pre-registration: long-horizon learned-Red test (written 3-Nov, before any run)

Hypothesis: with 8 rounds a Red that learns has too little time to matter. A Thompson-sampling Red (Beta posterior per plan over the same four-plan library, reward = share of its events no rule alerted on, 0 without successful Impact) trained for 16 rounds against feedback Blue may give Blue a benefit over a fixed attacker. Red never sees the rules.

1. Dev screen: seeds 10-14, 16 rounds, 4B model, conditions llm_fixed_red (fixed Red) and coevo_evasive with variant thompson. Statistic: mean of rounds 15-16 native training-episode recall and FPR per seed, then mean over seeds.
2. Pass rule (as for earlier variants): learned-Red recall >= fixed recall + 0.05 and FPR <= fixed FPR + 0.01.
3. On pass: final run on fresh seeds 35-44 for both conditions (16 rounds), frozen rules scored once on test seeds 100-109. Claim "long-horizon learned Red helps" only if co-evolved minus fixed-Red native recall has a 95% bootstrap interval above zero and FPR does not rise by more than 0.01.
4. On fail: reported in Appendix B and the follow-up summary; no further tuning of this variant on dev or test seeds.
5. Expectation stated in advance: the existing evasive Red (explore 4 rounds, then exploit) gave +0.087 [-0.072, +0.241] at 8 rounds; we expect at most a modest change.
