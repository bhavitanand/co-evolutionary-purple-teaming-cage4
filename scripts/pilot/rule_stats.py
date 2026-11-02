"""Structure of the final rule sets (no LLM, no CAGE): category mix, redundancy, rule size. -> results/pilot/rule_stats.md"""
import json
import pathlib
import statistics as st
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[2]
SETS = [("LLM, fixed Red", "results/pilot", "llm_fixed_red"), ("LLM, no feedback", "results/pilot", "coevo_nofeedback"),
        ("LLM, co-evolved", "results/pilot", "coevo"), ("LLM, per-action signal", "results/pilot", "coevo_aware"),
        ("Random rules", "results/pilot", "random_rules"), ("Co-evolved, cap 20", "results/pilot_cap20", "coevo")]


def constraints(rule):
    det = rule["detection"]
    out = set()
    for name, sel in det.items():
        if name == "condition" or not isinstance(sel, dict):
            continue
        for k, v in sel.items():
            vals = v if isinstance(v, list) else [v]
            out.update((k, str(x)) for x in vals)
    return frozenset(out)


rows = []
for label, d, cond in SETS:
    files = sorted((ROOT / d / "rules").glob(f"{cond}_seed*.json"))
    if not files:
        continue
    cats, dup, sizes, n_rules, distinct = Counter(), [], [], [], []
    for f in files:
        rules = json.loads(f.read_text(encoding="utf-8-sig"))["rules"]
        tot = near = 0
        for agent, rs in rules.items():
            sigs = [constraints(r) for r in rs]
            for i, r in enumerate(rs):
                cats[r.get("logsource", {}).get("category", "?")] += 1
                sizes.append(len(sigs[i]))
                tot += 1
                if any(j != i and sigs[i] and sigs[j] and len(sigs[i] & sigs[j]) / len(sigs[i] | sigs[j]) >= 0.8 for j in range(len(rs))):
                    near += 1
        n_rules.append(tot)
        dup.append(near / tot if tot else 0.0)
    total = sum(cats.values())
    rows.append((label, len(files), st.mean(n_rules), 100 * st.mean(dup), st.mean(sizes), {k: 100 * v / total for k, v in cats.items()}))
allc = sorted({k for r in rows for k in r[5]})
out = ["# Rule-set structure (final rules per run)", "", "| set | runs | rules per run | rules with a near-duplicate (%) | constraints per rule | " + " | ".join(f"% {c}" for c in allc) + " |",
       "|---|---|---|---|---|" + "---|" * len(allc)]
for lab, n, nr, dp, sz, cm in rows:
    out.append(f"| {lab} | {n} | {nr:.1f} | {dp:.0f} | {sz:.1f} | " + " | ".join(f"{cm.get(c, 0):.0f}" for c in allc) + " |")
(ROOT / "results/pilot/rule_stats.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out))
