"""Summarise the DEV variants (seeds 10-14, training episodes only) -> results/pilot_dev/summary.md."""
import json
import pathlib
import statistics as st

ROOT = pathlib.Path(__file__).resolve().parents[2]
D = ROOT / "results/pilot_dev"
out = ["# Dev variants (coevo, dev seeds 10-14, training episodes; mean of rounds 7-8 per seed, then mean over seeds)", "",
       "| variant | seeds | native recall | native FPR | native precision | active rules |", "|---|---|---|---|---|---|"]
for v in ("base", "cap20", "coverage", "recycle", "richfb", "promptred", "agg"):
    f = D / v / "train_log.jsonl"
    if not f.exists():
        continue
    rows = [json.loads(x) for x in f.read_text(encoding="utf-8-sig").splitlines() if x.strip()]
    per = {}
    for r in rows:
        if r["round"] >= 7:
            n = r["scores"]["native"]
            per.setdefault(r["seed"], []).append((n["recall"], n["fpr"] or 0.0, n["precision"], r["active_rules"] if isinstance(r["active_rules"], int) else len(r["active_rules"])))
    if not per:
        continue
    m = lambda i: st.mean(st.mean(x[i] for x in v_) for v_ in per.values())  # noqa: E731
    out.append(f"| {v} | {len(per)} | {m(0):.3f} | {m(1):.3f} | {m(2):.3f} | {m(3):.0f} |")
(D / "summary.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out))
