"""Does the evasive Red actually respond to Blue? Reads results/pilot/train_log.jsonl (utf-8-sig) -> results/pilot/red_adapt.md."""
import json
import pathlib
import statistics as st
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[2]
rows = [json.loads(l) for l in (ROOT / "results/pilot/train_log.jsonl").read_text(encoding="utf-8-sig").splitlines() if l.strip()]  # noqa: E741
out = ["# Evasive Red: does it respond to Blue? (training episodes)", ""]
for cond in ("coevo_evasive", "evasive_nofeedback"):
    r = [x for x in rows if x["condition"] == cond]
    seeds = sorted({x["seed"] for x in r})
    out.append(f"## {cond}: {len(seeds)} runs, {len(r)} rounds")
    ex = [x for x in r if x.get("source") == "evasive_exploit"]
    out.append("Exploit-phase plan choice: " + ", ".join(f"{k} {v}" for k, v in Counter(x["plan_name"] for x in ex).most_common()))
    # per plan: mean caught share (recall, all events) when played, and mean Impact successes
    by = defaultdict(list)
    for x in r:
        a = x["scores"]["all"]
        if a["recall"] is not None:
            by[x["plan_name"]].append((a["recall"], x["red_success"].get("Impact", 0)))
    for k, v in sorted(by.items()):
        out.append(f"- {k}: n={len(v)}, mean caught {st.mean(a for a, _ in v):.2f}, mean successful Impact {st.mean(b for _, b in v):.1f}")
    # switching: how often does Red change plan between consecutive exploit rounds
    sw = tot = 0
    for s in seeds:
        seq = [x["plan_name"] for x in sorted((y for y in r if y["seed"] == s), key=lambda y: y["round"])][4:]
        sw += sum(a != b for a, b in zip(seq, seq[1:]))
        tot += max(len(seq) - 1, 0)
    out.append(f"Plan switches between consecutive exploit rounds: {sw}/{tot}")
    # trend of the caught share by round
    for rnd in range(1, 9):
        v = [x["scores"]["all"]["recall"] for x in r if x["round"] == rnd and x["scores"]["all"]["recall"] is not None]
        if v:
            out.append(f"  round {rnd}: mean caught {st.mean(v):.2f} (n={len(v)})")
    out.append("")
(ROOT / "results/pilot/red_adapt.md").write_text("\n".join(out), encoding="utf-8")
print("\n".join(out))
