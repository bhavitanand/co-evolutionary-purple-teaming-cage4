"""Pre-registered dev rule for the long-horizon learned-Red test. Reads results/pilot_dev/long_fixed and long_thompson (dev seeds 10-14, 16 rounds),
mean of rounds 15-16 per seed then over seeds. Prints PASS/FAIL: learned Red passes if native recall >= fixed + 0.05 and FPR <= fixed + 0.01."""
import json
import pathlib
import statistics as st

D = pathlib.Path(__file__).resolve().parents[2] / "results/pilot_dev"


def m(name):
    rows = [json.loads(x) for x in (D / name / "train_log.jsonl").read_text(encoding="utf-8-sig").splitlines() if x.strip()]
    per = {}
    for r in rows:
        if r["round"] >= 15:
            n = r["scores"]["native"]
            per.setdefault(r["seed"], []).append((n["recall"], n["fpr"] or 0.0))
    return len(per), st.mean(st.mean(a for a, _ in v) for v in per.values()), st.mean(st.mean(b for _, b in v) for v in per.values())


nf, rf, ff = m("long_fixed")
nt, rt, ft = m("long_thompson")
ok = rt >= rf + 0.05 and ft <= ff + 0.01
line = f"dev rule: {'pass' if ok else 'fail'} learned Red {rt:.3f}/{ft:.3f} (n={nt}) vs fixed {rf:.3f}/{ff:.3f} (n={nf})"
(D / "long_rule.txt").write_text(line + "\n", encoding="utf-8")
print(line)
raise SystemExit(0 if ok else 1)
