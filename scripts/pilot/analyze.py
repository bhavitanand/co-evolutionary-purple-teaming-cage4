"""Pilot: extra analysis on the frozen-rule results (no LLM, no CAGE needed).

  python scripts/pilot/analyze.py results/pilot/results_final.json > results/pilot/analysis.md

Reads per-run values saved by eval_rules.py and writes
  1. bootstrap 95% intervals for DIFFERENCES between conditions (runs are independent, so each side is resampled on its own),
  2. native recall per Red strategy for every condition (which attacker styles are missed).
"""
from __future__ import annotations

import json
import random
import statistics
import sys

SEEN_KEY = "seen Red strategies"
PAIRS = [("coevo", "llm_fixed_red"), ("coevo", "coevo_nofeedback"), ("coevo_aware", "coevo"), ("coevo_aware", "coevo_nofeedback")]
NAMES = {"static": "Static", "random_rules": "Random rules", "llm_fixed_red": "LLM, fixed Red", "coevo_nofeedback": "LLM co-evolved, no feedback",
         "coevo": "LLM co-evolved", "coevo_aware": "LLM co-evolved, per-action signal"}
REDS = ["cage4_default", "aggressive", "stealthy", "deception_aware", "hit_and_run"]


def diff_ci(a: list[float], b: list[float], n: int = 10000, seed: int = 0) -> tuple[float, float, float]:
    rng = random.Random(seed)
    ds = sorted(statistics.mean(rng.choices(a, k=len(a))) - statistics.mean(rng.choices(b, k=len(b))) for _ in range(n))
    return statistics.mean(a) - statistics.mean(b), ds[int(0.025 * n)], ds[int(0.975 * n) - 1]


def main(path: str) -> None:
    res = json.load(open(path, encoding="utf-8"))
    print("# Extra analysis (frozen rules, test seeds 100-109)\n")
    print("## Differences between conditions, seen Red strategies, native events (mean difference [95% bootstrap CI])\n")
    print("| A - B | recall | FPR | precision |\n|---|---|---|---|")
    for a, b in PAIRS:
        if a not in res or b not in res:
            continue
        cells = []
        for m in ("recall", "fpr", "precision"):
            k = f"{SEEN_KEY}|native|{m}"
            d, lo, hi = diff_ci(res[a][k]["runs"], res[b][k]["runs"])
            cells.append(f"{d:+.3f} [{lo:+.3f}, {hi:+.3f}]")
        print(f"| {NAMES[a]} - {NAMES[b]} | " + " | ".join(cells) + " |")
    print("\n## Native recall by Red strategy (mean over runs)\n")
    print("| condition | " + " | ".join(REDS) + " |\n|" + "---|" * (len(REDS) + 1))
    for c in ("static", "random_rules", "llm_fixed_red", "coevo_nofeedback", "coevo", "coevo_aware"):
        if c not in res:
            continue
        cells = []
        for r in REDS:
            v = res[c].get(f"red:{r}|native|recall")
            cells.append("n/a" if not v else f"{statistics.mean(v['runs']):.2f}")
        print(f"| {NAMES[c]} | " + " | ".join(cells) + " |")


if __name__ == "__main__":
    main(sys.argv[1])
