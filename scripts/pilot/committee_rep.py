"""Committee analysis on 20 independent runs per condition (seeds 0-9 from results/pilot plus seeds 15-24 from results/pilot_rep).
Disjoint groups of k runs (k = 1, 2, 3, 5, 10), union of their rules, scored on the 40 seen test episodes (native events).
Writes results/pilot/committee_rep.json and committee_rep.md. Run with the .venv-cyborg python."""
import json
import pathlib
import random
import statistics as st
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "pilot"))
import hybrid_lib as H  # noqa: E402
from src.rules.schema import Rule  # noqa: E402

CONDS = [("llm_fixed_red", "LLM, fixed Red"), ("coevo", "LLM, co-evolved")]
KS = [1, 2, 3, 5, 10]


def load(cond):
    runs = []
    for d in ("results/pilot", "results/pilot_rep"):
        for f in sorted((ROOT / d / "rules").glob(f"{cond}_seed*.json")):
            j = json.loads(f.read_text(encoding="utf-8-sig"))["rules"]
            runs.append({a: [Rule.from_dict(r) for r in rs] for a, rs in j.items()})
    return runs


def boot(vals, n=10000, seed=0):
    rng = random.Random(seed)
    ms = sorted(st.mean(rng.choices(vals, k=len(vals))) for _ in range(n))
    return st.mean(vals), ms[int(0.025 * n)], ms[int(0.975 * n) - 1]


def diff_ci(a, b, n=10000, seed=0):
    rng = random.Random(seed)
    ds = sorted(st.mean(rng.choices(a, k=len(a))) - st.mean(rng.choices(b, k=len(b))) for _ in range(n))
    return st.mean(a) - st.mean(b), ds[int(0.025 * n)], ds[int(0.975 * n) - 1]


res = {}
lines = ["# Committee analysis on 20 runs per condition (disjoint groups; mean [95% bootstrap CI over groups])", "",
         "| condition | runs pooled | groups | rules | recall | FPR | precision |", "|---|---|---|---|---|---|---|"]
for cond, label in CONDS:
    runs = load(cond)
    print(cond, len(runs), "runs", flush=True)
    for k in KS:
        groups = [runs[i:i + k] for i in range(0, len(runs) - k + 1, k)]
        ev = [H.evaluate(H.merged(*g)) for g in groups]
        rules = st.mean(sum(len(rs) for r in g for rs in r.values()) for g in groups)
        res[f"{cond}|{k}"] = {"groups": len(groups), "rules": rules, **{m: [e[m] for e in ev] for m in ("precision", "recall", "fpr")}}
        cells = []
        for m in ("recall", "fpr", "precision"):
            v = [e[m] for e in ev]
            cells.append(f"{boot(v)[0]:.3f} [{boot(v)[1]:.3f}, {boot(v)[2]:.3f}]" if len(v) > 2 else f"{st.mean(v):.3f}")
        lines.append(f"| {label} | {k} | {len(groups)} | {rules:.0f} | " + " | ".join(cells) + " |")
        print(lines[-1], flush=True)
lines += ["", "## Differences, co-evolved minus fixed Red (mean [95% bootstrap CI over groups]; only where each side has at least 3 groups)", "",
          "| runs pooled | recall | FPR |", "|---|---|---|"]
for k in KS:
    a, b = res[f"coevo|{k}"], res[f"llm_fixed_red|{k}"]
    if a["groups"] >= 3 and b["groups"] >= 3:
        r = diff_ci(a["recall"], b["recall"])
        f = diff_ci(a["fpr"], b["fpr"])
        lines.append(f"| {k} | {r[0]:+.3f} [{r[1]:+.3f}, {r[2]:+.3f}] | {f[0]:+.3f} [{f[1]:+.3f}, {f[2]:+.3f}] |")
(ROOT / "results/pilot/committee_rep.json").write_text(json.dumps(res), encoding="utf-8")
(ROOT / "results/pilot/committee_rep.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines[-8:]))
