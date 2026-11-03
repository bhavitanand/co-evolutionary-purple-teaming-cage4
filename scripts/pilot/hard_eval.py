"""Harder test: add benign events that copy the signature of attacker events (category, dst_port, protocol, service, process, parent process,
privilege) but take their context (zone, subnet, host, addresses) from real benign events of the same Blue agent. Level h = number of such
hard benign events per native attacker event (0 = the original test). The hard events are INVENTED by us and labelled benign (source_action
GreenHardNegative); they show how rule sets behave when benign traffic looks like the attack on the fields a port rule or process rule uses.
Frozen rules only (no training). Seen test episodes, native events. -> results/pilot_hard/hard_eval.md/json (run with .venv-cyborg python)."""
import copy
import json
import os
import pathlib
import random
import statistics as st
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "pilot"))
import baselines as B  # noqa: E402,F401  (reuses uniform/load helpers)
import hybrid_lib as H  # noqa: E402
from src.loop.coevo import apply_rules, score  # noqa: E402
from src.rules.schema import Rule  # noqa: E402

SIG = ["category", "dst_port", "protocol", "service_name", "process_name", "parent_process", "privilege", "is_decoy"]
CTX = ["zone", "subnet", "host_id", "src_ip", "dst_ip"]
LEVELS = [0, 1, 4]
COPY = float(os.environ.get("CTX_COPY", "0"))  # share of look-alike events whose context (zone, host, addresses) is copied from the attacker event instead of a benign one
TAG = os.environ.get("HARD_TAG", "")
if os.environ.get("HARD_LEVELS"):
    LEVELS = [int(x) for x in os.environ["HARD_LEVELS"].split(",")]
QUICK = bool(os.environ.get("HARD_QUICK"))


def harden(ep, h, seed):
    rng = random.Random(seed)
    evs = [e for e in ep["events"] if e["provenance"] == "native"]
    atk = [e for e in evs if e["label_red"] in (1, "1")]
    ben = [e for e in evs if e["label_red"] in (0, "0")]
    out = [copy.deepcopy(e) for e in ep["events"]]
    if h == 0:
        return {**ep, "events": out}
    n = 0
    for _ in range(h * len(atk)):
        a = rng.choice(atk)
        pool = [b for b in ben if b["blue_agent"] == a["blue_agent"]]
        if not pool:
            continue
        b = rng.choice(pool)
        e = copy.deepcopy(a)
        if COPY == 0 or rng.random() >= COPY:
            for k in CTX:
                e[k] = b.get(k)
        n += 1
        e.update(event_id=f"hn{n:06d}", label_red=0, source_agent="green", source_action="GreenHardNegative", step=rng.randint(0, ep["last_step"]))
        out.append(e)
    out.sort(key=lambda e: e["step"])
    return {**ep, "events": out}


def ev_sets(eps):
    return eps


def evaluate(run, eps):
    acc = {"recall": [], "fpr": []}
    for ep in eps:
        sc = score(ep["events"], apply_rules(ep["events"], run), ep["last_step"])["native"]
        for m in acc:
            if sc[m] is not None:
                acc[m].append(sc[m])
    return {m: st.mean(v) for m, v in acc.items()}


def boot(v, n=4000, seed=0):
    rng = random.Random(seed)
    ms = sorted(st.mean(rng.choices(v, k=len(v))) for _ in range(n))
    return st.mean(v), ms[int(0.025 * n)], ms[int(0.975 * n) - 1]


def cell(vals):
    if len(vals) < 4:
        return f"{st.mean(vals):.3f}"
    m, lo, hi = boot(vals)
    return f"{m:.3f} [{lo:.3f}, {hi:.3f}]"


folders = ("results/pilot", "results/pilot_rep")
sets = {"Static hand-written (10 rules)": [B.uniform(H.static)],
        "Learned rules, no LLM (12)": [B.uniform([Rule.from_dict(r) for r in json.loads((ROOT / "results/pilot_baselines/learned12.json").read_text(encoding="utf-8-sig"))])]}
for label, cond in ((("LLM, fixed Red", "llm_fixed_red"), ("LLM, co-evolved", "coevo")) if QUICK else (("LLM, fixed Red", "llm_fixed_red"), ("LLM, no feedback", "coevo_nofeedback"), ("LLM, co-evolved", "coevo"))):
    sets[label] = B.load_runs(cond, folders) if cond != "coevo_nofeedback" else B.load_runs(cond, ("results/pilot",))
runs_co = B.load_runs("coevo", folders)
for k in ((3,) if QUICK else (3, 5)):
    sets[f"LLM co-evolved, {k} runs pooled"] = [H.merged(*runs_co[i:i + k]) for i in range(0, len(runs_co) - k + 1, k)]

res, lines = {}, ["# Harder test: invented benign events that copy attacker signatures (frozen rules, seen test episodes, native events)", "",
                  f"Level h = hard benign events added per native attacker event (invented by us, labelled benign); context copied from the attacker event in {COPY:.0%} of them. Mean [95% bootstrap CI over runs or groups; no CI under 4].", "",
                  "| rule set | runs/groups | " + " | ".join(f"h={h} recall | h={h} FPR" for h in LEVELS) + " |", "|---|---|" + "---|---|" * len(LEVELS)]
hard = {h: [harden(ep, h, 1000 * h + i) for i, ep in enumerate(H.eps)] for h in LEVELS}
for name, runs in sets.items():
    row = []
    for h in LEVELS:
        ev = [evaluate(r, hard[h]) for r in runs]
        res[f"{name}|{h}"] = ev
        row += [cell([e["recall"] for e in ev]), cell([e["fpr"] for e in ev])]
    lines.append(f"| {name} | {len(runs)} | " + " | ".join(row) + " |")
    print(lines[-1], flush=True)
out = ROOT / "results/pilot_hard"
out.mkdir(exist_ok=True)
(out / f"hard_eval{TAG}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
(out / f"hard_eval{TAG}.json").write_text(json.dumps(res), encoding="utf-8")
