"""Explanatory illustrations for the start of the paper: hero (at a glance), worked example, rule listing, algorithm box.
All numbers in the hero panel come from the result files (results_final.json, committee.json)."""
import json
import pathlib
import statistics as st

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
FIG = ROOT / "paper/figs"
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"], "font.size": 7})
BLUE, RED, GREEN, AMBER, PURPLE, GREY = "#1f4e8c", "#b3392f", "#2b7a4b", "#c58a12", "#6a3d8f", "#6b6b6b"
MONO = {"family": "monospace", "size": 6.2}


def rbox(ax, x, y, w, h, fc, ec, lw=0.9, r=0.02):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0.004,rounding_size={r}", fc=fc, ec=ec, lw=lw))


def arrow(ax, p, q, color="#33507a", lw=1.0, rad=0.0, ls="-"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=8, lw=lw, color=color, linestyle=ls, connectionstyle=f"arc3,rad={rad}"))


def hero():
    fin = json.load(open(ROOT / "results/pilot/results_final.json", encoding="utf-8"))
    com = json.load(open(ROOT / "results/pilot/committee_rep.json", encoding="utf-8"))
    rec = lambda c: fin[c]["seen Red strategies|native|recall"]["ci"][0]  # noqa: E731
    fig = plt.figure(figsize=(7.2, 2.3))
    # panel A
    ax = fig.add_axes([0.02, 0.06, 0.30, 0.78])
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")
    rbox(ax, 0, 0, 10, 10, "#fbf7ee", AMBER)
    ax.text(5, 9.2, "Static rules age", ha="center", va="center", fontsize=8, fontweight="bold", color=AMBER)
    xs = [1, 2.2, 3.4, 4.6, 5.8, 7, 8.2, 9.2]
    att = [2.5, 3.1, 4.0, 4.8, 5.8, 6.6, 7.6, 8.4]
    cov = [7.4, 7.4, 7.2, 6.4, 5.4, 4.4, 3.5, 2.8]
    ax.fill_between(xs, cov, att, where=[a > c for a, c in zip(att, cov)], color=RED, alpha=0.18)
    ax.plot(xs, att, "-o", color=RED, ms=2.5, lw=1.4)
    ax.plot(xs, cov, "-o", color=BLUE, ms=2.5, lw=1.4)
    ax.text(5.6, 8.4, "attacker techniques", color=RED, fontsize=6.3, ha="center")
    ax.text(4.2, 1.1, "hand-written coverage", color=BLUE, fontsize=6.3, ha="center")
    ax.text(8.4, 5.1, "gap", color=RED, fontsize=6.5, ha="center", style="italic")
    ax.text(5, 0.3, "time  →", ha="center", fontsize=6, color=GREY)
    # panel B
    ax = fig.add_axes([0.34, 0.06, 0.34, 0.78])
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")
    rbox(ax, 0, 0, 10, 10, "#f3f7fc", BLUE)
    ax.text(5, 9.2, "A purple loop, automated", ha="center", va="center", fontsize=8, fontweight="bold", color=BLUE)
    rbox(ax, 0.6, 5.6, 3.5, 2.2, "#fbe9e7", RED)
    ax.text(2.35, 6.7, "Red agent\nplans, attacks", ha="center", va="center", fontsize=6.0, color=RED)
    rbox(ax, 5.9, 5.6, 3.5, 2.2, "#e6f2ea", GREEN)
    ax.text(7.65, 6.7, "5 Blue agents\nwrite rules", ha="center", va="center", fontsize=6.0, color=GREEN)
    rbox(ax, 3.2, 1.2, 3.6, 2.2, "#f2e8f7", PURPLE)
    ax.text(5.0, 2.3, "Score vs hidden\nlabels, feedback", ha="center", va="center", fontsize=6.6, color=PURPLE)
    arrow(ax, (4.2, 6.7), (5.8, 6.7), color=GREY)
    ax.text(5.0, 7.15, "events", fontsize=5.8, ha="center", color=GREY)
    arrow(ax, (7.6, 5.5), (6.2, 3.45), color=GREEN)
    arrow(ax, (3.8, 3.45), (2.4, 5.5), color=RED, rad=0.0)
    ax.text(5.0, 4.9, "every round", fontsize=6, ha="center", style="italic", color=GREY)
    # panel C
    ax = fig.add_axes([0.81, 0.14, 0.18, 0.66])
    labels = ["Hand-written", "Co-evolved\n(1 run, mean of 20)", "Fixed Red\n(1 run, mean of 20)", "Co-evolved\n(3 runs pooled)"]
    vals = [0.958, st.mean(com["coevo|1"]["recall"]), st.mean(com["llm_fixed_red|1"]["recall"]), st.mean(com["coevo|3"]["recall"])]
    cols = [GREY, RED, BLUE, GREEN]
    fpr = [0.193, st.mean(com["coevo|1"]["fpr"]), st.mean(com["llm_fixed_red|1"]["fpr"]), st.mean(com["coevo|3"]["fpr"])]
    ax.barh(range(4)[::-1], vals, color=cols, height=0.62)
    for i, (v, f) in enumerate(zip(vals, fpr)):
        ax.text(v + 0.03, 3 - i + 0.14, f"{v:.2f}", va="center", fontsize=6.6, fontweight="bold")
        ax.text(v + 0.03, 3 - i - 0.18, f"false alarms {f:.3f}", va="center", fontsize=5.0, color=GREY)
    ax.set_yticks(range(4)[::-1])
    ax.set_yticklabels(labels, fontsize=6)
    ax.set_xlim(0, 1.75)
    ax.set_xticks([0, 0.5, 1.0])
    ax.set_xlabel("native recall", fontsize=6)
    ax.tick_params(labelsize=6, length=2)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_title("What we measured", fontsize=8, fontweight="bold", color=GREEN, pad=7, loc="right")
    fig.savefig(FIG / "fig_hero.png", dpi=300)


