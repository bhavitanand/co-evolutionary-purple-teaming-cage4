"""Pilot: score FROZEN rule sets on TEST episodes (no feedback, no labels given to Blue).

Step 1  `--cache`: play test episodes once and store the bridge's labelled events (passive Blue, so one recording serves every
        condition): Red strategies x test seeds 100-109, results/pilot/test_events/<red>_s<seed>.json.gz
        Seen in training: cage4_default, aggressive, stealthy, deception_aware.  UNSEEN: hit_and_run (held out, test seeds only).
Step 2  `--score`: for every condition, apply each training run's final rules (per Blue agent, to that agent's events) to every
        cached episode; metrics overall and split by provenance; mean over test episodes per training run, then mean and 95%
        bootstrap CI over the training runs. The static 10-rule set is scored the same way (one run).
  python scripts/pilot/eval_rules.py --cache
  python scripts/pilot/eval_rules.py --score --md results/pilot/results.md --out results/pilot/results.json
"""
from __future__ import annotations

import argparse
import gzip
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
CAGE = ROOT / "external" / "cage-challenge-4"
if CAGE.exists():
    sys.path.insert(0, str(CAGE))

from src.eval.stats import bootstrap_ci  # noqa: E402
from src.rules.loader import load_rules  # noqa: E402
from src.rules.schema import Rule  # noqa: E402

TEST_SEEDS = list(range(100, 110))
SEEN = ["cage4_default", "aggressive", "stealthy", "deception_aware"]
UNSEEN = ["hit_and_run"]
LIBRARY = ["plan_stealth_probe", "plan_stealth_push", "plan_loud_push", "plan_mixed"]  # the evasive Red's repertoire, played as fixed test attackers
BLUE = [f"blue_agent_{i}" for i in range(5)]
LABELS = {"static": "Static hand-written rules", "random_rules": "Random exemplar rules + retirement",
          "llm_fixed_red": "LLM Blue vs fixed Red (no self-play)", "coevo_nofeedback": "LLM co-evolved, NO feedback (ablation)",
          "coevo": "LLM co-evolved (ours)", "coevo_aware": "LLM co-evolved, Red sees per-action detection",
          "coevo_evasive": "LLM Blue vs EVASIVE Red (feedback)", "evasive_nofeedback": "LLM Blue vs EVASIVE Red, NO feedback"}
ORDER = ["static", "random_rules", "llm_fixed_red", "coevo_nofeedback", "coevo", "coevo_aware", "coevo_evasive", "evasive_nofeedback"]


def cache(out_dir: pathlib.Path, reds: list[str], seeds: list[int]) -> None:
    from src.loop.coevo import EpisodePlayer
    player = EpisodePlayer()
    try:
        for red in reds:
            for s in seeds:
                path = out_dir / "test_events" / f"{red}_s{s}.json.gz"
                if path.exists():
                    continue
                if red.startswith("plan_"):
                    from src.agents.red.evasive import LIBRARY as PLANS
                    from src.agents.red.llm_red import PlannedRed
                    ep = player.play(PlannedRed, s, steps=500, plan=PLANS[red[5:]].to_dict())
                else:
                    ep = player.play(red, s, steps=500)
                path.parent.mkdir(parents=True, exist_ok=True)
                with gzip.open(path, "wt", encoding="utf-8") as f:
                    json.dump({"red": red, "seed": s, "last_step": ep["last_step"], "events": ep["events"],
                               "red_actions": dict(ep["red_actions"]), "red_success": dict(ep["red_success"])}, f)
                print(f"cached {red} seed {s}: {len(ep['events'])} events", flush=True)
    finally:
        player.close()


def load_test(out_dir: pathlib.Path) -> dict[str, list[dict]]:
    data: dict[str, list[dict]] = {}
    for red in SEEN + UNSEEN + LIBRARY:
        for s in TEST_SEEDS:
            p = out_dir / "test_events" / f"{red}_s{s}.json.gz"
            if p.exists():
                with gzip.open(p, "rt", encoding="utf-8") as f:
                    data.setdefault(red, []).append(json.load(f))
    return data


