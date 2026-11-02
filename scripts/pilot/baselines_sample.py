"""Sample efficiency of the non-LLM learned baseline: fit on the first k episodes of ONE Red strategy (cage4_default, seeds 0..k-1; the LLM
runs see 8 training episodes per run), score on all seen test episodes (native) and on the unseen hit_and_run.
Writes results/pilot_baselines/sample_efficiency.md (run with the .venv-cyborg python)."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "pilot"))
import baselines as B  # noqa: E402

test = B.load_eps(ROOT / "results/pilot/test_events", B.SEEN, range(100, 110))
unseen = B.load_eps(ROOT / "results/pilot/test_events", ["hit_and_run"], range(100, 110))
test_s, unseen_s = B.strip(test), B.strip(unseen)
L = ["# Sample efficiency of the learned (non-LLM) baseline", "",
     "Fit on k episodes of one Red strategy (cage4_default, seeds 0..k-1), budget 12 rules, scored on 40 seen test episodes and on 10 unseen hit_and_run episodes (native).", "",
     "| k training episodes | rules found | recall | FPR | recall unseen | FPR unseen | recall, no enriched fields | FPR, no enriched fields |", "|---|---|---|---|---|---|---|---|"]
for k in (1, 2, 4, 8):
    tr = B.load_eps(B.OUT / "train_events", ["cage4_default"], range(k))
    for tag, trn, te, un in (("", tr, test, unseen), ("s", B.strip(tr), test_s, unseen_s)):
        rules = B.learn_rules(trn, 12)
        run = B.uniform(rules)
        if tag == "":
            a, b = B.evaluate(run, te), B.evaluate(run, un)
            n = len(rules)
        else:
            c = B.evaluate(run, te)
    L.append(f"| {k} | {n} | {a['recall']:.3f} | {a['fpr']:.3f} | {b['recall']:.3f} | {b['fpr']:.3f} | {c['recall']:.3f} | {c['fpr']:.3f} |")
    print(L[-1], flush=True)
(B.OUT / "sample_efficiency.md").write_text("\n".join(L) + "\n", encoding="utf-8")
