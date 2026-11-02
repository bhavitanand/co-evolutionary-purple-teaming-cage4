"""Per-rule behaviour on the cached SEEN test episodes (native events only): which rules ever fire, which catch attackers,
how concentrated the caught attacker events are. -> results/pilot/per_rule.md (run with .venv-cyborg python)."""
import gzip
import json
import pathlib
import statistics as st
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
CAGE = ROOT / "external" / "cage-challenge-4"
if CAGE.exists():
    sys.path.insert(0, str(CAGE))
from src.loop.coevo import apply_rules  # noqa: E402
from src.rules.schema import Rule  # noqa: E402

SEEN = ["cage4_default", "aggressive", "stealthy", "deception_aware"]
SEEDS = range(100, 110)
CONDS = [("LLM, fixed Red", "llm_fixed_red"), ("LLM, no feedback", "coevo_nofeedback"), ("LLM, co-evolved", "coevo"), ("Random rules", "random_rules")]
eps = []
for red in SEEN:
    for s in SEEDS:
        with gzip.open(ROOT / f"results/pilot/test_events/{red}_s{s}.json.gz", "rt", encoding="utf-8") as f:
            eps.append(json.load(f)["events"])
rows = []
HITS = {}
for label, cond in CONDS:
    files = sorted((ROOT / "results/pilot/rules").glob(f"{cond}_seed*.json"))
    stats = []
    for f in files:
        d = json.loads(f.read_text(encoding="utf-8-sig"))["rules"]
        rules = [(a, Rule.from_dict(r)) for a, rs in d.items() for r in rs]
        fires = {r.rule_id: [0, 0, 0] for _, r in rules}  # [attacker native, benign native, synthetic] alerts
        for ev in eps:
            lab = {e["event_id"]: e for e in ev}
            for al in apply_rules(ev, {a: [r for aa, r in rules if aa == a] for a in {x for x, _ in rules}}):
                e = lab.get(al.event_id)
                if e is None:
                    continue
                if e["provenance"] != "native":
                    fires[al.rule_id][2] += 1
                    continue
                k = 0 if e["label_red"] == "1" or e["label_red"] == 1 else 1
                fires[al.rule_id][k] += 1
        n = len(rules)
        never = sum(1 for v in fires.values() if sum(v) == 0)
        atk = sum(1 for v in fires.values() if v[0] > 0)
        noisy = sum(1 for v in fires.values() if v[1] > v[0] and v[0] + v[1] > 0)
        # rules needed to explain 80% of the caught attacker events (greedy by attacker hits)
        hits = sorted((v[0] for v in fires.values()), reverse=True)
        HITS.setdefault(cond, []).append(hits)
        tot = sum(hits)
        need, acc = 0, 0
        for h in hits:
            if acc >= 0.8 * tot or tot == 0:
                break
            acc += h
            need += 1
        stats.append((n, 100 * never / n, 100 * atk / n, 100 * noisy / n, need))
    rows.append((label, len(files), *[st.mean(x[i] for x in stats) for i in range(5)]))
out = ["# Per-rule behaviour on seen test episodes (never fire = no alert on any native or synthetic event; mean over runs)", "",
       "| set | runs | rules | never fire (%) | fire on native attacker events (%) | mostly benign alerts (%) | rules for 80% of attacker alerts |", "|---|---|---|---|---|---|---|"]
out += [f"| {r[0]} | {r[1]} | {r[2]:.1f} | {r[3]:.0f} | {r[4]:.0f} | {r[5]:.0f} | {r[6]:.1f} |" for r in rows]
(ROOT / "results/pilot/per_rule_hits.json").write_text(json.dumps(HITS), encoding="utf-8")
(ROOT / "results/pilot/per_rule.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out))
