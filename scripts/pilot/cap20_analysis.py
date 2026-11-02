"""cap20 (higher rule cap) vs standard cap, and the three LLM conditions at cap 20. Prints markdown (results/pilot_cap20/analysis.md).

Usage: python scripts/pilot/cap20_analysis.py > results/pilot_cap20/analysis.md
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from analyze import SEEN_KEY, diff_ci  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
new = json.load(open(ROOT / "results/pilot_cap20/results.json", encoding="utf-8"))
old = json.load(open(ROOT / "results/pilot/results_final.json", encoding="utf-8"))
K = {m: f"{SEEN_KEY}|native|{m}" for m in ("recall", "fpr", "precision")}
ROWS = [("Fixed Red, cap 12", old, "llm_fixed_red"), ("Fixed Red, cap 20", new, "llm_fixed_red"),
        ("No feedback, cap 12", old, "coevo_nofeedback"), ("No feedback, cap 20", new, "coevo_nofeedback"),
        ("Co-evolved, cap 12", old, "coevo"), ("Co-evolved, cap 20", new, "coevo")]
print("# cap20 analysis (native, seen Red strategies; mean [95% bootstrap CI] over runs)\n")
print("| row | runs | recall | FPR | precision |\n|---|---|---|---|---|")
for lab, src, c in ROWS:
    if c not in src:
        continue
    cells = []
    for m in ("recall", "fpr", "precision"):
        v = src[c][K[m]]
        cells.append(f"{v['ci'][0]:.3f} [{v['ci'][1]:.3f}, {v['ci'][2]:.3f}]")
    print(f"| {lab} | {src[c][K['recall']]['n_runs']} | " + " | ".join(cells) + " |")
print("\n| difference | recall | FPR | precision |\n|---|---|---|---|")
DIFFS = [("co-evolved minus fixed Red, cap 20", (new, "coevo"), (new, "llm_fixed_red")),
         ("co-evolved minus no feedback, cap 20", (new, "coevo"), (new, "coevo_nofeedback")),
         ("no feedback minus fixed Red, cap 20", (new, "coevo_nofeedback"), (new, "llm_fixed_red")),
         ("co-evolved cap 20 minus cap 12", (new, "coevo"), (old, "coevo")),
         ("fixed Red cap 20 minus cap 12", (new, "llm_fixed_red"), (old, "llm_fixed_red")),
         ("no feedback cap 20 minus cap 12", (new, "coevo_nofeedback"), (old, "coevo_nofeedback"))]
for lab, (sa, ca), (sb, cb) in DIFFS:
    if ca not in sa or cb not in sb:
        continue
    cells = []
    for m in ("recall", "fpr", "precision"):
        d, lo, hi = diff_ci(sa[ca][K[m]]["runs"], sb[cb][K[m]]["runs"])
        cells.append(f"{d:+.3f} [{lo:+.3f}, {hi:+.3f}]")
    print(f"| {lab} | " + " | ".join(cells) + " |")
