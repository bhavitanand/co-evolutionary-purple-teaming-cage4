"""Why the testbed is easy: field profile of native benign vs attacker events on the 40 seen test episodes.
Writes results/pilot_baselines/field_profile.md (any python)."""
import collections
import glob
import gzip
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
ev = []
for f in sorted(glob.glob(str(ROOT / "results/pilot/test_events/*.json.gz"))):
    if "hit_and_run" in f or "plan_" in f:
        continue
    ev += [e for e in json.load(gzip.open(f, "rt", encoding="utf-8"))["events"] if e["provenance"] != "synthetic"]
b = [e for e in ev if e["label_red"] == 0]
a = [e for e in ev if e["label_red"] == 1]
bn = [e for e in b if e["category"] == "network_connection"]
an = [e for e in a if e["category"] == "network_connection"]
bp = [e for e in b if e["category"] == "process_creation"]
ap = [e for e in a if e["category"] == "process_creation"]
top = collections.Counter(e["dst_port"] for e in an).most_common(6)
L = ["# Field profile of native test events (40 seen episodes)", "",
     f"- native events: {len(ev)}; attacker {len(a)} ({len(a) / len(ev):.1%}); benign {len(b)}",
     f"- benign network events: {len(bn)}; with dst_port >= 1024: {sum(1 for e in bn if (e['dst_port'] or 0) >= 1024)}",
     f"- attacker network events: {len(an)}; top dst_ports: " + ", ".join(f"{p}: {n} ({n / len(an):.1%})" for p, n in top),
     f"- attacker network events to a well-known port (< 1024): {sum(1 for e in an if (e['dst_port'] or 0) < 1024)} ({sum(1 for e in an if (e['dst_port'] or 0) < 1024) / len(an):.1%})",
     f"- benign process events: {len(bp)}; with parent_process systemd: {sum(1 for e in bp if e['parent_process'] == 'systemd')}; with privilege elevated: {sum(1 for e in bp if e['privilege'] == 'elevated')}",
     f"- attacker process events: {len(ap)}; with a daemon parent (sshd, apache2, haraka, tomcat): {sum(1 for e in ap if e['parent_process'] in ('sshd', 'apache2', 'haraka', 'tomcat'))}; with parent systemd: {sum(1 for e in ap if e['parent_process'] == 'systemd')}",
     f"- share of attacker native events that are network events: {len(an) / len(a):.1%}",
     f"- native events by Red action: " + ", ".join(f"{k} {v}" for k, v in collections.Counter(e['source_action'] for e in a).most_common())]
(ROOT / "results/pilot_baselines/field_profile.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L))
