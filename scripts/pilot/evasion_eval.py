"""Evasion stress test on FROZEN rule sets: the attacker changes details of its native events and we re-score recall.
Perturbation families (applied to every native attacker event it applies to): port (network events get a random port 1024-65535),
process (process_name replaced by a process name seen on benign events), parent (parent_process replaced by a benign parent),
privilege (privilege replaced by a benign value), all four. Labels do not change; FPR is unchanged because benign events are untouched.
These perturbations are invented by us (not real attacker behaviour); they test how much of each rule set's recall depends on one
detail. Seen test episodes, native events. -> results/pilot_evasion/evasion_eval.md/json (run with .venv-cyborg python)."""
import copy
import json
import pathlib
import random
import statistics as st
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "pilot"))
import baselines as B  # noqa: E402
import hybrid_lib as H  # noqa: E402
from src.loop.coevo import apply_rules, score  # noqa: E402
from src.rules.schema import Rule  # noqa: E402

KINDS = ["none", "port", "process", "parent", "privilege", "all"]


def perturb(ep, kind, seed):
    rng = random.Random(seed)
    evs = [copy.deepcopy(e) for e in ep["events"]]
    nat = [e for e in evs if e["provenance"] == "native"]
    ben = [e for e in nat if e["label_red"] in (0, "0")]
    procs = sorted({e["process_name"] for e in ben if e.get("process_name")}) or [None]
    parents = sorted({e["parent_process"] for e in ben if e.get("parent_process")}) or [None]
    privs = sorted({e["privilege"] for e in ben if e.get("privilege")}) or [None]
    if kind == "none":
        return {**ep, "events": evs}
    for e in nat:
        if e["label_red"] not in (1, "1"):
            continue
        if kind in ("port", "all") and e.get("dst_port") is not None:
            e["dst_port"] = rng.randint(1024, 65535)
        if kind in ("process", "all") and e.get("process_name"):
            e["process_name"] = rng.choice(procs)
        if kind in ("parent", "all") and e.get("parent_process"):
            e["parent_process"] = rng.choice(parents)
        if kind in ("privilege", "all") and e.get("privilege"):
            e["privilege"] = rng.choice(privs)
    return {**ep, "events": evs}


def recall(run, eps):
    v = []
    for ep in eps:
        r = score(ep["events"], apply_rules(ep["events"], run), ep["last_step"])["native"]["recall"]
        if r is not None:
            v.append(r)
    return st.mean(v)


def boot(v, n=4000, seed=0):
    rng = random.Random(seed)
    ms = sorted(st.mean(rng.choices(v, k=len(v))) for _ in range(n))
    return st.mean(v), ms[int(0.025 * n)], ms[int(0.975 * n) - 1]


def cell(v):
    if len(v) < 4:
        return f"{st.mean(v):.3f}"
    m, lo, hi = boot(v)
    return f"{m:.3f} [{lo:.3f}, {hi:.3f}]"


folders = ("results/pilot", "results/pilot_rep")
sets = {"Static hand-written (10 rules)": [B.uniform(H.static)],
        "Learned rules, no LLM (12)": [B.uniform([Rule.from_dict(r) for r in json.loads((ROOT / "results/pilot_baselines/learned12.json").read_text(encoding="utf-8-sig"))])],
        "LLM, fixed Red": B.load_runs("llm_fixed_red", folders), "LLM, no feedback": B.load_runs("coevo_nofeedback", ("results/pilot",)),
        "LLM, co-evolved": B.load_runs("coevo", folders)}
runs_co = B.load_runs("coevo", folders)
for k in (3, 5, 10):
    sets[f"LLM co-evolved, {k} runs pooled"] = [H.merged(*runs_co[i:i + k]) for i in range(0, len(runs_co) - k + 1, k)]
data = {k: [perturb(ep, k, 7000 + i) for i, ep in enumerate(H.eps)] for k in KINDS}
res = {}
lines = ["# Evasion stress test: attacker changes one detail of its native events (frozen rules, seen test episodes, native recall)", "",
         "Perturbations are invented by us. Mean recall [95% bootstrap CI over runs or groups; no CI under 4]. FPR is unchanged (benign events untouched).", "",
         "| rule set | runs/groups | " + " | ".join(KINDS) + " |", "|---|---|" + "---|" * len(KINDS)]
for name, runs in sets.items():
    row = []
    for k in KINDS:
        v = [recall(r, data[k]) for r in runs]
        res[f"{name}|{k}"] = v
        row.append(cell(v))
    lines.append(f"| {name} | {len(runs)} | " + " | ".join(row) + " |")
    print(lines[-1], flush=True)
out = ROOT / "results/pilot_evasion"
out.mkdir(exist_ok=True)
(out / "evasion_eval.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
(out / "evasion_eval.json").write_text(json.dumps(res), encoding="utf-8")