def example():
    fig, ax = plt.subplots(figsize=(3.45, 3.35))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")
    rbox(ax, 0.2, 7.9, 9.6, 1.9, "#fbe9e7", RED)
    ax.text(0.5, 9.45, "1  Red acts", fontsize=7, fontweight="bold", color=RED, va="center")
    ax.text(0.5, 8.5, "ExploitRemoteService on a mail server; the\nsimulator creates a process record (hidden label: 1)", fontsize=6, va="center")
    arrow(ax, (5, 7.85), (5, 7.15), color=GREY)
    rbox(ax, 0.2, 4.3, 9.6, 2.8, "#f3f7fc", BLUE)
    ax.text(0.5, 6.75, "2  Bridge emits an event (Blue sees these fields only)", fontsize=7, fontweight="bold", color=BLUE, va="center")
    ax.text(0.5, 5.35, "category      process_creation\nparent_process haraka\nprocess_name  bash\nprivilege     elevated\nzone          restricted_zone_a", fontsize=6.0, family="monospace", va="center")
    ax.text(6.0, 5.35, "provenance: synthetic\n(enriched fields:\nprocess names)", fontsize=5.6, va="center", color=GREY, style="italic")
    arrow(ax, (5, 4.25), (5, 3.65), color=GREY)
    rbox(ax, 0.2, 1.65, 9.6, 1.95, "#e6f2ea", GREEN)
    ax.text(0.5, 3.25, "3  A Blue-written rule matches (blue_0_r8_0)", fontsize=7, fontweight="bold", color=GREEN, va="center")
    ax.text(0.5, 2.25, "parent_process = haraka AND process_name = bash\nAND privilege = elevated      confidence 0.95", fontsize=6.0, family="monospace", va="center")
    arrow(ax, (5, 1.6), (5, 1.0), color=GREY)
    rbox(ax, 0.2, 0.0, 9.6, 0.95, "#f2e8f7", PURPLE)
    ax.text(0.5, 0.48, "4  Alert on an attacker event, counted as a true positive", fontsize=6.6, fontweight="bold", color=PURPLE, va="center")
    fig.savefig(FIG / "fig_example.png", dpi=300, bbox_inches="tight", pad_inches=0.03)


