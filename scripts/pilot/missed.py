"""Pilot: what do the frozen rule sets miss? Native attacker events on the seen test episodes, grouped by event category
and by source action (labels are used here for ANALYSIS only, never for rule writing).

  ..\\.venv-cyborg\\Scripts\\python.exe scripts/pilot/missed.py > results/pilot/missed.md
"""
from __future__ import annotations

import pathlib
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "pilot"))

from eval_rules import SEEN, load_test, rule_sets  # noqa: E402
from src.loop.coevo import apply_rules  # noqa: E402

NAMES = {"static": "Static", "random_rules": "Random rules", "llm_fixed_red": "LLM, fixed Red", "coevo_nofeedback": "LLM co-evolved, no feedback",
         "coevo": "LLM co-evolved", "coevo_aware": "LLM co-evolved, per-action signal"}


def main() -> None:
    out_dir = ROOT / "results" / "pilot"
    test, sets = load_test(out_dir), rule_sets(out_dir)
    print("# What the frozen rule sets catch, native attacker events, seen Red strategies\n")
    print("Share of native attacker events caught, by the action that produced them (mean over runs).\n")
    actions: list[str] = []
    table: dict[str, dict[str, float]] = {}
    for cond, runs in sets.items():
        tot: Counter = Counter()
        hit: Counter = Counter()
        for run in runs:
            for red in SEEN:
                for ep in test[red]:
                    alerted = {a.event_id for a in apply_rules(ep["events"], run)}
                    for e in ep["events"]:
                        if e["label_red"] == 1 and e["provenance"] == "native":
                            key = f"{e['source_action']} / {e['category']}"
                            tot[key] += 1
                            hit[key] += e["event_id"] in alerted
        table[cond] = {k: hit[k] / tot[k] for k in tot}
        for k in tot:
            if k not in actions:
                actions.append(k)
    cols = [c for c in NAMES if c in table]
    print("| action / event category | " + " | ".join(NAMES[c] for c in cols) + " |")
    print("|" + "---|" * (len(cols) + 1))
    for k in sorted(actions):
        print(f"| {k} | " + " | ".join(f"{table[c].get(k, float('nan')):.2f}" for c in cols) + " |")


if __name__ == "__main__":
    main()
