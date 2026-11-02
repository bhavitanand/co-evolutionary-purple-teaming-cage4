"""Helpers (shared) for hybrid.py and committee.py. Original docstring: Two CPU-only checks on the frozen rule sets (seen test episodes, native events):
  1. HYBRID: hand-written static rules + one LLM run's rules.
  2. COMMITTEE: union of the rule sets of 3 independent runs of one condition (runs i, i+1, i+2 mod 10).
-> results/pilot/hybrid.md (run with .venv-cyborg python)."""
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
from src.eval.stats import bootstrap_ci  # noqa: E402
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
static = load_rules(str(ROOT / "configs" / "static_blue_rules.json"))


def evaluate(run):
    acc = {"precision": [], "recall": [], "fpr": []}
    for ep in eps:
        sc = score(ep["events"], apply_rules(ep["events"], run), ep["last_step"])["native"]
        for m in acc:
            if sc[m] is not None:
                acc[m].append(sc[m])
    return {m: st.mean(v) for m, v in acc.items()}


def load_runs(cond):
    out = []
    for f in sorted((ROOT / "results/pilot/rules").glob(f"{cond}_seed*.json")):
        d = json.loads(f.read_text(encoding="utf-8-sig"))["rules"]
        out.append({a: [Rule.from_dict(r) for r in rs] for a, rs in d.items()})
    return out


def merged(*runs):
    return {a: [r for run in runs for r in run.get(a, [])] for a in BLUE}


def summarise(label, results):
    cells = []
    for m in ("precision", "recall", "fpr"):
        mean, lo, hi = bootstrap_ci([r[m] for r in results], n_resamples=4000)
        cells.append(f"{mean:.3f} [{lo:.3f}, {hi:.3f}]")
    return f"| {label} | {len(results)} | " + " | ".join(cells) + " |"


