"""Paper figures: architecture diagram, recall/FPR bars, recall-vs-FPR trade-off. Numbers come only from results/*.json."""
import json
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
FIG = ROOT / "paper/figs"
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"], "font.size": 6.5, "axes.linewidth": 0.6})
K = "seen Red strategies|native|"
fin = json.load(open(ROOT / "results/pilot/results_final.json", encoding="utf-8"))
ev = json.load(open(ROOT / "results/pilot/results_evasive.json", encoding="utf-8"))
ROWS = [("Static (hand-written)", fin, "static", "#6b6b6b"), ("Random rules", fin, "random_rules", "#e69f00"),
        ("LLM, fixed Red", fin, "llm_fixed_red", "#0072b2"), ("Co-evolved, no feedback", fin, "coevo_nofeedback", "#009e73"),
        ("Co-evolved (full)", fin, "coevo", "#cc3311"), ("Co-evolved, per-action signal", fin, "coevo_aware", "#56b4e9"),
        ("Evasive Red (full)", ev, "coevo_evasive", "#8c564b"), ("Evasive Red, no feedback", ev, "evasive_nofeedback", "#b8a000")]


def val(src, c, m):
    mean, lo, hi = src[c][K + m]["ci"]
    return mean, (mean if lo is None else lo), (mean if hi is None else hi)


def box(ax, x, y, w, h, text, fc="#eef3fb", ec="#33507a", fs=6.2):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.01,rounding_size=0.015", fc=fc, ec=ec, lw=0.7))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, linespacing=1.15)


def arrow(ax, p, q, color="#33507a", ls="-"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=7, lw=0.7, color=color, linestyle=ls))


def architecture():
    fig, ax = plt.subplots(figsize=(3.45, 3.9))
    ax.set_xlim(-0.04, 1.04)
    ax.set_ylim(0, 1)
    ax.axis("off")
    red, blue, sim, gt = "#fbe9e7", "#e6f2ea", "#f3f0e6", "#f2e8f7"
    box(ax, 0.02, 0.86, 0.44, 0.12, "Red planner\n(LLM or scripted evasive)\nonce per round", red, "#a33")
    box(ax, 0.54, 0.86, 0.44, 0.12, "Red executor (FSM)\nplays 500 steps,\nlegal actions only", red, "#a33")
    arrow(ax, (0.46, 0.92), (0.54, 0.92))
    box(ax, 0.02, 0.66, 0.96, 0.12, "CAGE-4 enterprise simulation (Blue, Green and Red agents)\nnative observations, Green benign traffic, ground truth", sim, "#7a6a33")
    arrow(ax, (0.76, 0.86), (0.76, 0.78))
    box(ax, 0.54, 0.46, 0.44, 0.14, "Telemetry bridge\n16 Blue-visible fields;\nnative / enriched / synthetic\ntags; labels hidden", "#eef3fb")
    arrow(ax, (0.76, 0.66), (0.76, 0.60))
    box(ax, 0.02, 0.46, 0.44, 0.14, "5 Blue agents (LLM)\n≤5 Sigma-style rules each\nper round; validator\nrejects invalid rules", blue, "#2f6b45")
    arrow(ax, (0.54, 0.53), (0.46, 0.53))
    box(ax, 0.02, 0.26, 0.44, 0.12, "Active rule set\n≤12 rules per agent,\nper-event matching", "#fff7e0", "#8a6d00")
    arrow(ax, (0.24, 0.46), (0.24, 0.38))
    box(ax, 0.54, 0.26, 0.44, 0.12, "Scoring vs hidden labels\n(training seeds only):\nprecision, recall, FPR", gt, "#6a3d8f")
    arrow(ax, (0.46, 0.32), (0.54, 0.32))
    box(ax, 0.02, 0.06, 0.44, 0.12, "Feedback to Blue:\nper-rule precision, missed\nand noisy patterns; retire\nweak rules", blue, "#2f6b45", fs=5.8)
    box(ax, 0.54, 0.06, 0.44, 0.12, "Feedback to Red:\nshare of its activity caught\n(optionally per action)", red, "#a33", fs=5.8)
    arrow(ax, (0.60, 0.26), (0.40, 0.18))
    arrow(ax, (0.76, 0.26), (0.76, 0.18))
    ax.plot([0.02, -0.03, -0.03], [0.12, 0.12, 0.53], color="#2f6b45", lw=0.7, ls="--")
    arrow(ax, (-0.03, 0.53), (0.02, 0.53), color="#2f6b45", ls="--")
    ax.plot([0.98, 1.03, 1.03], [0.12, 0.12, 0.92], color="#a33", lw=0.7, ls="--")
    arrow(ax, (1.03, 0.92), (0.98, 0.92), color="#a33", ls="--")
    fig.savefig(FIG / "fig_architecture.png", dpi=300, bbox_inches="tight", pad_inches=0.03)


