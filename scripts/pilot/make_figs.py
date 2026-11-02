"""Pilot: training curves and training statistics from results/pilot/train_log.jsonl.
Writes paper/figs/fig_training.png and results/pilot/train_summary.json. Run with an env that has matplotlib."""
from __future__ import annotations

import json
import pathlib
import statistics
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = pathlib.Path(__file__).resolve().parents[2]
LOG = ROOT / "results" / "pilot" / "train_log.jsonl"
ORDER = ["random_rules", "llm_fixed_red", "coevo_nofeedback", "coevo"]
LABEL = {"random_rules": "Random rules", "llm_fixed_red": "LLM, fixed Red", "coevo_nofeedback": "LLM co-evolved, no feedback", "coevo": "LLM co-evolved"}
COLOR = {"random_rules": "#7f7f7f", "llm_fixed_red": "#1f77b4", "coevo_nofeedback": "#ff7f0e", "coevo": "#2ca02c"}


def load() -> dict[tuple, dict]:
    recs: dict[tuple, dict] = {}
    for line in LOG.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            r = json.loads(line)
            recs[(r["condition"], r["seed"], r["round"])] = r  # last record wins (restarts)
    return recs


def main() -> None:
    recs = load()
    plt.rcParams.update({"font.family": "serif", "font.size": 7, "axes.linewidth": 0.6})
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.35))
    summary: dict = {}
    for ax, (part, metric, title) in zip(axes, [("native", "recall", "Native recall"), ("all", "fpr", "FPR (all events)"), ("all", "precision", "Precision (all events)")]):
        for cond in ORDER:
            by_round: dict[int, list[float]] = defaultdict(list)
            for (c, s, r), rec in recs.items():
                v = rec["scores"][part][metric]
                if c == cond and v is not None:
                    by_round[r].append(v)
            rounds = sorted(by_round)
            if not rounds:
                continue
            mean = [statistics.mean(by_round[r]) for r in rounds]
            se = [statistics.stdev(by_round[r]) / len(by_round[r]) ** 0.5 if len(by_round[r]) > 1 else 0.0 for r in rounds]
            lo = [m - e for m, e in zip(mean, se)]
            hi = [m + e for m, e in zip(mean, se)]
            ax.plot(rounds, mean, color=COLOR[cond], label=LABEL[cond], lw=1.1)
            ax.fill_between(rounds, lo, hi, color=COLOR[cond], alpha=0.18, lw=0)
        ax.set_title(title)
        ax.set_xlabel("round")
        ax.set_ylim(0, 1.02)
        ax.grid(alpha=0.25, lw=0.4)
    h, l = axes[0].get_legend_handles_labels()  # noqa: E741
    fig.legend(h, l, fontsize=6, frameon=False, loc="lower center", ncol=len(l))
    fig.tight_layout(pad=0.4, rect=(0, 0.1, 1, 1))
    out = ROOT / "paper" / "figs" / "fig_training.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=300)
    for cond in ORDER:
        rs = [r for (c, s, r_), r in recs.items() if c == cond]
        if not rs:
            continue
        blue = [r["blue"] for r in rs if r["blue"].get("llm_calls")]
        summary[cond] = {"records": len(rs), "runs": len({s for (c, s, _) in recs if c == cond}),
                         "mean_active_rules": round(statistics.mean(r["active_rules"] for r in rs), 1),
                         "retired_total": sum(len(r["retired"]) for r in rs),
                         "llm_calls": sum(b["llm_calls"] for b in blue),
                         "rules_valid_pct": round(100 * sum(b["valid_final"] for b in blue) / max(sum(b["objects_found"] for b in blue), 1), 1) if blue else None,
                         "fallback_agent_rounds": sum(b["fallbacks"] for b in blue) if blue else None,
                         "mean_round_seconds": round(statistics.mean(r["seconds"] for r in rs), 1)}
        if cond.startswith("coevo"):
            plans = [r["plan"] for r in rs if r.get("plan")]
            summary[cond]["red_plans"] = len(plans)
            summary[cond]["red_scan_mix"] = {k: sum(p["scan"] == k for p in plans) for k in ("aggressive", "stealthy", "mixed")}
            summary[cond]["red_goals"] = {g: sum(p["goal"] == g for p in plans) for g in sorted({p["goal"] for p in plans})}
            summary[cond]["red_fallbacks"] = sum(1 for r in rs if r.get("source") == "fallback")
    (ROOT / "results" / "pilot" / "train_summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
