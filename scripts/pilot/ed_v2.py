import pathlib
p = pathlib.Path("paper/paper_v2.md")
t = p.read_text(encoding="utf-8")
R = [
("Scan connections may resemble the benign connections of Green agents, which would make precise rules hard to write, but we did not test this.",
 "Scan connections go to ports below 1024 in 81.7% of cases, whereas none of the 2,927 benign connections do, so scans are separable by port; the LLM rules mostly add further constraints, such as zone, address or process, and so miss them (Section VI-G)."),
(", although we did not test this directly.", "."),
("we did not examine why, and a real network may differ.",
 "the delay is measured from the first native attacker event, and most episodes begin with a successful PrivilegeEscalate that the bridge reports as a synthetic event. A real network may differ."),
("Some rationales also assert more than the data shows, for example treating SSH on port 3390 as evasion; we did not check how often such connections occur in benign traffic.",
 "Some rationales are well founded: port 3390 never occurs in benign traffic in the test episodes (0 of 2,927 benign connections, against 674 attacker events), so the rule that treats SSH on port 3390 as suspicious is sound, even if its stated reason (evasion) is more than the data shows."),
("We did not examine why so many rules stay silent; one plausible reason is that rules combining two to three field constraints are too specific to match the events that occur, but we did not test this.",
 "Silent rules are somewhat more specific than rules that fire: 2.7 against 2.3 constraints per rule for the co-evolved sets, 2.6 against 2.2 for fixed Red and 2.7 against 2.2 without feedback (results/pilot_baselines/extra_checks.md)."),
("; we did not test why the model writes them.", "."),
("we did not test a larger planner.", "a larger planner is the natural next test."),
("(numbers from Tables 1 and 16 and Section 6.7)", "(numbers from Tables I and XVI and Section 6.7)"),
("with six conditions, a no-feedback ablation", "with six main conditions and two with a scripted evasive Red, a no-feedback ablation"),
("The interval for the co-evolved system does not overlap that of the fixed-Red baseline, so co-evolution with a varied Red improved recall in these ten runs (the replication below qualifies this).",
 "In the ten main runs the interval of the co-evolved system does not overlap that of the fixed-Red baseline (0.49 against 0.26). The replication below, with twenty runs per condition, puts the difference at +0.076 [-0.035, +0.184], so we treat the first estimate as optimistic."),
("and the static rule set has a single run and no interval.", "and the static rule set is deterministic, so it has a single run and no interval."),
]
for a, b in R:
    assert t.count(a) == 1, a[:50]
    t = t.replace(a, b)
p.write_text(t, encoding="utf-8")
print("ok", len(R))