def bars():
    fig, axes = plt.subplots(1, 2, figsize=(3.45, 2.55), sharey=True)
    for ax, m, title, xl in ((axes[0], "recall", "Native recall", (0, 1)), (axes[1], "fpr", "Native FPR", (0, 0.66))):
        for i, (lab, src, c, col) in enumerate(ROWS[::-1]):
            mean, lo, hi = val(src, c, m)
            ax.barh(i, mean, color=col, height=0.66)
            if hi > mean or lo < mean:
                ax.errorbar(mean, i, xerr=[[mean - lo], [hi - mean]], color="black", lw=0.6, capsize=1.5)
        ax.set_xlim(*xl)
        ax.set_title(title, fontsize=7)
        ax.tick_params(labelsize=6, length=2)
        ax.grid(axis="x", lw=0.3, alpha=0.5)
        ax.set_axisbelow(True)
    axes[0].set_yticks(range(len(ROWS)))
    axes[0].set_yticklabels([r[0] for r in ROWS[::-1]], fontsize=5.8)
    fig.tight_layout(w_pad=0.6)
    fig.savefig(FIG / "fig_bars.png", dpi=300, bbox_inches="tight", pad_inches=0.03)


def tradeoff():
    fig, ax = plt.subplots(figsize=(3.45, 2.5))
    for lab, src, c, col in ROWS:
        r, rl, rh = val(src, c, "recall")
        f, fl, fh = val(src, c, "fpr")
        has = rh != r or rl != r
        ax.errorbar(f, r, xerr=[[f - fl], [fh - f]] if has else None, yerr=[[r - rl], [rh - r]] if has else None,
                    fmt="o", ms=4, color=col, lw=0.6, capsize=1, label=lab)
    ax.set_xscale("symlog", linthresh=0.01)
    ax.set_xlim(-0.002, 0.7)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("False-positive rate on benign events (symlog)", fontsize=6.5)
    ax.set_ylabel("Native recall", fontsize=6.5)
    ax.grid(lw=0.3, alpha=0.5)
    ax.tick_params(labelsize=6, length=2)
    ax.legend(fontsize=5, frameon=False, loc="lower right", handletextpad=0.2, labelspacing=0.25)
    fig.tight_layout()
    fig.savefig(FIG / "fig_tradeoff.png", dpi=300, bbox_inches="tight", pad_inches=0.03)


if __name__ == "__main__":
    architecture()
    bars()
    tradeoff()
    print("ok")


def concentration():
    """Fig 5: share of native attacker alerts explained by the k most productive rules (mean over runs)."""
    hits = json.load(open(ROOT / "results/pilot/per_rule_hits.json", encoding="utf-8"))
    names = [("llm_fixed_red", "LLM, fixed Red", "#0072b2"), ("coevo_nofeedback", "Co-evolved, no feedback", "#009e73"),
             ("coevo", "Co-evolved (full)", "#cc3311"), ("random_rules", "Random rules", "#e69f00")]
    fig, ax = plt.subplots(figsize=(3.45, 2.3))
    for key, lab, col in names:
        curves = []
        for h in hits[key]:
            tot = sum(h) or 1
            acc, cur = 0, [0.0]
            for v in h:
                acc += v
                cur.append(acc / tot)
            curves.append(cur)
        n = min(len(c) for c in curves)
        mean = [sum(c[i] for c in curves) / len(curves) for i in range(n)]
        ax.plot(range(n), mean, color=col, lw=1.2, label=lab)
    ax.axhline(0.8, color="gray", lw=0.5, ls="--")
    ax.set_xlim(0, 40)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("Rules ranked by native attacker alerts (k)", fontsize=6.5)
    ax.set_ylabel("Share of attacker alerts\nexplained by top k rules", fontsize=6.5)
    ax.grid(lw=0.3, alpha=0.5)
    ax.tick_params(labelsize=6, length=2)
    ax.legend(fontsize=5.5, frameon=False, loc="lower right")
    fig.tight_layout()
    fig.savefig(FIG / "fig_concentration.png", dpi=300, bbox_inches="tight", pad_inches=0.03)


concentration()


def committee_fig():
    """Fig 6: committee size sweep (disjoint groups of independent runs, union of rules)."""
    data = json.load(open(ROOT / "results/pilot/committee.json", encoding="utf-8"))
    conds = [("llm_fixed_red", "LLM, fixed Red", "#0072b2"), ("coevo_nofeedback", "Co-evolved, no feedback", "#009e73"), ("coevo", "Co-evolved (full)", "#cc3311"), ("coevo_evasive", "Evasive Red (full)", "#8c564b")]
    fig, ax = plt.subplots(figsize=(3.45, 2.6))
    for key, lab, col in conds:
        xs, ys = [], []
        for k in (1, 2, 3, 5, 10):
            d = data[f"{key}|{k}"]
            xs.append(sum(d["fpr"]) / len(d["fpr"]))
            ys.append(sum(d["recall"]) / len(d["recall"]))
        ax.plot(xs, ys, "-o", color=col, ms=3, lw=1, label=lab)
        for k, x, y in zip((1, 2, 3, 5, 10), xs, ys):
            ax.annotate(str(k), (x, y), textcoords="offset points", xytext=(3, -7), fontsize=5, color=col)
    ax.plot([0.193], [0.958], "s", color="#6b6b6b", ms=4, label="Hand-written rules")
    ax.set_xscale("symlog", linthresh=0.01)
    ax.set_xlim(0, 0.3)
    ax.set_ylim(0.2, 1.02)
    ax.set_xlabel("False-positive rate (symlog); labels = runs pooled", fontsize=6.2)
    ax.set_ylabel("Native recall", fontsize=6.5)
    ax.grid(lw=0.3, alpha=0.5)
    ax.tick_params(labelsize=6, length=2)
    ax.legend(fontsize=5.3, frameon=False, loc="lower right")
    fig.tight_layout()
    fig.savefig(FIG / "fig_committee.png", dpi=300, bbox_inches="tight", pad_inches=0.03)


committee_fig()
