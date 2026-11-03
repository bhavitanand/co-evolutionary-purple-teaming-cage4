"""Measured replacements for open questions in the paper (seen test episodes, native events): do scans look like benign traffic, how often
does a benign event use port 3390, are silent rules more specific than firing ones, what is the first attacker event of an episode.
-> results/pilot_baselines/extra_checks.md (run with .venv-cyborg python)."""
import gzip
import json
import pathlib
import statistics as st
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
CAGE = ROOT / "external" / "cage-challenge-4"
if CAGE.exists():
    sys.path.insert(0, str(CAGE))
from src.loop.coevo import apply_rules  # noqa: E402
from src.rules.schema import Rule  # noqa: E402

SEEN = ["cage4_default", "aggressive", "stealthy", "deception_aware"]
eps = []
for red in SEEN:
    for s in range(100, 110):
        with gzip.open(ROOT / f"results/pilot/test_events/{red}_s{s}.json.gz", "rt", encoding="utf-8") as f:
            eps.append(json.load(f)["events"])
nat = [[e for e in ev if e["provenance"] == "native"] for ev in eps]
out = ["# Extra checks on the seen test episodes (native events)", ""]

# 1 scans vs benign connections
scan = [e for ev in nat for e in ev if e["label_red"] in (1, "1") and e["category"] == "network_connection" and "Discovery" in str(e["source_action"])]
expl = [e for ev in nat for e in ev if e["label_red"] in (1, "1") and e["category"] == "network_connection" and "Exploit" in str(e["source_action"])]
ben = [e for ev in nat for e in ev if e["label_red"] in (0, "0") and e["category"] == "network_connection"]
wk = lambda xs: 100 * st.mean(int(e["dst_port"]) < 1024 for e in xs if e["dst_port"] is not None)  # noqa: E731
out += [f"- Scan connections: {len(scan)}; {wk(scan):.1f}% to ports below 1024. Exploit connections: {len(expl)}; {wk(expl):.1f}%. Benign connections: {len(ben)}; {wk(ben):.1f}%.", ""]
# 2 port 3390
b3390 = sum(1 for e in ben if e["dst_port"] == 3390)
a3390 = sum(1 for ev in nat for e in ev if e["label_red"] in (1, "1") and e["dst_port"] == 3390)
out += [f"- dst_port 3390: {b3390} benign events, {a3390} attacker events.", ""]
# 3 silent vs firing rules (co-evolved and fixed-Red, 4B)
for cond, label in [("coevo", "co-evolved"), ("llm_fixed_red", "fixed Red"), ("coevo_nofeedback", "no feedback")]:
    sil, fire = [], []
    for f in sorted((ROOT / "results/pilot/rules").glob(f"{cond}_seed*.json")):
        d = json.loads(f.read_text(encoding="utf-8-sig"))["rules"]
        rules = [(a, Rule.from_dict(r), r) for a, rs in d.items() for r in rs]
        hit = set()
        for ev in eps:
            for al in apply_rules(ev, {a: [r for aa, r, _ in rules if aa == a] for a in {x for x, _, _ in rules}}):
                hit.add(al.rule_id)

        def ncons(raw):
            n = 0
            for k, sel in raw["detection"].items():
                if k != "condition":
                    n += sum(len(x) for x in (sel if isinstance(sel, list) else [sel]) if isinstance(x, dict))
            return n
        for _, r, raw in rules:
            (fire if r.rule_id in hit else sil).append(ncons(raw))
    out.append(f"- {label}: silent rules average {st.mean(sil):.2f} constraints (n={len(sil)}), firing rules {st.mean(fire):.2f} (n={len(fire)}).")
out.append("")
# 4 first attacker event
first = Counter()
for ev in eps:
    atk = sorted((e for e in ev if e["label_red"] in (1, "1")), key=lambda e: e["step"])
    if atk:
        first[(atk[0]["provenance"], str(atk[0]["source_action"]))] += 1
out += [f"- First attacker event of each of the {len(eps)} episodes: " + ", ".join(f"{k[0]} {k[1]}: {v}" for k, v in first.most_common()), ""]
(ROOT / "results/pilot_baselines/extra_checks.md").write_text("\n".join(out), encoding="utf-8")
print("\n".join(out))
