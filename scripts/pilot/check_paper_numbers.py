"""QA: every number in the paper's result tables I, II, VI, VII, VIII must equal the value in the result JSON (3 decimals)."""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
md = (ROOT / "paper/paper.md").read_text(encoding="utf-8").split("\n")
J = lambda p: json.load(open(ROOT / p, encoding="utf-8"))  # noqa: E731
fin, ev, glm, cap = J("results/pilot/results_final.json"), J("results/pilot/results_evasive.json"), J("results/pilot_glm/results_n3.json"), J("results/pilot_cap20/results.json")
SEEN, UN = "seen Red strategies|native|", "UNSEEN Red (hit_and_run)|native|"


def fmt(src, c, key, m):
    mean, lo, hi = src[c][key + m]["ci"]
    return f"{mean:.3f}" if lo is None else f"{mean:.3f} [{lo:.3f}, {hi:.3f}]"


def table_rows(prefix):
    for i, ln in enumerate(md):
        if ln.startswith("Table: ") and prefix in ln:
            rows, j = [], i + 2
            while j < len(md) and " | " in md[j]:
                rows.append([c.strip() for c in md[j].split(" | ")])
                j += 1
            return rows
    raise SystemExit("table not found " + prefix)


bad = n = 0


def chk(label, got, want):
    global bad, n
    n += 1
    if got != want:
        bad += 1
        print("MISMATCH", label, "paper:", got, "files:", want)


T1 = {"Static hand-written rules": ("static", fin), "Random exemplar rules + retirement": ("random_rules", fin), "LLM Blue vs fixed Red": ("llm_fixed_red", fin),
      "LLM co-evolved, no feedback": ("coevo_nofeedback", fin), "LLM co-evolved": ("coevo", fin), "LLM co-evolved, per-action signal": ("coevo_aware", fin)}
for pre, key in (("Frozen rules on the four seen", SEEN), ("Frozen rules on the held-out", UN)):
    for r in table_rows(pre):
        c, src = T1[r[0]]
        for k, m in zip(r[2:], ("precision", "recall", "fpr")):
            chk(f"{pre[:12]} {r[0]} {m}", k, fmt(src, c, key, m))
for r in table_rows("Evasive-Red test"):
    c, src = {"Fixed Red": ("llm_fixed_red", fin), "Co-evolved (LLM Red)": ("coevo", fin), "Co-evolved vs evasive Red": ("coevo_evasive", ev), "Evasive Red, no feedback": ("evasive_nofeedback", ev)}[r[0]]
    chk("evasive recall " + r[0], r[1], fmt(src, c, SEEN, "recall"))
    chk("evasive fpr " + r[0], r[2], fmt(src, c, SEEN, "fpr"))
for r in table_rows("Larger writer model"):
    c = {"Fixed Red": "llm_fixed_red", "No feedback": "coevo_nofeedback", "Co-evolved": "coevo"}[r[0]]
    chk("glm seen recall " + r[0], r[1], fmt(glm, c, SEEN, "recall"))
    chk("glm seen fpr " + r[0], r[2], fmt(glm, c, SEEN, "fpr"))
    chk("glm unseen recall " + r[0], r[3], fmt(glm, c, UN, "recall"))
for r in table_rows("Effect of a higher cap"):
    lab = r[0]
    src = cap if "cap 20" in lab else fin
    c = "llm_fixed_red" if lab.startswith("Fixed") else ("coevo_nofeedback" if lab.startswith("No feedback") else "coevo")
    for k, m in zip(r[1:], ("recall", "fpr", "precision")):
        chk(f"cap {lab} {m}", k, fmt(src, c, SEEN, m))
print(f"checked {n} numbers, {bad} mismatches")
