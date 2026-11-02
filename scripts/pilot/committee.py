"""Committee size sweep with DISJOINT groups of independent runs (union of their rules), seen test episodes, native events.
-> results/pilot/committee.json + committee.md (run with .venv-cyborg python)."""
import json
import pathlib
import statistics as st
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "pilot"))
import hybrid_lib as H  # noqa: E402

SIZES = [1, 2, 3, 5, 10]
res = {}
lines = ["# Committee size sweep (disjoint groups of independent runs; seen test episodes, native events)", "",
         "| condition | committee size | groups | rules in committee | precision | recall | FPR |", "|---|---|---|---|---|---|---|"]
for label, cond in (("LLM, fixed Red", "llm_fixed_red"), ("LLM, no feedback", "coevo_nofeedback"), ("LLM, co-evolved", "coevo"),
                    ("LLM, evasive Red", "coevo_evasive"), ("LLM, evasive Red, no feedback", "evasive_nofeedback")):
    runs = H.load_runs(cond)
    for k in SIZES:
        groups = [runs[i:i + k] for i in range(0, len(runs) - k + 1, k)]
        ev = [H.evaluate(H.merged(*g)) for g in groups]
        nrules = st.mean(sum(len(rs) for r in g for rs in r.values()) for g in groups)
        res[f"{cond}|{k}"] = {"groups": len(groups), "rules": nrules, **{m: [e[m] for e in ev] for m in ("precision", "recall", "fpr")}}
        lines.append(f"| {label} | {k} | {len(groups)} | {nrules:.0f} | {st.mean(e['precision'] for e in ev):.3f} | {st.mean(e['recall'] for e in ev):.3f} | {st.mean(e['fpr'] for e in ev):.3f} |")
        print(lines[-1], flush=True)
(ROOT / "results/pilot/committee.json").write_text(json.dumps(res), encoding="utf-8")
(ROOT / "results/pilot/committee.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
