# Pre-registration: port-hopping Red (written 3-Nov ~19:00, before any run)

Motivation: the evasion stress test (results/pilot_evasion/evasion_eval.md) shows that every frozen rule set loses almost all recall when the attacker only changes the destination port of its native events (co-evolved single run 0.368 -> 0.012). CAGE-4's Red cannot do this, so co-evolution never faced the one detail that carries detection.

Design: condition `coevo` (LLM Red planner + feedback Blue, 4B model, 8 rounds) with variant `porthop`: from round 2, if the previous round caught at least 30% of Red's events (all events, training labels), Red's native network events get a random destination port 1-1024..65535 that round (events and labels otherwise unchanged). Blue's feedback is the standard training feedback. Ten fresh training seeds 35-44 (never used for tuning), one run each, no variants tuned.

Test (once, seeds 100-109, seen strategies, native events): frozen rules scored (a) on the original test episodes and (b) on the same episodes with Red's ports re-drawn as in the evasion test (kind "port").
Claim "training against a port-hopping Red improves robustness to evasion" is supported only if recall under (b), porthop-trained minus the 20 original coevo runs, has a 95% bootstrap interval above zero AND FPR on (a) does not rise by more than 0.02. Otherwise reported as not supported. Whatever happens is reported.
