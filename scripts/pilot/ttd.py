"""Time to detect (steps from the first attacker event to the first alert) and share of episodes with any detection,
frozen rules on the 40 SEEN test episodes. -> results/pilot/ttd.md (run with .venv-cyborg python)."""
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
from src.loop.coevo import apply_rules, score  # noqa: E402
from src.rules.loader import load_rules  # noqa: E402
from src.rules.schema import Rule  # noqa: E402

SEEN = ["cage4_default", "aggressive", "stealthy", "deception_aware"]
eps = []
for red in SEEN:
    for s in range(100, 110):
        with gzip.open(ROOT / f"results/pilot/test_events/{red}_s{s}.json.gz", "rt", encoding="utf-8") as f:
            eps.append(json.load(f))
BLUE = [f"blue_agent_{i}" for i in range(5)]
CONDS = [("Static hand-written", "static"), ("Random rules", "random_rules"), ("LLM, fixed Red", "llm_fixed_red"),
         ("LLM, no feedback", "coevo_nofeedback"), ("LLM, co-evolved", "coevo"), ("LLM, per-action signal", "coevo_aware")]
rows = []
for label, cond in CONDS:
    if cond == "static":
        st_rules = load_rules(str(ROOT / "configs" / "static_blue_rules.json"))
        runs = [{a: list(st_rules) for a in BLUE}]
    else:
        runs = []
        for f in sorted((ROOT / "results/pilot/rules").glob(f"{cond}_seed*.json")):
            d = json.loads(f.read_text(encoding="utf-8-sig"))["rules"]
            runs.append({a: [Rule.from_dict(r) for r in rs] for a, rs in d.items()})
    det_share, medians = [], []
    for run in runs:
        ttds, found = [], 0
        for ep in eps:
            sc = score(ep["events"], apply_rules(ep["events"], run), ep["last_step"])
            t = sc["native"]["time_to_detect"]
            if t is not None:
                found += 1
                ttds.append(t)
        det_share.append(100 * found / len(eps))
        medians.append(st.median(ttds) if ttds else float("nan"))
    ok = [m for m in medians if m == m]
    rows.append((label, len(runs), st.mean(det_share), st.mean(ok) if ok else float("nan")))
out = ["# Time to detect on seen test episodes (native events; frozen rules; mean over runs)", "",
       "| set | runs | episodes with any native attacker alert (%) | median steps to first alert (mean over runs) |", "|---|---|---|---|"]
out += [f"| {a} | {b} | {c:.0f} | {d:.1f} |" for a, b, c, d in rows]
(ROOT / "results/pilot/ttd.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out))
