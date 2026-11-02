"""Which fields do the final rules constrain? Per condition (final rule sets, all runs): share of rules using dst_port, share using an
enriched field (protocol, service_name, process_name, parent_process, privilege), and share of network_connection rules that use dst_port.
Writes results/pilot_baselines/field_usage.md. Run with any python (no CAGE needed)."""
import json
import pathlib
import statistics as st

ROOT = pathlib.Path(__file__).resolve().parents[2]
ENRICHED = {"protocol", "service_name", "process_name", "parent_process", "privilege"}
SETS = [("LLM, fixed Red", "results/pilot/rules", "llm_fixed_red"), ("LLM, no feedback", "results/pilot/rules", "coevo_nofeedback"),
        ("LLM, co-evolved", "results/pilot/rules", "coevo"), ("Co-evolved, cap 20", "results/pilot_cap20/rules", "coevo")]


def fields(rule):
    out = set()
    for k, sel in rule["detection"].items():
        if k == "condition":
            continue
        for sel_ in (sel if isinstance(sel, list) else [sel]):
            if isinstance(sel_, dict):
                out |= {f.split("|")[0] for f in sel_}
    return out


rows = []
for label, d, cond in SETS:
    per = []
    for f in sorted((ROOT / d).glob(f"{cond}_seed*.json")):
        rules = [r for rs in json.loads(f.read_text(encoding="utf-8-sig"))["rules"].values() for r in rs]
        fs = [(r["logsource"].get("category"), fields(r)) for r in rules]
        net = [x for c, x in fs if c == "network_connection"]
        per.append((len(rules), st.mean("dst_port" in x for _, x in fs), st.mean(bool(x & ENRICHED) for _, x in fs),
                    st.mean(bool(x & ENRICHED) and "dst_port" not in x for _, x in fs), st.mean("dst_port" in x for x in net) if net else 0))
    m = lambda i: 100 * st.mean(p[i] for p in per)  # noqa: E731
    rows.append(f"| {label} | {len(per)} | {st.mean(p[0] for p in per):.1f} | {m(1):.0f} | {m(2):.0f} | {m(3):.0f} | {m(4):.0f} |")
out = ["# Fields used by the final LLM rules (mean over runs)", "",
       "Enriched fields: protocol, service_name, process_name, parent_process, privilege (filled in by a seeded rule where the simulator lacks them).", "",
       "| set | runs | rules per run | % rules using dst_port | % using an enriched field | % using an enriched field and no dst_port | % of network_connection rules using dst_port |",
       "|---|---|---|---|---|---|---|", *rows]
(ROOT / "results/pilot_baselines/field_usage.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out))