def rule_sets(out_dir: pathlib.Path) -> dict[str, list[dict[str, list[Rule]]]]:
    """condition -> list of runs, each {blue_agent: [Rule]}."""
    sets: dict[str, list[dict[str, list[Rule]]]] = {}
    static = load_rules(str(ROOT / "configs" / "static_blue_rules.json"))
    sets["static"] = [{a: list(static) for a in BLUE}]
    for path in sorted((out_dir / "rules").glob("*_seed*.json")) if (out_dir / "rules").exists() else []:
        d = json.loads(path.read_text(encoding="utf-8"))
        sets.setdefault(d["condition"], []).append({a: [Rule.from_dict(r) for r in rs] for a, rs in d["rules"].items()})
    return sets


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--cache", action="store_true")
    ap.add_argument("--score", action="store_true")
    ap.add_argument("--out-dir", default="results/pilot")
    ap.add_argument("--reds", nargs="+", default=SEEN + UNSEEN)
    ap.add_argument("--seeds", type=int, nargs="+", default=TEST_SEEDS)
    ap.add_argument("--md", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    out_dir = ROOT / args.out_dir
    if args.cache:
        bad = [s for s in args.seeds if s not in TEST_SEEDS]
        if bad:
            raise SystemExit(f"{bad} are not test seeds (100-109)")
        cache(out_dir, args.reds, args.seeds)
    if args.score:
        from src.loop.coevo import apply_rules, score
        test, sets = load_test(out_dir), rule_sets(out_dir)
        groups = {"seen Red strategies": SEEN, "UNSEEN Red (hit_and_run)": UNSEEN, "EVASIVE Red plan library": LIBRARY}
        results: dict = {}
        for cond, runs in sets.items():
            per_run: dict[str, dict[str, list[float]]] = {}
            for run in runs:
                acc: dict[tuple, list[float]] = {}
                for gname, reds in groups.items():
                    for red in reds:
                        for ep in test.get(red, []):
                            sc = score(ep["events"], apply_rules(ep["events"], run), ep["last_step"])
                            for part in ("all", "native", "synthetic"):
                                for m in ("precision", "recall", "fpr"):
                                    v = sc[part][m]
                                    if v is not None:
                                        acc.setdefault((gname, part, m), []).append(v)
                            for m in ("precision", "recall", "fpr"):  # per Red strategy, native events (for the per-strategy breakdown)
                                v = sc["native"][m]
                                if v is not None:
                                    acc.setdefault((f"red:{red}", "native", m), []).append(v)
                for (gname, part, m), vals in acc.items():
                    per_run.setdefault(f"{gname}|{part}|{m}", {"runs": []})["runs"].append(sum(vals) / len(vals))
            results[cond] = {k: {"n_runs": len(v["runs"]), "ci": bootstrap_ci(v["runs"], n_resamples=4000), "runs": v["runs"]} for k, v in per_run.items()}
        if args.out:
            pathlib.Path(args.out).write_text(json.dumps(results, indent=1), encoding="utf-8")
        lines = ["# Pilot results (frozen rules on TEST seeds 100-109)", "",
                 "Mean over test episodes per training run, then mean [95% bootstrap CI] over training runs. "
                 "'native' = events CAGE-4 really produced (plus seeded enrichment); 'synthetic' = events we invented "
                 "(PrivilegeEscalate / Impact / DegradeServices): recall on those is easy by construction, never pool.", ""]
        for gname in groups:
            for part in ("all", "native", "synthetic"):
                lines += [f"## {gname} - {part} events", "", "| condition | runs | precision | recall | FPR |", "|---|---|---|---|---|"]
                for cond in ORDER:
                    if cond not in results:
                        continue
                    cells = []
                    for m in ("precision", "recall", "fpr"):
                        r = results[cond].get(f"{gname}|{part}|{m}")
                        if not r:
                            cells.append("n/a")
                        else:
                            est, lo, hi = r["ci"]
                            cells.append(f"{est:.3f}" + (f" [{lo:.3f}, {hi:.3f}]" if lo is not None else ""))
                    n = results[cond].get(f"{gname}|{part}|recall", {}).get("n_runs", 0)
                    lines.append(f"| {LABELS[cond]} | {n} | " + " | ".join(cells) + " |")
                lines.append("")
        text = "\n".join(lines)
        print(text)
        if args.md:
            pathlib.Path(args.md).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
