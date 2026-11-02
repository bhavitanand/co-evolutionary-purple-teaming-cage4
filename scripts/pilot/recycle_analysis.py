"""recycle (final, seeds 25-34) vs baseline co-evolved (seeds 0-9 and 15-24) and fixed Red (same seeds). Native, seen Red strategies.

Usage: python scripts/pilot/recycle_analysis.py > results/pilot_recycle/analysis.md
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from analyze import SEEN_KEY, diff_ci  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
L = lambda p: json.load(open(ROOT / p, encoding="utf-8"))  # noqa: E731
rec, main, rep = L("results/pilot_recycle/results.json"), L("results/pilot/results_final.json"), L("results/pilot_rep/results.json")
M = ("recall", "fpr", "precision")
K = {m: f"{SEEN_KEY}|native|{m}" for m in M}


def runs(m, c, *srcs):
    return [v for s in srcs for v in s[c][K[m]]["runs"]]


GROUPS = {"recycle (10 runs)": {m: runs(m, "coevo", rec) for m in M},
          "co-evolved baseline (20 runs)": {m: runs(m, "coevo", main, rep) for m in M},
          "fixed Red (20 runs)": {m: runs(m, "llm_fixed_red", main, rep) for m in M}}
print("# recycle final analysis (native, seen Red strategies)\n\n| row | runs | recall | FPR | precision |\n|---|---|---|---|---|")
for lab, g in GROUPS.items():
    cells = []
    for m in M:
        v = g[m]
        d, lo, hi = diff_ci(v, [0.0] * len(v))
        cells.append(f"{d:.3f} [{lo:.3f}, {hi:.3f}]")
    print(f"| {lab} | {len(g['recall'])} | " + " | ".join(cells) + " |")
print("\n| difference | recall | FPR | precision |\n|---|---|---|---|")
for lab, a, b in (("recycle minus co-evolved baseline", "recycle (10 runs)", "co-evolved baseline (20 runs)"),
                  ("recycle minus fixed Red", "recycle (10 runs)", "fixed Red (20 runs)")):
    cells = []
    for m in M:
        d, lo, hi = diff_ci(GROUPS[a][m], GROUPS[b][m])
        cells.append(f"{d:+.3f} [{lo:+.3f}, {hi:+.3f}]")
    print(f"| {lab} | " + " | ".join(cells) + " |")