def rule_listing():
    lines = [("title:", " Elevated bash spawned by haraka", GREEN), ("level:", " high", GREEN), ("logsource:", "", GREEN), ("  category:", " process_creation", GREEN),
             ("selections:", "", BLUE), ("  bash_from_haraka:", "", BLUE), ("    process_name:", " bash", BLUE), ("    parent_process:", " haraka", BLUE),
             ("  elevated_privilege:", "", BLUE), ("    privilege:", " elevated", BLUE), ("condition:", " bash_from_haraka and", RED), ("           ", " elevated_privilege", RED),
             ("confidence:", " 0.95", PURPLE), ("rationale:", " Haraka is a mail server;", PURPLE), ("            ", " bash with elevated privileges is", PURPLE), ("            ", " highly anomalous", PURPLE)]
    fig, ax = plt.subplots(figsize=(3.45, 2.45))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")
    ax.add_patch(Rectangle((0, 0), 10, 10, fc="#f6f8fb", ec="#c9d3e0", lw=0.8))
    ax.add_patch(Rectangle((0, 9.0), 10, 1.0, fc=BLUE, ec=BLUE))
    ax.text(0.3, 9.5, "Sigma-style rule written by a Blue agent (unedited, seed 3)", color="white", fontsize=6.4, va="center", fontweight="bold")
    for i, (k, v, c) in enumerate(lines):
        y = 8.4 - i * 0.52
        ax.text(0.35, y, k, color=c, va="center", fontweight="bold", **MONO)
        ax.text(0.35 + (len(k) + 2.2) * 0.178, y, v.strip(), color="#1d1d1d", va="center", **MONO)
    fig.savefig(FIG / "fig_rule.png", dpi=300, bbox_inches="tight", pad_inches=0.03)


def algorithm():
    L = [("Algorithm 1  One training run (8 rounds)", "h"), ("for r = 1 .. 8:", "k"),
         ("  # Blue proposes (feedback from round r-1)", "c"), ("  for each of 5 Blue agents:", "k"),
         ("    rules <- LLM(prompt: schema, patterns, feedback)", ""), ("    keep only rules that pass the validator (<= 5)", ""),
         ("    active <- last 12 rules (cap)", ""), ("  # Red plans, then the episode is played", "c"),
         ("  plan <- Red.plan(memory)   # LLM or evasive", ""), ("  events <- play_episode(plan, 500 steps)", ""),
         ("  # Score with hidden labels (training seeds only)", "c"), ("  P, R, FPR <- score(active, events)", ""),
         ("  # Feedback and retirement", "c"), ("  Blue.feedback <- per-rule precision, missed", ""), ("                   and noisy patterns", ""),
         ("  Red.memory <- share of its activity caught", ""), ("  retire rules with >= 3 fires and < 30% precision", ""),
         ("freeze active rules; score on held-out seeds", "k")]
    fig, ax = plt.subplots(figsize=(3.45, 3.0))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, len(L) * 0.62 + 0.6)
    ax.axis("off")
    ax.add_patch(Rectangle((0, 0), 10, len(L) * 0.62 + 0.6, fc="#faf7fd", ec="#cdbbe0", lw=0.8))
    for i, (t, kind) in enumerate(L):
        y = len(L) * 0.62 + 0.2 - (i + 0.5) * 0.62
        color = {"h": PURPLE, "k": BLUE, "c": GREEN, "": "#1d1d1d"}[kind]
        ax.text(0.3, y, t, color=color, va="center", fontweight="bold" if kind in ("h", "k") else "normal", style="italic" if kind == "c" else "normal", **MONO)
    fig.savefig(FIG / "fig_algo.png", dpi=300, bbox_inches="tight", pad_inches=0.03)


if __name__ == "__main__":
    hero()
    example()
    rule_listing()
    algorithm()
    print("ok")
