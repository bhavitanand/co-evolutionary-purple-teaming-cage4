import pathlib
p = pathlib.Path("paper/paper_v2.md")
t = p.read_text(encoding="utf-8").replace("\r\n", "\n")

def sub(a, b):
    global t
    assert t.count(a) == 1, a[:60]
    t = t.replace(a, b)

# RQ5 paragraph
i = t.index("To check whether the 4-billion-parameter writer drove the recall problem")
j = t.index("(0.019 against 0.072 without).", i) + len("(0.019 against 0.072 without).")
t = t[:i] + (
 "To check whether the 4-billion-parameter writer drove the recall problem, we repeated the three LLM conditions with GLM-4.7-Flash "
 "(a larger mixture-of-experts model, 3-bit quantised, same prompts and settings, used both as Blue writer and as Red planner) for ten training runs each "
 "and scored them on the same frozen test episodes (Table VII). Native recall was higher than for the small model against a fixed Red (0.69 against 0.26) "
 "and for the co-evolved system (0.65 against 0.49), and 0.78 against 0.67 without feedback. Native precision stayed at or above 0.98 and FPR at or below 0.07. "
 "The ordering seen with the small model did not appear: the co-evolved system was 0.042 below the fixed-Red baseline in recall (interval [-0.195, +0.114]), "
 "so we cannot claim a benefit of co-evolution over a fixed attacker with the larger model either. The no-feedback ablation again had the highest recall "
 "(co-evolved minus no feedback -0.130 [-0.267, +0.008]) and the highest FPR (0.066 against 0.033, difference -0.034 [-0.056, -0.010]). "
 "The larger planner did not make Red respond to Blue: it chose a stealth-reconnaissance goal in 66 of its 80 co-evolved rounds, and it changed its goal or scan style "
 "after 23 of 59 rounds in which at least half of its activity was caught, against 6 of 11 other rounds."
) + t[j:]
sub("Larger writer model (GLM-4.7-Flash), three runs per condition", "Larger writer model (GLM-4.7-Flash), ten runs per condition")
sub("Fixed Red | 0.663 [0.452, 0.772] | 0.034 [0.000, 0.090] | 0.652 [0.433, 0.794]", "Fixed Red | 0.693 [0.591, 0.784] | 0.042 [0.024, 0.061] | 0.695 [0.593, 0.787]")
sub("No feedback | 0.692 [0.518, 0.886] | 0.072 [0.000, 0.129] | 0.696 [0.579, 0.883]", "No feedback | 0.781 [0.705, 0.849] | 0.066 [0.046, 0.086] | 0.779 [0.707, 0.846]")
sub("Co-evolved | 0.588 [0.490, 0.747] | 0.019 [0.000, 0.030] | 0.581 [0.501, 0.709]", "Co-evolved | 0.652 [0.532, 0.769] | 0.033 [0.021, 0.046] | 0.640 [0.502, 0.770]")
sub("the second for only three runs per condition, so model-size effects are not established", "the second for ten runs per condition, so model-size effects are indicative only")
sub("Larger-model check | GLM-4.7-Flash, 3-bit, three runs per condition", "Larger-model check | GLM-4.7-Flash, 3-bit, ten runs per condition")
sub("about 46 process-hours, 14 of them for the larger model", "about 85 process-hours, 53 of them for the larger model")
sub("roughly 3 to 9 minutes with the larger model", "roughly 4 to 12 minutes with the larger model")
sub("a confirmatory check uses GLM-4.7-Flash", "a robustness check uses GLM-4.7-Flash")
sub("in a three-run check with a larger model", "in a ten-run check with a larger model")
sub("and neither a scripted evasive Red nor a larger rule budget changed that", "and neither a larger model, a scripted evasive Red nor a larger rule budget changed that")
# discussion
k = t.index("with GLM-4.7-Flash the co-evolved system did not beat the fixed-Red baseline on recall")
end = t.index("cannot settle it,", k) + len("cannot settle it,")
t = t[:k] + "with GLM-4.7-Flash and ten runs per condition the co-evolved system did not beat the fixed-Red baseline on recall (-0.042 [-0.195, +0.114]) and its Red planner did not respond to Blue," + t[end:]
# appendix B
sub("we tried three Blue-side variants on five development seeds (10 to 14)", "we tried eight Blue-side and Red-side variants on five development seeds (10 to 14)")
sub("The variants were the baseline prompt, a higher cap on active rules per agent (20 instead of 12), and a generic coverage hint added to the prompt (cover every event category in the zone's common patterns, and prefer one rule per distinct pattern).",
    "The variants were the baseline prompt, a higher cap on active rules per agent (20 instead of 12), a generic coverage hint added to the prompt (cover every event category in the zone's common patterns, and prefer one rule per distinct pattern), rule recycling (rules that stay silent for two rounds are retired and new rules that were mostly benign are dropped), a richer feedback summary (coverage by event category and exact missed attacker patterns), an explicit reaction rule in the Red prompt, count-within-window aggregate rules, and a prompt that asks for simple one- or two-field rules.")
sub("Coverage hint | 0.528 | 0.065 | 0.966 | about 60",
    "Coverage hint | 0.528 | 0.065 | 0.966 | about 60\nRecycling | 0.685 | 0.008 | 0.997 | about 58\nRicher feedback | 0.468 | 0.006 | 0.996 | about 60\nExplicit Red reaction rule | 0.549 | 0.016 | 0.994 | about 60\nAggregate rules | 0.565 | 0.021 | 0.990 | about 60\nSimple-rule prompt | 0.545 | 0.030 | 0.989 | about 60")
sub("These are training-episode numbers over five seeds and serve only to choose a variant; they are not evidence.",
    "Only the higher cap and recycling met the rule. Recycling was then run once on ten new training seeds (25 to 34) and scored on the test seeds: native recall 0.495 [0.410, 0.579] at the same false-positive level, which is +0.127 [+0.003, +0.246] over the twenty pooled baseline runs, an interval that only just excludes zero. These are training-episode numbers over five seeds and serve only to choose a variant; they are not evidence.")
p.write_text(t, encoding="utf-8")
print("ok")
