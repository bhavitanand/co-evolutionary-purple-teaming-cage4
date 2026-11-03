"""Score the port-hopping-Red runs (results/pilot_porthop) once on the test seeds, as pre-registered in results/PREREG_porthop.md:
native recall on the original seen test episodes and with Red's ports re-drawn (kind "port", same perturbation as evasion_eval.py), FPR on the original;
compared with the 20 original co-evolved runs (values from results/pilot_evasion/evasion_eval.json and results/pilot_hard/hard_eval.json).
-> results/pilot_porthop/porthop_eval.md (run with .venv-cyborg python)."""
import json
import os
import pathlib
import random
import statistics as st
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "pilot"))
import baselines as B  # noqa: E402,F401
import hybrid_lib as H  # noqa: E402
from src.loop.coevo import apply_rules, score  # noqa: E402

sys.argv = [sys.argv[0]]


def perturb_port(ep, seed):
    import copy
    rng = random.Random(seed)
    evs = [copy.deepcopy(e) for e in ep["events"]]
    for e in evs:
        if e["provenance"] == "native" and e["label_red"] in (1, "1") and e.get("dst_port") is not None:
            e["dst_port"] = rng.randint(1024, 65535)
    return {**ep, "events": evs}


def metric(run, eps, m):
    v = []
    for ep in eps:
        r = score(ep["events"], apply_rules(ep["events"], run), ep["last_step"])["native"][m]
        if r is not None:
            v.append(r)
    return st.mean(v)


def boot(v, n=4000, seed=0):
    rng = random.Random(seed)
    ms = sorted(st.mean(rng.choices(v, k=len(v))) for _ in range(n))
    return st.mean(v), ms[int(0.025 * n)], ms[int(0.975 * n) - 1]


def diff(a, b, n=10000, seed=0):
    rng = random.Random(seed)
    ds = sorted(st.mean(rng.choices(a, k=len(a))) - st.mean(rng.choices(b, k=len(b))) for _ in range(n))
    return st.mean(a) - st.mean(b), ds[int(0.025 * n)], ds[int(0.975 * n) - 1]


DIR = os.environ.get("PORTHOP_DIR", "pilot_porthop")
runs = B.load_runs("coevo", (f"results/{DIR}",))
orig = H.eps
hop = [perturb_port(ep, 7000 + i) for i, ep in enumerate(orig)]  # same seeds as evasion_eval.py (kind "port" is the 2nd kind but perturb seeds use 7000 + i there too)
rec0 = [metric(r, orig, "recall") for r in runs]
rec1 = [metric(r, hop, "recall") for r in runs]
fpr0 = [metric(r, orig, "fpr") for r in runs]
base = json.load(open(ROOT / "results/pilot_evasion/evasion_eval.json"))
hard = json.load(open(ROOT / "results/pilot_hard/hard_eval.json"))
b_rec0, b_rec1 = base["LLM, co-evolved|none"], base["LLM, co-evolved|port"]
b_fpr0 = [e["fpr"] for e in hard["LLM, co-evolved|0"]]
f = lambda v: "%.3f [%.3f, %.3f]" % boot(v)  # noqa: E731
d = lambda a, b: "%+.3f [%+.3f, %+.3f]" % diff(a, b)  # noqa: E731
lines = [f"# Port-hopping Red ({DIR}): robustness of rules trained against it (pre-registered, see results/PREREG_*.md)", "",
         "Frozen rules, seen test episodes, native events. Mean [95% bootstrap CI over runs].", "",
         "| rule sets | runs | recall, original test | recall, ports re-drawn | FPR, original test |", "|---|---|---|---|---|",
         f"| coevo trained vs port-hopping Red, {DIR} (seeds 35-44) | {len(runs)} | {f(rec0)} | {f(rec1)} | {f(fpr0)} |",
         f"| coevo, original Red (20 runs) | 20 | {f(b_rec0)} | {f(b_rec1)} | {f(b_fpr0)} |", "",
         f"Difference (port-hop trained minus original), recall with ports re-drawn: {d(rec1, b_rec1)}; recall, original test: {d(rec0, b_rec0)}; FPR, original test: {d(fpr0, b_fpr0)}.",
         "", "Pre-registered claim (robustness improves) is supported only if the first difference has an interval above zero and the FPR difference is at most +0.02."]
out = ROOT / "results" / DIR
(out / "porthop_eval.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
