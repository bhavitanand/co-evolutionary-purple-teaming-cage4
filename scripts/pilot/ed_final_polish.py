"""One-off: add the field-usage finding (LLM rules use the port but narrow it with enriched context), fix the 'precise' framing in abstract/conclusion."""
p = "paper/paper.md"
s = open(p, encoding="utf-8", newline=None).read()


def sub(a, b):
    global s
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)


sub("The LLM-written rules are precise (native precision of at least 0.97, false-positive rate of at most 0.03) but incomplete: native recall is 0.49",
    "The LLM-written rules raise few false alarms (false-positive rate of at most 0.03) but are incomplete: native recall is 0.49")
sub("A baseline check shows that the testbed is easy to separate (attackers are 84% of native events): rules fitted without an LLM reach recall 0.94 to 1.00 at no false positives.",
    "A baseline check shows that the testbed is easy to separate (attackers are 84% of native events, so raw precision is flattered): a greedy learner with single-field rules reaches recall 0.94 to 1.00 at no false positives, whereas the LLM rules wrap the same discriminating port in narrow, analyst-style context and lean on fields our bridge filled in (blanking them cuts co-evolved recall from 0.49 to 0.19).")
# new paragraph in 6.7, before the Case Study heading
add = ("*What the LLM writes instead.* The LLM rules do use the discriminating field: 95 to 99 percent of their network rules constrain the destination port, and about 38 percent of all rules do. But a selection that constrains the destination port 22 and nothing else, which is how the learner's first rule starts, appears in only 1 of the 10 co-evolved runs (2 of 10 fixed-Red and 5 of 10 no-feedback runs); the LLM selections carry on average 2.1 constraints, such as zone, address, privilege or parent process. About 62 percent of all LLM rules rely on enriched fields (process name, parent process, privilege, protocol, service name) without constraining the port. These are rules that read well to an analyst, for example elevated bash under a mail-server parent, and they depend on fields that our bridge fills in by a seeded rule; this is consistent with the drop to 0.19 recall when those fields are blanked. We read this as narrow, context-rich rules that favour a low false-alarm rate over coverage; we did not test why the model writes them, for example by changing the prompt. Counts are in results/pilot_baselines/field_usage.md.\n")
k = "# Case Study: What the Rules Look Like"
assert s.count(k) == 1
s = s.replace(k, add + k)
sub("In a pilot with a small local model, the rules were precise but incomplete: native precision of at least 0.97 and false-positive rates of at most 0.03, with native recall",
    "In a pilot with a small local model, the rules raised few false alarms but were incomplete: false-positive rates of at most 0.03, with native recall")
sub("A baseline check showed that rule sets fitted without an LLM reach recall 0.94 to 1.00 at no false positives on this testbed, whose native test events are 84% attacker events, so the testbed is easy to separate and the LLM rules are not shown to beat simpler methods.",
    "A baseline check showed that rule sets fitted without an LLM reach recall 0.94 to 1.00 at no false positives on this testbed, whose native test events are 84% attacker events (so raw precision is flattered), and that a greedy learner finds the discriminating destination port from a single episode. The LLM rules use that port too, but mostly wrapped in narrow context and in fields our bridge filled in, and the testbed is easy to separate, so the LLM rules are not shown to beat simpler methods.")
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
